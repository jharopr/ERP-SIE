"""Actualiza el addon y sincroniza el login administrador en una base existente.

No recrea volúmenes. Ejecutar antes del seed y con el respaldo de scripts/backup.py.
"""
import json
import subprocess
from configurar import ROOT, leer_env


def run(*args, input=None, check=True):
    r = subprocess.run(['docker', 'compose', *args], cwd=ROOT, input=input, text=True,
                       capture_output=True, encoding='utf-8', errors='replace')
    if check and r.returncode:
        print(r.stdout[-5000:]); print(r.stderr[-7000:])
        raise RuntimeError('Falló la actualización de Odoo; se conservaron los volúmenes.')
    return r


def main():
    env = leer_env()
    databases = run('exec', '-T', 'db', 'psql', '-U', env['POSTGRES_USER'], '-d', 'postgres', '-Atqc',
                    'SELECT datname FROM pg_database').stdout.splitlines()
    if env['ODOO_DB'] not in databases:
        print('Base nueva: el seed instalará el addon MYS.')
        return
    installed = run('exec', '-T', 'db', 'psql', '-U', env['POSTGRES_USER'], '-d', env['ODOO_DB'], '-Atqc',
                    "SELECT state FROM ir_module_module WHERE name='mys_erp'", check=False)
    run('stop', 'compuerta', 'odoo')
    if installed.stdout.strip() in ('installed', 'to upgrade'):
        run('run', '--rm', '--no-deps', '-T', 'odoo', '-d', env['ODOO_DB'], '-u', 'mys_erp',
            '--stop-after-init', '--no-http', '--log-level=warn')
        print('Addon MYS actualizado; datos conservados.')
    payload = json.dumps([env['ODOO_USER'], env['ODOO_PASSWORD']])
    code = ('import json\nlogin,password=json.loads(' + repr(payload) + ')\n'
            'u=env["res.users"].sudo().search([("login","=",login)])\n'
            'assert len(u)==1, "Administrador no encontrado"\n'
            'u.write({"password":password})\nenv.cr.commit()\n')
    run('run', '--rm', '--no-deps', '-T', 'odoo', 'shell', '-d', env['ODOO_DB'], '--no-http', '--log-level=error', input=code)
    print('Contraseña del administrador sincronizada desde .env.')


if __name__ == '__main__':
    main()
