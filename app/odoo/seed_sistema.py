"""Inicializa Odoo y el Agente SIE, instala MYS y carga el catálogo de 50 productos.

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

CATALOGO = Path(os.environ.get('CATALOGO_PATH', '/catalogo/productos_50.json'))


def instalar_mys(odoo):
    odoo.x('ir.module.module', 'update_list')
    modules = odoo.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
    if not modules:
        raise RuntimeError('No se encuentra mys_erp. Revise el montaje /mnt/extra-addons.')
    if modules[0]['state'] != 'installed':
        legacy.llamar_tolerante(odoo, 'ir.module.module', 'button_immediate_install', [modules[0]['id']])
        odoo.conectar()


def usuarios(odoo):
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
    owner, _ = odoo.upsert('res.users', [('login', '=', 'ger-demo-01')],
                          {'name': 'Dueño Demo MYS', 'login': 'ger-demo-01', 'password': os.environ['ODOO_OWNER_PASSWORD'],
                           group_field: [(6, 0, [g for g in owner_groups if g])], 'action_id': home})
    admin = odoo.buscar('res.users', [('login', '=', os.environ['ODOO_USER'])])[0]
    odoo.x('res.users', 'write', [admin], {group_field: [(4, odoo.ref('mys_erp.group_mys_manager'))], 'action_id': home})
    legacy.log(f'Usuarios preparados: vendedor, dueño e integración de lectura ({reader}). Claves no impresas.')
    return seller


def catalogo(odoo, data, ubicacion):
    ids = {}
    for p in data['productos']:
        parent, _ = odoo.upsert('product.category', [('name', '=', p['categoria']), ('parent_id', '=', False)],
                               {'name': p['categoria']})
        category, _ = odoo.upsert('product.category', [('name', '=', p['subcategoria']), ('parent_id', '=', parent)],
                                 {'name': p['subcategoria'], 'parent_id': parent})
        values = {'name': p['nombre'], 'default_code': p['sku'], 'list_price': float(p['precio_venta']),
                  'type': 'consu', 'is_storable': True, 'sale_ok': True, 'purchase_ok': True,
                  'taxes_id': [(6, 0, [])], 'supplier_taxes_id': [(6, 0, [])], 'categ_id': category,
                  'mys_catalogo': True, 'mys_datos_sinteticos': True, 'mys_codigo_fuente': p['codigo_original'],
                  'mys_fila_fuente': p['source_row'], 'mys_archivo_fuente': data['metadata']['archivo_fuente'],
                  'mys_lote_sha256': data['metadata']['sha256_fuente'], 'mys_prioridad_demo': p['prioridad_demo'],
                  'mys_precio_mayorista': float(p['precio_mayorista'] or p['precio_venta']), 'active': True}
        if p['costo_referencia'] is not None:
            values['standard_price'] = float(p['costo_referencia'])
        template, _ = odoo.upsert('product.template', [('default_code', '=', p['sku'])], values)
        product = odoo.buscar('product.product', [('product_tmpl_id', '=', template)])[0]
        ids[p['sku']] = product
        # No crea ni modifica reservas. Los saldos objetivo son explícitamente de prueba.
        quant, _ = odoo.upsert('stock.quant', [('product_id', '=', product), ('location_id', '=', ubicacion)],
                              {'product_id': product, 'location_id': ubicacion, 'inventory_quantity': p['stock_demo']})
        legacy.llamar_tolerante(odoo, 'stock.quant', 'action_apply_inventory', [quant])
    legacy.log(f'Catálogo cargado: {len(ids)} referencias de empresa + 2 SKU académicos PC3.')
    return ids


def datos_comerciales(odoo, repo, data, productos, vendedor, ubicacion):
    now = ahora_lima()
    clients = {}
    for i in range(1, 9):
        ref = f'CLI-DEMO-{i:03d}'
        clients[ref], _ = odoo.upsert('res.partner', [('ref', '=', ref)],
                                     {'name': f'Cliente de prueba {i:03d}', 'ref': ref, 'mys_demo': True,
                                      'mys_segmento': 'nuevo' if i != 2 else 'recurrente',
                                      'mys_identidad_revisada': True, 'active': True, 'customer_rank': 1})
        with repo.conexion() as db:
            db.execute('INSERT INTO clientes_ext VALUES(?,?,?) ON CONFLICT(ref) DO UPDATE SET identity_reviewed=1',
                       (ref, 1, 'PUBLICO_GENERAL_NUEVO'))
    supplier, _ = odoo.upsert('res.partner', [('ref', '=', 'PROV-DEMO-001')],
                              {'name': 'Proveedor de audio de prueba', 'ref': 'PROV-DEMO-001', 'is_company': True,
                               'supplier_rank': 1, 'mys_demo': True, 'mys_segmento': 'proveedor'})
    # Registrar leads y oportunidades reales de Odoo, conservando los IDs del agente.
    for i in range(1, 7):
        odoo.upsert('crm.lead', [('name', '=', f'LEAD-MYS-{i:03d}')],
                    {'name': f'LEAD-MYS-{i:03d}', 'type': 'lead', 'partner_id': clients[f'CLI-DEMO-{i:03d}'],
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
        oid, _ = odoo.upsert('crm.lead', [('name', '=', opp)],
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
    legacy.log('8 clientes, 1 proveedor, 6 leads y 3 oportunidades/cotizaciones de catálogo preparados.')


def main():
    data = json.loads(CATALOGO.read_text(encoding='utf-8'))
    if len(data['productos']) != 50 or len({p['sku'] for p in data['productos']}) != 50:
        raise RuntimeError('Se requieren exactamente 50 productos de catálogo con SKU únicos.')
    if '--reiniciar' not in sys.argv and '--crear-v3' not in sys.argv:
        config = Config.desde_entorno()
        existing = legacy.Odoo(config.odoo_url, config.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
        if config.odoo_db in existing.proxy('/xmlrpc/2/db').list():
            existing.conectar()
            modules = existing.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
            if modules and modules[0]['state'] == 'installed' and len(existing.buscar('product.template', [('mys_catalogo', '=', True)])) == 50:
                usuarios(existing)
                print('Instalación existente: usuarios sincronizados. Cotizaciones, versiones, stock y decisiones conservados.', flush=True)
                return
    # Mantiene todos los casos y reglas del paquete existente. Instala el addon como
    # parte del primer arranque para que sus campos estén presentes antes del seed.
    legacy.MODULOS += ['mys_erp']
    if '--reiniciar' in sys.argv:
        cfg = Config.desde_entorno()
        admin = legacy.Odoo(cfg.odoo_url, cfg.odoo_db, os.environ['ODOO_USER'], os.environ['ODOO_PASSWORD'])
        if cfg.odoo_db in admin.proxy('/xmlrpc/2/db').list():
            admin.conectar()
            installed = admin.leer('ir.module.module', [('name', '=', 'mys_erp')], ['state'])
            if installed and installed[0]['state'] == 'installed':
                admin.x('mys.gateway', 'action_reset_demo', [])
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
    print('SISTEMA MYS LISTO: 50 referencias de catálogo, 2 SKU PC3, Odoo y Agente SIE conectados.', flush=True)


if __name__ == '__main__':
    main()
