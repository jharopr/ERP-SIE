"""Simulación local de I03-I08. No importa Odoo ni ejecuta pedidos reales.

Solo biblioteca estándar. Los proveedores de maestros son fixtures confiables,
separadas del payload de la solicitud. La validación de entrada sigue el schema;
los tests opcionales con jsonschema verifican además los schemas completos.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "arquitectura/contratos/solicitud-pedido-v1.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CENT = Decimal("0.01")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def valid_request(payload):
    """Aplica las restricciones exactas del schema de entrada sin dependencias."""
    schema = load_json(SCHEMA_PATH)
    if not isinstance(payload, dict) or set(payload) != set(schema["required"]):
        return False
    for key, spec in schema["properties"].items():
        value = payload[key]
        if "$ref" in spec:
            rule = schema["$defs"]["identifier"]
            if (not isinstance(value, str) or not rule["minLength"] <= len(value) <= rule["maxLength"]
                    or re.fullmatch(rule["pattern"], value) is None):
                return False
        elif "const" in spec:
            if value != spec["const"]:
                return False
        else:
            integer = type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer())
            if not integer or value < spec["minimum"]:
                return False
    return True


class TransitionSimulator:
    def __init__(self, masters, database=":memory:"):
        self.masters = deepcopy(masters)
        self.now = datetime.fromisoformat(self.masters["business_time"])
        if self.now.tzinfo is None:
            raise ValueError("business_time debe incluir zona horaria")
        self.db = sqlite3.connect(str(database), timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS requests (
                company_id TEXT NOT NULL, request_id TEXT NOT NULL,
                payload_hash TEXT NOT NULL, quotation_id TEXT NOT NULL,
                quotation_version INTEGER NOT NULL, opportunity_id TEXT NOT NULL,
                response_json TEXT NOT NULL,
                PRIMARY KEY (company_id, request_id),
                UNIQUE (company_id, quotation_id, quotation_version)
            );
            CREATE TABLE IF NOT EXISTS audit (
                event_id INTEGER PRIMARY KEY, company_id TEXT, request_id TEXT, correlation_id TEXT,
                actor_id TEXT NOT NULL, interface_id TEXT NOT NULL,
                event_type TEXT NOT NULL, code TEXT NOT NULL, occurred_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS crm_feedback (
                company_id TEXT NOT NULL, request_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL, projection_json TEXT NOT NULL,
                PRIMARY KEY (company_id, request_id)
            );
        """)

    def close(self):
        self.db.close()

    def _event(self, request, actor, interface, event, code):
        data = request if isinstance(request, dict) else {}
        # Formatos inválidos no se copian a la bitácora, ni siquiera como referencias.
        safe_id = lambda key: data.get(key) if isinstance(data.get(key), str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", data[key]) else None
        self.db.execute("INSERT INTO audit(company_id,request_id,correlation_id,actor_id,interface_id,event_type,code,occurred_at) VALUES(?,?,?,?,?,?,?,?)",
                        (safe_id("company_id"), safe_id("request_id"), safe_id("correlation_id"), actor, interface, event, code, self.now.isoformat()))

    def _response(self, request, code, message, action, role="VENTAS", status="RECHAZADA", total=None, conditions=None):
        data = request if valid_request(request) else {}
        follow_up = {"VALIDADA": "SIN_TAREA", "DESCUENTO_SIN_APROBACION": "PENDIENTE_APROBACION",
                     "DISPONIBILIDAD_PARCIAL": "NEGOCIAR_PROMESA", "DEPENDENCIA_NO_DISPONIBLE": "RECUPERAR_SERVICIO",
                     "NO_AUTORIZADO": "REVISAR_ACCESO", "IDEMPOTENCIA_CONFLICTO": "CONSULTAR_ORIGINAL",
                     "COTIZACION_YA_EVALUADA": "CONSULTAR_ORIGINAL"}.get(code, "CORREGIR_DATOS")
        response_id = "RESP-" + hashlib.sha256(canonical([data.get("company_id"), data.get("request_id"), status, code]).encode()).hexdigest()[:20] if data else None
        return {"contract_version": "1.1", "request_id": data.get("request_id"),
                "response_id": response_id,
                "correlation_id": data.get("correlation_id"), "quotation_id": data.get("quotation_id"),
                "quotation_version": int(data["quotation_version"]) if data else None, "status": status, "code": code,
                "message": message, "responsible_role": role, "required_action": action,
                "total": total, "currency": "PEN" if total is not None else None,
                "order_id": None, "order_state": "NO_CONFIRMADO", "conditions": conditions or [],
                "follow_up_state": follow_up,
                "attention_due_at": None if status == "ACEPTADA" else (self.now + timedelta(hours=24)).isoformat()}

    def _authorized(self, request, actor):
        user = self.masters["actors"].get(actor, {})
        return (user.get("role") == "VENTAS" and user.get("company_id") == request["company_id"]
                and request["opportunity_id"] in user.get("opportunities", []))

    def submit(self, request, actor="VEN-DEMO-01", resume=False):
        """Persistencia atómica; resume solo reevalúa una solicitud PENDIENTE."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if not valid_request(request):
                self._event({}, actor, "I07", "DENEGADA", "CONTRATO_INVALIDO")
                result = self._response(request, "CONTRATO_INVALIDO", "Formato de solicitud inválido.", "Corregir el mensaje según el schema 1.1.")
            elif not self._authorized(request, actor):
                self._event(request, actor, "I07", "DENEGADA", "NO_AUTORIZADO")
                result = self._response(request, "NO_AUTORIZADO", "Sin permiso sobre compañía u oportunidad.", "Solicitar revisión de acceso; no cambiar el rol del payload.")
            else:
                result = self._submit_authorized(request, actor, resume)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    def _submit_authorized(self, request, actor, resume):
        normalized = {**request, "quotation_version": int(request["quotation_version"])}
        digest = hashlib.sha256(canonical(normalized).encode("utf-8")).hexdigest()
        key = (request["company_id"], request["request_id"])
        existing = self.db.execute("SELECT * FROM requests WHERE company_id=? AND request_id=?", key).fetchone()
        if existing:
            if existing["payload_hash"] != digest:
                self._event(request, actor, "I03", "CONFLICTO", "IDEMPOTENCIA_CONFLICTO")
                return self._response(request, "IDEMPOTENCIA_CONFLICTO", "Clave usada con otro payload.", "Consultar la solicitud original; no sobrescribirla.")
            previous = json.loads(existing["response_json"])
            if previous["status"] != "PENDIENTE" or not resume:
                self._event(request, actor, "I03", "REINTENTO", previous["code"])
                return previous
            self._event(request, actor, "I03", "REANUDADA", "RECIBIDA")
        else:
            duplicate = self.db.execute("SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=?",
                                        (request["company_id"], request["quotation_id"], request["quotation_version"])).fetchone()
            if duplicate:
                self._event(request, actor, "I03", "CONFLICTO", "COTIZACION_YA_EVALUADA")
                return self._response(request, "COTIZACION_YA_EVALUADA", "La versión ya tiene una solicitud.", "Consultar la solicitud original autorizada.")
            self._event(request, actor, "I03", "RECIBIDA", "RECIBIDA")

        result = self._evaluate(request, actor)
        self._event(request, actor, "I07", "DECISION", result["code"])
        if existing:
            self.db.execute("UPDATE requests SET response_json=? WHERE company_id=? AND request_id=?", (canonical(result), *key))
        else:
            self.db.execute("INSERT INTO requests VALUES(?,?,?,?,?,?,?)", (*key, digest, request["quotation_id"], request["quotation_version"], request["opportunity_id"], canonical(result)))
        self._publish_feedback(request, result, actor)
        return result

    def _publish_feedback(self, request, response, actor):
        """I08: proyección CRM atómica con decisión y bitácora; no cierra la oportunidad."""
        projection = {"opportunity_id": request["opportunity_id"], "quotation_id": request["quotation_id"],
                      "quotation_version": request["quotation_version"], "response_id": response["response_id"],
                      "status": response["status"], "code": response["code"],
                      "responsible_role": response["responsible_role"], "required_action": response["required_action"],
                      "follow_up_state": response["follow_up_state"], "attention_due_at": response["attention_due_at"],
                      "conditions": response["conditions"], "order_id": response["order_id"],
                      "order_state": response["order_state"], "opportunity_lost": False, "updated_at": self.now.isoformat()}
        self.db.execute("INSERT INTO crm_feedback VALUES(?,?,?,?) ON CONFLICT(company_id,request_id) DO UPDATE SET projection_json=excluded.projection_json",
                        (request["company_id"], request["request_id"], request["opportunity_id"], canonical(projection)))
        self._event(request, actor, "I08", "CRM_ACTUALIZADO", response["code"])

    def _evaluate(self, request, actor):
        fail = lambda code, msg, action="Corregir datos, versionar y obtener nueva aceptación.", role="VENTAS": self._response(request, code, msg, action, role)
        company = request["company_id"]
        customer = self.masters["customers"].get(request["customer_id"], {})
        opportunity = self.masters["opportunities"].get(request["opportunity_id"], {})
        quote = self.masters["quotations"].get(request["quotation_id"], {})
        self._event(request, actor, "I04", "CONSULTA", "SNAPSHOT_COMERCIAL")
        if (not all(obj.get("company_id") == company for obj in (customer, opportunity, quote))
                or opportunity.get("type") != "opportunity"
                or opportunity.get("customer_id") != request["customer_id"]
                or quote.get("customer_id") != request["customer_id"]
                or quote.get("opportunity_id") != request["opportunity_id"]
                or quote.get("seller_id") != actor):
            return fail("DATOS_INCONSISTENTES", "Maestros, compañía, vendedor o vínculos no coinciden.")
        if not customer.get("active") or not customer.get("identity_reviewed"):
            return fail("CLIENTE_NO_VALIDADO", "Cliente inactivo o coincidencia sin revisar.")
        consent = customer.get("consent", {})
        if (consent.get("purpose") != "ATENDER_COTIZACION" or consent.get("channel") != opportunity.get("channel")
                or not consent.get("evidence_ref") or not consent.get("valid_until")):
            return fail("CONTACTO_NO_AUTORIZADO", "Falta evidencia vigente para atender por el canal declarado.")
        try:
            consent_until = datetime.fromisoformat(consent["valid_until"])
            if consent_until.tzinfo is None or consent_until < self.now:
                raise ValueError("Evidencia vencida")
        except (ValueError, TypeError):
            return fail("CONTACTO_NO_AUTORIZADO", "La evidencia del canal no tiene vigencia válida.")
        delivery = quote.get("delivery", {})
        try:
            requested_at = datetime.fromisoformat(delivery["requested_date"])
            if (quote.get("payment_terms") != "CONTADO" or delivery.get("mode") != "RECOJO_LOCAL"
                    or delivery.get("location_id") != self.masters["availability"].get("location_id")
                    or not delivery.get("location_id") or type(delivery.get("partial_delivery_accepted")) is not bool
                    or requested_at.tzinfo is None or requested_at < self.now):
                raise ValueError("Condiciones sin validar")
        except (KeyError, ValueError, TypeError):
            return fail("CONDICIONES_POR_VALIDAR", "Revisar pago al contado, lugar, modalidad y fecha solicitada; no se autoriza crédito.")
        if quote["version"] != request["quotation_version"]:
            return fail("VERSION_OBSOLETA", "La versión solicitada no es la vigente.")
        if quote["state"] != "sent":
            return fail("COTIZACION_NO_ENVIADA", "La cotización no está en estado enviado.")
        valid_until = datetime.fromisoformat(quote["valid_until"])
        if self.now > valid_until:
            return fail("COTIZACION_VENCIDA", "La vigencia comercial terminó.")
        acceptance = self.masters["acceptances"].get(request["acceptance_id"], {})
        expected = {"company_id": company, "quotation_id": request["quotation_id"],
                    "quotation_version": request["quotation_version"], "customer_id": request["customer_id"], "total": quote["total"]}
        if any(acceptance.get(key) != value for key, value in expected.items()):
            return fail("ACEPTACION_INVALIDA", "La aceptación no corresponde al snapshot cotizado.")
        accepted_at = datetime.fromisoformat(acceptance["accepted_at"])
        if accepted_at > self.now or accepted_at > valid_until:
            return fail("ACEPTACION_INVALIDA", "La aceptación no tiene una fecha válida.")

        total = Decimal("0.00")
        max_discount = Decimal("0.00")
        quantities = {}
        try:
            if quote["currency"] != "PEN" or not quote["lines"]:
                raise ValueError("Moneda o líneas inválidas")
            for line in quote["lines"]:
                product = self.masters["products"].get(line["sku"], {})
                price, discount = Decimal(line["unit_price"]), Decimal(line["discount_pct"])
                quantity = line["quantity"]
                if (not product.get("active") or product.get("company_id") != company
                        or product.get("currency") != quote["currency"]
                        or not price.is_finite() or price <= 0 or price != Decimal(product["unit_price"])
                        or not discount.is_finite() or not Decimal("0") <= discount <= Decimal("100")
                        or type(quantity) is not int or quantity < 1):
                    raise ValueError("Línea no válida")
                total += (price * quantity * (1 - discount / 100)).quantize(CENT, rounding=ROUND_HALF_UP)
                max_discount = max(max_discount, discount)
                quantities[line["sku"]] = quantities.get(line["sku"], 0) + quantity
            if total != Decimal(quote["total"]):
                raise ValueError("Total no coincide")
        except (KeyError, InvalidOperation, ValueError, TypeError):
            return fail("PRECIO_INVALIDO", "Precio, producto, cantidad, descuento o total no coincide con el catálogo.")

        total_text = format(total, ".2f")
        self._event(request, actor, "I06", "CONSULTA", "POLITICA_DESCUENTO")
        if max_discount > Decimal(self.masters["policy"]["max_seller_discount"]):
            approved = False
            for approval in self.masters["approvals"]:
                approver = self.masters["actors"].get(approval.get("approver_id"), {})
                if (approval.get("company_id") == company and approval.get("quotation_id") == request["quotation_id"]
                        and approval.get("quotation_version") == request["quotation_version"]
                        and approval.get("total") == total_text and approval.get("status") == "APROBADA"
                        and approval.get("approver_id") != quote["seller_id"]
                        and approver.get("role") == "GERENCIA" and approver.get("company_id") == company
                        and datetime.fromisoformat(approval["approved_at"]) <= self.now <= datetime.fromisoformat(approval["valid_until"])):
                    approved = True
                    break
            if not approved:
                return fail("DESCUENTO_SIN_APROBACION", "El descuento supera el 5 % y no tiene aprobación válida.",
                            "Gerencia debe decidir; después preparar nueva versión y aceptación.", "GERENCIA")

        stock = self.masters["availability"]
        self._event(request, actor, "I05", "CONSULTA", "DISPONIBILIDAD")
        if not stock.get("available") or stock.get("company_id") != company:
            return self._response(request, "DEPENDENCIA_NO_DISPONIBLE", "No hay lectura confiable de disponibilidad.",
                                  "Recuperar dependencia y reanudar la misma solicitud.", "ADMINISTRADOR_Y_VENTAS", "PENDIENTE", total_text)
        conditions = []
        for sku, quantity in quantities.items():
            available = stock["quantities"].get(sku)
            if type(available) is not int or available < 0:
                return self._response(request, "DEPENDENCIA_NO_DISPONIBLE", "Lectura de stock incompleta o inválida.",
                                      "Corregir proveedor y reanudar la misma solicitud.", "ADMINISTRADOR_Y_VENTAS", "PENDIENTE", total_text)
            if available < quantity:
                conditions.append({"sku": sku, "requested_quantity": quantity, "available_quantity": available,
                                   "pending_quantity": quantity - available, "delivery_mode": delivery["mode"],
                                   "location_id": delivery["location_id"], "requested_date": delivery["requested_date"],
                                   "promised_date": None, "requires_customer_acceptance": True})
        if conditions:
            return self._response(request, "DISPONIBILIDAD_PARCIAL", "Disponibilidad insuficiente para lo cotizado.",
                                  "Revisar cantidad/plazo con el cliente; nueva versión y aceptación.", "VENTAS", "PROMESA_CONDICIONADA", total_text, conditions)
        return self._response(request, "VALIDADA", "Solicitud validada; confirmación operativa pendiente.",
                              "Informar resultado; revalidar al confirmar operativamente en otro incremento.", "VENTAS", "ACEPTADA", total_text)

    def get(self, company, request_id, actor="VEN-DEMO-01"):
        row = self.db.execute("SELECT * FROM requests WHERE company_id=? AND request_id=?", (company, request_id)).fetchone()
        if row is None:
            return None
        if not self._authorized({"company_id": company, "opportunity_id": row["opportunity_id"]}, actor):
            raise PermissionError("Sin acceso al resultado de la solicitud")
        return json.loads(row["response_json"])

    def get_crm_feedback(self, company, request_id, actor="VEN-DEMO-01"):
        # Reutiliza la misma comprobación de ámbito antes de exponer el seguimiento.
        if self.get(company, request_id, actor) is None:
            return None
        row = self.db.execute("SELECT projection_json FROM crm_feedback WHERE company_id=? AND request_id=?",
                              (company, request_id)).fetchone()
        return json.loads(row[0]) if row else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON de solicitud")
    parser.add_argument("--masters", type=Path, default=FIXTURES / "maestros.json")
    parser.add_argument("--database", default=":memory:", help="SQLite local; por defecto efímera")
    parser.add_argument("--actor", default="VEN-DEMO-01", help="Identidad de prueba, fuera del payload")
    parser.add_argument("--resume", action="store_true", help="Reevaluar solo si está PENDIENTE")
    args = parser.parse_args()
    simulator = TransitionSimulator(load_json(args.masters), args.database)
    try:
        print(json.dumps(simulator.submit(load_json(args.request), args.actor, args.resume), ensure_ascii=False, indent=2))
    finally:
        simulator.close()


if __name__ == "__main__":
    main()
