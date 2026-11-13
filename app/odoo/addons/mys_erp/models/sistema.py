"""Interfaz nativa y controles de negocio. El motor R01–R12 permanece en la compuerta."""
import base64
import html
import hashlib
import hmac
import json
import os
import re
import time
import uuid

import requests
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

REF = re.compile(r'^(COT-[A-Za-z0-9_-]+) v([1-9][0-9]*)$')
# Tope de descuento del vendedor: misma política que aplica la compuerta (max_seller_discount, R08).
TOPE_VENDEDOR = 5.0
# El contexto RPC no puede construir esta identidad; solo la acción validada la usa.
CONFIRMATION_TOKEN = object()


class Gateway(models.AbstractModel):
    _name = 'mys.gateway'
    _description = 'Puente privado a las reglas y al agente'

    def _manager(self):
        return self.env.user.has_group('mys_erp.group_mys_manager')

    def action_reset_demo(self):
        if not self.env.user.has_group('base.group_system') or not self.env.context.get('mys_seed'):
            raise AccessError(_('El reinicio requiere administración explícita del escenario.'))
        self.env['mys.decision'].sudo().search([]).unlink()
        self.env['mys.evaluation'].sudo().search([]).unlink()
        self.env['sale.order'].sudo().search([('mys_quotation_id', '!=', False)]).write({
            'mys_locked': False, 'mys_acceptance_id': False, 'mys_acceptance_hash': False, 'mys_approval_hash': False,
            'mys_request_id': False, 'mys_correlation_id': False, 'mys_status': False, 'mys_response': False})
        return True

    def _role(self):
        if self._manager():
            return 'GERENCIA'
        if self.env.user.has_group('mys_erp.group_mys_seller'):
            return 'VENTAS'
        raise AccessError(_('Su usuario no tiene un rol comercial MYS.'))

    def _headers(self):
        role = self._role()
        # En esta instalación la compañía MYS es única. Nunca se acepta compañía/rol del navegador.
        company = self.env.ref('base.main_company')
        if self.env.company != company:
            raise AccessError(_('Seleccione la compañía MYS para usar el agente y las reglas.'))
        login = self.env.user.login
        # Códigos internos del contrato (VEN-/GER-) para los usuarios de la tienda.
        actor = {'vendedor01': 'VEN-DEMO-01', 'gerente': 'GER-DEMO-01'}.get(login)
        actor = actor or ('GER' if role == 'GERENCIA' else 'VEN') + '-ODOO-' + str(self.env.uid)
        data = {'uid': self.env.uid, 'actor_id': actor, 'rol': role, 'company_id': 'MYS-DEMO',
                'exp': int(time.time()) + 600}
        encoded = base64.urlsafe_b64encode(json.dumps(data, separators=(',', ':')).encode()).decode().rstrip('=')
        secret = os.environ.get('ODOO_BRIDGE_SECRET', '')
        token = os.environ.get('TOKEN_ODOO', '')
        if not secret or not token:
            raise UserError(_('Falta configurar el puente interno de Odoo.'))
        signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        return {'Authorization': 'Bearer ' + token, 'X-MYS-Context': encoded + '.' + signature}

    def _request(self, method, path, data=None):
        try:
            response = requests.request(method, os.environ.get('COMPUERTA_URL', 'http://compuerta:8000') + path,
                                        headers=self._headers(), json=data, timeout=25)
            result = response.json()
        except (requests.RequestException, ValueError):
            raise UserError(_('La compuerta no está disponible. Conserve la solicitud y reintente.')) from None
        if not response.ok:
            raise UserError(str(result.get('detail') or result.get('message') or 'La operación no se pudo completar.'))
        return result

    def _register_commercial(self, order):
        if self._role() != 'VENTAS' or order.user_id != self.env.user:
            raise AccessError(_('La aceptación y evaluación corresponden al vendedor asignado.'))
        if order.company_id != self.env.company:
            raise AccessError(_('La cotización pertenece a otra compañía.'))
        partner = order.partner_id
        return self._request('POST', '/integracion/contexto', {
            'opportunity_id': order.opportunity_id.mys_reference,
            'customer_id': partner.ref, 'seller_uid': self.env.uid,
            'identidad_revisada': partner.mys_identidad_revisada,
            'segmento': 'PUBLICO_GENERAL_NUEVO' if partner.mys_segmento != 'recurrente' else 'CLIENTE_RECURRENTE'})


