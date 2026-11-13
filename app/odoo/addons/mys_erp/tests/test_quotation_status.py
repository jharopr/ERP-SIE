import json
import uuid
from datetime import timedelta
from unittest.mock import patch

from lxml import etree
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQuotationStatus(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Cliente estado comercial'})
        self.product = self.env['product.product'].create({'name': 'Autoradio estado', 'list_price': 100})
        self.lead = self.env['crm.lead'].create({'name': 'Consulta de autoradio', 'type': 'opportunity',
                                               'partner_id': self.partner.id})
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'opportunity_id': self.lead.id,
            'client_order_ref': 'COT-STATUS-%s v1' % uuid.uuid4().hex,
            'validity_date': fields.Date.context_today(self.env.user) + timedelta(days=2),
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 2,
                                  'price_unit': 100, 'tax_id': [(5, 0, 0)]})]})

    def evaluate(self, status='ACEPTADA', code='VALIDADA'):
        self.order.write({'state': 'sent', 'mys_status': status,
            'mys_acceptance_id': 'ACE-STATUS', 'mys_acceptance_hash': self.order._mys_hash(),
            'mys_request_id': 'SOL-STATUS-%s' % self.order.id,
            'mys_response': json.dumps({'respuesta': {'status': status, 'code': code}})})
        return self.env['mys.evaluation'].create({
            'order_id': self.order.id, 'user_id': self.env.uid,
            'company_id': self.order.company_id.id, 'request_id': self.order.mys_request_id,
            'correlation_id': 'COR-STATUS-%s' % self.order.id, 'status': status, 'code': code})

    def test_ready_requires_valid_evaluation_acceptance_and_current_offer(self):
        self.assertEqual(self.order.mys_commercial_state, 'unevaluated')
        self.evaluate()
        self.assertEqual(self.order.mys_commercial_state, 'ready')
        self.order.write({'mys_acceptance_hash': 'aceptacion-antigua'})
        self.assertEqual(self.order.mys_commercial_state, 'awaiting_customer')
        self.assertNotIn(self.order, self.env['sale.order'].search([('mys_commercial_state', '=', 'ready')]))

    def test_expiry_updates_without_editing_the_quote(self):
        self.evaluate()
        self.assertEqual(self.order.mys_commercial_state, 'ready')
        expiry = self.order.validity_date
        with patch.object(fields.Date, 'context_today', return_value=expiry + timedelta(days=1)):
            self.order.invalidate_recordset(['mys_commercial_state', 'mys_commercial_label', 'mys_commercial_note'])
            self.assertEqual(self.order.mys_commercial_state, 'expired')
        self.assertEqual(self.order.validity_date, expiry)

    def test_technical_failure_and_partial_stock_remain_distinct(self):
        self.evaluate('PENDIENTE', 'DEPENDENCIA_NO_DISPONIBLE')
        self.assertEqual(self.order.mys_commercial_state, 'verification_pending')
        self.order.write({'mys_status': 'PROMESA_CONDICIONADA'})
        self.assertEqual(self.order.mys_commercial_state, 'availability')

    def test_discount_request_pending_and_rejection(self):
        self.order.order_line.discount = 10
        evaluation = self.evaluate('RECHAZADA', 'DESCUENTO_SIN_APROBACION')
        self.assertEqual(self.order.mys_commercial_state, 'approval_required')
        with patch.object(type(self.env['mys.decision']), '_mys_avisar_dueno', return_value=None):
            decision = self.env['mys.decision'].create({
                'evaluation_id': evaluation.id, 'user_id': self.env.uid,
                'company_id': self.order.company_id.id, 'tipo': 'DESCUENTO',
                'escalation_id': 'ESC-STATUS', 'state': 'ESPERANDO_DECISION'})
        self.assertEqual(self.order.mys_commercial_state, 'approval_pending')
        decision.write({'state': 'DECIDIDO', 'decision': 'RECHAZADA'})
        self.assertEqual(self.order.mys_commercial_state, 'needs_changes')

    def test_new_version_replaces_old_without_rewriting_its_result(self):
        self.evaluate('RECHAZADA', 'DATOS_INVALIDOS')
        self.assertEqual(self.order.mys_commercial_state, 'needs_changes')
        new = self.order._mys_new_version()
        self.assertEqual(self.order.mys_commercial_state, 'superseded')
        self.assertIn(new.name, self.order.mys_commercial_label)
        self.assertEqual(self.order.mys_result, 'RECHAZADA')
        self.assertEqual(new.mys_commercial_state, 'unevaluated')
        self.assertIn(self.order, self.env['sale.order'].search([('mys_commercial_state', '=', 'superseded')]))
        new.write({'state': 'cancel'})
        self.assertEqual(new.mys_commercial_state, 'cancelled')
        self.assertEqual(self.order.mys_commercial_state, 'needs_changes')

    def test_accepted_without_required_discount_approval_is_not_ready(self):
        from dateutil.relativedelta import relativedelta
        self.product.write({'mys_sin_rotacion_desde': fields.Date.today() - relativedelta(months=7),
                            'mys_evidencia_comercial': 'Fixture de liquidación sintética'})
        self.order.order_line.discount = 10
        self.evaluate()
        self.assertEqual(self.order.mys_commercial_state, 'needs_changes')
        self.order.write({'mys_approval_hash': self.order._mys_hash()})
        self.assertEqual(self.order.mys_commercial_state, 'ready')
        self.order.write({'mys_approval_hash': 'autorizacion-antigua'})
        self.assertEqual(self.order.mys_commercial_state, 'authorization_review')

    def test_list_has_one_commercial_column_and_form_keeps_the_details(self):
        admin = self.env.ref('base.user_admin')
        views = self.env['sale.order'].with_user(admin).get_views(
            [(self.env.ref('mys_erp.view_commercial_list').id, 'list'),
             (self.env.ref('sale.view_order_form').id, 'form')])['views']
        tree = etree.fromstring(views['list']['arch'])
        names = tree.xpath('./field/@name')
        self.assertIn('state', names)
        self.assertIn('mys_commercial_label', names)
        self.assertFalse({'mys_result', 'mys_discount_state', 'mys_discount_target_id'} & set(names))
        for name in ('mys_result', 'mys_discount_state', 'mys_discount_target_id', 'mys_commercial_note'):
            self.assertIn('name="%s"' % name, views['form']['arch'])
        self.assertEqual(self.order.with_user(admin).mys_commercial_state, 'unevaluated')
