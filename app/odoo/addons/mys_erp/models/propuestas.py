"""Propuestas del Agente SIE en la cotización: el vendedor las aplica (nueva versión) o las descarta.

El agente nunca escribe en Odoo: solo registra la propuesta en la compuerta. Aplicarla es una acción
del vendedor, con su usuario y sus permisos. Si algo falla, la transacción completa se deshace.
"""
import html

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class OrderPropuesta(models.Model):
    _inherit = 'sale.order'

    mys_propuesta_id = fields.Char('Propuesta del agente', compute='_compute_mys_propuesta')
    mys_propuesta_html = fields.Html('Detalle de la propuesta', compute='_compute_mys_propuesta', sanitize=True)

    def _compute_mys_propuesta(self):
        for order in self:
            order.mys_propuesta_id = False
            order.mys_propuesta_html = False
            if not order._origin.id or not order.mys_quotation_id or order.state not in ('draft', 'sent'):
                continue
            try:
                data = self.env['mys.gateway']._request(
                    'GET', '/propuestas?quotation_id=%s&estado=PENDIENTE' % order.mys_quotation_id)
            except (UserError, AccessError):
                continue  # sin rol comercial o compuerta caída: la cotización se ve igual, sin propuesta
            propuestas = [p for p in data.get('propuestas', []) if p['version_base'] == order.mys_version]
            if propuestas:
                order.mys_propuesta_id = propuestas[0]['propuesta_id']
                order.mys_propuesta_html = order._mys_render_propuesta(propuestas[0])

    @staticmethod
    def _mys_render_propuesta(p):
        e = html.escape
        textos = {'modificar': 'Cambiar', 'agregar': 'Agregar', 'quitar': 'Quitar'}
        cambios = ''.join('<li>%s <b>%s</b>%s%s</li>' % (
            textos.get(c['accion'], c['accion']), e(c['sku']),
            ' · cantidad %g' % c['cantidad'] if 'cantidad' in c else '',
            ' · descuento %g %%' % c['descuento'] if 'descuento' in c else '') for c in p['cambios'])
        v = p['vista_previa']
        filas = ''.join(
            '<tr%s><td>%s</td><td style="text-align:right">%g</td><td style="text-align:right">S/ %s</td>'
            '<td style="text-align:right">%g %%</td><td style="text-align:right">S/ %s</td></tr>' % (
                ' style="color:#b42318;font-weight:bold"' if l['supera_tope'] else '',
                e('%s %s' % (l['sku'], l['producto'] or '')), l['cantidad'], l['precio'], l['descuento'], l['subtotal'])
            for l in v['lineas'])
        aviso = ('<p style="color:#b42318;margin:6px 0 0">Algún descuento pasa el tope del vendedor (%g %%): '
                 'al evaluar la nueva versión se necesitará la decisión del gerente.</p>' % v['tope_vendedor']
                 if v['supera_tope'] else '')
        return ('<p style="margin:0 0 4px"><b>%s</b> · motivo: %s</p><ul style="margin:0 0 6px">%s</ul>'
                '<table class="table table-sm" style="margin:0"><tr><th>Producto</th><th style="text-align:right">Cant.</th>'
                '<th style="text-align:right">Precio</th><th style="text-align:right">Desc.</th>'
                '<th style="text-align:right">Subtotal</th></tr>%s</table>'
                '<p style="margin:6px 0 0">Total actual: <b>S/ %s</b> → total propuesto: <b>S/ %s</b></p>%s') % (
                    e(p['propuesta_id']), e(p['motivo']), cambios, filas, v['total_actual'], v['total_propuesto'], aviso)

    def _mys_remitente(self):
        # La nota del historial no debe fallar si el usuario no tiene correo configurado.
        return self.env.user.email_formatted or self.env.company.email_formatted or 'agente-sie@mys-demo.local'

    def _mys_propuesta_vigente(self):
        self.ensure_one()
        self._mys_seller()
        if not self.mys_propuesta_id:
            raise UserError(_('No hay una propuesta pendiente para esta versión.'))
        propuesta = self.env['mys.gateway']._request('GET', '/propuestas/%s' % self.mys_propuesta_id)
        if (propuesta['estado'] != 'PENDIENTE' or propuesta['cotizacion'] != self.mys_quotation_id
                or propuesta['version_base'] != self.mys_version):
            raise UserError(_('La propuesta ya no corresponde a esta versión de la cotización.'))
        return propuesta

    def action_mys_aplicar_propuesta(self):
        """El vendedor acepta la propuesta: se crea la versión siguiente con los cambios, a su nombre."""
        propuesta = self._mys_propuesta_vigente()
        nueva = self._mys_new_version().with_env(self.env)  # la copia se crea con sudo; los cambios, como el vendedor
        Product = self.env['product.product']
        for c in propuesta['cambios']:
            producto = Product.search([('default_code', '=', c['sku'])], limit=1)
            if not producto:
                raise UserError(_('El producto %s ya no existe en Odoo.') % c['sku'])
            linea = nueva.order_line.filtered(lambda l: l.product_id == producto and not l.display_type)[:1]
            if c['accion'] == 'quitar':
                linea.unlink()
            elif c['accion'] == 'modificar' and linea:
                valores = {}
                if 'cantidad' in c:
                    valores['product_uom_qty'] = c['cantidad']
                if 'descuento' in c:
                    valores['discount'] = c['descuento']
                linea.write(valores)
            else:
                nueva.write({'order_line': [(0, 0, {'product_id': producto.id, 'product_uom_qty': c.get('cantidad', 1),
                                                    'discount': c.get('descuento', 0.0)})]})
        nueva.message_post(body=_('Versión creada al aplicar la propuesta %s del Agente SIE (%s). Aplicada por %s.') % (
            propuesta['propuesta_id'], propuesta['motivo'], self.env.user.name), subtype_xmlid='mail.mt_note', email_from=self._mys_remitente())
        # Al final: si la compuerta no registra la aplicación, toda la operación se deshace.
        self.env['mys.gateway']._request('POST', '/propuestas/%s/resolver' % propuesta['propuesta_id'],
                                         {'accion': 'APLICADA', 'nueva_version': nueva.mys_version})
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': nueva.id,
                'view_mode': 'form', 'target': 'current'}

    def action_mys_descartar_propuesta(self):
        propuesta = self._mys_propuesta_vigente()
        self.env['mys.gateway']._request('POST', '/propuestas/%s/resolver' % propuesta['propuesta_id'],
                                         {'accion': 'DESCARTADA'})
        self.message_post(body=_('Propuesta %s del Agente SIE descartada por %s.') % (
            propuesta['propuesta_id'], self.env.user.name), subtype_xmlid='mail.mt_note', email_from=self._mys_remitente())
        return {'type': 'ir.actions.client', 'tag': 'reload'}
