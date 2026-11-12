"""Comprueba chat integrado real, entrada privada y herramientas con el rol Odoo.

Si Gemini está habilitado envía una consulta de catálogo de prueba (usa la API configurada).
"""
import json
import subprocess
import httpx
from configurar import ROOT, leer_env
from verificar_odoo import Cliente


def audit():
    code = '''from app.config import Config
from app.repositorio import Repositorio
import json
r=Repositorio(Config.desde_entorno().database)
with r.conexion() as db:
 rows=db.execute("SELECT a.event_id,a.actor_id,e.actor_type,a.code FROM audit a JOIN audit_ext e ON e.event_id=a.event_id WHERE e.actor_type='AGENTE' AND a.code='buscar_productos' ORDER BY a.event_id").fetchall()
print(json.dumps([dict(r) for r in rows]))
'''
    r = subprocess.run(['docker', 'compose', 'exec', '-T', 'compuerta', 'python', '-'], cwd=ROOT,
                       input=code, capture_output=True, text=True, encoding='utf-8', check=True)
    return json.loads(r.stdout)


def main():
    env = leer_env()
    n8n = 'http://localhost:' + env.get('N8N_PORT', '5678')
    checks = []
    def ok(label, result):
        assert result, label
        checks.append(label)
        print('OK ' + label, flush=True)
    response = httpx.post(n8n+'/webhook/mys-agente-integrado', json={'chatInput': 'hola'}, timeout=30)
    ok('Webhook sin secreto interno rechazado', response.status_code in (401, 403))
    for path in ('/webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat', '/form/decision-dueno', '/form/modo-determinista'):
        ok('Interfaz anterior despublicada: '+path, httpx.get(n8n+path, timeout=30).status_code == 404)
    c = Cliente('http://localhost:'+env.get('APP_PORT', '8088'), env, 'ven-demo-01', env['ODOO_SELLER_PASSWORD'])
    status = c.rpc('/mys/agent/status')
    ok('Estado del agente disponible con sesión Odoo', bool(status['code']))
    before = audit()
    answer = None
    if status['enabled']:
        answer = c.rpc('/mys/agent/chat', {'message': 'Busca radios con pantalla en el catálogo usando buscar_productos. '
                         'Muestra dos productos con SKU y precio exacto. Solo consulta, sin realizar modificaciones.'})
        if answer['ok']:
            ok('Conversación Gemini desde Odoo sin otra contraseña', bool(answer['message']))
            after = audit()
            fresh = [e for e in after if e['event_id'] not in {v['event_id'] for v in before}]
            ok('Herramienta real conserva actor vendedor y actor_type AGENTE',
               bool(fresh) and all(e['actor_id'] == 'VEN-DEMO-01' and e['actor_type'] == 'AGENTE' for e in fresh))
        else:
            ok('Agotamiento de cuota del proveedor informado correctamente', answer.get('code') == 'CUOTA_AGOTADA')
            status = c.rpc('/mys/agent/status')
            ok('Estado del agente refleja falta de cuota', not status['enabled'] and status['code'] == 'CUOTA_AGOTADA')
        combined = json.dumps(answer)
        ok('Respuesta sin credenciales', not any(env[k] in combined for k in
                  ('GEMINI_API_KEY', 'TOKEN_ODOO', 'TOKEN_AGENTE', 'N8N_WEBHOOK_SECRET') if env.get(k)))
    else:
        answer = c.rpc('/mys/agent/chat', {'message': 'Consulta de prueba'})
        ok('Chat deshabilitado informa causa sin pedir contraseña', not answer['ok'] and bool(answer['message']))
    evidence = {'checks': checks, 'count': len(checks), 'status': status,
                'response': answer, 'gemini_real_tested': bool(answer and answer.get('ok'))}
    filename = 'validacion_chat_odoo.json' if evidence['gemini_real_tested'] else 'validacion_chat_estado_actual.json'
    (ROOT/'evidencias'/filename).write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('CHAT INTEGRADO: '+str(len(checks))+' comprobaciones correctas.', flush=True)


if __name__ == '__main__':
    main()
