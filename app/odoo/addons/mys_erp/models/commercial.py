"""Listas comerciales, confirmación humana y eventos persistentes de la operación."""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from .sistema import CONFIRMATION_TOKEN, TOPE_VENDEDOR


class OperationEvent(models.Model):
    _name = 'mys.operation.event'
    _description = 'Evento comercial MYS'
    _order = 'occurred_at, id'

    order_id = fields.Many2one('sale.order', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True)
    user_id = fields.Many2one('res.users', required=True)
    occurred_at = fields.Datetime(default=fields.Datetime.now, required=True)
    event_type = fields.Char(required=True)
    code = fields.Char(required=True)
    detail = fields.Text()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mys_confirmed_at = fields.Datetime('Fecha de confirmación', readonly=True, copy=False, index=True)
    mys_result = fields.Selection([
        ('unevaluated', 'Sin evaluar'), ('ACEPTADA', 'Aceptada'), ('RECHAZADA', 'Rechazada'),
        ('PENDIENTE', 'Pendiente'), ('PROMESA_CONDICIONADA', 'Promesa condicionada'),
    ], string='Evaluación de esta versión', compute='_compute_mys_result', store=True, index=True,
       help='Verifica las reglas de esta versión: datos, vigencia, aceptación, descuento y stock. La aprobación del gerente no cambia un resultado histórico.')
    mys_evaluation_code = fields.Char('Motivo de evaluación', compute='_compute_mys_evaluation_code', store=True)
    mys_decision_ids = fields.One2many('mys.decision', 'order_id', string='Decisiones del dueño')
    mys_applied_decision_ids = fields.One2many('mys.decision', 'new_order_id', string='Autorizaciones de esta versión')
    mys_discount_state = fields.Selection([
        ('not_required', 'No requiere aprobación'), ('not_requested', 'Sin solicitud'),
        ('pending', 'Pendiente del dueño'), ('approved', 'Aprobada para esta versión'),
        ('approved_next', 'Aprobada para nueva versión'), ('review', 'Revisar aprobación'),
        ('rejected', 'Rechazada'), ('no_decision', 'Sin decisión / vencida'),
    ], string='Autorización del descuento', compute='_compute_mys_discount_state', store=True, index=True,
       help='Autoriza superar el 5 %. Aplica a una versión e importe concretos; la nueva oferta requiere aceptación y evaluación.')
    mys_discount_target_id = fields.Many2one('sale.order', string='Versión autorizada',
                                             compute='_compute_mys_discount_target', compute_sudo=True)
    mys_delivery_state = fields.Selection([
        ('none', 'Sin entrega'), ('pending', 'Pendiente'), ('partial', 'Parcial'), ('done', 'Entregada'),
    ], string='Entrega', compute='_compute_mys_delivery_state', store=True, index=True)

    @api.depends('mys_status')
    def _compute_mys_result(self):
        for order in self:
            order.mys_result = order.mys_status or 'unevaluated'

    @api.depends('mys_response')
    def _compute_mys_evaluation_code(self):
        for order in self:
            order.mys_evaluation_code = order._mys_evaluation_code()

    @api.depends('order_line.discount', 'order_line.product_id', 'order_line.product_uom_qty',
                 'order_line.price_unit', 'order_line.tax_id', 'order_line.product_uom',
                 'partner_id', 'user_id', 'opportunity_id', 'currency_id', 'validity_date',
                 'client_order_ref', 'company_id', 'amount_total', 'mys_approval_hash',
                 'mys_decision_ids.state', 'mys_decision_ids.decision', 'mys_decision_ids.tipo',
                 'mys_decision_ids.new_order_id', 'mys_applied_decision_ids.decision')
    def _compute_mys_discount_state(self):
        for order in self:
            decision = order.mys_decision_ids.filtered(lambda d: d.tipo == 'DESCUENTO').sorted('id', reverse=True)[:1]
            if max(order.order_line.mapped('discount') or [0]) <= TOPE_VENDEDOR:
                state = 'not_required'
            elif order.mys_approval_hash:
                state = 'approved' if order.mys_approval_hash == order._mys_hash() else 'review'
            elif order.mys_applied_decision_ids.filtered(lambda d: d.tipo == 'DESCUENTO' and d.decision == 'APROBADA'):
                state = 'review'
            elif decision.decision:
                state = {'APROBADA': 'approved_next', 'RECHAZADA': 'rejected'}.get(decision.decision, 'no_decision')
            elif decision.state == 'ESPERANDO_DECISION':
                state = 'pending'
            else:
                state = 'no_decision' if decision else 'not_requested'
            order.mys_discount_state = state

    @api.depends('mys_decision_ids.decision', 'mys_decision_ids.new_order_id',
                 'mys_applied_decision_ids.decision', 'mys_approval_hash')
    def _compute_mys_discount_target(self):
        for order in self:
            decisions = order.mys_decision_ids.filtered(
                lambda d: d.tipo == 'DESCUENTO' and d.decision == 'APROBADA' and d.new_order_id
            ).sorted('id', reverse=True)[:1]
            applied = order.mys_applied_decision_ids.filtered(
                lambda d: d.tipo == 'DESCUENTO' and d.decision == 'APROBADA')
            order.mys_discount_target_id = order if applied else decisions.new_order_id

    @api.depends('picking_ids.state', 'order_line.qty_delivered', 'order_line.product_uom_qty')
    def _compute_mys_delivery_state(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: not l.display_type and l.product_id.type == 'consu')
            if not order.picking_ids:
                state = 'none'
            elif lines and all(float_compare(l.qty_delivered, l.product_uom_qty,
                                             precision_rounding=l.product_uom.rounding) >= 0 for l in lines):
                state = 'done'
            elif any(l.qty_delivered > 0 for l in lines):
                state = 'partial'
            else:
                state = 'pending'
            order.mys_delivery_state = state

    def _mys_log(self, event_type, code, detail=None):
        for order in self:
            self.env['mys.operation.event'].sudo().create({
                'order_id': order.id, 'user_id': self.env.uid,
                'event_type': event_type, 'code': code, 'detail': detail,
            })

    def _mys_new_version(self):
        self.ensure_one()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', [self.mys_quotation_id or str(self.id)])
        if self.sudo().search_count([('mys_quotation_id', '=', self.mys_quotation_id), ('state', '=', 'sale')]):
            raise UserError(_('Esta cotización ya generó una venta. Cree una nueva cotización para otra operación.'))
        return super()._mys_new_version()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._mys_log('COTIZACION', 'CREADA')
        return orders

    def write(self, vals):
        previous = {o.id: (o.state, o.mys_acceptance_id) for o in self}
        result = super().write(vals)
        for order in self:
            state, acceptance = previous[order.id]
            if order.state != state:
                order._mys_log('VENTA' if order.state == 'sale' or order.mys_confirmed_at else 'COTIZACION',
                               {'draft': 'BORRADOR', 'sent': 'PRESENTADA', 'sale': 'CONFIRMADA', 'cancel': 'CANCELADA'}.get(order.state, order.state))
            if order.mys_acceptance_id and order.mys_acceptance_id != acceptance:
                order._mys_log('ACEPTACION', 'REGISTRADA', _('Aceptación del cliente registrada por el vendedor.'))
        return result

    def _mys_check_confirmation(self):
        # Se comprueba cada vez, incluso al invocar action_confirm por RPC.
        for order in self:
            order._mys_seller()
            order._mys_check_discount_policy()
            self.env.cr.execute('SELECT id FROM sale_order WHERE id = %s FOR UPDATE', [order.id])
            self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', [order.mys_quotation_id or str(order.id)])
            order.invalidate_recordset()
            if order.state != 'sent' or not order.opportunity_id or not order.opportunity_id.active:
                raise UserError(_('Solo se confirma una cotización presentada de una oportunidad activa.'))
            if order.opportunity_id._mys_current_order() != order or not order.opportunity_id._mys_can_close():
                raise UserError(_('Confirme la versión vigente, aceptada por el cliente y evaluada ACEPTADA / VALIDADA.'))
            if max(order.order_line.mapped('discount') or [0]) > TOPE_VENDEDOR and order.mys_approval_hash != order._mys_hash():
                raise UserError(_('La aprobación del descuento no corresponde a esta versión y total.'))
            gateway = self.env['mys.gateway']
            gateway._register_commercial(order)
            result = gateway._request('POST', '/solicitudes/%s/validar-confirmacion' % order.mys_request_id)
            response = result['respuesta']
            if response.get('status') != 'ACEPTADA' or response.get('code') != 'VALIDADA':
                raise UserError(_('No se pudo confirmar: %s. %s') % (
                    response.get('message', ''), response.get('required_action', 'Revise las condiciones y cree una nueva versión.')))

    def _mys_finish_confirmation(self):
        for order in self:
            # La reserva ocurre dentro de la misma transacción que la confirmación.
            # Si otro pedido consumió el stock desde la lectura de la compuerta, se revierte todo.
            pickings = order.sudo().picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            pickings.action_assign()
            moves = pickings.move_ids.filtered(lambda m: m.product_id.is_storable and m.state not in ('done', 'cancel'))
            if any(move.state != 'assigned' for move in moves):
                raise UserError(_('El stock cambió: no fue posible reservar toda la venta. No se confirmó el pedido.'))
            order.sudo().write({'mys_confirmed_at': fields.Datetime.now()})
            order.opportunity_id._mys_sync_pipeline()

    def _action_cancel(self):
        for order in self:
            order.check_access('write')
            if not self.env['mys.gateway']._manager():
                order._mys_seller()
        return super(SaleOrder, self.with_context(_mys_confirmation=CONFIRMATION_TOKEN))._action_cancel()

    def action_mys_trace(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.client', 'tag': 'mys.workspace',
                'params': {'page': 'trace', 'order_id': self.id, 'query': self.name}}


class Decision(models.Model):
    _inherit = 'mys.decision'
    order_id = fields.Many2one(related='evaluation_id.order_id', string='Cotización', store=True, index=True)
    partner_id = fields.Many2one(related='order_id.partner_id', string='Cliente', store=True)
    # El vendedor puede leer el motivo en su propio seguimiento; write sigue
    # reservado al dueño por el control de negocio de mys.decision.
    motivo = fields.Text('Motivo del dueño', groups=False)
    mys_decided_at = fields.Datetime('Fecha de decisión', readonly=True)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('decision') and vals.get('state') == 'DECIDIDO':
            vals.setdefault('mys_decided_at', fields.Datetime.now())
        return super().write(vals)

    def action_mys_trace(self):
        self.ensure_one()
        self.check_access('read')
        return self.order_id.action_mys_trace()


class Evaluation(models.Model):
    _inherit = 'mys.evaluation'
    partner_id = fields.Many2one(related='order_id.partner_id', string='Cliente', store=True)

    def action_trace(self):
        self.ensure_one()
        self.check_access('read')
        return self.order_id.action_mys_trace()
