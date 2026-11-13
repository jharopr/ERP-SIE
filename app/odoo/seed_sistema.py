"""Inicializa Odoo y el Agente SIE, instala MYS y carga el catálogo completo de la empresa.

Ejecutar en compuerta: python /plataforma/seed_sistema.py [--reiniciar].
--reiniciar limpia solamente las transacciones de la demo del agente. No elimina
la base Odoo ni los pedidos ajenos. Las escrituras requieren el administrador.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, '/srv')
spec = importlib.util.spec_from_file_location('seed_original', '/seed/seed_odoo.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
from app import escenario as E
from app.config import Config, ahora_lima
from app.repositorio import Repositorio

CATALOGO = Path(os.environ.get('CATALOGO_PATH', '/catalogo/productos.json'))


def instalar_mys(odoo):
    odoo.x('ir.module.module', 'update_list')
    modules = odoo.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
    if not modules:
        raise RuntimeError('No se encuentra mys_erp. Revise el montaje /mnt/extra-addons.')
    if modules[0]['state'] != 'installed':
        legacy.llamar_tolerante(odoo, 'ir.module.module', 'button_immediate_install', [modules[0]['id']])
        odoo.conectar()


RENOMBRES = {'ven-demo-01': ('vendedor01', 'Vendedor 01'), 'ger-demo-01': ('gerente', 'Gerente')}


def renombrar_usuarios(odoo):
    """Instalaciones anteriores: renombra los usuarios en lugar de crear otros (conserva su historial)."""
    for viejo, (nuevo, nombre) in RENOMBRES.items():
        antes = odoo.buscar('res.users', [('login', '=', viejo)])
        if antes and not odoo.buscar('res.users', [('login', '=', nuevo)]):
            odoo.x('res.users', 'write', antes[:1], {'login': nuevo, 'name': nombre})
            legacy.log(f'usuario {viejo} renombrado a {nuevo}')
    empresa = odoo.buscar('res.company', [('name', '=', 'MYS Demo (datos sintéticos)')])
    if empresa:
        odoo.x('res.company', 'write', empresa, {'name': 'Importaciones MYS Hermanos'})


def usuarios(odoo):
    renombrar_usuarios(odoo)
    group_field = 'groups_id'
    if 'group_ids' in odoo.x('res.users', 'fields_get', attributes=['type']):
        group_field = 'group_ids'
    reader_group = odoo.ref('mys_erp.group_agente_lectura')
    reader, _ = odoo.upsert('res.users', [('login', '=', os.environ['ODOO_READER_USER'])],
                           {'name': 'Integración Agente SIE (solo lectura)', 'login': os.environ['ODOO_READER_USER'],
                            'password': os.environ['ODOO_READER_PASSWORD'], group_field: [(6, 0, [reader_group])]})
    seller = odoo.buscar('res.users', [('login', '=', E.VENDEDOR_LOGIN)])[0]
    home = odoo.ref('mys_erp.action_workspace')
    odoo.x('res.users', 'write', [seller], {'password': os.environ['ODOO_SELLER_PASSWORD'],
           group_field: [(4, odoo.ref('mys_erp.group_mys_seller'))], 'action_id': home})
    owner_groups = [odoo.ref(g) for g in ['base.group_user', 'sales_team.group_sale_manager',
                                         'stock.group_stock_manager', 'purchase.group_purchase_manager',
                                         'mys_erp.group_mys_manager']]
    owner, _ = odoo.upsert('res.users', [('login', '=', 'gerente')],
                          {'name': 'Gerente', 'login': 'gerente', 'password': os.environ['ODOO_OWNER_PASSWORD'],
                           'email': os.environ.get('CORREO_DUENO') or 'dueno@mys-demo.local',
                           group_field: [(6, 0, [g for g in owner_groups if g])], 'action_id': home})
    # admin es la cuenta técnica: configura Odoo, pero NO aprueba. Solo el gerente decide.
    admin = odoo.buscar('res.users', [('login', '=', os.environ['ODOO_USER'])])[0]
    odoo.x('res.users', 'write', [admin], {group_field: [(3, odoo.ref('mys_erp.group_mys_manager'))], 'action_id': False})
    legacy.log(f'Usuarios preparados: vendedor, dueño e integración de lectura ({reader}). Claves no impresas.')
    return seller


def catalogo(odoo, data, ubicacion):
    ids = {}
    # Categorías una sola vez (dos niveles, como en la lista de la empresa).
    padres, categorias = {}, {}
    for nombre in sorted({p['categoria'] for p in data['productos']}):
        padres[nombre], _ = odoo.upsert('product.category', [('name', '=', nombre), ('parent_id', '=', False)],
                                        {'name': nombre})
    for padre, sub in sorted({(p['categoria'], p['subcategoria']) for p in data['productos']}):
        categorias[(padre, sub)], _ = odoo.upsert('product.category', [('name', '=', sub), ('parent_id', '=', padres[padre])],
                                                  {'name': sub, 'parent_id': padres[padre]})
    uom = {'unidad': odoo.ref('uom.product_uom_unit'), 'metro': odoo.ref('uom.product_uom_meter')}
    existentes = {t['default_code']: t['id'] for t in odoo.leer('product.template',
                  [('default_code', 'in', [p['sku'] for p in data['productos']])], ['default_code'])}
    for p in data['productos']:
        servicio = p.get('tipo') == 'servicio'
        unidad = uom['metro'] if p.get('unidad') == 'metro' and uom['metro'] else uom['unidad']
        category = categorias[(p['categoria'], p['subcategoria'])]
        values = {'name': p['nombre'], 'default_code': p['sku'], 'list_price': float(p['precio_venta']),
                  'type': 'service' if servicio else 'consu', 'is_storable': not servicio,
                  'uom_id': unidad, 'uom_po_id': unidad, 'sale_ok': True, 'purchase_ok': True,
                  'taxes_id': [(6, 0, [])], 'supplier_taxes_id': [(6, 0, [])], 'categ_id': category,
                  'mys_catalogo': True, 'mys_datos_sinteticos': True, 'mys_codigo_fuente': p['codigo_original'],
                  'mys_fila_fuente': p['source_row'], 'mys_archivo_fuente': data['metadata']['archivo_fuente'],
                  'mys_lote_sha256': data['metadata']['sha256_fuente'], 'mys_prioridad_demo': p['prioridad_demo'],
                  'mys_precio_mayorista': float(p['precio_mayorista'] or p['precio_venta']), 'active': True}
        if p['costo_referencia'] is not None:
            values['standard_price'] = float(p['costo_referencia'])
        if p['sku'] in existentes:
            odoo.x('product.template', 'write', [existentes[p['sku']]], values)
        else:
            existentes[p['sku']] = odoo.x('product.template', 'create', values)
    ids = {v['default_code']: v['id'] for v in odoo.leer('product.product',
           [('default_code', 'in', [p['sku'] for p in data['productos']])], ['default_code'])}
    # No crea ni modifica reservas. Los saldos objetivo son explícitamente de prueba.
    # Un solo ajuste de inventario para los productos cuyo saldo difiere (los servicios no tienen stock).
    almacenables = {p['sku']: p for p in data['productos'] if p.get('tipo') != 'servicio'}
    quants = {q['product_id'][0]: q for q in odoo.leer('stock.quant',
              [('product_id', 'in', [ids[s] for s in almacenables]), ('location_id', '=', ubicacion)],
              ['product_id', 'quantity'])}
    por_aplicar = []
    for sku, p in almacenables.items():
        q = quants.get(ids[sku])
        if q and int(q['quantity']) == p['stock_demo']:
            continue
        if q:
            odoo.x('stock.quant', 'write', [q['id']], {'inventory_quantity': p['stock_demo']}, context={'inventory_mode': True})
            por_aplicar.append(q['id'])
        else:
            por_aplicar.append(odoo.x('stock.quant', 'create', {'product_id': ids[sku], 'location_id': ubicacion,
                                                                'inventory_quantity': p['stock_demo']},
                                      context={'inventory_mode': True}))
    if por_aplicar:
        legacy.llamar_tolerante(odoo, 'stock.quant', 'action_apply_inventory', por_aplicar)
    legacy.log(f'Catálogo cargado: {len(ids)} referencias de empresa ({len(por_aplicar)} saldos ajustados) + 2 SKU académicos PC3.')
    return ids


def datos_comerciales(odoo, repo, data, productos, vendedor, ubicacion):
    now = ahora_lima()
    odoo.x('res.partner', 'action_mys_prepare_demo_contacts')
    clients = {c['ref']: c['id'] for c in odoo.leer('res.partner',
               [('ref', 'in', [f'CLI-DEMO-{i:03d}' for i in range(1, 11)])], ['ref'])}
    for ref in clients:
        with repo.conexion() as db:
            db.execute('INSERT INTO clientes_ext VALUES(?,?,?) ON CONFLICT(ref) DO UPDATE SET identity_reviewed=1',
                       (ref, 1, 'PUBLICO_GENERAL_NUEVO'))
    supplier, _ = odoo.upsert('res.partner', [('ref', '=', 'PROV-DEMO-001')],
                              {'name': 'Proveedor de audio de prueba', 'ref': 'PROV-DEMO-001', 'is_company': True,
                               'supplier_rank': 1, 'mys_demo': True, 'mys_segmento': 'proveedor'})
    # Registrar leads y oportunidades reales de Odoo, conservando los IDs del agente.
    for i in range(1, 7):
        odoo.upsert('crm.lead', ['|', ('mys_demo_key', '=', f'LEAD-MYS-{i:03d}'), ('name', '=', f'LEAD-MYS-{i:03d}')],
                    {'name': f'LEAD-MYS-{i:03d}', 'type': 'lead', 'partner_id': clients[f'CLI-DEMO-{i:03d}'],
                     'mys_demo_key': f'LEAD-MYS-{i:03d}',
                     'user_id': vendedor, 'description': 'Visita espontánea en tienda. Datos sintéticos de demostración.'})
    opportunities = legacy.asegurar_oportunidades(odoo, clients)
    for opp, oid in opportunities.items():
        odoo.x('crm.lead', 'write', [oid], {'user_id': vendedor})
    cases = []
    with repo.conexion() as db:
        actors = db.execute('SELECT opportunities_json FROM actores WHERE actor_id=?', (E.VENDEDOR,)).fetchone()
        assigned = json.loads(actors[0])
    for i, p in enumerate(data['productos'][:3], 1):
        opp = f'OPP-CAT-{i:03d}'
        oid, _ = odoo.upsert('crm.lead', [('mys_reference', '=', opp)],
                             {'name': opp, 'type': 'opportunity', 'partner_id': clients['CLI-DEMO-003'],
                              'user_id': vendedor, 'description': 'Oportunidad de demostración con producto del catálogo.'})
        discount = 10 if i == 3 else 5
        total = format((Decimal(p['precio_venta']) * 5 * (1 - Decimal(discount) / 100)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP), 'f')
        cot, ace, request, cor = (f'COT-CAT-{i:03d}', f'ACE-CAT-{i:03d}', f'SOL-CAT-{i:03d}', f'COR-CAT-{i:03d}')
        values = {'partner_id': clients['CLI-DEMO-003'], 'user_id': vendedor, 'opportunity_id': oid,
                  'client_order_ref': f'{cot} v1', 'validity_date': now.date().isoformat()}
        quote, _ = odoo.upsert('sale.order', [('client_order_ref', '=', values['client_order_ref'])], values)
        state = odoo.leer('sale.order', [('id', '=', quote)], ['state'])[0]['state']
        if state not in ('draft', 'sent'):
            raise RuntimeError(f'{cot} ya se confirmó/canceló manualmente. No se sobrescribe; use una base demo nueva.')
        odoo.x('sale.order', 'write', [quote], {'order_line': [(5, 0, 0), (0, 0, {
            'product_id': productos[p['sku']], 'product_uom_qty': 5, 'price_unit': float(p['precio_venta']),
            'discount': discount, 'tax_id': [(6, 0, [])]})]})
        legacy.poner_estado(odoo, quote, state, 'sent')
        with repo.conexion() as db:
            db.execute('INSERT INTO aceptaciones VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(acceptance_id) DO UPDATE SET total=excluded.total,accepted_at=excluded.accepted_at',
                       (ace, E.COMPANY_ID, cot, 1, 'CLI-DEMO-003', total, now.isoformat(), 'SEED'))
        assigned.append(opp)
        cases.append({'id': f'CAT-{i:03d}', 'sku': p['sku'], 'total_cotizado': total,
                      'solicitud': {'contract_version': '1.0', 'company_id': E.COMPANY_ID, 'request_id': request,
                                    'correlation_id': cor, 'opportunity_id': opp, 'customer_id': 'CLI-DEMO-003',
                                    'quotation_id': cot, 'quotation_version': 1, 'acceptance_id': ace},
                      'estado_esperado': ['ACEPTADA', 'PROMESA_CONDICIONADA', 'RECHAZADA'][i-1]})
    with repo.conexion() as db:
        db.execute('UPDATE actores SET opportunities_json=? WHERE actor_id=?',
                   (json.dumps(sorted(set(assigned))), E.VENDEDOR))
    # Guardar el escenario de catálogo en el volumen de la compuerta para reproducirlo.
    Path('/data/casos_catalogo.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding='utf-8')
    odoo.x('res.partner', 'action_mys_prepare_demo_contacts')
    odoo.x('crm.lead', 'action_mys_prepare_demo_presentation')
    legacy.log('10 contactos peruanos de ejemplo, 1 proveedor, 6 leads y 3 oportunidades/cotizaciones de catálogo preparados.')


def historial_compras(odoo):
    """Ventas pasadas SINTÉTICAS (datos/historial_compras.json) para el perfil del cliente.

    Se confirman (con contexto de seed) y se cancela su entrega, así no reservan ni descuentan
    stock de los casos PC3. Idempotente: busca por la referencia HIS-… y no duplica.
    """
    from datetime import datetime, timedelta
    archivo = CATALOGO.parent / 'historial_compras.json'
    if not archivo.exists():
        return
    datos = json.loads(archivo.read_text(encoding='utf-8'))
    precios = {p['sku']: float(p['precio_venta']) for p in json.loads(CATALOGO.read_text(encoding='utf-8'))['productos']}
    skus = sorted({l[0] for o in datos['pedidos'] for l in o['lineas']})
    productos = {r['default_code']: r['id'] for r in odoo.leer('product.product', [('default_code', 'in', skus)], ['default_code'])}
    vendedor = odoo.buscar('res.users', [('login', '=', E.VENDEDOR_LOGIN)])[0]
    contexto = {'mys_seed': True, 'tracking_disable': True, 'mail_notrack': True}
    creados, contadores = 0, {}
    for pedido in datos['pedidos']:
        contadores[pedido['cliente']] = contadores.get(pedido['cliente'], 0) + 1
        ref = 'HIS-%s-%02d' % (pedido['cliente'], contadores[pedido['cliente']])
        if odoo.buscar('sale.order', [('client_order_ref', '=', ref)]):
            continue
        cliente = odoo.buscar('res.partner', [('ref', '=', pedido['cliente'])])
        if not cliente:
            continue
        oid = odoo.x('sale.order', 'create', {
            'partner_id': cliente[0], 'user_id': vendedor, 'client_order_ref': ref,
            'order_line': [(0, 0, {'product_id': productos[sku], 'product_uom_qty': cant, 'price_unit': precios[sku],
                                   'discount': desc, 'tax_id': [(6, 0, [])]}) for sku, cant, desc in pedido['lineas']]},
            context=contexto)
        if pedido['estado'] == 'sale':
            legacy.llamar_tolerante(odoo, 'sale.order', 'action_confirm', [oid], contexto)
            entregas = odoo.buscar('stock.picking', [('sale_id', '=', oid), ('state', 'not in', ['done', 'cancel'])])
            if entregas:  # la venta histórica no debe tocar el stock de la demo
                legacy.llamar_tolerante(odoo, 'stock.picking', 'action_cancel', entregas, contexto)
        else:
            legacy.llamar_tolerante(odoo, 'sale.order', 'action_cancel', [oid], {**contexto, 'disable_cancel_warning': True})
        fecha = (datetime.utcnow() - timedelta(days=pedido['dias'])).strftime('%Y-%m-%d %H:%M:%S')
        odoo.x('sale.order', 'write', [oid], {'date_order': fecha}, context=contexto)
        creados += 1
    legacy.log(f'historial de compras: {creados} pedidos nuevos (de {len(datos["pedidos"])} declarados).')


def categoria_pc3(odoo):
    """RAD-7BT y RAD-10X (casos PC3) bajo «Radios y Pantallas», no en la categoría genérica de Odoo."""
    padre, _ = odoo.upsert('product.category', [('name', '=', 'Radios y Pantallas'), ('parent_id', '=', False)],
                           {'name': 'Radios y Pantallas'})
    sub, _ = odoo.upsert('product.category', [('name', '=', 'Casos PC3 (genéricos)'), ('parent_id', '=', padre)],
                         {'name': 'Casos PC3 (genéricos)', 'parent_id': padre})
    plantillas = odoo.buscar('product.template', [('default_code', 'in', list(E.PRODUCTOS))])
    if plantillas:
        odoo.x('product.template', 'write', plantillas, {'categ_id': sub})


CANAL_DEMO = {'CLI-DEMO-001': 'whatsapp', 'CLI-DEMO-002': 'tienda', 'CLI-DEMO-003': 'telefono',
              'CLI-DEMO-004': 'web', 'CLI-DEMO-005': 'redes', 'CLI-DEMO-006': 'referido'}


def canales_demo(odoo):
    """Canal de entrada de los leads de la demo (solo si está vacío: no pisa lo registrado a mano)."""
    asignados = 0
    for ref, canal in CANAL_DEMO.items():
        leads = odoo.buscar('crm.lead', [('partner_id.ref', '=', ref), ('type', '=', 'lead'), ('mys_canal', '=', False)])
        if leads:
            odoo.x('crm.lead', 'write', leads, {'mys_canal': canal}, context={'tracking_disable': True})
            asignados += len(leads)
    legacy.log(f'canal de entrada asignado a {asignados} leads de la demo.')


def calcular_perfiles(odoo):
    """Perfil comercial de todos los clientes (las mismas reglas que la tarea diaria de Odoo)."""
    clientes = odoo.buscar('res.partner', ['|', ('customer_rank', '>', 0), ('mys_demo', '=', True),
                                           ('mys_segmento', '!=', 'proveedor'), ('ref', '!=', False)])
    if clientes:
        odoo.x('res.partner', 'action_mys_recalcular_perfil', clientes)
    niveles = odoo.leer('res.partner', [('id', 'in', clientes), ('mys_nivel', '!=', False)], ['ref', 'mys_nivel'])
    resumen = {}
    for c in niveles:
        resumen[c['mys_nivel']] = resumen.get(c['mys_nivel'], 0) + 1
    legacy.log(f'perfil comercial calculado para {len(clientes)} clientes: {resumen}')


def limpiar_notificaciones(odoo):
    """Cancela los avisos automáticos que el propio seed genera en Odoo («Te asignaron S000…»,
    «Cambio de contraseña»): con correo activo llenarían el buzón del dueño en cada arranque.
    Nunca toca los avisos de decisión ([MYS] …) ni correos ya enviados."""
    ids = odoo.buscar('mail.mail', [('state', 'in', ['outgoing', 'exception']), ('subject', 'not like', '[MYS]%')])
    if ids:
        odoo.x('mail.mail', 'write', ids, {'state': 'cancel'})  # cancelados: no se envían; el historial queda
        legacy.log(f'{len(ids)} avisos automáticos del seed cancelados (asignaciones y cambios de contraseña).')


def main():
    data = json.loads(CATALOGO.read_text(encoding='utf-8'))
    total = len(data['productos'])
    if total < 50 or len({p['sku'] for p in data['productos']}) != total:
        raise RuntimeError('El catálogo requiere al menos 50 productos (los de demostración) con SKU únicos.')
    if '--reiniciar' not in sys.argv and '--crear-v3' not in sys.argv:
        config = Config.desde_entorno()
        existing = legacy.Odoo(config.odoo_url, config.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
        if config.odoo_db in existing.proxy('/xmlrpc/2/db').list():
            existing.conectar()
            modules = existing.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
            if modules and modules[0]['state'] == 'installed' and len(existing.buscar('product.template', [('mys_catalogo', '=', True)])) == total:
                usuarios(existing)
                existing.x('res.partner', 'action_mys_prepare_demo_contacts')
                existing.x('crm.lead', 'action_mys_prepare_demo_presentation')
                categoria_pc3(existing)
                canales_demo(existing)
                historial_compras(existing)
                calcular_perfiles(existing)
                limpiar_notificaciones(existing)
                print('Instalación existente: usuarios sincronizados. Cotizaciones, versiones, stock y decisiones conservados.', flush=True)
                return
    # Mantiene todos los casos y reglas del paquete existente. Instala el addon como
    # parte del primer arranque para que sus campos estén presentes antes del seed.
    legacy.MODULOS += ['mys_erp']
    cfg0 = Config.desde_entorno()
    previo = legacy.Odoo(cfg0.odoo_url, cfg0.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
    if cfg0.odoo_db in previo.proxy('/xmlrpc/2/db').list():
        previo.conectar()
        renombrar_usuarios(previo)  # antes del seed original, que busca al vendedor por su login nuevo
    if '--reiniciar' in sys.argv:
        cfg = Config.desde_entorno()
        admin = legacy.Odoo(cfg.odoo_url, cfg.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
        if cfg.odoo_db in admin.proxy('/xmlrpc/2/db').list():
            admin.conectar()
            installed = admin.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
            if installed and installed[0]['state'] == 'installed':
                admin.x('mys.gateway', 'action_reset_demo', [], context={'mys_seed': True})
    legacy.main()
    config = Config.desde_entorno()
    odoo = legacy.Odoo(config.odoo_url, config.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
    odoo.conectar()
    instalar_mys(odoo)
    seller = usuarios(odoo)
    _, location = legacy.configurar_empresa(odoo)
    repo = Repositorio(config.database)
    with repo.conexion() as db:
        db.execute("INSERT INTO mapa_ids VALUES('usuario_odoo_id',?,?) ON CONFLICT(tipo,externo) DO UPDATE SET odoo=excluded.odoo",
                   (E.VENDEDOR, str(seller)))
    products = catalogo(odoo, data, location)
    datos_comerciales(odoo, repo, data, products, seller, location)
    categoria_pc3(odoo)
    canales_demo(odoo)
    historial_compras(odoo)
    calcular_perfiles(odoo)
    limpiar_notificaciones(odoo)
    print(f'SISTEMA MYS LISTO: {total} referencias de catálogo, 2 SKU PC3, Odoo y Agente SIE conectados.', flush=True)


if __name__ == '__main__':
    main()
