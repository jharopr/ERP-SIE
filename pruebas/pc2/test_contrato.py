"""Regresión de decisiones, controles y persistencia del contrato PC2."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from simulador import FIXTURES, TransitionSimulator, load_json, valid_request


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.masters = load_json(FIXTURES / "maestros.json")
        self.request = load_json(FIXTURES / "solicitud-normal.json")
        self.sim = TransitionSimulator(self.masters)

    def tearDown(self):
        self.sim.close()

    def count(self):
        return self.sim.db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]

    def test_normal_validates_without_operational_side_effects(self):
        before = deepcopy(self.sim.masters)
        result = self.sim.submit(self.request)
        self.assertEqual((result["status"], result["code"], result["total"]), ("ACEPTADA", "VALIDADA", "1900.00"))
        self.assertIsNone(result["order_id"])
        self.assertEqual(before, self.sim.masters)
        self.assertEqual(self.count(), 1)

    def test_unapproved_discount_rejects_and_escalates(self):
        result = self.sim.submit(load_json(FIXTURES / "solicitud-excepcion.json"))
        self.assertEqual((result["status"], result["code"], result["responsible_role"]),
                         ("RECHAZADA", "DESCUENTO_SIN_APROBACION", "GERENCIA"))
        self.assertEqual(self.sim.db.execute("SELECT COUNT(*) FROM audit WHERE interface_id='I05'").fetchone()[0], 0)

    def test_partial_availability_is_not_an_accepted_order(self):
        self.sim.masters["availability"]["quantities"]["AUT-DEMO-001"] = 3
        result = self.sim.submit(self.request)
        self.assertEqual(result["status"], "PROMESA_CONDICIONADA")
        self.assertEqual(result["conditions"][0]["available_quantity"], 3)
        self.assertIsNone(result["conditions"][0]["promised_date"])
        self.assertTrue(result["conditions"][0]["requires_customer_acceptance"])
        self.assertIsNone(result["order_id"])

    def test_crm_receives_one_follow_up_per_decision_and_replay_is_stable(self):
        request = load_json(FIXTURES / "solicitud-excepcion.json")
        response = self.sim.submit(request)
        feedback = self.sim.get_crm_feedback("MYS-DEMO", request["request_id"])
        self.assertEqual(feedback["response_id"], response["response_id"])
        self.assertEqual(feedback["follow_up_state"], "PENDIENTE_APROBACION")
        self.assertEqual(feedback["responsible_role"], "GERENCIA")
        self.assertEqual(feedback["attention_due_at"], "2026-10-16T18:00:00-05:00")
        self.assertFalse(feedback["opportunity_lost"])
        self.sim.submit(request)
        self.assertEqual(feedback, self.sim.get_crm_feedback("MYS-DEMO", request["request_id"]))
        self.assertEqual(self.sim.db.execute("SELECT COUNT(*) FROM crm_feedback").fetchone()[0], 1)
        self.assertEqual(self.sim.db.execute("SELECT COUNT(*) FROM audit WHERE interface_id='I08'").fetchone()[0], 1)
        with self.assertRaises(PermissionError):
            self.sim.get_crm_feedback("MYS-DEMO", request["request_id"], "VEN-DEMO-02")

    def test_resume_updates_crm_without_duplicate_tasks(self):
        self.sim.masters["availability"]["available"] = False
        self.sim.submit(self.request)
        self.assertEqual(self.sim.get_crm_feedback("MYS-DEMO", self.request["request_id"])["follow_up_state"], "RECUPERAR_SERVICIO")
        self.sim.masters["availability"]["available"] = True
        result = self.sim.submit(self.request, resume=True)
        feedback = self.sim.get_crm_feedback("MYS-DEMO", self.request["request_id"])
        self.assertEqual((feedback["status"], feedback["follow_up_state"]), ("ACEPTADA", "SIN_TAREA"))
        self.assertIsNone(feedback["attention_due_at"])
        self.assertEqual(feedback["order_state"], "NO_CONFIRMADO")
        self.assertEqual(feedback["response_id"], result["response_id"])
        self.assertEqual(self.sim.db.execute("SELECT COUNT(*) FROM crm_feedback").fetchone()[0], 1)

    def test_feedback_failure_rolls_back_decision_and_audit(self):
        def fail(*args):
            raise RuntimeError("No se pudo actualizar CRM")
        self.sim._publish_feedback = fail
        with self.assertRaises(RuntimeError):
            self.sim.submit(self.request)
        for name in ["requests", "crm_feedback", "audit"]:
            self.assertEqual(self.sim.db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0], 0)

    def test_missing_or_expired_channel_evidence_blocks_contact(self):
        for consent in [{}, {**self.masters["customers"]["CLI-DEMO-001"]["consent"], "valid_until": "2026-10-14T12:00:00-05:00"},
                        {**self.masters["customers"]["CLI-DEMO-001"]["consent"], "purpose": "MARKETING_MASIVO"}]:
            with self.subTest(consent=consent):
                sim = TransitionSimulator(self.masters)
                try:
                    sim.masters["customers"]["CLI-DEMO-001"]["consent"] = consent
                    self.assertEqual(sim.submit(self.request)["code"], "CONTACTO_NO_AUTORIZADO")
                finally:
                    sim.close()

    def test_unknown_payment_or_delivery_terms_cannot_be_accepted(self):
        for change in [{"payment_terms": "CREDITO_NO_VALIDADO"}, {"delivery": {}},
                       {"delivery": {**self.masters["quotations"]["COT-DEMO-001"]["delivery"], "location_id": "OTRO-ALMACEN"}}]:
            with self.subTest(change=change):
                sim = TransitionSimulator(self.masters)
                try:
                    sim.masters["quotations"]["COT-DEMO-001"].update(change)
                    self.assertEqual(sim.submit(self.request)["code"], "CONDICIONES_POR_VALIDAR")
                finally:
                    sim.close()

    def test_partial_promise_includes_quantity_gap_and_requested_delivery(self):
        self.sim.masters["availability"]["quantities"]["AUT-DEMO-001"] = 3
        result = self.sim.submit(self.request)
        condition = result["conditions"][0]
        self.assertEqual(condition["pending_quantity"], 2)
        self.assertEqual(condition["delivery_mode"], "RECOJO_LOCAL")
        self.assertEqual(condition["requested_date"], "2026-10-16T18:00:00-05:00")
        self.assertIsNone(condition["promised_date"])
        self.assertEqual(result["follow_up_state"], "NEGOCIAR_PROMESA")

    def test_same_key_replays_persisted_result_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.sqlite3"
            sim = TransitionSimulator(self.masters, database)
            expected = sim.submit(self.request)
            sim.close()
            sim = TransitionSimulator(self.masters, database)
            try:
                sim.masters["availability"]["quantities"]["AUT-DEMO-001"] = 0
                self.assertEqual(expected, sim.submit(self.request))
                self.assertEqual(sim.db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 1)
            finally:
                sim.close()

    def test_same_key_different_payload_does_not_overwrite_original(self):
        first = self.sim.submit(self.request)
        changed = deepcopy(self.request)
        changed["correlation_id"] = "OTRA-CORRELACION"
        self.assertEqual(self.sim.submit(changed)["code"], "IDEMPOTENCIA_CONFLICTO")
        self.assertEqual(self.sim.get("MYS-DEMO", self.request["request_id"]), first)

    def test_new_key_cannot_duplicate_quotation_version(self):
        self.sim.submit(self.request)
        changed = deepcopy(self.request)
        changed["request_id"] = "SOL-OTRA"
        self.assertEqual(self.sim.submit(changed)["code"], "COTIZACION_YA_EVALUADA")
        self.assertEqual(self.count(), 1)

    def test_json_schema_integer_numeric_representation_is_normalized(self):
        first = self.sim.submit(self.request)
        self.request["quotation_version"] = 1.0
        self.assertTrue(valid_request(self.request))
        self.assertEqual(self.sim.submit(self.request), first)

    def test_forbidden_roles_and_scope_cannot_submit_or_replay(self):
        self.sim.submit(self.request)
        for actor in ["ALM-DEMO-01", "GER-DEMO-01", "VEN-DEMO-02", "DESCONOCIDO"]:
            with self.subTest(actor=actor):
                self.assertEqual(self.sim.submit(self.request, actor)["code"], "NO_AUTORIZADO")
                with self.assertRaises(PermissionError):
                    self.sim.get("MYS-DEMO", self.request["request_id"], actor)
        self.assertEqual(self.count(), 1)

    def test_payload_cannot_self_authorize_or_supply_prices(self):
        for field in ["actor_role", "approved", "unit_price", "stock"]:
            changed = deepcopy(self.request)
            changed[field] = "INJECTED"
            with self.subTest(field=field):
                self.assertEqual(self.sim.submit(changed)["code"], "CONTRATO_INVALIDO")
        self.assertEqual(self.count(), 0)

    def test_required_fields_types_and_unknown_version(self):
        invalid = []
        for key in self.request:
            value = deepcopy(self.request)
            del value[key]
            invalid.append(value)
        for version in [True, 0, -1, 1.5, "1", None]:
            invalid.append({**self.request, "quotation_version": version})
        invalid.extend([[], None, {**self.request, "contract_version": "2.0"},
                        {**self.request, "request_id": "x" * 65}, {**self.request, "request_id": "a b"}])
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertFalse(valid_request(payload))
                self.assertEqual(self.sim.submit(payload)["code"], "CONTRATO_INVALIDO")
        self.assertEqual(self.count(), 0)

    def test_foreign_company_is_denied_before_any_cache_access(self):
        self.request["company_id"] = "OTRA-EMPRESA"
        self.assertEqual(self.sim.submit(self.request)["code"], "NO_AUTORIZADO")
        self.assertEqual(self.count(), 0)

    def test_customer_identity_ambiguity_blocks_transition(self):
        self.sim.masters["customers"]["CLI-DEMO-001"]["identity_reviewed"] = False
        self.assertEqual(self.sim.submit(self.request)["code"], "CLIENTE_NO_VALIDADO")

    def test_wrong_customer_or_opportunity_link_is_rejected(self):
        self.sim.masters["quotations"]["COT-DEMO-001"]["customer_id"] = "OTRO-CLIENTE"
        self.assertEqual(self.sim.submit(self.request)["code"], "DATOS_INCONSISTENTES")

    def test_stale_version_is_rejected(self):
        self.sim.masters["quotations"]["COT-DEMO-001"]["version"] = 2
        self.assertEqual(self.sim.submit(self.request)["code"], "VERSION_OBSOLETA")

    def test_expired_quotation_is_rejected(self):
        self.sim.masters["quotations"]["COT-DEMO-001"]["valid_until"] = "2026-10-14T23:59:59-05:00"
        self.assertEqual(self.sim.submit(self.request)["code"], "COTIZACION_VENCIDA")

    def test_draft_quotation_is_rejected(self):
        self.sim.masters["quotations"]["COT-DEMO-001"]["state"] = "draft"
        self.assertEqual(self.sim.submit(self.request)["code"], "COTIZACION_NO_ENVIADA")

    def test_acceptance_must_match_version_and_total(self):
        self.sim.masters["acceptances"]["ACE-DEMO-001"]["total"] = "1800.00"
        self.assertEqual(self.sim.submit(self.request)["code"], "ACEPTACION_INVALIDA")

    def test_price_tampering_is_rejected_even_if_acceptance_matches(self):
        self.sim.masters["quotations"]["COT-DEMO-001"]["lines"][0]["unit_price"] = "1.00"
        self.sim.masters["quotations"]["COT-DEMO-001"]["total"] = "4.75"
        self.sim.masters["acceptances"]["ACE-DEMO-001"]["total"] = "4.75"
        self.assertEqual(self.sim.submit(self.request)["code"], "PRECIO_INVALIDO")

    def test_approval_has_to_be_by_independent_manager_and_current_version(self):
        request = load_json(FIXTURES / "solicitud-excepcion.json")
        base = {"company_id": "MYS-DEMO", "quotation_id": "COT-DEMO-002", "quotation_version": 1,
                "total": "1800.00", "status": "APROBADA", "approver_id": "GER-DEMO-01",
                "approved_at": "2026-10-15T17:30:00-05:00", "valid_until": "2026-10-16T23:59:59-05:00"}
        for change in [{"approver_id": "VEN-DEMO-01"}, {"quotation_version": 2},
                       {"total": "1900.00"}, {"valid_until": "2026-10-14T23:59:59-05:00"}]:
            sim = TransitionSimulator(self.masters)
            try:
                sim.masters["approvals"] = [{**base, **change}]
                self.assertEqual(sim.submit(request)["code"], "DESCUENTO_SIN_APROBACION")
            finally:
                sim.close()
        self.sim.masters["approvals"] = [base]
        self.assertEqual(self.sim.submit(request)["status"], "ACEPTADA")

    def test_dependency_failure_remains_pending_until_explicit_resume(self):
        self.sim.masters["availability"]["available"] = False
        pending = self.sim.submit(self.request)
        self.assertEqual(pending["status"], "PENDIENTE")
        self.sim.masters["availability"]["available"] = True
        self.assertEqual(self.sim.submit(self.request), pending)
        self.assertEqual(self.sim.submit(self.request, resume=True)["status"], "ACEPTADA")
        self.assertEqual(self.count(), 1)

    def test_resume_rechecks_current_version(self):
        self.sim.masters["availability"]["available"] = False
        self.sim.submit(self.request)
        self.sim.masters["availability"]["available"] = True
        self.sim.masters["quotations"]["COT-DEMO-001"]["version"] = 2
        self.assertEqual(self.sim.submit(self.request, resume=True)["code"], "VERSION_OBSOLETA")

    def test_same_sku_lines_are_aggregated_for_availability(self):
        quote = self.sim.masters["quotations"]["COT-DEMO-001"]
        quote["lines"] = [{**quote["lines"][0], "quantity": 3}, {**quote["lines"][0], "quantity": 2}]
        self.sim.masters["availability"]["quantities"]["AUT-DEMO-001"] = 4
        result = self.sim.submit(self.request)
        self.assertEqual(result["status"], "PROMESA_CONDICIONADA")
        self.assertEqual(result["conditions"][0]["requested_quantity"], 5)

    def test_failure_during_decision_rolls_back_request_and_events(self):
        def fail(*args):
            raise RuntimeError("Falla técnica simulada antes del commit")
        original = self.sim._evaluate
        self.sim._evaluate = fail
        with self.assertRaises(RuntimeError):
            self.sim.submit(self.request)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.sim.db.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 0)
        self.sim._evaluate = original
        self.assertEqual(self.sim.submit(self.request)["status"], "ACEPTADA")

    def test_parallel_retries_have_one_persistent_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "parallel.sqlite3"
            sim = TransitionSimulator(self.masters, database)
            sim.close()
            def submit(_):
                worker = TransitionSimulator(self.masters, database)
                try:
                    return worker.submit(self.request)
                finally:
                    worker.close()
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(submit, range(8)))
            self.assertTrue(all(result == results[0] for result in results))
            sim = TransitionSimulator(self.masters, database)
            try:
                self.assertEqual(sim.db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 1)
            finally:
                sim.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
