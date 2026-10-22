"""Evidencia sintética del EP: frontera CRM-ERP, sin operaciones O2C posteriores.

Solo biblioteca estándar. Reutiliza sin modificar el simulador PC2 mediante
importlib; las expectativas proceden de un fixture independiente del resultado.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"
OUT = HERE / "evidencias"
SIMULATOR = ROOT / "pruebas/pc2/simulador.py"
ACTOR = "VEN-DEMO-01"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_simulator():
    spec = importlib.util.spec_from_file_location("ep_simulador_pc2", SIMULATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_masters(base, variant):
    masters = deepcopy(base)
    if variant == "stock_parcial":
        masters["availability"]["quantities"]["RAD-7BT"] = 3
    elif variant == "descuento_excepcional":
        quote = masters["quotations"]["COT-DEMO-001"]
        quote.update(version=2, total="1800.00")
        quote["lines"][0]["discount_pct"] = "10.00"
        masters["acceptances"] = {
            "ACE-EP-002": {
                "company_id": "MYS-DEMO", "quotation_id": "COT-DEMO-001",
                "quotation_version": 2, "customer_id": "CLI-DEMO-001",
                "total": "1800.00", "accepted_at": "2026-10-24T09:54:30-05:00",
                "notice": "Aceptación sintética de v2 para aislar el control de descuento. No autoriza a Gerencia ni acredita oferta empresarial aprobada."
            }
        }
    elif variant != "normal":
        raise ValueError(f"Variante desconocida: {variant}")
    return masters


def timeline(case, masters):
    request = case["request"]
    version = request["quotation_version"]
    quote = masters["quotations"][request["quotation_id"]]
    rows = [
        ("09:45:00", "Cliente / Ventas", "CLI-DEMO-001", "Consulta presencial y búsqueda de coincidencias", "Datos mínimos; identidad y segmentación sintéticas"),
        ("09:46:00", "Ventas", "LEAD-EP-001", "Registra necesidad de cinco autoradios para uso familiar", "Origen físico y visita espontánea; sin campaña"),
        ("09:48:00", "Ventas", "OPP-DEMO-001", "Califica y vincula la oportunidad", "Relación con lead y cliente único"),
        ("09:50:00", "Ventas / Inventario (lectura)", "RAD-7BT", f"Consulta disponibilidad sintética en TIENDA-DEMO: {masters['availability']['quantities']['RAD-7BT']} unidades", "Cada caso es independiente; consulta sin reserva ni fecha prometida"),
        ("09:52:00", "Ventas", "COT-DEMO-001 v1", "Prepara oferta de S/ 1900.00", "Cinco por S/ 400.00, descuento 5%; vence a las 18:00"),
    ]
    if version == 2:
        rows.append(("09:53:00", "Cliente / Ventas", "COT-DEMO-001 v2", "Solicita 10% y registra alternativa sintética por S/ 1800.00", "Sin aprobación del dueño; no se considera oferta autorizada"))
    accepted = masters["acceptances"][request["acceptance_id"]]
    rows.append((accepted["accepted_at"][11:19], "Cliente sintético", request["acceptance_id"],
                 f"Acepta sintéticamente COT-DEMO-001 v{version}",
                 "Misma versión, cliente e importe; no sustituye la autorización comercial"))
    rows.extend([
        ("09:55:00", "Ventas / Simulador", request["request_id"], "Somete solicitud al contrato 1.0", "Identidad de prueba fuera del mensaje; referencias correlacionadas"),
        ("09:55:01", "Simulador", request["request_id"], "Registra respuesta de evaluación", "Recepción y decisión auditadas en la misma transacción lógica; no confirma pedido ni reserva"),
        ("09:56:01", "Ventas / Simulador", request["request_id"], "Repite exactamente la misma solicitud", "Recupera respuesta original; una sola solicitud persistida")
    ])
    return {
        "kind": "LINEA_DE_TIEMPO_DIDACTICA_NO_OBSERVACION_EMPRESARIAL",
        "notice": "Eventos previos al envío son narrativa sintética. Solo audit contiene eventos realmente ejecutados por el simulador: recepción, consultas y decisión comparten la transacción lógica 09:55:01; el reintento se audita 09:56:01. No son tiempos de desempeño medidos.",
        "valid_until": quote["valid_until"],
        "events": [{"logical_time": f"2026-10-24T{time}-05:00", "actor": actor, "object": obj,
                    "event": event, "control": control, "correlation_id": "COR-EP-001"}
                   for time, actor, obj, event, control in rows]
    }


def conceptual_signal(case, response, masters):
    if case["case_id"] != "EP-S01" or response["status"] != "PROMESA_CONDICIONADA":
        return None
    condition = response["conditions"][0]
    return {
        "signal_id": "REP-EP-001", "source_case": case["case_id"],
        "correlation_id": response["correlation_id"], "request_id": response["request_id"],
        "opportunity_id": case["request"]["opportunity_id"],
        "quotation_id": response["quotation_id"], "quotation_version": response["quotation_version"],
        "sku": condition["sku"], "location_id": masters["availability"]["location_id"],
        "requested_quantity": condition["requested_quantity"],
        "available_quantity": condition["available_quantity"],
        "shortfall_quantity": condition["requested_quantity"] - condition["available_quantity"],
        "observed_at": masters["availability"]["observed_at"],
        "source_snapshot_ref": f"pruebas/ep-benjamin/evidencias/{case['case_id']}-entrada.json",
        "responsible_role": "DUENO_ABASTECIMIENTO",
        "kind": "SENAL_CONCEPTUAL_EVALUACION_P2P", "purchase_order_id": None,
        "reservation_id": None, "promised_date": None, "automatic_action": False
    }


def run_case(module, base, case):
    masters = prepare_masters(base, case["variant"])
    before = deepcopy(masters)
    request = deepcopy(case["request"])
    sim = module.TransitionSimulator(masters)
    checks = []

    def check(name, observed, expected):
        passed = observed == expected
        checks.append({"check": name, "expected": expected, "observed": observed, "passed": passed})
        if not passed:
            raise AssertionError(f"{case['case_id']}: {name}: {observed!r} != {expected!r}")

    try:
        check("Entrada cumple validación del contrato 1.0", module.valid_request(request), True)
        response = sim.submit(request, ACTOR)
        audit_first = [dict(row) for row in sim.db.execute("SELECT * FROM audit ORDER BY event_id")]
        check("Secuencia de códigos de la primera evaluación", [row["code"] for row in audit_first], case["expected_audit_codes"])
        for field, expected in case["expected"].items():
            check(f"Respuesta: {field}", response.get(field), expected)
        for field in ("contract_version", "request_id", "correlation_id", "quotation_id", "quotation_version"):
            check(f"Correlación respuesta/solicitud: {field}", response[field], request[field])
        schema = read_json(ROOT / "arquitectura/contratos/respuesta-pedido-v1.schema.json")
        check("Respuesta contiene exactamente campos del contrato", sorted(response), sorted(schema["required"]))
        check("Estado admitido por contrato", response["status"] in schema["properties"]["status"]["enum"], True)
        check("Código admitido por contrato", response["code"] in schema["properties"]["code"]["enum"], True)

        customer = masters["customers"][request["customer_id"]]
        lead = masters["leads"]["LEAD-EP-001"]
        opportunity = masters["opportunities"][request["opportunity_id"]]
        quote = masters["quotations"][request["quotation_id"]]
        acceptance = masters["acceptances"][request["acceptance_id"]]
        check("Segmento físico de la fixture", customer["segment"], "PUBLICO_GENERAL_NUEVO")
        check("Canal físico y visita espontánea", [opportunity["channel"], opportunity["source"]], ["FISICO", "VISITA_ESPONTANEA"])
        check("Cadena cliente/lead/oportunidad", [lead["customer_id"], lead["opportunity_id"], opportunity["lead_id"]], ["CLI-DEMO-001", "OPP-DEMO-001", "LEAD-EP-001"])
        check("Cadena cotización y aceptación de la misma versión", [quote["customer_id"], quote["opportunity_id"], quote["version"], acceptance["quotation_id"], acceptance["quotation_version"], acceptance["total"]], ["CLI-DEMO-001", "OPP-DEMO-001", request["quotation_version"], "COT-DEMO-001", request["quotation_version"], quote["total"]])
        check("Correlación de oportunidad", opportunity["correlation_id"], "COR-EP-001")
        check("Vigencia del día lógico simulado", quote["valid_until"], "2026-10-24T18:00:00-05:00")
        line = quote["lines"][0]
        arithmetic = Decimal(line["quantity"]) * Decimal(line["unit_price"]) * (1 - Decimal(line["discount_pct"]) / 100)
        check("Cuadre de importe cotizado", format(arithmetic, ".2f"), quote["total"])
        check("Cinco autoradios por S/ 400", [line["quantity"], line["unit_price"]], [5, "400.00"])
        check("Sin autorización del dueño inventada", masters["approvals"], [])

        sim.now += timedelta(minutes=1)
        repeated = sim.submit(request, ACTOR)
        audit = [dict(row) for row in sim.db.execute("SELECT * FROM audit ORDER BY event_id")]
        persisted = sim.get(request["company_id"], request["request_id"], ACTOR)
        count = sim.db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        tables = [row["name"] for row in sim.db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        check("Reintento devuelve respuesta idéntica", repeated, response)
        check("Una sola solicitud tras el reintento", count, 1)
        check("Consulta recupera respuesta persistida", persisted, response)
        check("Una sola decisión auditada", sum(row["event_type"] == "DECISION" for row in audit), 1)
        check("Un reintento auditado", sum(row["event_type"] == "REINTENTO" for row in audit), 1)
        check("Bitácora correlacionada", all(row["request_id"] == request["request_id"] and row["correlation_id"] == request["correlation_id"] and row["company_id"] == request["company_id"] and row["actor_id"] == ACTOR for row in audit), True)
        check("Tablas locales: sin pedidos ni reservas", tables, ["audit", "requests"])
        check("Maestros del simulador no modificados (SHA-256 canónico)", object_sha256(sim.masters), object_sha256(before))
        check("Maestros fuente no modificados (SHA-256 canónico)", object_sha256(masters), object_sha256(before))
        check("Stock permanece sin reserva o descuento", sim.masters["availability"]["quantities"]["RAD-7BT"], case["expected_stock"])
        signal = conceptual_signal(case, response, masters)
        check("Señal P2P conceptual esperada", signal, case["expected_signal"])
        if case["case_id"] == "EP-E01":
            check("Descuento rechazado antes de consultar stock", any(row["interface_id"] == "I05" for row in audit), False)

        result = {
            "case_id": case["case_id"], "kind": "SIMULACION_LOCAL_SIN_ODOO",
            "business_time": masters["business_time"], "request": request,
            "expected": deepcopy(case["expected"]), "observed": response,
            "repeated_response": repeated, "request_count": count,
            "conceptual_p2p_signal": signal, "timeline": timeline(case, masters),
            "chain": ["CLI-DEMO-001", "LEAD-EP-001", "OPP-DEMO-001", f"COT-DEMO-001 v{request['quotation_version']}", request["acceptance_id"], request["request_id"]],
            "audit": audit, "checks": checks, "passed": all(item["passed"] for item in checks),
            "limitations": [
                "No valida un journey observado, identidad de persona, política ni inventario reales.",
                "No confirma pedido ni reserva stock; no ejecuta factura, boleta, pago, entrega, posventa o compra.",
                "La línea de tiempo previa al envío es narrativa sintética, no log de un CRM operativo.",
                "La comprobación de salida revisa estructura y expectativas del caso; no es validación completa con motor JSON Schema."
            ]
        }
        write_json(OUT / f"{case['case_id']}-entrada.json", {"masters": masters, "request": request})
        write_json(OUT / f"{case['case_id']}.json", result)
        return {"case_id": case["case_id"], "expected_status": case["expected"]["status"], "expected_code": case["expected"]["code"], "status": response["status"], "code": response["code"], "checks": len(checks), "passed": result["passed"]}
    finally:
        sim.close()


def main():
    # Evita escribir __pycache__ al cargar el simulador ubicado fuera de esta carpeta.
    sys.dont_write_bytecode = True
    OUT.mkdir(exist_ok=True)
    module = load_simulator()
    base = read_json(FIXTURES / "maestros.json")
    cases = read_json(FIXTURES / "casos.json")["cases"]
    results = [run_case(module, base, case) for case in cases]
    total_checks = sum(case["checks"] for case in results)
    report = [
        "# EP Benjamin · Resultados de simulación local", "",
        "Archivo generado automáticamente por `generar_evidencias.py`; no editar manualmente.", "",
        f"**{len(results)} casos aprobados y {total_checks} comprobaciones satisfactorias.** Expectativas fijas independientes de las respuestas observadas.", "",
        "| Caso | Estado / código esperado | Estado / código observado | Comprobaciones | Resultado |",
        "| --- | --- | --- | ---: | --- |",
    ]
    report.extend(f"| [{item['case_id']}]({item['case_id']}.json) | `{item['expected_status']}` / `{item['expected_code']}` | `{item['status']}` / `{item['code']}` | {item['checks']} | {'Aprobado' if item['passed'] else 'Fallo'} |" for item in results)
    report.extend([
        "", "En todos los casos `order_id: null`; stock y maestros intactos. La repetición idéntica mantiene una sola solicitud y una sola decisión, con reintento adicional auditado.", "",
        "EP-S01: déficit sintético 2 para `RAD-7BT` en `TIENDA-DEMO`; señal `REP-EP-001` exclusivamente conceptual, sin compra, reserva ni fecha prometida.", "",
        "EP-E01: cotización v2 y aceptación sintética de la misma versión; el rechazo por falta de aprobación del dueño precede a la consulta de inventario. Evidencia de apoyo al análisis de excepción de Adrián.", "",
        "Fecha lógica simulada: 24/10/2026, zona -05:00. Solicitud 09:55, respuesta y auditoría inicial en la misma transacción 09:55:01; reintento 09:56:01. Vigencia de la oferta hasta las 18:00. No son tiempos de servicio medidos.", "",
        "La línea de tiempo anterior al envío es didáctica. No se valida un journey observado, identidad real ni una instalación de Odoo. Límite: solicitud/respuesta; no se ejecuta pedido, factura, entrega, posventa o P2P.", "",
        "[Manifiesto de ejecución UTC y hashes](ejecucion.json) · [Método y límites](../README.md)", ""
    ])
    (OUT / "resultados.md").write_text("\n".join(report), encoding="utf-8")
    inputs = [Path(__file__), HERE / "README.md", *sorted(FIXTURES.glob("*.json")), SIMULATOR,
              ROOT / "arquitectura/contratos/solicitud-pedido-v1.schema.json",
              ROOT / "arquitectura/contratos/respuesta-pedido-v1.schema.json"]
    outputs = [OUT / f"{case['case_id']}{suffix}.json" for case in cases for suffix in ("", "-entrada")] + [OUT / "resultados.md"]
    manifest = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "logical_business_time": "2026-10-24T09:55:01-05:00",
        "notice": "Hora UTC de ejecución real separada de la fecha lógica simulada del examen. Ninguna fecha lógica acredita una operación empresarial.",
        "executor": "Codex; ejecución automática local, revisión académica humana pendiente",
        "environment": {"python": platform.python_version(), "platform": platform.system(), "storage": "SQLite en memoria; instancia aislada por caso", "dependencies": "Solo biblioteca estándar"},
        "scope": "Contrato 1.0 hasta solicitud/respuesta; sin ejecución de pedido, factura, entrega o posventa. P2P: solo señal conceptual.",
        "cases": results, "checks_passed": total_checks,
        "input_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in inputs},
        "output_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in outputs},
        "reproducibility": "Los JSON de casos y entradas son deterministas con los mismos insumos. Solo este manifiesto cambia su UTC real y, si cambia el intérprete, el entorno."
    }
    write_json(OUT / "ejecucion.json", manifest)
    print(f"OK: {len(results)} casos, {manifest['checks_passed']} comprobaciones; evidencia en {OUT.relative_to(ROOT).as_posix()}")
    for result in results:
        print(f"{result['case_id']}: {result['status']} / {result['code']} / order_id=null")


if __name__ == "__main__":
    main()
