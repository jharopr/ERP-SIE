"""Resumen de lectura: conserva por separado las reglas y decisiones originales."""
from odoo import api, fields, models, _


COMMERCIAL_STATES = [
    ('unevaluated', 'Por evaluar'),
    ('approval_required', 'Solicitar aprobación'),
    ('approval_pending', 'Pendiente del gerente'),
    ('authorization_review', 'Revisar autorización'),
    ('needs_changes', 'Requiere corrección'),
    ('availability', 'Revisar disponibilidad'),
    ('verification_pending', 'Verificación pendiente'),
    ('awaiting_customer', 'Pendiente del cliente'),
    ('expired', 'Cotización vencida'),
    ('ready', 'Lista para confirmar'),
    ('superseded', 'Reemplazada por nueva versión'),
    ('confirmed', 'Venta confirmada'),
    ('cancelled', 'Cancelada'),
]


class QuotationStatus(models.Model):
    _inherit = 'sale.order'

    # No se almacena: la vigencia debe cambiar aunque nadie edite la oferta.
    mys_commercial_state = fields.Selection(
        COMMERCIAL_STATES, string='Estado comercial', compute='_compute_mys_commercial_summary',
        compute_sudo=True, search='_search_mys_commercial_state',
        help='Resumen de evaluación, autorización, aceptación y vigencia. Confirmar venta vuelve a verificar las reglas y el stock.')
    mys_commercial_label = fields.Char('Resumen comercial', compute='_compute_mys_commercial_summary', compute_sudo=True)
    mys_commercial_note = fields.Text('Detalle del estado comercial', compute='_compute_mys_commercial_summary', compute_sudo=True)

    @api.depends('state', 'mys_result', 'mys_discount_state', 'mys_acceptance_id',
                 'mys_acceptance_hash', 'mys_response', 'validity_date', 'mys_version',
                 'mys_quotation_id', 'partner_id.active', 'opportunity_id.active',
                 'partner_id', 'user_id', 'opportunity_id.partner_id',
                 'order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_unit',
                 'order_line.discount', 'order_line.tax_id', 'order_line.product_uom',
                 'currency_id', 'amount_total', 'client_order_ref',
                 'mys_evaluation_ids', 'mys_evaluation_ids.status', 'mys_evaluation_ids.code',
                 'opportunity_id.order_ids', 'opportunity_id.order_ids.state',
                 'mys_decision_ids.new_order_id')
    def _compute_mys_commercial_summary(self):
        labels = dict(COMMERCIAL_STATES)
        today = fields.Date.context_today(self.with_context(tz='America/Lima'))
        # Agrupa familias para no consultar cada versión por separado.
        families = self.filtered('mys_quotation_id')
        latest = {}
        if families:
            candidates = self.sudo().search([
                ('company_id', 'in', families.company_id.ids),
                ('mys_quotation_id', 'in', families.mapped('mys_quotation_id')),
                ('state', '!=', 'cancel'),
            ], order='mys_version desc, id desc')
            for candidate in candidates:
                latest.setdefault((candidate.company_id.id, candidate.mys_quotation_id), candidate)
        current = {lead.id: lead._mys_current_order() for lead in self.opportunity_id}
        for order in self:
            replacement = latest.get((order.company_id.id, order.mys_quotation_id))
            if not replacement or replacement.mys_version <= order.mys_version:
                replacement = current.get(order.opportunity_id.id)
                if not replacement or replacement.id <= order.id or replacement.partner_id != order.partner_id:
                    replacement = False
            state, note = order._mys_commercial_summary(today, replacement, current.get(order.opportunity_id.id))
            order.mys_commercial_state = state
            order.mys_commercial_label = (_('Reemplazada por %s') % replacement.name
                                          if state == 'superseded' else labels[state])
            order.mys_commercial_note = note

    def _mys_commercial_summary(self, today, replacement, current):
        self.ensure_one()
        if self.state == 'sale':
            return 'confirmed', _('La venta ya fue confirmada.')
        if self.state == 'cancel':
            return 'cancelled', _('El documento está cancelado. Su historial se conserva.')
        if replacement:
            return 'superseded', _('Continúe en %s. Esta oferta conserva su evaluación y decisiones originales.') % replacement.name
        if self.mys_discount_state == 'review':
            return 'authorization_review', _('La autorización no coincide con esta oferta. Revise la versión y el importe antes de continuar.')
        if self.validity_date and self.validity_date < today:
            return 'expired', _('La oferta venció. Prepare una nueva versión y obtenga una nueva aceptación del cliente.')
        if self.mys_discount_state == 'pending':
            return 'approval_pending', _('El gerente todavía debe responder la solicitud de descuento.')
        if self.mys_discount_state == 'rejected':
            return 'needs_changes', _('El gerente rechazó el descuento. Prepare otra oferta dentro de las condiciones autorizadas.')
        if self.mys_result == 'PENDIENTE':
            return 'verification_pending', _('La verificación no terminó. Reanude la evaluación; esto no significa falta de stock.')
        if self.mys_result == 'PROMESA_CONDICIONADA':
            return 'availability', _('Revise la disponibilidad y las condiciones con el cliente antes de preparar una nueva oferta.')
        if self.mys_result == 'RECHAZADA':
            if self._mys_evaluation_code() == 'DESCUENTO_SIN_APROBACION' and self.mys_discount_state in ('not_requested', 'no_decision'):
                return 'approval_required', _('Solicite al gerente la autorización del descuento desde la evaluación comercial.')
            return 'needs_changes', _('Revise el motivo de rechazo y prepare una nueva versión. La aprobación no modifica una evaluación histórica.')
        if self.mys_result == 'unevaluated':
            return 'unevaluated', _('Complete la oferta, registre la aceptación del cliente y evalúe las reglas comerciales.')
        if not self.mys_acceptance_id or self.mys_acceptance_hash != self._mys_hash():
            return 'awaiting_customer', _('Falta una aceptación del cliente que corresponda exactamente a esta oferta.')
        policy = self.sudo()._mys_discount_report()
        if policy['blocking_code']:
            return ('verification_pending' if policy['pending'] else 'needs_changes'), policy['message']
        if (self.mys_discount_state in ('not_required', 'approved') and self.opportunity_id
                and self.opportunity_id.active and self.partner_id.active and current == self
                and self.opportunity_id._mys_can_close()):
            return 'ready', _('Esta versión cumple las condiciones registradas. Confirmar venta vuelve a validar las reglas y el stock disponible.')
        return 'needs_changes', _('Revise la vigencia, la oportunidad, la aceptación y la autorización antes de confirmar.')

    @api.model
    def _search_mys_commercial_state(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            raise NotImplementedError('Operador no admitido para Estado comercial: %s' % operator)
        values = value if operator in ('in', 'not in') else [value]
        # La demo tiene un conjunto pequeño de ofertas; respeta las reglas de acceso
        # del usuario y evalúa la fecha actual, sin persistir un estado que pueda vencer.
        matching = self.search([]).filtered(lambda order: order.mys_commercial_state in values)
        return [('id', 'not in' if operator in ('!=', 'not in') else 'in', matching.ids)]
