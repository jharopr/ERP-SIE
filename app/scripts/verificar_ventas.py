"""Confirma y cancela únicamente la oferta sintética de verificar_odoo.py.

No modifica cotizaciones ajenas a esa prueba. La cancelación libera las reservas;
el pedido cancelado permanece como evidencia de trazabilidad.
"""
import ast
import json
from configurar import ROOT, leer_env
from verificar_odoo import Cliente


def main():
    env = leer_env()
    result = json.loads((ROOT / 'evidencias/validacion_odoo.json').read_text(encoding='utf-8'))
    order_id = result['new_version_order_id']
    url = 'http://localhost:' + env.get('APP_PORT', '8088')
    seller = Cliente(url, env, 'vendedor01', env['ODOO_SELLER_PASSWORD'])
    admin = Cliente(url, env, env['ODOO_USER'], env['ODOO_PASSWORD'])
    checks = []

    def ok(label, condition):
        assert condition, label
        checks.append(label)
        print('OK ' + label, flush=True)

    order = seller.call('sale.order', 'read', [[order_id]], fields=[
        'state', 'partner_id', 'mys_result', 'mys_discount_state', 'client_order_ref'])[0]
    assert order['partner_id'][1].startswith('Cliente prueba nativa '), 'Solo se permite la familia sintética del verificador.'
    assert order['client_order_ref'].startswith('COT-MYS-'), 'Referencia de prueba inesperada.'
    assert order['state'] == 'sent' and order['mys_result'] == 'ACEPTADA', 'Ejecute verificar_odoo.py para crear una oferta de prueba vigente.'

    def reserved():
        rows = admin.call('stock.quant', 'search_read', [[['location_id.usage', '=', 'internal']]],
                          fields=['reserved_quantity'])
        return sum(r['reserved_quantity'] for r in rows)

    baseline = reserved()
    confirmed = False
    try:
        seller.call('sale.order', 'action_confirm', [[order_id]])
        confirmed = True
        order = seller.call('sale.order', 'read', [[order_id]], fields=['state', 'mys_confirmed_at', 'mys_delivery_state'])[0]
        ok('Confirmación humana revalida con la compuerta y registra la venta', order['state'] == 'sale' and bool(order['mys_confirmed_at']))
        ok('Venta confirmada reserva productos y mantiene entrega pendiente', reserved() > baseline and order['mys_delivery_state'] == 'pending')
        for action, included in [('action_cotizaciones_mys', False), ('action_ventas_mys', True)]:
            data = seller.rpc('/web/action/load', {'action_id': 'mys_erp.' + action})
            domain = ast.literal_eval(data['domain'])
            found = seller.call('sale.order', 'search_count', [domain + [['id', '=', order_id]]])
            ok('Separación correcta en ' + data['name'], bool(found) == included)
        trace = seller.rpc('/mys/trace', {'order_id': order_id})
        ok('Trazabilidad reúne versiones de la oportunidad', {1, 2}.issubset({o['version'] for o in trace['orders']}))
        ok('Trazabilidad incluye motivo del dueño', any('Aprobación de demostración' in e['detail'] for e in trace['eventos']))
        ok('Trazabilidad incluye revalidación y confirmación',
           {'REVALIDACION_VENTA', 'VENTA'}.issubset({e['event_type'] for e in trace['eventos']}))
        filtered = seller.rpc('/mys/trace', {'order_id': order_id, 'version': '2', 'event_type': 'VENTA'})
        ok('Filtros de versión y tipo de evento funcionan', filtered['eventos'] and all(
            e['version'] == 2 and e['event_type'] == 'VENTA' for e in filtered['eventos']))
        for name in ('action_cotizaciones_mys', 'action_ventas_mys', 'action_evaluations', 'action_decisions'):
            action = seller.rpc('/web/action/load', {'action_id': 'mys_erp.' + name})
            view = seller.call(action['res_model'], 'get_views', [],
                views=[[action['search_view_id'][0], 'search']], options={})['views']['search']['arch']
            ok('Filtros comunes en ' + action['name'], all(key in view for key in ('partner_id', 'user_id', 'name="date"')))
    finally:
        if confirmed:
            seller.call('sale.order', 'action_cancel', [[order_id]], context={'disable_cancel_warning': True})
            ok('Cancelar la venta sintética libera todas sus reservas', abs(reserved() - baseline) < 0.0001)
    trace = seller.rpc('/mys/trace', {'order_id': order_id, 'event_type': 'VENTA'})
    ok('Historial conserva confirmación y cancelación', {'CONFIRMADA', 'CANCELADA'}.issubset({e['code'] for e in trace['eventos']}))
    (ROOT / 'evidencias/validacion_ventas.json').write_text(json.dumps({
        'order_id': order_id, 'checks': checks, 'count': len(checks), 'reservations_restored': True,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('VENTAS: %s comprobaciones correctas; reservas restauradas.' % len(checks), flush=True)


if __name__ == '__main__':
    main()
