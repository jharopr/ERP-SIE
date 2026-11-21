"""Contactos MYS y perfil comercial del cliente.

El perfil se calcula con REGLAS FIJAS a partir de las ventas confirmadas en Odoo (no con IA),
para que el resultado sea siempre el mismo y cualquiera pueda revisarlo. El agente y el gerente
lo leen para recomendar y decidir; el perfil NO cambia los topes de descuento (eso exigiría
cambiar las reglas del contrato y lo decide el negocio).
"""
from collections import Counter
from datetime import timedelta
import json
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from odoo.tools import file_open

# Reglas del perfil (documentadas en app/docs/PERFIL_CLIENTE.md)
VENTANA_DIAS = 180                 # últimos 6 meses
MAYORISTA_MONTO = 5000.0           # S/ comprados en la ventana
MAYORISTA_UNIDADES = 30            # unidades compradas en la ventana
FRECUENTE_COMPRAS = 3              # compras confirmadas en la ventana
INACTIVO_DIAS = 90                 # sin comprar desde hace más de 90 días

NIVELES = [('nuevo', 'Nuevo'), ('ocasional', 'Ocasional'), ('frecuente', 'Frecuente'), ('mayorista', 'Mayorista')]

# Categorías que se suelen comprar juntas en car audio (complementos).
COMPLEMENTOS = {
    'Radios y Pantallas': ['Cables y Conexiones', 'Medios y Parlantes', 'Servicios'],
    'Medios y Parlantes': ['Tweeters', 'Amplificadores', 'Cables y Conexiones'],
    'Subwoofers': ['Amplificadores', 'Cables y Conexiones'],
    'Amplificadores': ['Subwoofers', 'Cables y Conexiones', 'Accesorios Automotrices'],
    'Tweeters': ['Medios y Parlantes', 'Cables y Conexiones'],
    'Ecualizadores': ['Amplificadores', 'Cables y Conexiones'],
    'Cables y Conexiones': ['Accesorios Automotrices'],
}


def clasificar(compras, monto, unidades):
    """Nivel y motivo. Función pura: mismas cifras → mismo nivel."""
    if compras == 0:
        return 'nuevo', 'Sin compras confirmadas en los últimos 6 meses.'
    if monto >= MAYORISTA_MONTO:
        return 'mayorista', 'Compró S/ %s en 6 meses (umbral: S/ %s).' % (f'{monto:,.2f}', f'{MAYORISTA_MONTO:,.0f}')
    if unidades >= MAYORISTA_UNIDADES:
        return 'mayorista', 'Compró %g unidades en 6 meses (umbral: %d).' % (unidades, MAYORISTA_UNIDADES)
    if compras >= FRECUENTE_COMPRAS:
        return 'frecuente', '%d compras en 6 meses (umbral: %d).' % (compras, FRECUENTE_COMPRAS)
    return 'ocasional', '%d compra(s) en 6 meses.' % compras


def categoria_principal(product):
    """Categoría de primer nivel del catálogo MYS (ignora la raíz genérica «All» de Odoo)."""
    categ = product.categ_id
    cadena = []
    while categ:
        cadena.insert(0, categ.name)
        categ = categ.parent_id
    cadena = [c for c in cadena if c not in ('All', 'Todos', 'Saleable', 'Vendible')]
    return cadena[0] if cadena else 'Otros'


