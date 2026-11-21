"""Backup coherente de la demo. Pausa brevemente los procesos que escriben.

No se ejecuta al iniciar el sistema. Incluye registros y credenciales cifradas:
guardar el directorio resultante en un lugar protegido, fuera del paquete.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from configurar import ROOT, leer_env


def compose(*args, **kwargs):
    return subprocess.run(['docker','compose',*args],cwd=ROOT,check=True,**kwargs)


def main():
    env=leer_env()
    target=ROOT/'backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target.mkdir(parents=True)
    # El tar contiene SQLite y sus archivos WAL/SHM tal como estaban pausados.
    compose('pause','odoo','compuerta','n8n')
    try:
        with (target/'odoo.dump').open('wb') as out:
            compose('exec','-T','db','pg_dump','-U',env['POSTGRES_USER'],'-Fc',env['ODOO_DB'],stdout=out)
        for service,destination in [('odoo','/var/lib/odoo'),('compuerta','/data'),('n8n','/home/node/.n8n')]:
            container=compose('ps','-q',service,capture_output=True,text=True).stdout.strip()
            inspected=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
            volume=next(m['Name'] for m in inspected['Mounts'] if m['Destination']==destination)
            subprocess.run(['docker','run','--rm','--network','none','-v',volume+':/source:ro',
                            '-v',str(target)+':/backup','alpine:3.21',
                            'tar','-czf','/backup/'+service+'.tar.gz','-C','/source','.'],check=True)
    finally:
        compose('unpause','odoo','compuerta','n8n')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in target.iterdir() if p.is_file()}
    (target/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Backup guardado en '+str(target))
    print('Conservar una copia protegida de .env/N8N_ENCRYPTION_KEY por separado. No subir a Git ni al ZIP.')


if __name__=='__main__':
    main()
