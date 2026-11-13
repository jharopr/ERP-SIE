"""Títulos de demostración legibles sin modificar las referencias del contrato."""
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


HISTORICAL_NAMES = [
    ('Luis Enrique Valdivia Soto', 'luis.valdivia'),
    ('Patricia Maribel Palomino Díaz', 'patricia.palomino'),
    ('Renato Javier Poma Aguilar', 'renato.poma'),
    ('Diana Carolina Salcedo Núñez', 'diana.salcedo'),
    ('Óscar Manuel Alarcón Medina', 'oscar.alarcon'),
    ('Fiorella Andrea Cáceres Ruiz', 'fiorella.caceres'),
    ('Víctor Hugo Tello Meza', 'victor.tello'),
    ('Sandra Beatriz Ríos Espinoza', 'sandra.rios'),
    ('Ricardo Alonso Huanca Vega', 'ricardo.huanca'),
    ('Claudia Isabel Ponce Ayala', 'claudia.ponce'),
]
NEEDS = {
    'CLI-DEMO-001': 'Autoradio con Bluetooth para Toyota Yaris',
    'CLI-DEMO-002': 'Equipos de audio para taller de instalación',
    'CLI-DEMO-003': 'Pantalla Android y accesorios de instalación',
    'CLI-DEMO-004': 'Parlantes para Kia Picanto',
    'CLI-DEMO-005': 'Cámara de retroceso para Hyundai Accent',
    'CLI-DEMO-006': 'Equipos multimedia para vehículos de trabajo',
}


class LeadPresentation(models.Model):
    _inherit = 'crm.lead'

    mys_demo_key = fields.Char('Referencia de carga de ejemplo', readonly=True, copy=False, index=True)

    @api.model
    def action_mys_prepare_demo_presentation(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Solo el administrador puede preparar los títulos de demostración.'))
        return self._mys_prepare_demo_presentation()

    @api.model
    def _mys_prepare_demo_presentation(self):
        partners = self.env['res.partner'].with_context(active_test=False, tracking_disable=True)
        historical = partners.search([
            ('mys_demo', '=', True), ('name', '=like', 'Cliente prueba nativa %'),
        ], order='id').filtered(lambda p: re.fullmatch(r'Cliente prueba nativa [0-9a-f]{8}', p.name)
                               and p.ref == 'CLI-MYS-%s' % p.id)
        already_used = partners.search([('mys_documento_demo', '=like', 'DEMO-HIST-%')]).mapped('name')
        available = [(name, email) for name, email in HISTORICAL_NAMES if name not in already_used]
        for partner, (name, email) in zip(historical, available):
            # Mantiene el cliente archivado y los IDs usados en aceptaciones y versiones.
            partner.write({'name': name, 'email': email + '@example.com',
                           'mys_documento_demo': 'DEMO-HIST-%s' % partner.id,
                           'comment': '<p>Contacto ficticio del historial de demostración. '
                                      'Conserva sus cotizaciones y decisiones originales.</p>'})
        leads = self.with_context(active_test=False, tracking_disable=True).search([])
        leads._mys_fill_reference()
        changed = 0
        for lead in leads:
            technical = bool(re.fullmatch(r'(?:LEAD-MYS-\d+|OPP-(?:DEMO|CAT)-\d+|Venta desde Odoo [0-9a-f]{8}|Oportunidad de Cliente de prueba \d+)', lead.name or ''))
            if not technical or not lead.partner_id.mys_demo:
                continue
            order = lead._mys_current_order() or lead.order_ids.sorted('id', reverse=True)[:1]
            need = order.mys_subject if order and order.order_line else NEEDS.get(lead.partner_id.ref, 'Equipos de audio automotriz')
            values = {'name': '%s · %s' % (need, lead.partner_id.name),
                      'mys_demo_key': lead.mys_demo_key or lead.name,
                      'contact_name': lead.partner_id.name,
                      'email_from': lead.partner_id.email,
                      'phone': lead.partner_id.phone, 'mobile': lead.partner_id.mobile}
            lead.write(values)
            changed += 1
        return changed


class QuotationPresentation(models.Model):
    _inherit = 'sale.order'

    mys_subject = fields.Char('Productos / motivo', compute='_compute_mys_subject', store=True,
                              help='Resumen de los productos cotizados. El número y la referencia se conservan.')

    @api.depends('order_line.product_id.name', 'order_line.product_uom_qty', 'order_line.display_type')
    def _compute_mys_subject(self):
        for order in self:
            lines = order.order_line.filtered(lambda line: not line.display_type and line.product_id)
            parts = ['%g × %s' % (line.product_uom_qty, line.product_id.name) for line in lines[:2]]
            if len(lines) > 2:
                parts.append(_('otros productos'))
            order.mys_subject = ', '.join(parts) or _('Oferta por completar')
