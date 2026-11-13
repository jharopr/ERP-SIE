"""Canal de entrada del lead y cotizaciones visibles dentro de la oportunidad."""
from odoo import api, fields, models

CANALES = [
    ('whatsapp', 'WhatsApp'), ('tienda', 'Atención en tienda'), ('telefono', 'Llamada telefónica'),
    ('correo', 'Correo electrónico'), ('web', 'Página web'), ('redes', 'Redes sociales'), ('referido', 'Referido'),
]


class LeadCanal(models.Model):
    _inherit = 'crm.lead'

    mys_canal = fields.Selection(
        CANALES, string='Canal de entrada', index=True, compute='_compute_mys_canal', store=True, readonly=False,
        help='Por dónde llegó el cliente. Si no se indica, se toma el canal preferido del contacto.')
    mys_cotizaciones_count = fields.Integer('Número de cotizaciones', compute='_compute_mys_cotizaciones_count')

    @api.depends('partner_id')
    def _compute_mys_canal(self):
        # Solo completa si está vacío: el canal registrado por el vendedor no se sobrescribe.
        for lead in self:
            if not lead.mys_canal and lead.partner_id.mys_canal_preferido:
                lead.mys_canal = lead.partner_id.mys_canal_preferido

    @api.depends('order_ids')
    def _compute_mys_cotizaciones_count(self):
        for lead in self:
            lead.mys_cotizaciones_count = len(lead.order_ids)
