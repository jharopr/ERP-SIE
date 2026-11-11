"""Salud de Odoo, compuerta y n8n desde el equipo anfitrión (solo biblioteca estándar)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import urllib.request

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from ejecutar_casos import leer_env  # noqa: E402

# Consolas de Windows (cp1252) no imprimen «✓»: se fuerza UTF-8 sin abortar.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

env = leer_env()
chequeos = {
    "Odoo": f"http://localhost:{env.get('ODOO_PORT', '8069')}/web/health",
    "Compuerta": f"http://localhost:{env.get('COMPUERTA_PORT', '8000')}/salud",
    "n8n": f"http://localhost:{env.get('N8N_PORT', '5678')}/healthz",
}
ok = True
subprocess.run(["docker", "compose", "ps"], cwd=RAIZ)
for nombre, url in chequeos.items():
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            cuerpo = r.read().decode()
            extra = ""
            if nombre == "Compuerta":
                d = json.loads(cuerpo)
                extra = f" · Odoo visto por la compuerta: {d['odoo']}"
                ok &= bool(d["odoo"].get("disponible"))
            print(f"✓ {nombre} ({url}){extra}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"✗ {nombre} ({url}): {exc}")
sys.exit(0 if ok else 1)
