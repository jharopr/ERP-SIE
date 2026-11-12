"""Prepara una instancia NUEVA de n8n e importa los flujos existentes del Agente SIE.

Si ya hay propietario no cambia su cuenta. Contraseñas y tokens nunca se imprimen.
"""
from pathlib import Path
import json
import subprocess
import sys
import urllib.request
from configurar import ROOT, leer_env


def main():
    env = leer_env()
    url = 'http://localhost:' + env.get('N8N_PORT', '5678')
    with urllib.request.urlopen(url+'/rest/settings', timeout=15) as r:
        settings = json.load(r).get('data', {})
    if settings.get('userManagement', {}).get('showSetupOnFirstLoad'):
        body = {'email': env['N8N_OWNER_EMAIL'], 'firstName': 'Equipo', 'lastName': 'MYS',
                'password': env['N8N_OWNER_PASSWORD']}
        req = urllib.request.Request(url+'/rest/owner/setup', data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=20):
            print('Propietario local de n8n creado. Accesos en app/.env.')
    else:
        print('n8n ya tiene propietario. Se conserva su cuenta.')
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'agente-sie/scripts/generar_workflows.py')], check=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'agente-sie/scripts/importar_n8n.py')], check=True)


if __name__ == '__main__':
    main()