class ContactoMYS(models.Model):
    _inherit = 'res.partner'

    mys_demo = fields.Boolean('Datos de prueba MYS', index=True)
    mys_segmento = fields.Selection([('nuevo', 'Público general nuevo'), ('recurrente', 'Cliente recurrente'),
                                     ('proveedor', 'Proveedor de demostración')], string='Segmento comercial')
    mys_identidad_revisada = fields.Boolean('Identidad sintética revisada')
    mys_documento_demo = fields.Char('Documento de ejemplo', copy=False,
                                    help='Identificador ficticio para la demostración. No es un documento fiscal.')
    mys_canal_preferido = fields.Selection([
        ('whatsapp', 'WhatsApp'), ('telefono', 'Llamada telefónica'),
        ('correo', 'Correo electrónico'), ('tienda', 'Atención en tienda'),
    ], string='Canal preferido')

    @api.model
    def action_mys_prepare_demo_contacts(self):
        """Permite al seed sincronizar las fichas sin reiniciar operaciones."""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Solo el administrador puede preparar los contactos de demostración.'))
        return self._mys_prepare_demo_contacts()

    @api.model
    def _mys_prepare_demo_contacts(self):
        """Actualiza por referencia: conserva IDs, cotizaciones e historial.

        Los contactos manuales (como Benja) quedan fuera de esta carga. Solo se
        archivan los registros automáticos reconocidos por su nombre y referencia.
        """
        with file_open('mys_erp/demo/contactos_demo.json', 'r') as source:
            contacts = json.load(source)
        partners = self.with_context(active_test=False, tracking_disable=True,
                                     mail_create_nosubscribe=True)
        country = self.env.ref('base.pe')
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id), ('code', '=', '15'),
        ], limit=1)
        seller = self.env['res.users'].search([('login', '=', 'vendedor01')], limit=1)
        ids = []
        for contact in contacts:
            values = dict(contact, country_id=country.id, state_id=state.id,
                          mys_demo=True, mys_identidad_revisada=True,
                          customer_rank=1, active=True, is_company=False,
                          type='contact', lang='es_PE', tz='America/Lima')
            if seller:
                values['user_id'] = seller.id
            partner = partners.search([('ref', '=', contact['ref'])], limit=1)
            if partner:
                # Evita mensajes y escrituras innecesarias en cada arranque.
                changes = {key: value for key, value in values.items()
                           if (partner[key].id if partner._fields[key].type == 'many2one'
                               else partner[key]) != value}
                if changes:
                    partner.write(changes)
            else:
                partner = partners.create(values)
            ids.append(partner.id)
            # CRM conserva sus nombres/códigos y recibe los datos visibles del contacto.
            leads = self.env['crm.lead'].with_context(active_test=False, tracking_disable=True).search([
                ('partner_id', '=', partner.id),
            ])
            for lead in leads:
                details = {'contact_name': partner.name, 'email_from': partner.email,
                           'phone': partner.phone, 'mobile': partner.mobile,
                           'street': partner.street, 'street2': partner.street2,
                           'city': partner.city, 'zip': partner.zip,
                           'state_id': partner.state_id.id, 'country_id': partner.country_id.id}
                changes = {key: value for key, value in details.items()
                           if (lead[key].id if lead._fields[key].type == 'many2one'
                               else lead[key]) != value}
                if changes:
                    lead.write(changes)
        generated = partners.search([
            ('mys_demo', '=', True), ('supplier_rank', '=', 0),
            ('name', '=like', 'Cliente prueba nativa %'), ('id', 'not in', ids),
        ]).filtered(lambda p: re.fullmatch(r'Cliente prueba nativa [0-9a-f]{8}', p.name)
                    and p.ref == 'CLI-MYS-%s' % p.id and p.active)
        generated.write({'active': False})
        return ids

    # ---- Perfil comercial (calculado por reglas; se guarda para listar y filtrar) ----
    mys_nivel = fields.Selection(NIVELES, 'Nivel del cliente', readonly=True, index=True)
    mys_nivel_motivo = fields.Char('Por qué tiene ese nivel', readonly=True)
    mys_compras_6m = fields.Integer('Compras (6 meses)', readonly=True)
    mys_monto_6m = fields.Float('Monto comprado 6 meses (S/)', readonly=True, digits=(16, 2))
    mys_unidades_6m = fields.Float('Unidades compradas (6 meses)', readonly=True)
    mys_ticket_promedio = fields.Float('Ticket promedio (S/)', readonly=True, digits=(16, 2))
    mys_ultima_compra = fields.Date('Última compra', readonly=True)
    mys_dias_sin_compra = fields.Integer('Días sin comprar', readonly=True)
    mys_inactivo = fields.Boolean('Inactivo (más de 90 días sin comprar)', readonly=True)
    mys_descuento_promedio = fields.Float('Descuento promedio obtenido (%)', readonly=True, digits=(16, 2))
    mys_conversion = fields.Float('Cotizaciones que terminan en compra (%)', readonly=True, digits=(16, 1))
    mys_categorias_top = fields.Char('Categorías que más compra', readonly=True)
    mys_productos_top = fields.Char('Productos que más compra', readonly=True)
    mys_sugerencias = fields.Char('Complementos sugeridos', readonly=True)
    mys_perfil_fecha = fields.Datetime('Perfil calculado el', readonly=True)

    def _mys_calcular_perfil(self):
        """Calcula el perfil de estos contactos con sus ventas de los últimos 6 meses."""
        ahora = fields.Datetime.now()
        desde = ahora - timedelta(days=VENTANA_DIAS)
        Order = self.env['sale.order'].sudo()
        for partner in self.sudo():
            pedidos = Order.search([('partner_id', 'child_of', partner.commercial_partner_id.id),
                                    ('date_order', '>=', desde)])
            confirmados = pedidos.filtered(lambda o: o.state == 'sale')
            lineas = confirmados.order_line.filtered(lambda l: not l.display_type and l.product_id)
            compras = len(confirmados)
            monto = sum(confirmados.mapped('amount_total'))
            # Unidades físicas: sin servicios y sin productos vendidos por metro (cables), que inflarían el conteo.
            metro = self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
            unidades = sum(lineas.filtered(lambda l: l.product_id.type != 'service' and l.product_uom != metro)
                           .mapped('product_uom_qty'))
            nivel, motivo = clasificar(compras, monto, unidades)

            ultima = max(Order.search([('partner_id', 'child_of', partner.commercial_partner_id.id),
                                       ('state', '=', 'sale')]).mapped('date_order') or [False])
            dias = (ahora - ultima).days if ultima else 0
            inactivo = bool(ultima) and dias > INACTIVO_DIAS
            if inactivo:
                motivo += ' Atención: %d días sin comprar.' % dias

            por_categoria, por_producto = Counter(), Counter()
            for l in lineas:
                por_categoria[categoria_principal(l.product_id)] += l.price_subtotal
                por_producto[l.product_id.display_name] += l.product_uom_qty
            top_cat = [c for c, _ in por_categoria.most_common(3)]
            sugeridas = []
            for c in top_cat:
                for comp in COMPLEMENTOS.get(c, []):
                    if comp not in por_categoria and comp not in sugeridas:
                        sugeridas.append(comp)
            importe_lista = sum(l.price_unit * l.product_uom_qty for l in lineas)
            descuento = (sum(l.price_unit * l.product_uom_qty * l.discount / 100 for l in lineas) / importe_lista * 100
                         if importe_lista else 0.0)
            # Conversión: solo cotizaciones ya resueltas (compradas, anuladas o vencidas sin compra).
            # Una cotización enviada y aún vigente no cuenta como perdida.
            hoy = fields.Date.context_today(self)
            cerradas = pedidos.filtered(lambda o: o.state in ('sale', 'cancel') or
                                        (o.state == 'sent' and o.validity_date and o.validity_date < hoy))
            partner.write({
                'mys_nivel': nivel, 'mys_nivel_motivo': motivo, 'mys_compras_6m': compras,
                'mys_monto_6m': monto, 'mys_unidades_6m': unidades,
                'mys_ticket_promedio': monto / compras if compras else 0.0,
                'mys_ultima_compra': ultima.date() if ultima else False, 'mys_dias_sin_compra': dias,
                'mys_inactivo': inactivo, 'mys_descuento_promedio': descuento,
                'mys_conversion': len(confirmados) / len(cerradas) * 100 if cerradas else 0.0,
                'mys_categorias_top': ', '.join(top_cat) or False,
                'mys_productos_top': ', '.join('%s (%g)' % (p, q) for p, q in por_producto.most_common(3)) or False,
                'mys_sugerencias': ', '.join(sugeridas[:3]) or False,
                'mys_perfil_fecha': ahora,
            })
        return True

    def action_mys_recalcular_perfil(self):
        self.check_access('read')
        self._mys_calcular_perfil()
        return True

    @api.model
    def _cron_mys_perfiles(self):
        """Tarea programada diaria: recalcula el perfil de todos los clientes."""
        clientes = self.sudo().search(['|', ('customer_rank', '>', 0), ('mys_nivel', '!=', False),
                                       ('mys_segmento', '!=', 'proveedor')])
        clientes._mys_calcular_perfil()
        return True
