"""Validación formal opcional de schemas, fixtures, evidencia y entradas inválidas."""

from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
if (HERE / ".schema-runtime").exists():
    sys.path.insert(0, str(HERE / ".schema-runtime"))

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    raise SystemExit("Instalar validador opcional según README de pruebas PC2")

from simulador import FIXTURES, ROOT, load_json, valid_request


def date_time_with_zone(value):
    """Verifica las fechas del contrato aunque no se instalen extras de jsonschema."""
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})", value):
        return False
    try:
        return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def main():
    paths = [ROOT / "arquitectura/contratos/solicitud-pedido-v1.schema.json", ROOT / "arquitectura/contratos/respuesta-pedido-v1.schema.json"]
    schemas = [load_json(path) for path in paths]
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    checker = FormatChecker()
    checker.checks("date-time")(date_time_with_zone)
    request_validator, response_validator = [Draft202012Validator(s, format_checker=checker) for s in schemas]
    validated = []
    for path in sorted(FIXTURES.glob("solicitud-*.json")):
        request_validator.validate(load_json(path))
        validated.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    for path in sorted((HERE / "evidencias").glob("PC2-*.json")):
        record = load_json(path)
        request_validator.validate(record["request"])
        response_validator.validate(record["obtained"])
        validated.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    base = load_json(FIXTURES / "solicitud-normal.json")
    corpus = [None, [], {}, base]
    for field in base:
        for value in [None, True, False, -1, 0, 1, 1.0, 1.5, "", "a b", "a\nb", "a\n", "a" * 65, [], {}]:
            corpus.append({**base, field: value})
        corpus.append({key: value for key, value in base.items() if key != field})
    corpus.append({**base, "approved": True})
    for value in corpus:
        if request_validator.is_valid(value) != valid_request(value):
            raise AssertionError(f"Simulador y schema discrepan: {value!r}")
    # El perfil local no puede inventar pedido; el contrato admite referencia futura
    # únicamente con estado explícito CONFIRMADO y solicitud ACEPTADA.
    normal = load_json(HERE / "evidencias/PC2-N01.json")["obtained"]
    exception = load_json(HERE / "evidencias/PC2-E01.json")["obtained"]
    invalid_cases = [{**normal, "order_id": "PED-FALSO"}, {**normal, "code": "DESCUENTO_SIN_APROBACION"},
                     {**normal, "status": "PROMESA_CONDICIONADA"}, {**normal, "total": None},
                     {**normal, "order_state": "CONFIRMADO"}, {**normal, "attention_due_at": "mañana"},
                     {**exception, "attention_due_at": "mañana"},
                     {**exception, "attention_due_at": "2026-10-16T18:00:00"}]
    for invalid in invalid_cases:
        if response_validator.is_valid(invalid):
            raise AssertionError("El schema permite una respuesta incoherente")
    response_validator.validate({**normal, "order_id": "PED-FUTURO-001", "order_state": "CONFIRMADO"})
    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [*paths, *(ROOT / path for path in validated), Path(__file__)]}
    manifest = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "validator": f"jsonschema {version('jsonschema')}",
                "draft": "2020-12", "schema_count": len(schemas), "validated_files": validated,
                "request_consistency_cases": len(corpus), "invalid_response_cases": len(invalid_cases),
                "future_confirmed_response_shape_validated": True, "passed": True, "sha256": hashes}
    (HERE / "evidencias/esquemas.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(schemas)} schemas, {len(validated)} archivos y {len(corpus)} casos de consistencia")


if __name__ == "__main__":
    main()
