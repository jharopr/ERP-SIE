"""Compatibilidad: empaqueta la plataforma completa app/, sin secretos."""
import runpy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / "scripts"))
runpy.run_path(str(ROOT / "scripts/empaquetar.py"),run_name="__main__")
