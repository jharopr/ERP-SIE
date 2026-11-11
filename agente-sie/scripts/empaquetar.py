"""Arma GE703_PC3_Agente_G7_MYS.zip con el paquete, SIN .env, bases ni cachés.

    python scripts/empaquetar.py

Antes de comprimir verifica que ningún archivo contenga los valores secretos de .env.
"""

from __future__ import annotations

from pathlib import Path
import sys
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "GE703_PC3_Agente_G7_MYS"
EXCLUIR_DIR = {"__pycache__", ".pytest_cache", "data", ".git"}
EXCLUIR_ARCH = {".env"}
EXCLUIR_SUFIJO = (".sqlite3", ".sqlite3-journal", ".zip", ".pyc")


def secretos():
    env = RAIZ / ".env"
    if not env.exists():
        return []
    valores = []
    for linea in env.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, valor = linea.split("=", 1)
            if any(p in clave for p in ("PASSWORD", "TOKEN", "KEY")) and len(valor.strip()) >= 8 \
                    and not valor.strip().startswith("cambiar-esto"):
                valores.append(valor.strip())
    return valores


def archivos():
    for p in sorted(RAIZ.rglob("*")):
        rel = p.relative_to(RAIZ)
        if p.is_dir() or set(rel.parts) & EXCLUIR_DIR or p.name in EXCLUIR_ARCH or p.name.endswith(EXCLUIR_SUFIJO):
            continue
        yield p, rel


def main():
    prohibidos = secretos()
    lista = list(archivos())
    for p, rel in lista:
        try:
            texto = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for s in prohibidos:
            if s in texto:
                raise SystemExit(f"ABORTADO: {rel} contiene un valor secreto de .env")
    destino = RAIZ.parent / f"{NOMBRE}.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in lista:
            z.write(p, f"{NOMBRE}/{rel.as_posix()}")
    print(f"✓ {destino} ({len(lista)} archivos, {destino.stat().st_size // 1024} KB); sin .env ni secretos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
