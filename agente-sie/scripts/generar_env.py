"""Crea .env a partir de .env.example con claves aleatorias nuevas (Linux, macOS o Windows).

    python3 scripts/generar_env.py                     # sin clave de modelo (W1 se configura después o se usa W3)
    python3 scripts/generar_env.py --gemini "AQ.xxxx"  # además registra la clave de Gemini

No sobrescribe un .env existente salvo con --forzar. Cada persona debe generar el suyo:
no comparta su .env (contiene contraseñas y tokens).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import secrets

RAIZ = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gemini", default="", help="Clave de Google Gemini (opcional)")
    ap.add_argument("--forzar", action="store_true", help="Reemplaza un .env existente")
    args = ap.parse_args()
    destino = RAIZ / ".env"
    if destino.exists() and not args.forzar:
        raise SystemExit(".env ya existe; use --forzar para reemplazarlo (perderá acceso a datos creados con las claves anteriores)")
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    texto = re.sub(r"cambiar-esto[\w-]*", lambda _: secrets.token_urlsafe(24), texto)
    texto = re.sub(r"(?m)^GEMINI_API_KEY=.*$", f"GEMINI_API_KEY={args.gemini.strip()}", texto)
    destino.write_text(texto, encoding="utf-8", newline="\n")
    print(f"✓ {destino} creado con claves nuevas" + ("" if args.gemini else " (sin clave de Gemini)"))


if __name__ == "__main__":
    main()
