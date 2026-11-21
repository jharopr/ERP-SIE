"""Seguimiento comercial separado de la decisión de las reglas CRM–ERP."""
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError


STEPS = [
    ('qualified', 'Oportunidad calificada'),
    ('preparing', 'Cotización en preparación'),
    ('presented', 'Propuesta presentada'),
    ('review', 'En revisión / negociación'),
    ('validated', 'Cierre comercial validado'),
]
RESULTS = [(key, label) for key, label in [
    ('ACEPTADA', 'Aceptada'), ('RECHAZADA', 'Rechazada'),
    ('PROMESA_CONDICIONADA', 'Promesa condicionada'), ('PENDIENTE', 'Pendiente'),
]]


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    mys_commercial_step = fields.Selection(STEPS, string='Etapa comercial MYS', index=True)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    mys_current_order_id = fields.Many2one('sale.order', string='Cotización vigente',
                                          compute='_compute_mys_commercial')
    mys_evaluation_status = fields.Selection(RESULTS, string='Evaluación comercial',
                                            compute='_compute_mys_commercial')
    mys_evaluation_code = fields.Char('Motivo de evaluación', compute='_compute_mys_commercial')

    def _mys_current_order(self):
        """La oferta más reciente no anulada; un borrador nuevo sustituye a la anterior.

        Se consulta con sudo para que ocultar una oferta mediante reglas de acceso
        no permita cerrar con una oferta antigua. El usuario ya accede a la oportunidad.
        """
        self.ensure_one()
        return self.env['sale.order'].sudo().search([
            ('opportunity_id', '=', self.id), ('state', '!=', 'cancel'),
            ('company_id', '=', self.company_id.id or self.env.company.id),
        ], order='id desc', limit=1)

    @api.depends('order_ids', 'order_ids.state', 'order_ids.mys_status', 'order_ids.mys_response',
                 'order_ids.company_id', 'company_id')
    def _compute_mys_commercial(self):
        for lead in self:
            order = lead._mys_current_order() if lead.id and isinstance(lead.id, int) else self.env['sale.order']
            lead.mys_current_order_id = order
            lead.mys_evaluation_status = order.mys_status if order else False
            lead.mys_evaluation_code = order._mys_evaluation_code() if order else False

    @api.model
    def _mys_stage(self, step):
        return self.env.ref('mys_erp.stage_mys_' + step, raise_if_not_found=False)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        if self.env.context.get('mys_commercial_pipeline'):
            return self.env['crm.stage'].search([('mys_commercial_step', '!=', False)], order='sequence, id')
        return super()._read_group_stage_ids(stages, domain)

    def _stage_find(self, team_id=False, domain=None, order='sequence, id', limit=1):
        opportunity = self.env.context.get('default_type') == 'opportunity' or any(
            lead.type == 'opportunity' for lead in self)
        if opportunity and self._mys_stage('qualified'):
            domain = list(domain or []) + [('mys_commercial_step', '!=', False)]
        return super()._stage_find(team_id=team_id, domain=domain, order=order, limit=limit)

    def _mys_can_close(self):
        self.ensure_one()
        order = self._mys_current_order()
        if order and order.state == 'sale' and order.mys_confirmed_at and order.partner_id == self.partner_id:
            return True
        if not (self.type == 'opportunity' and self.partner_id and order and order.state == 'sent'
                and order.partner_id == self.partner_id and order.mys_quotation_id
                and order.mys_status == 'ACEPTADA' and order._mys_evaluation_code() == 'VALIDADA'
                and order.mys_acceptance_id and order.mys_acceptance_hash == order._mys_hash()
                and order.validity_date and order.validity_date >= fields.Date.context_today(
                    order.with_context(tz='America/Lima'))):
            return False
        return bool(self.env['mys.evaluation'].sudo().search_count([
            ('order_id', '=', order.id), ('request_id', '=', order.mys_request_id),
            ('status', '=', 'ACEPTADA'), ('code', '=', 'VALIDADA'),
        ]))

    def _mys_check_close(self):
        for lead in self:
            if not lead._mys_can_close():
                raise UserError(_(
                    'Para cerrar comercialmente, la cotización vigente debe estar presentada, '
                    'no vencida, aceptada por el cliente y evaluada como ACEPTADA / VALIDADA. '
                    'Una aprobación del gerente o una versión anterior no sustituyen estos requisitos.'
                ))

    def _mys_check_stage(self, stage, vals=None):
        vals = vals or {}
        for lead in self:
            if vals.get('type', lead.type) != 'opportunity':
                if stage.is_won or vals.get('probability', 0) >= 100:
                    lead._mys_check_close()
                continue
            if not stage or not stage.mys_commercial_step:
                raise UserError(_('Use las etapas del flujo comercial MYS para esta oportunidad.'))
            if stage.is_won or stage.mys_commercial_step == 'validated' or vals.get('probability', 0) >= 100:
                lead._mys_check_close()
                if any(vals.get(field, lead[field].id) != lead[field].id
                       for field in ('partner_id', 'company_id')):
                    raise UserError(_('No cambie cliente o compañía al cerrar; revise antes la cotización.'))
            if stage.mys_commercial_step == 'presented':
                order = lead._mys_current_order()
                if not order or order.state != 'sent':
                    raise UserError(_('Primero prepare/presente la cotización vigente desde Ventas.'))

    @api.model_create_multi
    def create(self, vals_list):
        qualified = self._mys_stage('qualified')
        if not qualified:
            return super().create(vals_list)
        original = []
        clean = []
        for values in vals_list:
            vals = dict(values)
            is_opportunity = vals.get('type', self.env.context.get('default_type', 'opportunity')) == 'opportunity'
            stage_id = vals.get('stage_id') or self.env.context.get('default_stage_id')
            original.append((stage_id, vals.get('probability', 0)))
            if is_opportunity:
                vals['stage_id'] = qualified.id
            clean.append(vals)
        leads = super().create(clean)
        for lead, (stage_id, probability) in zip(leads, original):
            if probability >= 100:
                lead._mys_check_close()
            if lead.type == 'opportunity' and stage_id and stage_id != qualified.id:
                lead.write({'stage_id': stage_id})
        return leads

    def write(self, vals):
        vals = dict(vals)
        if vals.get('type') == 'opportunity' and 'stage_id' not in vals:
            stage = self._mys_stage('qualified')
            if stage:
                vals['stage_id'] = stage.id
        if 'stage_id' in vals or vals.get('probability', 0) >= 100:
            for lead in self:
                stage = self.env['crm.stage'].browse(vals['stage_id']) if 'stage_id' in vals else lead.stage_id
                lead._mys_check_stage(stage, vals)
            # Al reabrir una oportunidad, no conservar la probabilidad de ganado.
            stage = self.env['crm.stage'].browse(vals['stage_id']) if vals.get('stage_id') else False
            if stage and not stage.is_won and any(l.stage_id.is_won for l in self):
                vals.setdefault('probability', min(min(self.mapped('automated_probability') or [0]), 99))
        result = super().write(vals)
        if {'type', 'partner_id', 'company_id'}.intersection(vals):
            self._mys_sync_pipeline()
        return result

    def action_set_won(self):
        self._mys_check_close()
        return self.write({'stage_id': self._mys_stage('validated').id, 'probability': 100})

    def _mys_sync_pipeline(self, preparing_order=None):
        """Nunca reactiva perdidas; PENDIENTE conserva una etapa comercial válida."""
        for lead in self.filtered(lambda l: l.type == 'opportunity' and l.active):
            qualified = lead._mys_stage('qualified')
            if not qualified:
                continue
            order = lead._mys_current_order()
            if not order:
                step = 'qualified'
            elif order.state == 'sale' and order.mys_confirmed_at:
                step = 'validated'
            elif order.state not in ('draft', 'sent'):
                step = 'review'
            elif preparing_order and order in preparing_order:
                step = 'preparing'
            elif order.mys_status == 'PENDIENTE' and lead.stage_id.mys_commercial_step not in (False, 'validated'):
                continue
            elif order.mys_status in ('RECHAZADA', 'PROMESA_CONDICIONADA'):
                step = 'review'
            elif lead._mys_can_close():
                step = 'validated'
            else:
                step = 'preparing' if order.state == 'draft' else 'presented'
            stage = lead._mys_stage(step)
            if lead.stage_id != stage:
                lead.write({'stage_id': stage.id})

    @api.model
    def _mys_migrate_pipeline(self):
        opportunities = self.with_context(active_test=False).search([('type', '=', 'opportunity')])
        # Se conserva la condición de perdido y todo el historial comercial.
        for lead in opportunities:
            if not lead.active:
                lead.write({'stage_id': self._mys_stage('qualified').id})
            else:
                lead._mys_sync_pipeline()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _mys_evaluation_code(self):
        self.ensure_one()
        try:
            return json.loads(self.mys_response or '{}').get('respuesta', {}).get('code') or False
        except (ValueError, TypeError, AttributeError):
            return False

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders.opportunity_id._mys_sync_pipeline()
        return orders

    def write(self, vals):
        commercial = {'order_line', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'user_id',
                      'opportunity_id', 'currency_id', 'pricelist_id', 'validity_date', 'client_order_ref', 'company_id', 'warehouse_id'}
        leads = self.opportunity_id
        result = super().write(vals)
        if commercial.intersection(vals) or 'state' in vals:
            (leads | self.opportunity_id)._mys_sync_pipeline(
                preparing_order=self if commercial.intersection(vals) and vals.get('state') != 'sent' else None)
        return result

    def unlink(self):
        leads = self.opportunity_id
        result = super().unlink()
        leads._mys_sync_pipeline()
        return result


class Evaluation(models.Model):
    _inherit = 'mys.evaluation'

    @api.model_create_multi
    def create(self, vals_list):
        evaluations = super().create(vals_list)
        evaluations.order_id.opportunity_id._mys_sync_pipeline()
        return evaluations

    def write(self, vals):
        result = super().write(vals)
        self.order_id.opportunity_id._mys_sync_pipeline()
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.order_id.opportunity_id._mys_sync_pipeline(preparing_order=lines.order_id)
        return lines

    def write(self, vals):
        orders = self.order_id
        result = super().write(vals)
        if {'product_id', 'product_uom_qty', 'price_unit', 'discount', 'tax_id', 'product_uom', 'order_id'}.intersection(vals):
            orders |= self.order_id
            orders.opportunity_id._mys_sync_pipeline(preparing_order=orders)
        return result

    def unlink(self):
        orders = self.order_id
        result = super().unlink()
        orders.opportunity_id._mys_sync_pipeline(preparing_order=orders)
        return result
