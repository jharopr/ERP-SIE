"""Aplica las credenciales de app/.env a una instalación local existente.

Sin borrar volúmenes: respalda PostgreSQL/n8n, actualiza el rol PostgreSQL y el
administrador Odoo, y recifra las credenciales n8n si cambió su clave. Requiere
administración local de Docker. No imprime contraseñas ni exportaciones privadas.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from configurar import ROOT, leer_env


def compose(*args, input=None):
    result = subprocess.run(['docker', 'compose', *args], cwd=ROOT, input=input,
                            capture_output=True, text=isinstance(input, str) or input is None)
    if result.returncode:
        # El stderr de psql/Odoo puede incluir parte del comando SQL. No lo volcar.
        raise RuntimeError('Falló docker compose ' + ' '.join(args[:3]) + '. No se muestran valores privados.')
    return result.stdout


def volumen(service, destination):
    container = compose('ps', '-aq', service).strip()
    if not container:
        return None
    result = subprocess.run(['docker', 'inspect', container], capture_output=True, text=True, check=True)
    return next((m['Name'] for m in json.loads(result.stdout)[0]['Mounts']
                 if m['Destination'] == destination and m['Type'] == 'volume'), None)


def respaldar_n8n(volume, backup):
    code = ('import tarfile; '
            'archive=tarfile.open("/backup/n8n-before.tar.gz","w:gz"); '
            'archive.add("/state",arcname="n8n"); archive.close()')
    result = subprocess.run(['docker', 'run', '--rm', '--network', 'none',
                              '-v', volume+':/state:ro', '-v', str(backup)+':/backup',
                              'python:3.12-slim', 'python', '-c', code], capture_output=True)
    if result.returncode:
        raise RuntimeError('No se pudo respaldar n8n; no se cambiará su clave.')


def recifrar_n8n():
    # El texto exportado solo existe en /tmp de este contenedor efímero. La copia
    # de recuperación del volumen sigue cifrada. Se validan datos/IDs tras importar.
    code = r'''
const fs = require('fs');
const cp = require('child_process');
const home = '/home/node/.n8n';
const conf = home + '/config';
const before = '/tmp/mys-encrypted-before';
const plain = '/tmp/mys-credentials.json';
const verify = '/tmp/mys-verify.json';
if (!fs.existsSync(conf)) { console.log(JSON.stringify({changed:false, reason:'new'})); process.exit(0); }
const config = JSON.parse(fs.readFileSync(conf, 'utf8'));
const oldKey = config.encryptionKey;
const newKey = process.env.N8N_ENCRYPTION_KEY;
if (!newKey || !oldKey) throw Error('Falta una clave de cifrado; no se modificó el volumen.');
if (oldKey === newKey) { console.log(JSON.stringify({changed:false, reason:'matches'})); process.exit(0); }
fs.cpSync(home, before, {recursive:true});
const execute = (args, key) => cp.execFileSync('n8n', args, {
    env:{...process.env, N8N_ENCRYPTION_KEY:key}, stdio:'pipe', maxBuffer:16*1024*1024
});
let stage = 'exportar con clave anterior';
try {
    execute(['export:credentials','--all','--decrypted','--output',plain], oldKey);
    const credentials = JSON.parse(fs.readFileSync(plain,'utf8'));
    stage = 'migrar llavero de la instancia';
    // n8n 2.46 conserva además las claves de datos/firma en deployment_key.
    // Importar credenciales sin migrar ese llavero deja la instancia incoherente.
    // Se usan los cifradores de esta misma versión, sin implementar criptografía.
    const {createRequire} = require('module');
    const nativeRequire = createRequire('/usr/local/lib/node_modules/n8n/package.json');
    const {Cipher} = nativeRequire('n8n-core');
    const oldCipher = new Cipher({encryptionKey:oldKey}, {});
    const newCipher = new Cipher({encryptionKey:newKey}, {});
    const {DatabaseSync} = require('node:sqlite');
    const database = new DatabaseSync(home+'/database.sqlite');
    const hasKeys = database.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deployment_key'").get();
    let migratedKeys = 0;
    if (hasKeys) {
        const rows = database.prepare('SELECT id,type,algorithm,value FROM deployment_key').all();
        const updates = [];
        for (const row of rows) {
            if (row.type === 'instance.id') continue; // identificador, no material cifrado
            let raw, wrapper;
            try {raw=oldCipher.decryptDEKWithInstanceKey(row.value); wrapper='gcm';}
            catch {raw=oldCipher.decryptWithInstanceKey(row.value); wrapper='cbc';}
            if (row.type==='data_encryption' && row.algorithm==='aes-256-cbc' && raw===oldKey) raw=newKey;
            const value = wrapper==='gcm' ? newCipher.encryptDEKWithInstanceKey(raw) : newCipher.encryptWithInstanceKey(raw);
            const recovered = wrapper==='gcm' ? newCipher.decryptDEKWithInstanceKey(value) : newCipher.decryptWithInstanceKey(value);
            if (recovered!==raw) throw Error('No se verificó una clave de instancia.');
            updates.push([value,row.id]);
        }
        database.exec('BEGIN IMMEDIATE');
        try {
            const update = database.prepare('UPDATE deployment_key SET value=? WHERE id=?');
            for (const values of updates) update.run(...values);
            database.exec('COMMIT');
        } catch(error) {database.exec('ROLLBACK');database.close();throw error;}
        migratedKeys = updates.length;
    }
    database.close();
    stage = 'aplicar nueva clave';
    config.encryptionKey = newKey;
    fs.writeFileSync(conf, JSON.stringify(config), {mode:0o600});
    stage = 'importar con nueva clave';
    if (credentials.length) {
        const imported = execute(['import:credentials','--input',plain], newKey).toString();
        // Algunas versiones de n8n capturan errores de importación y salen con
        // código cero. Exigir también la confirmación antes de verificar.
        if (!imported.includes('Successfully imported')) {
            throw Error('La CLI no confirmó la importación: '+imported);
        }
    }
    stage = 'verificar credenciales recifradas';
    execute(['export:credentials','--all','--decrypted','--output',verify], newKey);
    const after = JSON.parse(fs.readFileSync(verify,'utf8'));
    const sorted = (v) => Array.isArray(v) ? v.map(sorted) : v && typeof v==='object'
        ? Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])])) : v;
    const canonical = (v) => JSON.stringify(sorted(v));
    if (credentials.length !== after.length) throw Error('Cambió el número de credenciales.');
    for (const c of credentials) {
        const found = after.find(x => x.id === c.id);
        if (!found || canonical(found.data) !== canonical(c.data)) throw Error('Cambió una credencial.');
    }
    console.log(JSON.stringify({changed:true, preserved:credentials.length, instanceKeys:migratedKeys}));
} catch (error) {
    let detail = (String(error.message || '')+'\n'+String(error.stderr || '')+'\n'+String(error.stdout || '')).slice(-3000);
    for (const key of [oldKey,newKey]) detail = detail.split(key).join('[OCULTO]');
    detail = detail.replace(/[A-Za-z0-9_-]{25,}/g,'[OCULTO]');
    console.error('Etapa n8n: '+stage+'\n'+detail);
    // Los procesos CLI ya terminaron. Restaurar config y los archivos SQLite
    // anteriores, incluso si la importación falló a mitad de la operación.
    for (const name of ['config','database.sqlite','database.sqlite-wal','database.sqlite-shm']) {
        const src = before+'/'+name, dst = home+'/'+name;
        if (fs.existsSync(src)) fs.copyFileSync(src,dst);
        else if (fs.existsSync(dst)) fs.unlinkSync(dst);
    }
    console.error('No se completó el recifrado. Se restauró el estado anterior; copia privada conservada.');
    process.exitCode=1;
} finally {
    for (const file of [plain,verify]) if(fs.existsSync(file)) fs.unlinkSync(file);
}
'''
    output = compose('run', '--rm', '--no-deps', '-T', '--entrypoint', 'node', 'n8n', '-e', code)
    result = next(json.loads(line) for line in output.splitlines() if line.startswith('{'))
    print('n8n: '+ ('clave sincronizada; credenciales conservadas: '+str(result['preserved'])
                     if result['changed'] else 'clave de cifrado coherente.'))


def main():
    env = leer_env()
    for key in ('POSTGRES_USER','POSTGRES_PASSWORD','ODOO_DB','ODOO_USER','ODOO_PASSWORD','N8N_ENCRYPTION_KEY'):
        if not env.get(key):
            raise RuntimeError('Falta '+key+' en app/.env.')
    backup = ROOT/'backups'/('credenciales-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True)
    compose('stop','compuerta','n8n','odoo')
    compose('up','-d','--wait','--wait-timeout','90','db')

    # El socket local autentica al administrador del contenedor. No depende de
    # que la contraseña TCP del volumen coincida todavía con el .env actual.
    result = subprocess.run(['docker','compose','exec','-T','db','pg_dump',
                              '-U',env['POSTGRES_USER'],'-Fc',env['ODOO_DB']], cwd=ROOT,
                             capture_output=True)
    if result.returncode:
        raise RuntimeError('No se pudo respaldar la base existente. No se cambiaron las contraseñas.')
    (backup/'odoo-before.dump').write_bytes(result.stdout)
    volume = volumen('n8n','/home/node/.n8n')
    if volume:
        respaldar_n8n(volume,backup)

    role = '"'+env['POSTGRES_USER'].replace('"','""')+'"'
    password = "'"+env['POSTGRES_PASSWORD'].replace("'","''")+"'"
    sql = "SET standard_conforming_strings = on; SET log_statement = 'none';\nALTER ROLE "+role+" PASSWORD "+password+";\n"
    compose('exec','-T','db','psql','-X','-v','ON_ERROR_STOP=1','-U',env['POSTGRES_USER'],'-d','postgres',input=sql)
    compose('exec','-T','db','sh','-c',
            'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -h 127.0.0.1 -U "$POSTGRES_USER" -d postgres -Atqc "SELECT 1"')
    print('PostgreSQL: contraseña persistida sincronizada y autenticación TCP comprobada.')

    # La contraseña del login Odoo es independiente de PostgreSQL y de su clave
    # maestra. Actualizar solo el usuario pedido por el .env, sin recrear la base.
    payload = json.dumps([env['ODOO_USER'],env['ODOO_PASSWORD']])
    code = ('import json\nlogin,password=json.loads('+repr(payload)+')\n'
            'user=env["res.users"].sudo().with_context(active_test=False).search([("login","=",login)])\n'
            'assert len(user)==1, "Administrador Odoo no encontrado"\n'
            'user.write({"password":password})\nenv.cr.commit()\nprint("ODOO_CREDENCIAL_SINCRONIZADA")\n')
    compose('run','--rm','--no-deps','-T','odoo','shell','-d',env['ODOO_DB'],'--no-http','--log-level=error',input=code)
    print('Odoo: contraseña del administrador sincronizada, base conservada.')
    if volume:
        recifrar_n8n()
    print('Sincronización terminada. Backup privado en '+str(backup.relative_to(ROOT)))
    print('Iniciar ahora con: python scripts/iniciar.py')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print('No se completó la sincronización: '+str(error), file=sys.stderr)
        sys.exit(1)
