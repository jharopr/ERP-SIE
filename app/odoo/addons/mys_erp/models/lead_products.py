"""Necesidad del lead, cotización inicial e ingreso esperado de la oferta vigente."""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class LeadProducts(models.Model):
    _inherit = 'crm.lead'

    mys_product_line_ids = fields.One2many('mys.lead.product', 'lead_id', string='Productos solicitados', copy=True)
    mys_pricelist_id = fields.Many2one('product.pricelist', string='Tarifa',
                                      compute='_compute_mys_pricelist', store=True, readonly=False,
                                      check_company=True)
    mys_currency_id = fields.Many2one(related='mys_pricelist_id.currency_id', string='Moneda de la oferta')
    mys_estimated_untaxed = fields.Monetary('Importe estimado sin impuestos', currency_field='mys_currency_id',
                                           compute='_compute_mys_estimated_untaxed')
    mys_has_quotation = fields.Boolean(compute='_compute_mys_has_quotation')

    @api.depends('partner_id', 'company_id')
    def _compute_mys_pricelist(self):
        for lead in self:
            company = lead.company_id or self.env.company
            partner = lead.partner_id.with_company(company)
            pricelist = partner.property_product_pricelist if partner else self.env['product.pricelist']
            lead.mys_pricelist_id = pricelist or self.env['product.pricelist'].search([
                ('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company.id),
            ], order='sequence,id', limit=1)

    @api.depends('mys_product_line_ids.price_subtotal')
    def _compute_mys_estimated_untaxed(self):
        for lead in self:
            lead.mys_estimated_untaxed = sum(lead.mys_product_line_ids.mapped('price_subtotal'))

    @api.depends('order_ids')
    def _compute_mys_has_quotation(self):
        for lead in self:
            lead.mys_has_quotation = bool(lead.order_ids)

    def _mys_sync_expected_revenue(self, reset=False):
        for lead in self:
            if not lead.id or not isinstance(lead.id, int):
                continue
            company = lead.company_id or self.env.company
            order = lead._mys_current_order()
            if order:
                amount, currency = order.amount_untaxed, order.currency_id
            elif lead.order_ids:
                amount, currency = 0, company.currency_id
            elif lead.mys_product_line_ids:
                amount, currency = lead.mys_estimated_untaxed, lead.mys_currency_id
            elif reset:
                amount, currency = 0, company.currency_id
            else:
                continue
            amount = currency._convert(amount, company.currency_id, company,
                                       fields.Date.context_today(lead.with_context(tz='America/Lima')))
            if company.currency_id.compare_amounts(lead.expected_revenue, amount):
                # Evita recursión: conserva los controles normales del modelo CRM.
                super(LeadProducts, lead).write({'expected_revenue': amount})

    @api.onchange('mys_product_line_ids', 'mys_pricelist_id')
    def _onchange_mys_estimate(self):
        for lead in self:
            if lead.mys_product_line_ids and not lead.mys_has_quotation:
                company = lead.company_id or self.env.company
                lead.expected_revenue = lead.mys_currency_id._convert(
                    lead.mys_estimated_untaxed, company.currency_id, company,
                    fields.Date.context_today(lead.with_context(tz='America/Lima')))

    def _mys_ensure_initial_quotation(self):
        for lead in self.filtered(lambda l: l.type == 'opportunity' and l.active
                                  and l.partner_id and l.mys_product_line_ids):
            # Serializa la conversión y los reintentos; no duplica ofertas existentes.
            self.env.cr.execute('SELECT id FROM crm_lead WHERE id = %s FOR UPDATE', [lead.id])
            if self.env['sale.order'].sudo().search_count([('opportunity_id', '=', lead.id)]):
                continue
            lead.check_access('write')
            if not lead.mys_pricelist_id:
                raise UserError(_('Seleccione una tarifa antes de crear la cotización.'))
            company = lead.company_id or self.env.company
            order = self.env['sale.order'].with_company(company).create({
                'partner_id': lead.partner_id.id, 'opportunity_id': lead.id,
                'user_id': lead.user_id.id or self.env.uid, 'company_id': company.id,
                'team_id': lead.team_id.id, 'pricelist_id': lead.mys_pricelist_id.id,
                'origin': lead.name,
                'campaign_id': lead.campaign_id.id, 'medium_id': lead.medium_id.id,
                'source_id': lead.source_id.id,
                'order_line': [(0, 0, line._mys_quote_values()) for line in lead.mys_product_line_ids],
            })
            # La referencia se asigna después de crear las líneas: una oferta
            # nueva aún no tiene evaluación que consultar en la compuerta.
            order.sudo().write({'client_order_ref': 'COT-MYS-L%s v1' % lead.id})

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._mys_ensure_initial_quotation()
        leads._mys_sync_expected_revenue()
        return leads

    def write(self, vals):
        result = super().write(vals)
        if {'type', 'partner_id', 'mys_product_line_ids'}.intersection(vals):
            self._mys_ensure_initial_quotation()
        if {'mys_product_line_ids', 'mys_pricelist_id', 'partner_id', 'company_id', 'expected_revenue'}.intersection(vals):
            self._mys_sync_expected_revenue(reset='mys_product_line_ids' in vals)
        return result

    def _mys_sync_pipeline(self, preparing_order=None):
        result = super()._mys_sync_pipeline(preparing_order=preparing_order)
        self._mys_sync_expected_revenue()
        return result

    def action_mys_initial_quotation(self):
        self.ensure_one()
        self.check_access('write')
        if self.type != 'opportunity':
            raise UserError(_('Primero convierta el lead en oportunidad.'))
        if not self.partner_id or not self.mys_product_line_ids:
            raise UserError(_('Complete el cliente y los productos solicitados.'))
        self._mys_ensure_initial_quotation()
        return self.action_view_sale_quotation()


class LeadProduct(models.Model):
    _name = 'mys.lead.product'
    _description = 'Producto solicitado en el lead'
    _order = 'sequence,id'
    _check_company_auto = True

    lead_id = fields.Many2one('crm.lead', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='lead_id.company_id', store=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Producto', required=True, check_company=True,
                                 domain="[('sale_ok', '=', True), ('active', '=', True), ('type', '!=', 'combo')]")
    quantity = fields.Float('Cantidad', default=1, required=True, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one(related='product_id.uom_id', string='Unidad')
    currency_id = fields.Many2one(related='lead_id.mys_currency_id')
    price_unit = fields.Monetary('Precio unitario', compute='_compute_price')
    discount = fields.Float('Descuento de tarifa (%)', compute='_compute_price', digits='Discount')
    price_subtotal = fields.Monetary('Subtotal sin impuestos', compute='_compute_price')
    tax_ids = fields.Many2many('account.tax', compute='_compute_price', string='Impuestos')
    _sql_constraints = [('positive_quantity', 'CHECK(quantity > 0)', 'La cantidad debe ser mayor que cero.')]

    @api.depends('product_id', 'quantity', 'lead_id.mys_pricelist_id', 'lead_id.partner_id',
                 'lead_id.company_id', 'product_id.list_price', 'product_id.taxes_id')
    def _compute_price(self):
        for line in self:
            if not line.product_id or not line.lead_id.mys_pricelist_id:
                line.price_unit = line.discount = line.price_subtotal = 0
                line.tax_ids = False
                continue
            company = line.lead_id.company_id or self.env.company
            # Reutiliza el cálculo nativo de Ventas: tarifa, moneda, impuestos,
            # posición fiscal, unidad y descuentos por cantidad. No crea registros.
            order = self.env['sale.order'].with_company(company).new({
                'partner_id': line.lead_id.partner_id.id, 'company_id': company.id,
                'pricelist_id': line.lead_id.mys_pricelist_id.id,
                'date_order': fields.Datetime.now(),
            })
            preview = self.env['sale.order.line'].new({
                'order_id': order, 'product_id': line.product_id.id,
                'product_uom_qty': line.quantity, 'product_uom': line.product_uom_id.id,
            })
            line.price_unit = preview.price_unit
            line.discount = preview.discount
            line.price_subtotal = preview.price_subtotal
            line.tax_ids = preview.tax_id

    def _mys_quote_values(self):
        self.ensure_one()
        if not self.product_id.active or not self.product_id.sale_ok or self.product_id.type == 'combo':
            raise UserError(_('Seleccione un producto activo disponible para venta.'))
        return {'product_id': self.product_id.id, 'product_uom_qty': self.quantity,
                'product_uom': self.product_uom_id.id, 'price_unit': self.price_unit,
                'discount': self.discount, 'tax_id': [(6, 0, self.tax_ids.ids)]}

    def _mys_check_editable(self):
        self.lead_id.check_access('write')
        if self.env['sale.order'].sudo().search_count([('opportunity_id', 'in', self.lead_id.ids)]):
            raise UserError(_('El detalle inicial ya generó una cotización. Modifique la oferta desde Ventas; '
                              'si fue evaluada, cree una nueva versión.'))

    @api.model
    def _mys_check_values(self, vals):
        if {'price_unit', 'discount', 'price_subtotal', 'tax_ids', 'currency_id', 'company_id'}.intersection(vals):
            raise AccessError(_('Los precios e importes se obtienen de la tarifa; no se editan directamente en el lead.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._mys_check_values(vals)
            lead = self.env['crm.lead'].browse(vals.get('lead_id') or self.env.context.get('default_lead_id'))
            lead.check_access('write')
            if self.env['sale.order'].sudo().search_count([('opportunity_id', 'in', lead.ids)]):
                raise UserError(_('La oportunidad ya tiene cotización; agregue los productos desde Ventas.'))
        lines = super().create(vals_list)
        lines.lead_id._mys_sync_expected_revenue()
        return lines

    def write(self, vals):
        self._mys_check_values(vals)
        self._mys_check_editable()
        if vals.get('lead_id'):
            destination = self.env['crm.lead'].browse(vals['lead_id'])
            destination.check_access('write')
            if self.env['sale.order'].sudo().search_count([('opportunity_id', '=', destination.id)]):
                raise UserError(_('La oportunidad de destino ya tiene cotización.'))
        leads = self.lead_id
        result = super().write(vals)
        (leads | self.lead_id)._mys_sync_expected_revenue(reset=True)
        return result

    def unlink(self):
        self._mys_check_editable()
        leads = self.lead_id
        result = super().unlink()
        leads._mys_sync_expected_revenue(reset=True)
        return result
