"""Crea las credenciales de n8n desde .env e importa W1, W2 y W3. Luego los activa.

    python scripts/importar_n8n.py

- Las credenciales se generan en memoria y se pasan por stdin al contenedor; no se
  escribe ningún archivo con tokens en el equipo anfitrión. El archivo temporal dentro
  del contenedor se borra al terminar.
- Si .env tiene GEMINI_API_KEY, también crea la credencial «Gemini (Agente SIE)»;
  si no, créela a mano en n8n (README, paso 5).
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from generar_workflows import CRED, IDS  # noqa: E402
from ejecutar_casos import leer_env  # noqa: E402


def compose(*args, entrada=None, check=True):
    r = subprocess.run(["docker", "compose", *args], cwd=RAIZ, input=entrada, capture_output=True, text=True)
    if check and r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit(f"Falló: docker compose {' '.join(args[:4])}…")
    return r


def main():
    env = leer_env()
    credenciales = [
        {**CRED["ventas"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_VENTAS']}"}},
        {**CRED["gerencia"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_GERENCIA']}"}},
    ]
    if env.get("GEMINI_API_KEY"):
        credenciales.append({**CRED["gemini"], "type": "googlePalmApi",
                             "data": {"host": "https://generativelanguage.googleapis.com", "apiKey": env["GEMINI_API_KEY"]}})
    compose("exec", "-T", "n8n", "sh", "-c", "umask 077 && cat > /tmp/agente-sie-cred.json", entrada=json.dumps(credenciales))
    try:
        compose("exec", "-T", "n8n", "n8n", "import:credentials", "--input=/tmp/agente-sie-cred.json")
    finally:
        compose("exec", "-T", "n8n", "rm", "-f", "/tmp/agente-sie-cred.json", check=False)
    print(f"✓ credenciales importadas: {', '.join(c['name'] for c in credenciales)}")
    if not env.get("GEMINI_API_KEY"):
        print("  · falta la credencial «Gemini (Agente SIE)»: créela en n8n (README paso 5) o use W3")
    compose("exec", "-T", "n8n", "n8n", "import:workflow", "--separate", "--input=/workflows")
    print("✓ flujos W1, W2 y W3 importados")
    for clave in ("W2", "W3", "W1"):
        r = compose("exec", "-T", "n8n", "n8n", "publish:workflow", f"--id={IDS[clave]}", check=False)
        if r.returncode:  # versiones sin «publish»: activar con update:workflow
            compose("exec", "-T", "n8n", "n8n", "update:workflow", f"--id={IDS[clave]}", "--active=true")
    compose("restart", "n8n")
    print("✓ flujos activados; n8n reiniciado (espere ~20 s)")


if __name__ == "__main__":
    main()
