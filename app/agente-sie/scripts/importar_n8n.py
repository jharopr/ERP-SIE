"""Crea las credenciales de n8n desde .env e importa W1, W2 y W3. Luego los activa.

    python scripts/importar_n8n.py

- Las credenciales se generan en memoria y se pasan por stdin al contenedor; no se
  escribe ningún archivo con tokens en el equipo anfitrión. El archivo temporal dentro
  del contenedor se borra al terminar.
- Proveedor del modelo según LLM_PROVIDER en .env:
    gemini (por defecto) → credencial «Gemini (Agente SIE)» con GEMINI_API_KEY
    anthropic            → credencial «Claude (Agente SIE)» con ANTHROPIC_API_KEY y modelo
                           ANTHROPIC_MODEL (por defecto claude-haiku-5-5). El W4 del repositorio
                           no cambia: el nodo del modelo se reemplaza solo al importarlo.
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


def proveedor(env):
    """(nombre, clave) del modelo de lenguaje configurado."""
    if env.get("LLM_PROVIDER", "gemini").strip().lower() == "anthropic":
        return "anthropic", env.get("ANTHROPIC_API_KEY", "").strip()
    return "gemini", env.get("GEMINI_API_KEY", "").strip()


def w4_con_claude(env):
    """W4 con el nodo de Claude en lugar del de Gemini (mismo agente, herramientas y prompt)."""
    w4 = json.loads((RAIZ / "n8n" / "workflows" / "W4_odoo_integrado.json").read_text(encoding="utf-8"))
    viejo = next(n for n in w4["nodes"] if n["type"] == "@n8n/n8n-nodes-langchain.lmChatGoogleGemini")
    nuevo = {**viejo, "name": "Modelo Claude", "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic", "typeVersion": 1.6,
             "parameters": {"model": {"__rl": True, "mode": "id", "value": env.get("ANTHROPIC_MODEL", "claude-haiku-5-5")},
                            # Pensamiento adaptativo con esfuerzo bajo: rápido para chat y llamadas a herramientas.
                            "options": {"maxTokensToSample": 4096, "thinkingMode": "adaptive", "effort": "low"}},
             "credentials": {"anthropicApi": CRED["claude"]}}
    w4["nodes"] = [nuevo if n is viejo else n for n in w4["nodes"]]
    w4["connections"]["Modelo Claude"] = w4["connections"].pop(viejo["name"])
    return w4


def main():
    env = leer_env()
    nombre, clave = proveedor(env)
    credenciales = [
        {**CRED['agente'], 'type': 'httpHeaderAuth', 'data': {'name': 'Authorization', 'value': 'Bearer ' + env['TOKEN_AGENTE']}},
        {**CRED['webhook'], 'type': 'httpHeaderAuth', 'data': {'name': 'X-MYS-Webhook', 'value': env['N8N_WEBHOOK_SECRET']}},
        {**CRED["ventas"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_VENTAS']}"}},
        {**CRED["gerencia"], "type": "httpHeaderAuth", "data": {"name": "Authorization", "value": f"Bearer {env['TOKEN_GERENCIA']}"}},
        {**CRED["form_dueno"], "type": "httpBasicAuth", "data": {"user": "gerente", "password": env['ODOO_OWNER_PASSWORD']}},
        {**CRED["form_ventas"], "type": "httpBasicAuth", "data": {"user": "vendedor01", "password": env['ODOO_SELLER_PASSWORD']}},
    ]
    if clave and nombre == "gemini":
        credenciales.append({**CRED["gemini"], "type": "googlePalmApi",
                             "data": {"host": "https://generativelanguage.googleapis.com", "apiKey": clave}})
    elif clave:
        credenciales.append({**CRED["claude"], "type": "anthropicApi",
                             "data": {"apiKey": clave, "url": "https://api.anthropic.com"}})
    compose("exec", "-T", "n8n", "sh", "-c", "umask 077 && cat > /tmp/agente-sie-cred.json", entrada=json.dumps(credenciales))
    try:
        compose("exec", "-T", "n8n", "n8n", "import:credentials", "--input=/tmp/agente-sie-cred.json")
    finally:
        compose("exec", "-T", "n8n", "rm", "-f", "/tmp/agente-sie-cred.json", check=False)
    print(f"✓ credenciales importadas: {', '.join(c['name'] for c in credenciales)}")
    if not clave:
        print(f"  · falta la clave del proveedor «{nombre}» en .env: el chat queda deshabilitado")
    compose("exec", "-T", "n8n", "n8n", "import:workflow", "--separate", "--input=/workflows")
    print("✓ definiciones W1/W2/W3 históricas y W4 integrado importadas")
    if nombre == "anthropic":
        compose("exec", "-T", "n8n", "sh", "-c", "cat > /tmp/w4-claude.json", entrada=json.dumps(w4_con_claude(env)))
        try:
            compose("exec", "-T", "n8n", "n8n", "import:workflow", "--input=/tmp/w4-claude.json")
        finally:
            compose("exec", "-T", "n8n", "rm", "-f", "/tmp/w4-claude.json", check=False)
        print(f"✓ W4 usa Claude ({env.get('ANTHROPIC_MODEL', 'claude-haiku-5-5')})")
    # Las interfaces independientes se retiran. Conservamos sus definiciones como evidencia histórica.
    for clave in ('W1', 'W2', 'W3'):
        compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', f'--id={IDS[clave]}', check=False)
    if not clave:
        compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', f"--id={IDS['W4']}", check=False)
        compose('restart', 'n8n')
        print(f'Sin clave de {nombre}: chat deshabilitado; los módulos y reglas de Odoo permanecen disponibles.')
        return
    for clave in ("W5", "W4"):
        r = compose("exec", "-T", "n8n", "n8n", "publish:workflow", f"--id={IDS[clave]}", check=False)
        if r.returncode:  # versiones sin «publish»: activar con update:workflow
            compose("exec", "-T", "n8n", "n8n", "update:workflow", f"--id={IDS[clave]}", "--active=true")
    compose("restart", "n8n")
    print("✓ chat privado W4 activado; el usuario ingresa únicamente por Odoo")


if __name__ == "__main__":
    main()
