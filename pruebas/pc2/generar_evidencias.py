"""Ejecuta casos PC2, valida resultados y registra evidencia local sin Odoo."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

from simulador import FIXTURES, ROOT, TransitionSimulator, load_json
from calibrar_andina import main as generate_andina


OUT = Path(__file__).resolve().parent / "evidencias"


def main():
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(Path(__file__).parent), "-p", "test_*.py", "-v"],
                           capture_output=True, text=True, encoding="utf-8")
    if tests.returncode:
        print(tests.stdout + tests.stderr)
        raise SystemExit(tests.returncode)
    OUT.mkdir(exist_ok=True)
    (OUT / "unittest.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    masters = load_json(FIXTURES / "maestros.json")
    normal = load_json(FIXTURES / "solicitud-normal.json")
    exception = load_json(FIXTURES / "solicitud-excepcion.json")
    cases = [
        ("PC2-N01", normal, "normal", "ACEPTADA", "VALIDADA"),
        ("PC2-E01", exception, "normal", "RECHAZADA", "DESCUENTO_SIN_APROBACION"),
        ("PC2-P01", normal, "partial", "PROMESA_CONDICIONADA", "DISPONIBILIDAD_PARCIAL"),
        ("PC2-T01", normal, "unavailable", "PENDIENTE", "DEPENDENCIA_NO_DISPONIBLE"),
    ]
    results = []
    for case_id, request, mode, status, code in cases:
        source = deepcopy(masters)
        if mode == "partial":
            source["availability"]["quantities"]["AUT-DEMO-001"] = 3
        if mode == "unavailable":
            source["availability"]["available"] = False
        sim = TransitionSimulator(source)
        try:
            response = sim.submit(request)
            passed = response["status"] == status and response["code"] == code and response["order_id"] is None
            if not passed:
                raise AssertionError((case_id, response))
            result = {"case_id": case_id, "kind": "SIMULACION_LOCAL_SIN_ODOO", "actor": "VEN-DEMO-01",
                      "business_time": source["business_time"], "fixture_variant": mode,
                      "expected": {"status": status, "code": code, "order_id": None}, "obtained": response,
                      "passed": passed, "request": request,
                      "crm_feedback": sim.get_crm_feedback(request["company_id"], request["request_id"]),
                      "audit": [dict(row) for row in sim.db.execute("SELECT * FROM audit ORDER BY event_id")],
                      "request_count": sim.db.execute("SELECT COUNT(*) FROM requests").fetchone()[0],
                      "masters_unchanged": sim.masters == source}
            if not result["masters_unchanged"]:
                raise AssertionError("Se modificaron maestros durante la evaluación")
            (OUT / f"{case_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results.append({"case_id": case_id, "status": status, "code": code, "passed": passed})
        finally:
            sim.close()
    generate_andina()
    tracked_inputs = [Path(__file__), Path(__file__).with_name("simulador.py"), Path(__file__).with_name("test_contrato.py"),
                      Path(__file__).with_name("calibrar_andina.py"), Path(__file__).with_name("test_andina.py"),
                      *sorted(FIXTURES.glob("*.json")), *sorted((ROOT / "arquitectura/contratos").glob("*.schema.json"))]
    manifest = {"executed_at_utc": datetime.now(timezone.utc).isoformat(),
                "executor": "Codex (ejecución automatizada); revisión humana pendiente",
                "environment": {"python": platform.python_version(), "platform": platform.system(), "database": "SQLite local en memoria"},
                "scope": "Contrato simulado; sin Odoo, PostgreSQL, WhatsApp API ni UBLHUB", "tests": "unittest.txt",
                "cases": results, "sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked_inputs}}
    (OUT / "ejecucion.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: pruebas automáticas y {len(results)} casos documentados; evidencia en {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
