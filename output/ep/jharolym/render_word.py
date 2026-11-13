"""Usa el renderizador de la habilidad con Word como conversor PDF en Windows."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

RUNTIME = Path('C:/Users/JHARO/.cache/codex-runtimes/codex-primary-runtime')
SKILL = Path('C:/Users/JHARO/.codex/plugins/cache/openai-primary-runtime/documents/26.1020.11127/skills/documents')
os.environ['PATH'] = str(RUNTIME / 'dependencies/native/poppler/Library/bin') + os.pathsep + os.environ['PATH']
spec = importlib.util.spec_from_file_location('render_docx', SKILL / 'render_docx.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)

def word_to_pdf(doc_path, user_profile, convert_tmp_dir, stem, verbose=False):
    pdf_path = Path(convert_tmp_dir) / (stem + '.pdf')
    result = subprocess.run([
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', str(Path(__file__).with_name('exportar_word_pdf.ps1')),
        '-DocxPath', str(Path(doc_path).resolve()), '-PdfPath', str(pdf_path),
    ], capture_output=True, text=True, timeout=180)
    log = result.stdout + result.stderr
    if verbose:
        print(log)
    return (str(pdf_path) if result.returncode == 0 and pdf_path.exists() else '', log)

renderer.convert_to_pdf = word_to_pdf
renderer.main()
