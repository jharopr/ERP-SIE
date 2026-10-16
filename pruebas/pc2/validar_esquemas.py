"""Validación formal opcional de schemas, fixtures, evidencia y entradas inválidas."""

from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
if (HERE / ".schema-runtime").exists():
    sys.path.insert(0, str(HERE / ".schema-runtime"))

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Instalar validador opcional según README de pruebas PC2")

from simulador import FIXTURES, ROOT, load_json, valid_request


def main():
    paths = [ROOT / "arquitectura/contratos/solicitud-pedido-v1.schema.json", ROOT / "arquitectura/contratos/respuesta-pedido-v1.schema.json"]
    schemas = [load_json(path) for path in paths]
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    request_validator, response_validator = map(Draft202012Validator, schemas)
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
    # Una respuesta que convierte promesa en éxito o inventa un pedido es inválida.
    normal = load_json(HERE / "evidencias/PC2-N01.json")["obtained"]
    for invalid in [{**normal, "order_id": "PED-FALSO"}, {**normal, "code": "DESCUENTO_SIN_APROBACION"},
                    {**normal, "status": "PROMESA_CONDICIONADA"}, {**normal, "total": None}]:
        if response_validator.is_valid(invalid):
            raise AssertionError("El schema permite una respuesta incoherente")
    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [*paths, *(ROOT / path for path in validated), Path(__file__)]}
    manifest = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "validator": f"jsonschema {version('jsonschema')}",
                "draft": "2020-12", "schema_count": len(schemas), "validated_files": validated,
                "request_consistency_cases": len(corpus), "invalid_response_cases": 4, "passed": True, "sha256": hashes}
    (HERE / "evidencias/esquemas.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(schemas)} schemas, {len(validated)} archivos y {len(corpus)} casos de consistencia")


if __name__ == "__main__":
    main()
