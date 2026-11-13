from odoo import api, fields, models


class ProductoMYS(models.Model):
    _inherit = 'product.template'

    mys_catalogo = fields.Boolean('Catálogo seleccionado MYS', index=True)
    mys_codigo_fuente = fields.Char('Código original del catálogo', copy=False)
    mys_fila_fuente = fields.Integer('Fila del Excel', copy=False)
    mys_archivo_fuente = fields.Char('Archivo de origen', copy=False)
    mys_lote_sha256 = fields.Char('SHA-256 del catálogo fuente', copy=False)
    mys_prioridad_demo = fields.Integer('Orden de selección demo')
    mys_datos_sinteticos = fields.Boolean('Stock de prueba', default=False)
    mys_precio_mayorista = fields.Monetary('Precio mayorista de referencia', currency_field='currency_id')
    mys_disponible = fields.Float('Disponible sin reserva', compute='_compute_mys_disponible')

    @api.depends('product_variant_ids.free_qty')
    def _compute_mys_disponible(self):
        for product in self:
            product.mys_disponible = sum(product.product_variant_ids.mapped('free_qty'))
