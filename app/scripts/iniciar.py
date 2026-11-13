"""Instala/inicia la plataforma de demostración desde cualquier directorio.

python scripts/iniciar.py              # conserva transacciones
python scripts/iniciar.py --reiniciar  # reinicia solamente la demo comercial
python scripts/iniciar.py --sin-n8n    # omite importación, no detiene el servicio
"""
import argparse
import subprocess
import sys
import time
import urllib.request
from configurar import ROOT, leer_env, main as configurar


def run(*args):
    try:
        subprocess.run(list(args), cwd=ROOT, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError('No se completó el arranque. Revise: docker compose logs --tail 80 odoo n8n. '
                           'Si cambió las claves de una instalación existente, ejecute '
                           'python scripts/sincronizar_credenciales.py y vuelva a iniciar.') from None


def comprobar_postgres():
    """pg_isready solo comprueba disponibilidad; esta consulta exige contraseña TCP."""
    result = subprocess.run(
        ['docker','compose','exec','-T','db','sh','-c',
         'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -h 127.0.0.1 -U "$POSTGRES_USER" -d postgres -Atqc "SELECT 1"'],
        cwd=ROOT, capture_output=True, text=True)
    if result.returncode or result.stdout.strip() != '1':
        raise RuntimeError('PostgreSQL conserva una contraseña distinta de POSTGRES_PASSWORD en app/.env. '
                           'Cambiar .env no actualiza un volumen ya inicializado. Ejecute '
                           'python scripts/sincronizar_credenciales.py; conserva la base y crea un respaldo.')


def esperar(url):
    deadline = time.monotonic()+180
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5):
                return
        except OSError:
            time.sleep(3)
    raise SystemExit('El servicio no respondió a tiempo: '+url)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reiniciar', action='store_true')
    parser.add_argument('--sin-n8n', action='store_true')
    args=parser.parse_args()
    configurar()
    run('docker','compose','up','-d','--wait','--wait-timeout','90','db')
    comprobar_postgres()
    run(sys.executable, '-X', 'utf8', 'scripts/actualizar_odoo.py')
    run('docker','compose','up','-d','--build','--wait','--wait-timeout','240')
    run('docker','compose','exec','-T','compuerta','python','/plataforma/seed_sistema.py',
        *(['--reiniciar'] if args.reiniciar else []))
    if not args.sin_n8n:
        esperar('http://localhost:'+leer_env().get('N8N_PORT','5678')+'/healthz')
        run(sys.executable,'-X','utf8','scripts/preparar_n8n.py')
        esperar('http://localhost:'+leer_env().get('N8N_PORT','5678')+'/healthz')
    print('Plataforma lista. Odoo MYS: http://localhost:'+leer_env().get('APP_PORT','8088'))
    print('Contraseñas locales en app/.env. Abra una sesión nueva del agente al reiniciar la demo.')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
