"""Política solicitada por el equipo: datos de Odoo, sin decisiones del LLM."""
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class PolicyProduct(models.Model):
    _inherit = 'product.template'

    mys_origen_mercaderia = fields.Selection([
        ('unknown', 'Sin verificar'), ('imported', 'Importado'), ('domestic', 'Nacional'),
    ], string='Origen comercial', default='unknown')
    mys_costo_verificado = fields.Boolean('Costo revisado para descuentos')
    mys_sin_rotacion_desde = fields.Date('Sin rotación desde (evidencia revisada)')
    mys_evidencia_comercial = fields.Char('Referencia de evidencia comercial')

    def _mys_check_policy_editor(self, values):
        protected = {'mys_origen_mercaderia', 'mys_costo_verificado',
                     'mys_sin_rotacion_desde', 'mys_evidencia_comercial'}
        if protected.intersection(values) and not (self.env.su or any(self.env.user.has_group(g) for g in (
                'base.group_system', 'stock.group_stock_manager', 'mys_erp.group_mys_manager'))):
            raise AccessError(_('Los datos que sustentan descuentos requieren gerencia o administración de inventario.'))

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            self._mys_check_policy_editor(values)
        return super().create(values_list)

    def write(self, values):
        self._mys_check_policy_editor(values)
        return super().write(values)


