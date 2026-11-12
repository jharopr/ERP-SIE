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
    r = subprocess.run(["docker", "compose", *args], cwd=RAIZ.parent, input=entrada, capture_output=True, text=True)
    if check and r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit(f"Falló: docker compose {' '.join(args[:4])}…")
    return r


def main():
    env = leer_env()
    credenciales = [
        {**CRED['agente'], 'type': 'httpHeaderAuth', 'data': {'name': 'Authorization', 'value': 'Bearer ' + env['TOKEN_AGENTE']}},
        {**CRED['webhook'], 'type': 'httpHeaderAuth', 'data': {'name': 'X-MYS-Webhook', 'value': env['N8N_WEBHOOK_SECRET']}},
        {**CRED["ventas"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_VENTAS']}"}},
        {**CRED["gerencia"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_GERENCIA']}"}},
        {**CRED["form_dueno"], "type": "httpBasicAuth", "data": {"user": "ger-demo-01", "password": env['ODOO_OWNER_PASSWORD']}},
        {**CRED["form_ventas"], "type": "httpBasicAuth", "data": {"user": "ven-demo-01", "password": env['ODOO_SELLER_PASSWORD']}},
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
    print("✓ definiciones W1/W2/W3 históricas y W4 integrado importadas")
    # Las interfaces independientes se retiran. Conservamos sus definiciones como evidencia histórica.
    for clave in ('W1', 'W2', 'W3'):
        compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', f'--id={IDS[clave]}', check=False)
    if not env.get('GEMINI_API_KEY', '').strip():
        compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', f"--id={IDS['W4']}", check=False)
        compose('restart', 'n8n')
        print('Sin GEMINI_API_KEY: chat deshabilitado; los módulos y reglas de Odoo permanecen disponibles.')
        return
    for clave in ("W5", "W4"):
        r = compose("exec", "-T", "n8n", "n8n", "publish:workflow", f"--id={IDS[clave]}", check=False)
        if r.returncode:  # versiones sin «publish»: activar con update:workflow
            compose("exec", "-T", "n8n", "n8n", "update:workflow", f"--id={IDS[clave]}", "--active=true")
    compose("restart", "n8n")
    print("✓ chat privado W4 activado; el usuario ingresa únicamente por Odoo")


if __name__ == "__main__":
    main()
