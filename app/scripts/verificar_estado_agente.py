"""Comprueba estados sin cambiar el .env ni realizar llamadas al proveedor.

Ejecuta el controlador instalado en Odoo con respuestas de Gemini simuladas.
"""
import subprocess
from configurar import ROOT, leer_env


def main():
    code = '''
import os
from unittest.mock import patch, Mock
from odoo.addons.mys_erp.controllers.sistema import Sistema, _AGENT_CACHE
controller=Sistema()
cases=[('', None, None, 'SIN_API_KEY'),
       ('prueba-controlador', 403, {}, 'API_KEY_RECHAZADA'),
       ('prueba-controlador', 429, {}, 'CUOTA_AGOTADA'),
       ('prueba-controlador', 200, {'models':[]}, 'MODELO_NO_DISPONIBLE')]
for key, status, body, expected in cases:
    _AGENT_CACHE.clear()
    result=Mock(status_code=status, ok=status==200)
    result.json.return_value=body
    with patch.dict(os.environ, {'GEMINI_API_KEY':key}), patch('requests.get', return_value=result) as call:
        data=controller._agent_status()
        assert data['code']==expected and not data['enabled'], data
        assert 'prueba-controlador' not in str(data)
        if not key: call.assert_not_called()
        print('OK '+expected)
print('ESTADO_AGENTE: 4 comprobaciones correctas; entorno real conservado.')
'''
    subprocess.run(['docker', 'compose', 'run', '--rm', '--no-deps', '-T', 'odoo', 'shell', '-d', leer_env()['ODOO_DB'],
                    '--no-http', '--log-level=error'], input=code, cwd=ROOT, text=True, encoding='utf-8', check=True)


if __name__ == '__main__':
    main()