class DiscountPolicy(models.Model):
    _inherit = 'sale.order'

    mys_policy_summary = fields.Text('Análisis de las reglas de descuento', compute='_compute_mys_policy_summary')

    def mys_analyze_discount(self):
        """API de lectura para Odoo/n8n: no expone costos unitarios ni aprueba."""
        self.check_access('read')
        return {str(order.id): order.sudo()._mys_discount_report() for order in self}

    def _mys_discount_report(self):
        self.ensure_one()
        today = fields.Date.context_today(self.with_context(tz='America/Lima'))
        lines = self.order_line.filtered(lambda line: not line.display_type and line.product_id)
        quantities = defaultdict(float)
        for line in lines:
            quantities[line.product_id.id] += line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id)
        history = self.env['sale.order.line'].sudo().search([
            ('order_id.company_id', '=', self.company_id.id),
            ('order_id.partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
            ('order_id.state', '=', 'sale'), ('order_id', '!=', self.id),
            ('display_type', '=', False), ('qty_delivered', '>', 0),
        ]) if self.partner_id else self.env['sale.order.line']
        delivered = sum(line.product_uom._compute_quantity(line.qty_delivered, line.product_id.uom_id)
                        for line in history if line.product_id.type != 'service'
                        and line.product_id.uom_id.category_id == self.env.ref('uom.product_uom_unit').category_id)
        purchased_months = {(fields.Datetime.context_timestamp(
            line.with_context(tz='America/Lima'), line.order_id.date_order).year,
            fields.Datetime.context_timestamp(line.with_context(tz='America/Lima'), line.order_id.date_order).month)
            for line in history}
        first = today.replace(day=1)
        monthly = all(((first - relativedelta(months=n)).year, (first - relativedelta(months=n)).month)
                      in purchased_months for n in (1, 2, 3))
        products = lines.product_id.with_company(self.company_id)
        cost_known = bool(lines) and all(p.product_tmpl_id.mys_costo_verificado
                    and p.product_tmpl_id.mys_evidencia_comercial for p in products)
        margin_high = None
        if cost_known:
            costs = sum(line.product_id.with_company(self.company_id).standard_price *
                        line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id) for line in lines)
            sale_amount = self.currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
                                                    self.company_id, today)
            margin_pen = self.company_id.currency_id._convert(sale_amount - costs, self.env.ref('base.PEN'),
                                                              self.company_id, today)
            margin_high = self.env.ref('base.PEN').compare_amounts(margin_pen, 2000) > 0
        regular = []
        liquidation = []
        for line in lines.filtered(lambda line: line.discount > 0):
            product = line.product_id
            unit_items = product.type != 'service' and product.uom_id.category_id == self.env.ref('uom.product_uom_unit').category_id
            if line.discount <= 5:
                origin = product.product_tmpl_id.mys_origen_mercaderia
                volume = unit_items and quantities[product.id] > 5
                if volume:
                    eligible = True
                elif not unit_items:
                    eligible = False
                elif origin == 'unknown' or not product.product_tmpl_id.mys_evidencia_comercial:
                    eligible = None
                elif origin == 'imported':
                    quants = self.env['stock.quant'].sudo().search([
                        ('company_id', '=', self.company_id.id), ('product_id', '=', product.id),
                        ('location_id', 'child_of', self.warehouse_id.lot_stock_id.id),
                        ('location_id.usage', '=', 'internal'),
                    ])
                    free = sum(q.quantity - q.reserved_quantity for q in quants)
                    eligible = free <= 20
                else:
                    eligible = False
                regular.append({'sku': product.default_code or str(product.id),
                                'quantity': quantities[product.id], 'eligible': eligible})
            else:
                since = product.product_tmpl_id.mys_sin_rotacion_desde
                evidence = product.product_tmpl_id.mys_evidencia_comercial
                if since and evidence:
                    last_move = self.env['stock.move'].sudo().search([
                        ('company_id', '=', self.company_id.id), ('product_id', '=', product.id),
                        ('state', '=', 'done'), ('location_dest_id.usage', '=', 'customer'),
                    ], order='date desc', limit=1)
                    if last_move:
                        since = max(since, fields.Date.to_date(last_move.date))
                    liquidation.append(since < today - relativedelta(months=6))
                else:
                    liquidation.append(None)
        loyalty = delivered > 10 or monthly
        liquidated = (all(value is True for value in liquidation) if liquidation
                      else False)
        strategic = margin_high is True or loyalty or liquidated
        unknown = margin_high is None or any(value is None for value in liquidation)
        exceptional_eligible = True if strategic else (None if unknown else False)
        blocked_code, message, pending = None, None, False
        if any(item['eligible'] is False for item in regular):
            blocked_code = 'DESCUENTO_REGULAR_NO_ELEGIBLE'
            message = 'Hasta 5 % requiere más de 5 unidades del mismo producto o saldo importado de hasta 20 unidades disponibles.'
        elif any(item['eligible'] is None for item in regular):
            blocked_code, pending = 'CRITERIOS_DESCUENTO_NO_VERIFICADOS', True
            message = 'Verifique el origen del producto para justificar el descuento regular; no se puede suponer que es importado.'
        if any(line.discount > 5 for line in lines) and exceptional_eligible is not True:
            blocked_code = 'CRITERIOS_DESCUENTO_NO_VERIFICADOS' if exceptional_eligible is None else 'DESCUENTO_EXCEPCIONAL_NO_ELEGIBLE'
            pending = exceptional_eligible is None
            message = 'Más de 5 % requiere margen comercial mayor a S/ 2 000, fidelidad comprobada o liquidación por más de 6 meses sin rotación. Complete la evidencia faltante.'
        return {'revision': 'MYS-2026-11-13', 'regular': regular,
                'exceptional_eligible': exceptional_eligible,
                'criteria': {'margin_above_2000_pen': margin_high, 'delivered_units': delivered,
                             'loyalty_above_10_units': delivered > 10,
                             'monthly_last_3_complete_months': monthly, 'liquidation_over_6_months': liquidated},
                'requires_manager': any(line.discount > 5 for line in lines),
                'blocking_code': blocked_code, 'message': message, 'pending': pending}

    def _compute_mys_policy_summary(self):
        for order in self:
            report = order.sudo()._mys_discount_report()
            c = report['criteria']
            def label(value):
                return 'Sin verificar' if value is None else ('Cumple' if value else 'No cumple')
            order.mys_policy_summary = '\n'.join([
                report['message'] or 'Criterios comprobados. La autorización del gerente sigue siendo obligatoria por encima del 5 %.',
                'Más de 10 unidades entregadas: %s (%g unidades netas).' % (label(c['loyalty_above_10_units']), c['delivered_units']),
                'Compras en los 3 meses completos anteriores: %s.' % label(c['monthly_last_3_complete_months']),
                'Margen comercial estimado mayor a S/ 2 000: %s.' % label(c['margin_above_2000_pen']),
                'Más de 6 meses sin rotación, con evidencia: %s.' % label(c['liquidation_over_6_months']),
            ])

    def _mys_check_discount_policy(self):
        for order in self:
            report = order.sudo()._mys_discount_report()
            if report['blocking_code']:
                raise UserError(report['message'])


class PolicyLead(models.Model):
    _inherit = 'crm.lead'

    mys_policy_summary = fields.Text('Análisis comercial del cliente', compute='_compute_policy_summary')

    def _compute_policy_summary(self):
        for lead in self:
            order = lead._mys_current_order()
            lead.mys_policy_summary = order.mys_policy_summary if order else 'Prepare la cotización para analizar cantidades, margen y descuentos. La fidelidad se comprobará con ventas entregadas de Odoo.'

    def _mys_can_close(self):
        return super()._mys_can_close() and not self._mys_current_order().sudo()._mys_discount_report()['blocking_code']
