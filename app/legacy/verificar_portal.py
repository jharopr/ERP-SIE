"""Verifica Odoo real, catálogo, permisos, casos y panel sin imprimir contraseñas.

Genera evidencias/sistema.json. No modifica productos, stock ni pedidos.
Los casos CAT se evalúan de forma idempotente por la compuerta.
"""
from __future__ import annotations
from datetime import datetime, timezone
import http.cookiejar
import json
from pathlib import Path
import urllib.error
import urllib.request
import xmlrpc.client
from configurar import ROOT, leer_env


def main():
    env = leer_env()
    base = 'http://127.0.0.1:' + env.get('COMPUERTA_PORT','8000')
    web = 'http://127.0.0.1:' + env.get('APP_PORT','8088')
    odoo = 'http://127.0.0.1:' + env.get('ODOO_PORT','8069')
    common = xmlrpc.client.ServerProxy(odoo+'/xmlrpc/2/common', allow_none=True)
    objects = xmlrpc.client.ServerProxy(odoo+'/xmlrpc/2/object', allow_none=True)
    uid = common.authenticate(env['ODOO_DB'], env['ODOO_READER_USER'], env['ODOO_READER_PASSWORD'], {})
    assert uid, 'La cuenta técnica no puede autenticarse en Odoo.'

    def rpc(model, method, *args, **kwargs):
        return objects.execute_kw(env['ODOO_DB'],uid,env['ODOO_READER_PASSWORD'],model,method,list(args),kwargs)

    checks = []
    def check(name, observed, expected=True):
        passed = observed == expected
        checks.append({'comprobacion':name,'observado':observed,'esperado':expected,'correcto':passed})
        print(('OK' if passed else 'ERROR')+' '+name)

    count = rpc('product.template','search_count',[('mys_catalogo','=',True)])
    check('50 productos del catálogo en Odoo', count, 50)
    check('Cuenta técnica no es usuario interno con permisos heredados', rpc('res.users','read',[uid],fields=['share'])[0]['share'])
    for model in ['res.partner','crm.lead','sale.order','sale.order.line','product.product','product.template','stock.quant']:
        for operation in ['write','create','unlink']:
            allowed = rpc(model,'check_access_rights',operation,raise_exception=False)
            check('Integración sin permiso '+operation+' en '+model, allowed, False)

    jar = http.cookiejar.CookieJar()
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def call(path, method='GET', data=None):
        req=urllib.request.Request(web+'/api/panel/'+path,method=method,
                                  data=json.dumps(data).encode() if data is not None else (b'' if method=='POST' else None),
                                  headers={'Content-Type':'application/json'})
        with browser.open(req, timeout=60) as response:
            return json.load(response)

    call('sesion','POST',{'rol':'VENTAS','password':env['ODOO_SELLER_PASSWORD']})
    catalog=call('catalogo')
    check('Panel lee 50 productos de Odoo real',len(catalog['productos']),50)
    check('50 precios disponibles', all(p['precio'] is not None for p in catalog['productos']))
    before = {p['sku']:(p['fisico'],p['reservado'],p['disponible']) for p in catalog['productos']}
    cases = [c for c in call('casos')['casos'] if c['id'].startswith('CAT-')]
    check('Tres casos con productos del catálogo',len(cases),3)
    results=[]
    for case in cases:
        result=call('casos/'+case['id']+'/evaluar','POST')
        response=result['respuesta']
        check(case['id']+' resultado comercial', response['status'], case['estado_esperado'])
        check(case['id']+' no crea pedido', response['order_id'], None)
        repeat=call('casos/'+case['id']+'/evaluar','POST')
        check(case['id']+' reintento estable',repeat,result)
        if response['code']=='DESCUENTO_SIN_APROBACION':
            events=call('bitacora/'+response['correlation_id'])['eventos']
            check('CAT-003 rechazo previo a I05',not any(e['interface_id']=='I05' for e in events))
        results.append({'caso':case['id'], 'respuesta':response})
    after={p['sku']:(p['fisico'],p['reservado'],p['disponible']) for p in call('catalogo')['productos']}
    check('Inventario de los 50 productos intacto',before,after)
    for path in ['form/decision-dueno','form/modo-determinista',
                 'webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat']:
        try:
            with urllib.request.urlopen('http://localhost:'+env.get('N8N_PORT','5678')+'/'+path,timeout=10) as r:
                code=r.status
        except urllib.error.HTTPError as e:
            code=e.code
        check('n8n protege '+path,code,401)
    out=ROOT/'evidencias'
    out.mkdir(exist_ok=True)
    report={'ejecutado_utc':datetime.now(timezone.utc).isoformat(),'entorno':'Odoo 18 + PostgreSQL 16 + FastAPI + n8n + Nginx reales en Docker',
            'comprobaciones':checks,'casos_catalogo':results,'correcto':all(c['correcto'] for c in checks)}
    (out/'sistema.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{sum(c["correcto"] for c in checks)}/{len(checks)} verificaciones correctas. app/evidencias/sistema.json')
    if not report['correcto']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
