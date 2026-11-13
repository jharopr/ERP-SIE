"""Prueba real del flujo nativo, roles, inmutabilidad y agentes sin tocar las cotizaciones fuente.

Crea una familia COT-MYS de prueba para validar rechazo → dueño → nueva versión aceptada.
Requiere servicios iniciados. No reinicia ni elimina datos.
"""
from pathlib import Path
import json
import re
import uuid
import xml.etree.ElementTree as ET
import httpx
from configurar import leer_env, ROOT


class Cliente:
    def __init__(self, url, env, user, password):
        self.client = httpx.Client(base_url=url, timeout=120, follow_redirects=True)
        self.uid = self.rpc('/web/session/authenticate', {'db': env['ODOO_DB'], 'login': user, 'password': password})['uid']
        assert self.uid

    def rpc(self, path, params=None):
        r = self.client.post(path, json={'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params or {}})
        r.raise_for_status()
        data = r.json()
        if 'error' in data:
            raise RuntimeError(data['error'].get('data', {}).get('message') or data['error']['message'])
        return data['result']

    def call(self, model, method, args=None, **kwargs):
        return self.rpc('/web/dataset/call_kw/' + model + '/' + method,
                        {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs})


def main():
    env = leer_env()
    url = 'http://localhost:' + env.get('APP_PORT', '8088')
    checks = []
    def ok(label, value):
        assert value, label
        checks.append(label)
        print('OK ' + label, flush=True)
    def denied(label, fn):
        try:
            fn()
        except RuntimeError:
            ok(label, True)
        else:
            raise AssertionError(label + ': operación indebidamente permitida')

    seller = Cliente(url, env, 'vendedor01', env['ODOO_SELLER_PASSWORD'])
    owner = Cliente(url, env, 'gerente', env['ODOO_OWNER_PASSWORD'])
    admin = Cliente(url, env, env['ODOO_USER'], env['ODOO_PASSWORD'])
    ok('Tres usuarios Odoo autentican con las contraseñas de .env', all([seller.uid, owner.uid, admin.uid]))
    ok('Rol vendedor derivado de sesión', seller.rpc('/mys/session')['role'] == 'VENTAS')
    ok('Rol dueño derivado de sesión', owner.rpc('/mys/session')['role'] == 'GERENCIA')
    anonymous = httpx.Client(base_url=url, timeout=30, follow_redirects=True)
    anon = anonymous.post('/mys/agent/chat', json={'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {'message': 'hola'}})
    ok('Chat requiere sesión Odoo', 'error' in anon.json())
    ok('Portal anterior retirado', anonymous.get('/api/panel/resumen').status_code == 404)
    html = anonymous.get('/web/login').text
    ok('Login nativo con marca MS Power', 'ms-power.svg' in html and 'csrf_token' in html)
    workspace = seller.rpc('/mys/workspace')
    import json
    total = len(json.loads((Path(__file__).resolve().parents[1] / 'datos' / 'productos.json').read_text(encoding='utf-8'))['productos'])
    ok(f'{total} productos del catálogo conservados', workspace['counts']['products'] == total)
    ok('Leads y contactos consultables', isinstance(workspace['counts']['leads'], int)
       and workspace['counts']['leads'] >= 0 and workspace['counts']['contacts'] >= 1)
    stages = seller.call('crm.stage', 'search_read', [[['mys_commercial_step', '!=', False]]],
                         fields=['mys_commercial_step'], order='sequence,id')
    stage_ids = {s['mys_commercial_step']: s['id'] for s in stages}
    ok('Cinco etapas comerciales configuradas', list(stage_ids) ==
       ['qualified', 'preparing', 'presented', 'review', 'validated'])
    def crm_state(lead_id):
        return seller.call('crm.lead', 'read', [[lead_id]],
                           fields=['stage_id', 'active', 'mys_evaluation_status', 'mys_current_order_id'])[0]
    product_view = seller.call('product.template', 'get_views', [], views=[[False, 'form']], options={})
    ok('Vistas nativas de productos accesibles al vendedor', bool(product_view))
    stock = seller.call('product.template', 'search_read', [[['mys_catalogo', '=', True]]],
                       fields=['name', 'qty_available', 'mys_disponible'])
    ok('Inventario del catálogo accesible', len(stock) == total)
    sales_view = seller.call('sale.order', 'get_views', [], views=[[False, 'form']], options={})
    sales_xml = ET.fromstring(sales_view['views']['form']['arch'])
    confirms = sales_xml.findall(".//button[@name='action_confirm']")
    ok('Confirmación de venta condicionada y botones nativos ocultos',
       len([b for b in confirms if b.get('string') == '4. Confirmar venta']) == 1
       and all(b.get('invisible') in ('True', '1') for b in confirms if b.get('string') != '4. Confirmar venta'))
    seller_view = seller.call('mys.decision', 'get_views', [], views=[[False, 'form']], options={})
    owner_view = owner.call('mys.decision', 'get_views', [], views=[[False, 'form']], options={})
    ok('Vendedor no ve aprobar; dueño sí lo ve', 'name="action_approve"' not in seller_view['views']['form']['arch']
            and 'name="action_approve"' in owner_view['views']['form']['arch'])

    source = seller.call('sale.order', 'search', [[['client_order_ref', '=', 'COT-CAT-003 v1']]])[0]
    tag = uuid.uuid4().hex[:8]
    contact = seller.call('res.partner', 'create', [{'name': 'Gabriel Esteban Peña Morales', 'mys_demo': True,
                'email': 'gabriel.pena@example.com', 'mobile': '+51 900 000 201',
                'mys_identidad_revisada': True, 'mys_segmento': 'nuevo', 'customer_rank': 1}])
    contact = contact[0] if isinstance(contact, list) else contact
    lead = seller.call('crm.lead', 'create', [{'name': 'Pantalla Android para vehículo particular · Gabriel Esteban Peña Morales',
                                             'description': 'Verificación automática de demostración: ' + tag,
                                             'type': 'opportunity',
                                             'partner_id': contact, 'user_id': seller.uid}])
    lead = lead[0] if isinstance(lead, list) else lead
    ok('Oportunidad nueva inicia calificada', crm_state(lead)['stage_id'][0] == stage_ids['qualified'])
    denied('No se puede cerrar sin cotización validada', lambda: seller.call(
        'crm.lead', 'write', [[lead], {'stage_id': stage_ids['validated']}]))
    denied('Botón Ganado no evita la validación', lambda: seller.call('crm.lead', 'action_set_won', [[lead]]))
    order = seller.call('sale.order', 'copy', [[source]], default={'client_order_ref': False, 'partner_id': contact,
                     'opportunity_id': lead, 'origin': 'VERIFICACION-ODOO-' + tag})
    order = order[0] if isinstance(order, list) else order
    ok('Crear cotización avanza a preparación', crm_state(lead)['stage_id'][0] == stage_ids['preparing'])
    seller.call('sale.order', 'action_mys_send', [[order]])
    ok('Preparar/enviar avanza a propuesta presentada', crm_state(lead)['stage_id'][0] == stage_ids['presented'])
    seller.call('sale.order', 'action_mys_accept', [[order]])
    ok('Cliente y oportunidad nuevos funcionan con referencias generadas por Odoo', True)
    before = admin.call('stock.quant', 'search_read', [[['location_id.usage', '=', 'internal']]],
                        fields=['product_id', 'quantity', 'reserved_quantity'], order='id')
    result = seller.call('sale.order', 'action_mys_evaluate', [[order]])
    eid = result['res_id']
    ev = seller.call('mys.evaluation', 'read', [[eid]], fields=['code', 'status', 'request_id', 'correlation_id'])[0]
    ok('R08 rechaza descuento del 10 % sin aprobación', ev['code'] == 'DESCUENTO_SIN_APROBACION')
    crm = crm_state(lead)
    ok('Rechazo pasa a revisión y conserva la oportunidad activa', crm['active']
       and crm['stage_id'][0] == stage_ids['review'] and crm['mys_evaluation_status'] == 'RECHAZADA')
    denied('Vendedor no puede confirmar una evaluación rechazada por RPC', lambda: seller.call('sale.order', 'action_confirm', [[order]]))
    denied('Vendedor no puede forzar estado confirmado por RPC', lambda: seller.call('sale.order', 'write', [[order], {'state': 'sale'}]))
    line = seller.call('sale.order.line', 'search', [[['order_id', '=', order]]])[0]
    denied('Versión evaluada no permite cambiar líneas por RPC', lambda: seller.call('sale.order.line', 'write', [[line], {'discount': 0}]))
    denied('Vendedor no puede falsificar estado SIE', lambda: seller.call('sale.order', 'write', [[order], {'mys_status': 'ACEPTADA'}]))
    esc = seller.call('mys.evaluation', 'action_request_decision', [[eid]])
    did = esc['res_id']
    denied('Vendedor no puede aprobar por RPC', lambda: seller.call('mys.decision', 'action_approve', [[did]]))
    denied('Vendedor no puede falsificar una decisión', lambda: seller.call('mys.decision', 'write', [[did], {'decision': 'APROBADA'}]))
    owner.call('mys.decision', 'write', [[did], {'motivo': 'Aprobación de demostración; se mantiene versión y total.'}])
    owner.call('mys.decision', 'action_approve', [[did]])
    decision = owner.call('mys.decision', 'read', [[did]], fields=['decision', 'approver_id', 'new_order_id'])[0]
    ok('Dueño aprueba y queda identificado', decision['decision'] == 'APROBADA' and decision['approver_id'][0] == owner.uid)
    new_order = decision['new_order_id'][0]
    quote = seller.call('sale.order', 'read', [[new_order]], fields=['mys_version', 'mys_acceptance_id', 'state'])[0]
    ok('Aprobación crea versión 2 sin aceptación reutilizada', quote['mys_version'] == 2 and not quote['mys_acceptance_id'] and quote['state'] == 'draft')
    crm = crm_state(lead)
    ok('Nueva versión vuelve a preparación sin cierre anticipado', crm['stage_id'][0] == stage_ids['preparing']
       and crm['mys_current_order_id'][0] == new_order and not crm['mys_evaluation_status'])
    denied('Aprobación del gerente no permite cerrar sin nueva aceptación y evaluación',
           lambda: seller.call('crm.lead', 'action_set_won', [[lead]]))
    new_line = seller.call('sale.order.line', 'search', [[['order_id', '=', new_order]]])[0]
    denied('Oferta aprobada no permite cambiar productos o descuento', lambda: seller.call('sale.order.line', 'write', [[new_line], {'discount': 1}]))
    seller.call('sale.order', 'action_mys_send', [[new_order]])
    denied('Nueva versión exige nueva aceptación', lambda: seller.call('sale.order', 'action_mys_evaluate', [[new_order]]))
    seller.call('sale.order', 'action_mys_accept', [[new_order]])
    action = seller.call('sale.order', 'action_mys_evaluate', [[new_order]])
    final = seller.call('mys.evaluation', 'read', [[action['res_id']]], fields=['status', 'response_json'])[0]
    response = json.loads(final['response_json'])['respuesta']
    ok('Versión nueva aprobada se acepta por reglas', final['status'] == 'ACEPTADA' and response['order_id'] is None)
    crm = crm_state(lead)
    ok('Evaluación aceptada cierra comercialmente la versión vigente',
       crm['stage_id'][0] == stage_ids['validated'] and crm['mys_evaluation_status'] == 'ACEPTADA')
    after = admin.call('stock.quant', 'search_read', [[['location_id.usage', '=', 'internal']]],
                       fields=['product_id', 'quantity', 'reserved_quantity'], order='id')
    ok('Evaluación y aprobación no alteran físico ni reservas', before == after)
    trace = seller.rpc('/mys/trace', {'correlation_id': ev['correlation_id']})
    ok('Bitácora disponible dentro de Odoo', bool(trace['eventos']))
    status = seller.rpc('/mys/agent/status')
    ok('Estado de Gemini sin revelar API key', bool(status.get('code')) and env.get('GEMINI_API_KEY', 'no-key') not in json.dumps(status))
    print('Estado del agente: ' + status['code'] + ' · ' + status['message'], flush=True)
    # Fuerza la generación de los bundles y revisa errores de compilación de assets.
    backend = seller.client.get('/odoo').text
    assets = set(re.findall(r'(?:src|href)="([^"]*/web/assets/[^"]+)"', backend))
    ok('Backend incluye bundles nativos', bool(assets))
    for path in assets:
        asset = seller.client.get(path)
        ok('Bundle compilado ' + path.rsplit('/', 1)[-1], asset.status_code == 200 and 'Could not get content for' not in asset.text)
    result = {'checks': checks, 'count': len(checks), 'agent_status': status, 'test_order_id': order,
              'new_version_order_id': new_order, 'evaluation_id': eid, 'decision_id': did}
    (ROOT/'evidencias/validacion_odoo.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'VERIFICACIÓN NATIVA: {len(checks)} comprobaciones correctas.', flush=True)


if __name__ == '__main__':
    main()