class Lead(models.Model):
    _inherit = 'crm.lead'
    mys_reference = fields.Char('Referencia SIE', readonly=True, copy=False, index=True,
                                help='Referencia interna estable. Cambiar el título no cambia este código.')

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads:
            if not lead.mys_reference:
                reference = lead.name if re.fullmatch(r'OPP-[A-Za-z0-9_-]+', lead.name or '') else 'OPP-MYS-%s' % lead.id
                super(Lead, lead).write({'mys_reference': reference})
        return leads

    def _mys_fill_reference(self):
        """Completa instalaciones antiguas sin cambiar referencias ya utilizadas."""
        for lead in self:
            if not lead.mys_reference:
                lead.mys_reference = lead.name if re.fullmatch(r'OPP-[A-Za-z0-9_-]+', lead.name or '') else 'OPP-MYS-%s' % lead.id


class Order(models.Model):
    _inherit = 'sale.order'
    mys_quotation_id = fields.Char('Referencia de cotización', compute='_compute_mys_reference', store=True)
    mys_version = fields.Integer('Versión SIE', compute='_compute_mys_reference', store=True)
    mys_acceptance_id = fields.Char('Aceptación registrada', readonly=True, copy=False)
    mys_acceptance_hash = fields.Char(readonly=True, copy=False)
    mys_approval_hash = fields.Char(readonly=True, copy=False)
    mys_request_id = fields.Char('Solicitud', readonly=True, copy=False)
    mys_correlation_id = fields.Char('Correlación', readonly=True, copy=False)
    mys_status = fields.Selection([(x, x.replace('_', ' ').title()) for x in
                                  ('ACEPTADA', 'RECHAZADA', 'PROMESA_CONDICIONADA', 'PENDIENTE')],
                                 string='Resultado comercial', readonly=True, copy=False)
    mys_response = fields.Text('Respuesta de las reglas', readonly=True, copy=False)
    mys_locked = fields.Boolean('Versión evaluada', readonly=True, copy=False)
    mys_evaluation_ids = fields.One2many('mys.evaluation', 'order_id', string='Evaluaciones')
    _sql_constraints = [('mys_unique_version', 'unique(company_id, mys_quotation_id, mys_version)',
                         'Ya existe esta versión de cotización SIE. Cree una nueva versión.')]

    @api.depends('client_order_ref')
    def _compute_mys_reference(self):
        for order in self:
            match = REF.fullmatch(order.client_order_ref or '')
            order.mys_quotation_id = match.group(1) if match else False
            order.mys_version = int(match.group(2)) if match else 0

    def _mys_privileged(self):
        return self.env.su or (self.env.user.has_group('base.group_system') and self.env.context.get('mys_seed'))

    def _mys_check_edit(self):
        if self._mys_privileged():
            return
        if any(o.mys_locked for o in self):
            raise UserError(_('Esta versión ya se evaluó. Cree una nueva versión para cambiar la oferta.'))
        # También bloquea resultados recién creados desde el chat antes de la sincronización visual.
        for order in self.filtered('mys_quotation_id'):
            status = self.env['mys.gateway']._request('GET', '/integracion/cotizaciones/%s/%s' %
                                                      (order.mys_quotation_id, order.mys_version))
            if status['evaluada']:
                raise UserError(_('La compuerta ya evaluó esta versión. Cree una nueva versión para modificarla.'))

    def _mys_hash(self):
        self.ensure_one()
        data = [self.partner_id.id, self.user_id.id, self.opportunity_id.id, self.currency_id.id,
                str(self.validity_date), self.client_order_ref,
                [(l.product_id.id, l.product_uom_qty, l.price_unit, l.discount, l.tax_id.ids, l.product_uom.id)
                 for l in self.order_line if not l.display_type], self.amount_total]
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    @api.model_create_multi
    def create(self, vals_list):
        if not self._mys_privileged() and any(any(k.startswith('mys_') for k in vals) for vals in vals_list):
            raise AccessError(_('Los resultados SIE se registran mediante las acciones comerciales.'))
        if not self._mys_privileged() and any(v.get('state', 'draft') not in ('draft', 'sent', 'cancel') for v in vals_list):
            raise AccessError(_('No se pueden crear pedidos confirmados en este alcance de demostración.'))
        return super().create(vals_list)

    def write(self, vals):
        if any(k.startswith('mys_') for k in vals) and not self._mys_privileged():
            raise AccessError(_('No se pueden alterar resultados, solicitudes ni aceptaciones por RPC.'))
        confirming = self.env.context.get('_mys_confirmation') is CONFIRMATION_TOKEN
        if 'state' in vals and vals['state'] not in ('draft', 'sent', 'cancel') and not (self._mys_privileged() or confirming):
            raise AccessError(_('La evaluación comercial no confirma pedidos.'))
        commercial = {'order_line', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'user_id',
                      'opportunity_id', 'currency_id', 'pricelist_id', 'validity_date', 'client_order_ref', 'company_id', 'warehouse_id', 'state'}
        changed = commercial.intersection(vals) - ({'state'} if confirming else set())
        if changed:
            self._mys_check_edit()
            if (commercial - {'state'}).intersection(vals) and not self._mys_privileged() and any(self.mapped('mys_approval_hash')):
                raise UserError(_('Esta oferta tiene aprobación para su versión e importe. Cree una nueva versión para cambiarla.'))
            # Una aceptación deja de valer ante cualquier cambio de la oferta anterior a evaluar.
            if not self._mys_privileged():
                self.sudo().write({'mys_acceptance_id': False, 'mys_acceptance_hash': False})
        return super().write(vals)

    def unlink(self):
        self._mys_check_edit()
        return super().unlink()

    def copy(self, default=None):
        defaults = dict(default or {})
        if not self._mys_privileged():
            defaults.setdefault('client_order_ref', False)
        return super().copy(defaults)

    def action_confirm(self):
        if self.env.context.get('mys_seed') and self._mys_privileged():
            return super().action_confirm()
        self._mys_check_confirmation()
        result = super(Order, self.with_context(_mys_confirmation=CONFIRMATION_TOKEN)).action_confirm()
        self._mys_finish_confirmation()
        return result

    def _mys_seller(self):
        self.ensure_one()
        self.check_access('write')
        if self.env['mys.gateway']._role() != 'VENTAS' or self.user_id != self.env.user:
            raise AccessError(_('Esta acción corresponde al vendedor asignado.'))
        if self.company_id != self.env.company:
            raise AccessError(_('Compañía incorrecta.'))

    def action_mys_send(self):
        self._mys_seller()
        self._mys_check_edit()
        if self.state not in ('draft', 'sent') or not self.order_line or not self.opportunity_id:
            raise UserError(_('Complete cliente, oportunidad y productos en una cotización sin confirmar.'))
        if self.opportunity_id.type != 'opportunity' or self.opportunity_id.partner_id != self.partner_id:
            raise UserError(_('La oportunidad debe estar convertida y corresponder al mismo cliente.'))
        if not self.partner_id.ref:
            self.partner_id.write({'ref': 'CLI-MYS-%s' % self.partner_id.id, 'mys_demo': True})
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', self.partner_id.ref):
            raise UserError(_('La referencia del cliente debe usar letras, números y guiones.'))
        values = {'state': 'sent'}
        if not self.validity_date:
            values['validity_date'] = fields.Date.context_today(self)
        if not self.mys_quotation_id:
            values['client_order_ref'] = 'COT-MYS-%s v1' % self.id
        self.write(values)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_mys_accept(self):
        self._mys_seller()
        if self.mys_locked or self.state != 'sent' or not self.mys_quotation_id:
            raise UserError(_('Primero prepare/envíe la cotización. Una versión evaluada requiere nueva versión.'))
        if not self.partner_id.mys_identidad_revisada:
            raise UserError(_('Marque «Identidad revisada» en la ficha MYS del cliente.'))
        gateway = self.env['mys.gateway']
        gateway._register_commercial(self)
        acceptance = self.mys_acceptance_id or 'ACE-' + uuid.uuid5(uuid.NAMESPACE_URL,
                     'mys/%s/%s/%s/%s' % (self.company_id.id, self.mys_quotation_id, self.mys_version, self._mys_hash())).hex[:24]
        if not self.mys_acceptance_id:
            current = gateway._request('GET', '/cotizaciones/%s/%s' % (self.mys_quotation_id, self.mys_version))
            if acceptance not in current['aceptaciones']:
                gateway._request('POST', '/aceptaciones', {'acceptance_id': acceptance,
                                'quotation_id': self.mys_quotation_id, 'version': self.mys_version})
        self.sudo().write({'mys_acceptance_id': acceptance, 'mys_acceptance_hash': self._mys_hash()})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_mys_evaluate(self):
        self._mys_seller()
        if self.state != 'sent' or not self.mys_quotation_id:
            raise UserError(_('Primero prepare/envíe esta cotización.'))
        if not self.mys_acceptance_id or self.mys_acceptance_hash != self._mys_hash():
            raise UserError(_('Registre la aceptación del cliente para la oferta actual antes de evaluar.'))
        gateway = self.env['mys.gateway']
        gateway._register_commercial(self)
        operation = uuid.uuid5(uuid.NAMESPACE_URL, 'mys-evaluation/%s/%s/%s' %
                              (self.company_id.id, self.mys_quotation_id, self.mys_version)).hex[:24]
        rid = self.mys_request_id or 'SOL-' + operation
        cor = self.mys_correlation_id or 'COR-' + operation
        payload = {'contract_version': '1.0', 'company_id': 'MYS-DEMO', 'request_id': rid, 'correlation_id': cor,
                   'opportunity_id': self.opportunity_id.mys_reference, 'customer_id': self.partner_id.ref,
                   'quotation_id': self.mys_quotation_id, 'quotation_version': self.mys_version,
                   'acceptance_id': self.mys_acceptance_id}
        if self.mys_status == 'PENDIENTE':
            result = gateway._request('POST', '/solicitudes/%s/reanudar' % rid)
        else:
            result = gateway._request('POST', '/solicitudes', payload)
        r = result['respuesta']
        self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ['mys-sync-%s' % self.company_id.id])
        self.sudo().write({'mys_request_id': rid, 'mys_correlation_id': cor, 'mys_status': r['status'],
                           'mys_response': json.dumps(result, ensure_ascii=False, indent=2), 'mys_locked': True})
        evaluation = self.env['mys.evaluation'].sudo().search([('request_id', '=', rid)], limit=1)
        values = {'order_id': self.id, 'user_id': self.user_id.id, 'company_id': self.company_id.id,
                  'request_id': rid, 'correlation_id': cor, 'status': r['status'], 'code': r['code'],
                  'message': r['message'], 'required_action': r.get('required_action'),
                  'response_json': json.dumps(result, ensure_ascii=False, indent=2)}
        if evaluation:
            evaluation.write(values)
        else:
            evaluation = self.env['mys.evaluation'].sudo().create(values)
        return {'type': 'ir.actions.act_window', 'res_model': 'mys.evaluation', 'res_id': evaluation.id,
                'view_mode': 'form', 'target': 'current'}

    def _mys_new_version(self):
        self.ensure_one()
        family = self.mys_quotation_id
        if not family:
            raise UserError(_('Esta cotización aún no tiene referencia SIE.'))
        # Serializa versiones concurrentes de la familia.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', [family])
        versions = self.sudo().search([('mys_quotation_id', '=', family)])
        # Una versión ANULADA no debe ocupar el número siguiente (p. ej. la v3 de un ensayo anterior
        # anulada por el reinicio de la demo): se renombra y el número queda libre para la aprobación.
        vigentes = versions.filtered(lambda o: o.state != 'cancel')
        siguiente = max(vigentes.mapped('mys_version') or [0]) + 1
        for anulada in versions.filtered(lambda o: o.state == 'cancel' and o.mys_version >= siguiente):
            anulada.sudo().write({'client_order_ref': '%s v%s (anulada %s)' % (family, anulada.mys_version, anulada.id)})
        version = siguiente
        return self.sudo().copy({'client_order_ref': '%s v%s' % (family, version), 'state': 'draft',
                                 'validity_date': fields.Date.context_today(self), 'origin': self.name})

    def action_mys_new_version(self):
        self._mys_seller()
        order = self._mys_new_version()
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': order.id, 'view_mode': 'form'}


class OrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _mys_changed(self, orders):
        orders._mys_check_edit()
        if not orders._mys_privileged():
            if any(orders.mapped('mys_approval_hash')):
                raise UserError(_('La oferta aprobada requiere una nueva versión para cambiar productos o precios.'))
            orders.sudo().write({'mys_acceptance_id': False, 'mys_acceptance_hash': False})

    @api.model_create_multi
    def create(self, vals_list):
        orders = self.env['sale.order'].browse([v['order_id'] for v in vals_list if v.get('order_id')])
        self._mys_changed(orders)
        return super().create(vals_list)

    def write(self, vals):
        if {'product_id', 'product_uom_qty', 'price_unit', 'discount', 'tax_id', 'product_uom', 'order_id'}.intersection(vals):
            self._mys_changed(self.order_id | self.env['sale.order'].browse(vals.get('order_id', [])))
        return super().write(vals)

    def unlink(self):
        self._mys_changed(self.order_id)
        return super().unlink()


class Evaluation(models.Model):
    _name = 'mys.evaluation'
    _description = 'Evaluación comercial MYS'
    _order = 'id desc'
    _rec_name = 'request_id'
    order_id = fields.Many2one('sale.order', 'Cotización', required=True, ondelete='restrict', readonly=True)
    user_id = fields.Many2one('res.users', 'Vendedor', required=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', required=True, readonly=True)
    request_id = fields.Char('Solicitud', required=True, readonly=True, index=True)
    correlation_id = fields.Char('Correlación', readonly=True)
    status = fields.Char('Estado', readonly=True)
    code = fields.Char('Regla / código', readonly=True)
    message = fields.Text('Diagnóstico', readonly=True)
    required_action = fields.Text('Siguiente paso', readonly=True)
    response_json = fields.Text('Respuesta y condiciones', readonly=True)
    decision_ids = fields.One2many('mys.decision', 'evaluation_id', string='Decisiones')
    _sql_constraints = [('unique_request', 'unique(request_id)', 'La solicitud ya está registrada.')]

    def action_request_decision(self):
        self.ensure_one()
        self.check_access('read')
        self.order_id._mys_seller()
        tipo = {'DESCUENTO_SIN_APROBACION': 'DESCUENTO', 'DISPONIBILIDAD_PARCIAL': 'REPOSICION'}.get(self.code)
        if not tipo:
            raise UserError(_('Este resultado no requiere una decisión comercial del dueño.'))
        result = self.env['mys.gateway']._request('POST', '/escalamientos', {
            'tipo': tipo, 'request_id': self.request_id, 'resumen': 'Solicitud de revisión desde Odoo: ' + self.code})
        self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ['mys-sync-%s' % self.company_id.id])
        decision = self.env['mys.decision'].sudo().search([('escalation_id', '=', result['escalation_id'])], limit=1)
        if not decision:
            decision = self.env['mys.decision'].sudo().create({
                'evaluation_id': self.id, 'user_id': self.user_id.id, 'company_id': self.company_id.id,
                'escalation_id': result['escalation_id'], 'tipo': tipo, 'state': 'ESPERANDO_DECISION',
                'total': result.get('total'), 'target_version': result.get('version_aprobacion'),
                'deadline': result['plazo_hasta']})
        return {'type': 'ir.actions.act_window', 'res_model': 'mys.decision', 'res_id': decision.id, 'view_mode': 'form'}

    def action_trace(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.client', 'tag': 'mys.workspace',
                'params': {'page': 'trace', 'correlation_id': self.correlation_id}}


