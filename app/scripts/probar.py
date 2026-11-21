"""Pruebas unitarias desde app/.venv o un entorno con requirements-dev.txt."""
from pathlib import Path
import subprocess
import sys
import tempfile
from configurar import ROOT

parent = ROOT / '.test-runs'
parent.mkdir(exist_ok=True)
# Un directorio nuevo evita borrar resultados anteriores o temporales ajenos.
base = Path(tempfile.mkdtemp(prefix='pruebas-', dir=parent)) / 'pytest'
sys.exit(subprocess.call([sys.executable, '-m', 'pytest', str(ROOT/'agente-sie/compuerta/tests'),
                          '-q', '--tb=short', '--basetemp='+str(base)], cwd=ROOT))
