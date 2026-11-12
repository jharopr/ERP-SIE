"""Empaqueta app/ para el docente, excluyendo claves, caches, backups y bases."""
from pathlib import Path
import hashlib
import json
import zipfile
from configurar import ROOT, leer_env

EXCLUDE = {'.git','.venv','.pytest_cache','__pycache__','.test-runs','backups','dist','logs','node_modules','data'}


def main():
    env=leer_env()
    public_demo = {'ODOO_PASSWORD': 'admin', 'ODOO_SELLER_PASSWORD': 'ven-demo-01', 'ODOO_OWNER_PASSWORD': 'ger-demo-01'}
    private=[v for k,v in env.items() if (any(word in k for word in ('PASSWORD','TOKEN','KEY','SECRET'))
             and len(v)>=8 and not v.startswith('cambiar-esto') and public_demo.get(k) != v)]
    files=[]
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDE for part in rel.parts) or path.name.startswith('.env') and path.name!='.env.example':
            continue
        if path.suffix in {'.pyc','.sqlite3','.zip'} or '.sqlite3-' in path.name:
            continue
        content=path.read_bytes()
        for value in private:
            if value.encode() in content:
                raise SystemExit('El paquete contiene un secreto en '+rel.as_posix()+'. No se generó el ZIP.')
        files.append((path,rel,content))
    target=ROOT/'dist'
    target.mkdir(exist_ok=True)
    archive=target/'GE703_PC3_Sistema_MYS.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path,rel,content in files:
            z.writestr('app/'+rel.as_posix(),content)
    manifest={'archivo':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'archivos':len(files),'sin_env_bases_o_secretos':True}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Paquete app/dist/{archive.name}: {len(files)} archivos, sin claves ni bases.')


if __name__=='__main__':
    main()