class Decision(models.Model):
    _name = 'mys.decision'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Decisión del dueño MYS'
    _order = 'id desc'
    _rec_name = 'escalation_id'
    evaluation_id = fields.Many2one('mys.evaluation', 'Evaluación', required=True, ondelete='restrict', readonly=True)
    order_id = fields.Many2one(related='evaluation_id.order_id', string='Cotización')
    user_id = fields.Many2one('res.users', 'Vendedor', readonly=True, required=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True, required=True)
    # Detalle para decidir sin salir de la pantalla (solo lectura; sale de la cotización evaluada).
    partner_id = fields.Many2one(related='order_id.partner_id', string='Cliente')
    order_line_ids = fields.One2many(related='order_id.order_line', string='Productos de la cotización')
    currency_id = fields.Many2one(related='order_id.currency_id')
    amount_total = fields.Monetary(related='order_id.amount_total', string='Total de la cotización', currency_field='currency_id')
    unidades = fields.Float('Unidades', compute='_compute_detalle')
    descuento_max = fields.Float('Descuento pedido (%)', compute='_compute_detalle')
    tope_vendedor = fields.Float('Tope del vendedor (%)', compute='_compute_detalle')
    ahorro_cliente = fields.Monetary('Descuento en soles', compute='_compute_detalle', currency_field='currency_id')
    escalation_id = fields.Char('Escalamiento', required=True, readonly=True)
    tipo = fields.Char('Tipo', readonly=True)
    state = fields.Char('Estado', readonly=True)
    total = fields.Char('Total verificado', readonly=True)
    target_version = fields.Integer('Versión a aprobar', readonly=True)
    deadline = fields.Char('Vence (hora Lima)', readonly=True)
    motivo = fields.Text('Motivo del dueño', groups='mys_erp.group_mys_manager')
    decision = fields.Selection([(x, x.replace('_', ' ').title()) for x in
                                 ('APROBADA', 'RECHAZADA', 'OFRECER_PARCIAL', 'EVALUAR_REPOSICION', 'DESCARTAR')],
                                string='Decisión', readonly=True)
    approver_id = fields.Many2one('res.users', 'Decidido por', readonly=True)
    new_order_id = fields.Many2one('sale.order', 'Nueva versión', readonly=True)
    _sql_constraints = [('unique_escalation', 'unique(escalation_id)', 'El escalamiento ya está registrado.')]

    @api.depends('order_id.order_line.discount', 'order_id.order_line.product_uom_qty', 'order_id.order_line.price_unit')
    def _compute_detalle(self):
        for decision in self:
            lineas = decision.order_id.order_line.filtered(lambda l: not l.display_type)
            decision.unidades = sum(lineas.mapped('product_uom_qty'))
            decision.descuento_max = max(lineas.mapped('discount') or [0.0])
            decision.tope_vendedor = TOPE_VENDEDOR
            decision.ahorro_cliente = sum(l.price_unit * l.product_uom_qty * l.discount / 100 for l in lineas)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Llega igual si la excepción se escaló con el botón del vendedor o desde el chat del agente.
        for record in records.filtered(lambda r: r.state == 'ESPERANDO_DECISION'):
            record.sudo()._mys_avisar_dueno()
        return records

    def write(self, vals):
        if not self.env.su and (set(vals) - {'motivo'} or not self.env['mys.gateway']._manager()):
            raise AccessError(_('Solo el dueño puede registrar el motivo. La decisión usa los botones autorizados.'))
        result = super().write(vals)
        if vals.get('state') and vals['state'] != 'ESPERANDO_DECISION':
            # Decidida, vencida o sin decisión: la tarea pendiente del dueño se cierra.
            self.sudo().activity_unlink(['mail.mail_activity_data_todo'])
        return result

    def _mys_duenos(self):
        """Usuarios con rol de dueño (no la cuenta técnica de administración) y distintos del vendedor."""
        group = self.env.ref('mys_erp.group_mys_manager')
        campo = 'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'
        excluidos = self.env.ref('base.user_admin') | self.env.ref('base.user_root') | self.user_id
        return self.env['res.users'].sudo().search([(campo, 'in', group.id), ('share', '=', False)]) - excluidos

    def _mys_enlace(self):
        base = (os.environ.get('PUBLIC_APP_URL') or
                self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')).rstrip('/')
        return '%s/odoo/mys.decision/%s' % (base, self.id)

    def _mys_avisar_dueno(self):
        """Tarea en Odoo + correo al dueño. Un fallo de correo no impide registrar la excepción."""
        self.ensure_one()
        duenos = self._mys_duenos()
        if not duenos:
            return
        que = 'Aprobar descuento mayor al 5 %' if self.tipo == 'DESCUENTO' else 'Decidir faltante de stock'
        cotizacion = '%s v%s' % (self.order_id.mys_quotation_id or self.order_id.name, self.order_id.mys_version or '')
        resumen = '%s · %s · S/ %s (%s)' % (que, cotizacion, self.total or '—', self.escalation_id)
        enlace = self._mys_enlace()
        e = html.escape
        for dueno in duenos:
            self.with_context(mail_activity_quick_update=True).activity_schedule(
                'mail.mail_activity_data_todo', user_id=dueno.id, summary=resumen[:120],
                note='Vence: %s (hora Lima). Revise y pulse el botón de decisión.' % (self.deadline or '—'))
        filas = ''.join('<tr><td style="padding:4px 12px 4px 0;color:#475467">%s</td><td><b>%s</b></td></tr>' % (e(k), e(str(v)))
                        for k, v in [('Cotización', cotizacion), ('Cliente', self.order_id.partner_id.display_name),
                                     ('Vendedor', self.user_id.name), ('Total verificado', 'S/ %s' % (self.total or '—')),
                                     ('Escalamiento', self.escalation_id), ('Responder antes de', self.deadline or '—')])
        celda = 'padding:4px 8px;border-bottom:1px solid #eaecf0'
        productos = ''.join(
            '<tr><td style="%s">%s</td><td style="%s;text-align:right">%s</td><td style="%s;text-align:right">S/ %.2f</td>'
            '<td style="%s;text-align:right">%s %%</td><td style="%s;text-align:right">S/ %.2f</td></tr>' % (
                celda, e(l.product_id.display_name), celda, ('%g' % l.product_uom_qty), celda, l.price_unit,
                celda + (';color:#b42318;font-weight:bold' if l.discount > TOPE_VENDEDOR else ''), ('%g' % l.discount),
                celda, l.price_subtotal)
            for l in self.order_id.order_line.filtered(lambda l: not l.display_type))
        detalle = ('<p style="margin:16px 0 4px"><b>Detalle de la cotización</b> (tope del vendedor: %g %%)</p>'
                   '<table style="border-collapse:collapse;font-size:13px"><tr style="color:#475467">'
                   '<th style="text-align:left;padding:4px 8px">Producto</th><th style="padding:4px 8px">Cant.</th>'
                   '<th style="padding:4px 8px">Precio</th><th style="padding:4px 8px">Desc.</th>'
                   '<th style="padding:4px 8px">Subtotal</th></tr>%s</table>') % (TOPE_VENDEDOR, productos)
        encabezado = ('<div style="font-family:Arial,sans-serif;font-size:14px;color:#101828;max-width:620px">'
                      '<h2 style="margin:0 0 8px">%s</h2><p>El vendedor solicitó su decisión en el sistema MYS.</p>'
                      '<table>%s</table>') % (e(que), filas)
        pie = ('<p style="margin:20px 0"><a href="%s" style="padding:10px 18px;border-radius:6px;background:#1a7f37;'
               'color:#fff;text-decoration:none">Abrir la decisión en Odoo</a></p>'
               '<p style="color:#667085;font-size:12px">Ingrese con su usuario de dueño. Ninguna opción crea pedidos '
               'ni reservas. Si no decide en 10 minutos, la oportunidad queda en seguimiento.</p></div>') % e(enlace)
        cuerpo = encabezado + detalle + pie
        destinos = [d.email for d in duenos if d.email]
        if destinos:
            try:
                mail = self.env['mail.mail'].sudo().create({
                    'subject': '[MYS] ' + resumen, 'body_html': cuerpo, 'email_to': ','.join(destinos),
                    'email_from': os.environ.get('CORREO_REMITENTE') or self.env.company.email or 'agente-sie@mys-demo.local',
                    'auto_delete': False})
                mail.send(raise_exception=False)
            except Exception:  # noqa: BLE001 - el aviso es complementario a la tarea en Odoo
                pass
        self.message_post(body=_('Aviso enviado al dueño (%s): tarea en Odoo%s.') % (
            ', '.join(duenos.mapped('name')), ' y correo' if destinos else ''), subtype_xmlid='mail.mt_note')

    def _decide(self, decision):
        self.ensure_one()
        self.check_access('write')
        if not self.env['mys.gateway']._manager() or self.env.user == self.user_id:
            raise AccessError(_('La decisión requiere un dueño diferente del vendedor.'))
        if not self.motivo or len(self.motivo.strip()) < 3 or len(self.motivo) > 280:
            raise UserError(_('Ingrese un motivo de 3 a 280 caracteres.'))
        self.env.cr.execute('SELECT id FROM mys_decision WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if self.state != 'ESPERANDO_DECISION':
            raise UserError(_('Esta solicitud ya fue decidida.'))
        new_order = self.env['sale.order']
        if self.tipo == 'DESCUENTO' and decision == 'APROBADA':
            self.order_id._mys_check_discount_policy()
            new_order = self.order_id._mys_new_version()
            if new_order.mys_version != self.target_version or format(new_order.amount_total, '.2f') != self.total:
                raise UserError(_('Ya existe otra versión o cambió el total. Solicite una evaluación y aprobación nuevas.'))
            new_order.sudo().write({'mys_approval_hash': new_order._mys_hash()})
        result = self.env['mys.gateway']._request('POST', '/escalamientos/%s/decision' % self.escalation_id,
                                                 {'decision': decision, 'motivo': self.motivo.strip()})
        self.sudo().write({'decision': decision, 'state': 'DECIDIDO', 'approver_id': self.env.uid,
                           'new_order_id': new_order.id if new_order else False})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_approve(self):
        return self._decide('APROBADA')

    def action_reject(self):
        return self._decide('RECHAZADA')

    def action_partial(self):
        return self._decide('OFRECER_PARCIAL')

    def action_replenish(self):
        return self._decide('EVALUAR_REPOSICION')

    def action_discard(self):
        return self._decide('DESCARTAR')
