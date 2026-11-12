from odoo import fields, models


class ContactoMYS(models.Model):
    _inherit = 'res.partner'

    mys_demo = fields.Boolean('Datos de prueba MYS', index=True)
    mys_segmento = fields.Selection([('nuevo', 'Público general nuevo'), ('recurrente', 'Cliente recurrente'),
                                     ('proveedor', 'Proveedor de demostración')], string='Segmento comercial')
    mys_identidad_revisada = fields.Boolean('Identidad sintética revisada')
