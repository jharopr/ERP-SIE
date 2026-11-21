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


# ---- Rotación de productos (análisis comercial de solo lectura) --------------------------------
# Reglas fijas (documentadas en docs/ANALISIS_COMERCIAL.md). Cobertura = días que dura el stock
# disponible al ritmo de venta del periodo.
COBERTURA_ALTA_DIAS = 60      # se agota en 2 meses o menos → rotación alta
COBERTURA_BAJA_DIAS = 180     # dura más de 6 meses → rotación baja


def clasificar_rotacion(vendidas, disponible, dias):
    """Clasificación y cobertura en días. Función pura: mismas cifras → mismo resultado."""
    if disponible <= 0:
        return 'agotado', 0.0
    if vendidas <= 0:
        return 'sin_movimiento', False
    cobertura = disponible / (vendidas / dias)
    if cobertura <= COBERTURA_ALTA_DIAS:
        return 'alta', cobertura
    if cobertura <= COBERTURA_BAJA_DIAS:
        return 'media', cobertura
    return 'baja', cobertura


class ProductoRotacion(models.Model):
    _inherit = 'product.product'

    @api.model
    def mys_rotacion(self, dias=90, ubicacion_id=False):
        """Rotación por producto con ventas CONFIRMADAS: solo totales por SKU, sin clientes, pedidos
        ni costos. Lo usan el agente (usuario de solo lectura) y el gerente; no escribe nada."""
        from datetime import timedelta
        from .contacto import categoria_principal

        self.check_access('read')
        dias = max(7, min(int(dias or 90), 365))
        ahora = fields.Datetime.now()
        desde = ahora - timedelta(days=dias)
        companias = self.env.companies.ids
        # Los clientes de la prueba de carga (CARGA-…) no son ventas del negocio.
        carga = self.env['res.partner'].sudo().with_context(active_test=False).search([('ref', '=like', 'CARGA-%')]).ids
        lineas = self.env['sale.order.line'].sudo().search([
            ('state', '=', 'sale'), ('display_type', '=', False), ('product_id', '!=', False),
            ('company_id', 'in', companias), ('order_partner_id', 'not in', carga)])
        vendidas, pedidos, ultima = {}, {}, {}
        for l in lineas:
            pid, fecha = l.product_id.id, l.order_id.date_order
            if fecha >= desde:
                vendidas[pid] = vendidas.get(pid, 0.0) + l.product_uom_qty
                pedidos.setdefault(pid, set()).add(l.order_id.id)
            if pid not in ultima or fecha > ultima[pid]:
                ultima[pid] = fecha

        dominio_stock = [('company_id', 'in', companias), ('location_id.usage', '=', 'internal')]
        if ubicacion_id:
            dominio_stock.append(('location_id', 'child_of', int(ubicacion_id)))
        stock = {p.id: (fisico, reservado) for p, fisico, reservado in self.env['stock.quant'].sudo()._read_group(
            dominio_stock, ['product_id'], ['quantity:sum', 'reserved_quantity:sum'])}

        productos = self.sudo().search([('sale_ok', '=', True), ('type', '!=', 'service'),
                                        '|', ('company_id', '=', False), ('company_id', 'in', companias)])
        resultado = []
        for p in productos:
            fisico, reservado = stock.get(p.id, (0.0, 0.0))
            disponible = fisico - reservado
            v = vendidas.get(p.id, 0.0)
            clase, cobertura = clasificar_rotacion(v, disponible, dias)
            u = ultima.get(p.id)
            resultado.append({
                'sku': p.default_code or '', 'nombre': p.name, 'categoria': categoria_principal(p),
                'unidad': p.uom_id.name, 'precio': p.list_price,
                'vendidas': v, 'pedidos': len(pedidos.get(p.id, ())),
                'ultima_venta': fields.Date.to_string(u.date()) if u else False,
                'dias_sin_venta': (ahora - u).days if u else False,
                'stock_fisico': fisico, 'reservado': reservado, 'disponible': disponible,
                'cobertura_dias': round(cobertura, 1) if cobertura is not False else False,
                'clasificacion': clase,
            })
        return {'dias': dias, 'desde': fields.Date.to_string(desde.date()), 'productos': resultado}
