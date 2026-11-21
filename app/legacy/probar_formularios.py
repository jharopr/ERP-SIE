"""Prueba W3 y W2 autenticados contra n8n real, sin invocar un modelo de IA."""
from datetime import datetime, timezone
import base64
import http.cookiejar
import json
import time
import urllib.error
import urllib.request
import uuid
from configurar import ROOT, leer_env


def main():
    env=leer_env()
    base='http://127.0.0.1:'+env.get('N8N_PORT','5678')
    gate='http://127.0.0.1:'+env.get('COMPUERTA_PORT','8000')
    checks=[]

    def api(path, method='GET', data=None, rol='VENTAS'):
        token=env['TOKEN_'+rol]
        req=urllib.request.Request(gate+path,method=method,data=json.dumps(data).encode() if data is not None else None,
                                   headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as r:
            return json.load(r)

    def form(path, values, rol):
        name='ven-demo-01' if rol=='VENTAS' else 'ger-demo-01'
        password=env['ODOO_SELLER_PASSWORD' if rol=='VENTAS' else 'ODOO_OWNER_PASSWORD']
        auth='Basic '+base64.b64encode((name+':'+password).encode()).decode()
        boundary=uuid.uuid4().hex
        chunks=[f'--{boundary}\r\nContent-Disposition: form-data; name="field-{i}"\r\n\r\n{v}\r\n' for i,v in enumerate(values)]
        body=(''.join(chunks)+f'--{boundary}--\r\n').encode()
        req=urllib.request.Request(base+'/form/'+path,data=body,
                                   headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Authorization':auth})
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode()
            if 'json' not in r.headers.get('Content-Type',''):
                return raw
            payload=json.loads(raw)
        waiting=payload.get('formWaitingUrl')
        if not waiting:
            return json.dumps(payload,ensure_ascii=False)
        # No registrar la URL temporal: forma parte del acceso a la ejecución.
        for _ in range(15):
            try:
                req=urllib.request.Request(waiting,headers={'Authorization':auth})
                with urllib.request.urlopen(req,timeout=10) as r:
                    return r.read().decode()
            except urllib.error.HTTPError as error:
                if error.code not in (404,409):
                    raise
                time.sleep(1)
        raise RuntimeError('El formulario no terminó su ejecución a tiempo.')

    html=form('modo-determinista',['PC3-N01'],'VENTAS')
    checks.append({'comprobacion':'W3 ejecuta el caso normal sin modelo','correcto':'VALIDADA' in html and 'ACEPTADA' in html})
    case=api('/solicitudes/SOL-CAT-002')
    assert case['respuesta']['status']=='PROMESA_CONDICIONADA', 'Ejecute verificar_sistema.py antes de probar n8n.'
    esc=api('/escalamientos','POST',{'tipo':'REPOSICION','request_id':'SOL-CAT-002','resumen':'Prueba de escalamiento desde el formulario autenticado W2.'})
    html=form('decision-dueno',[esc['escalation_id'],'EVALUAR_REPOSICION','Evaluar la necesidad de demostración, sin compra automática.'],'GERENCIA')
    state=api('/escalamientos/'+esc['escalation_id'])
    checks.append({'comprobacion':'W2 registra la decisión del dueño autenticado',
                   'correcto':state['estado']=='DECIDIDO' and state['decision']=='EVALUAR_REPOSICION'})
    events=api('/bitacora?correlation_id=COR-CAT-002')['eventos']
    checks.append({'comprobacion':'Decisión atribuida a GER-DEMO-01 en bitácora',
                   'correcto':any(e['event_type']=='DECISION_DUENO' and e['actor_id']=='GER-DEMO-01' for e in events)})
    out=ROOT/'evidencias'
    out.mkdir(exist_ok=True)
    report={'ejecutado_utc':datetime.now(timezone.utc).isoformat(),'entorno':'n8n 2.46.7 real + Compuerta + Odoo real',
            'comprobaciones':checks,'modelo_ia_ejecutado':False,'correcto':all(c['correcto'] for c in checks)}
    (out/'n8n.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for check in checks:
        print(('OK' if check['correcto'] else 'ERROR')+' '+check['comprobacion'])
    if not report['correcto']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
