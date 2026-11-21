import json
import uuid
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCommercial(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = [cls.env.ref('base.group_user').id, cls.env.ref('mys_erp.group_mys_seller').id]
        cls.seller = cls.env['res.users'].create({'name': 'Vendedor comercial de prueba',
            'login': 'mys-commercial-test', 'email': 'commercial-test@mys-demo.local', 'groups_id': [(6, 0, groups)]})
        cls.other = cls.env['res.users'].create({'name': 'Otro vendedor comercial',
            'login': 'mys-commercial-other', 'email': 'commercial-other@mys-demo.local', 'groups_id': [(6, 0, groups)]})
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente comercial de prueba',
            'ref': 'CLI-TEST-COMMERCIAL', 'mys_identidad_revisada': True})
        cls.product = cls.env['product.product'].create({'name': 'Producto comercial de prueba',
            'list_price': 100, 'taxes_id': [(5, 0, 0)], 'type': 'consu', 'is_storable': True})

    def setUp(self):
        super().setUp()
        self.lead = self.env['crm.lead'].with_user(self.seller).create({
            'name': 'Oportunidad comercial de prueba', 'type': 'opportunity',
            'partner_id': self.partner.id, 'user_id': self.seller.id})
        self.order = self.env['sale.order'].sudo().create({
            'partner_id': self.partner.id, 'user_id': self.seller.id, 'opportunity_id': self.lead.id,
            'client_order_ref': 'COT-COMMERCIAL-%s v1' % uuid.uuid4().hex,
            'validity_date': fields.Date.context_today(self.env.user) + timedelta(days=2),
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 2,
                                   'price_unit': 100, 'tax_id': [(5, 0, 0)]})]})
        self.Gateway = type(self.env['mys.gateway'])

    def accept(self):
        self.order.write({'state': 'sent'})
        self.order.write({'mys_status': 'ACEPTADA', 'mys_locked': True,
            'mys_acceptance_id': 'ACE-COMMERCIAL', 'mys_acceptance_hash': self.order._mys_hash(),
            'mys_request_id': 'SOL-COMMERCIAL-%s' % self.order.id,
            'mys_response': json.dumps({'respuesta': {'status': 'ACEPTADA', 'code': 'VALIDADA'}})})
        self.env['mys.evaluation'].sudo().create({'order_id': self.order.id, 'user_id': self.seller.id,
            'company_id': self.order.company_id.id, 'request_id': self.order.mys_request_id,
            'correlation_id': 'COR-COMMERCIAL-%s' % self.order.id, 'status': 'ACEPTADA', 'code': 'VALIDADA'})

    def mock_gateway(self, code='VALIDADA'):
        return patch.object(self.Gateway, '_request', return_value={
            'respuesta': {'status': 'ACEPTADA' if code == 'VALIDADA' else 'RECHAZADA',
                          'code': code, 'message': code, 'required_action': 'Revisar'}})

    def stock(self, quantity):
        self.env['stock.quant']._update_available_quantity(self.product, self.order.warehouse_id.lot_stock_id, quantity)

    def test_rpc_cannot_force_sale_or_fake_confirmation_context(self):
        for ctx in ({}, {'_mys_confirmation': True}, {'_mys_confirmation': 'authorized'}):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.order.with_user(self.seller).with_context(**ctx).write({'state': 'sale'})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.order.with_user(self.seller).action_confirm()

    def test_confirmation_revalidates_reserves_and_separates_lists(self):
        self.stock(10)
        self.accept()
        with self.mock_gateway(), patch.object(self.Gateway, '_register_commercial', return_value={}):
            self.order.with_user(self.seller).action_confirm()
        self.assertEqual(self.order.state, 'sale')
        self.assertTrue(self.order.mys_confirmed_at)
        self.assertEqual(self.order.mys_acceptance_hash, self.order._mys_hash())
        self.assertEqual(self.lead.stage_id.mys_commercial_step, 'validated')
        self.assertTrue(all(m.state == 'assigned' for m in self.order.sudo().picking_ids.move_ids))
        self.assertEqual(self.order.mys_delivery_state, 'pending')
        self.assertTrue(self.env['mys.operation.event'].search_count([
            ('order_id', '=', self.order.id), ('code', '=', 'CONFIRMADA')]))
        from odoo.tools.safe_eval import safe_eval
        quote_domain = safe_eval(self.env.ref('mys_erp.action_cotizaciones_mys').domain)
        sale_domain = safe_eval(self.env.ref('mys_erp.action_ventas_mys').domain)
        self.assertNotIn(self.order, self.env['sale.order'].search(quote_domain))
        self.assertIn(self.order, self.env['sale.order'].search(sale_domain))
        with self.assertRaises(UserError):
            self.order._mys_new_version()
        self.order.with_user(self.seller)._action_cancel()
        self.assertEqual(self.order.state, 'cancel')
        self.assertIn(self.order, self.env['sale.order'].search(sale_domain))
        self.assertFalse(self.env['stock.quant'].search([
            ('product_id', '=', self.product.id), ('reserved_quantity', '>', 0)]))

    def test_revalidation_failure_does_not_confirm(self):
        self.stock(10)
        self.accept()
        with self.mock_gateway('DESCUENTO_SIN_APROBACION'), patch.object(self.Gateway, '_register_commercial', return_value={}):
            with self.assertRaises(UserError), self.cr.savepoint():
                self.order.with_user(self.seller).action_confirm()
        self.assertEqual(self.order.state, 'sent')
        self.assertFalse(self.order.picking_ids)

    def test_stock_race_rolls_back_confirmation(self):
        self.accept()
        with self.mock_gateway(), patch.object(self.Gateway, '_register_commercial', return_value={}):
            with self.assertRaises(UserError), self.cr.savepoint():
                self.order.with_user(self.seller).action_confirm()
        self.assertEqual(self.order.state, 'sent')
        self.assertFalse(self.order.mys_confirmed_at)
        self.assertFalse(self.order.picking_ids)

    def test_old_version_cannot_confirm(self):
        self.accept()
        self.order._mys_new_version()
        with self.assertRaises(UserError), self.cr.savepoint():
            self.order.with_user(self.seller).action_confirm()

    def test_discount_and_evaluation_are_independent(self):
        self.assertEqual(self.order.mys_result, 'unevaluated')
        self.order.order_line.write({'discount': 10})
        self.assertEqual(self.order.mys_discount_state, 'not_requested')
        self.accept()
        ev = self.order.mys_evaluation_ids
        with patch.object(type(self.env['mys.decision']), '_mys_avisar_dueno', return_value=None):
            decision = self.env['mys.decision'].sudo().create({'evaluation_id': ev.id,
                'user_id': self.seller.id, 'company_id': self.order.company_id.id,
                'escalation_id': 'ESC-COMMERCIAL-%s' % self.order.id, 'tipo': 'DESCUENTO',
                'state': 'ESPERANDO_DECISION'})
        self.assertEqual(self.order.mys_discount_state, 'pending')
        decision.write({'state': 'DECIDIDO', 'decision': 'RECHAZADA'})
        self.assertEqual(self.order.mys_discount_state, 'rejected')
        self.assertEqual(self.order.mys_result, 'ACEPTADA')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.order.with_user(self.seller).action_confirm()

    def test_approval_labels_original_and_authorized_version_separately(self):
        self.order.order_line.discount = 10
        self.order.write({'mys_status': 'RECHAZADA'})
        evaluation = self.env['mys.evaluation'].create({
            'order_id': self.order.id, 'user_id': self.seller.id,
            'company_id': self.order.company_id.id, 'request_id': 'SOL-PRESENTATION',
            'correlation_id': 'COR-PRESENTATION', 'status': 'RECHAZADA',
            'code': 'DESCUENTO_SIN_APROBACION'})
        new = self.order._mys_new_version()
        decision = self.env['mys.decision'].create({
            'evaluation_id': evaluation.id, 'user_id': self.seller.id,
            'company_id': self.order.company_id.id, 'tipo': 'DESCUENTO',
            'escalation_id': 'ESC-PRESENTATION', 'state': 'DECIDIDO',
            'decision': 'APROBADA', 'new_order_id': new.id, 'target_version': new.mys_version})
        new.write({'mys_approval_hash': new._mys_hash()})
        self.assertEqual(self.order.mys_result, 'RECHAZADA')
        self.assertEqual(self.order.mys_discount_state, 'approved_next')
        self.assertEqual(self.order.mys_discount_target_id, new)
        self.assertEqual(self.order.with_user(self.env.ref('base.user_admin')).mys_discount_target_id.id, new.id)
        self.assertEqual(new.mys_discount_state, 'approved')
        self.assertEqual(new.mys_result, 'unevaluated')
        self.assertEqual(new.mys_discount_target_id, new)
        # Un cambio administrativo no puede hacer parecer vigente una autorización vieja.
        new.order_line.price_unit = 120
        self.assertEqual(new.mys_discount_state, 'review')

    def test_trace_expands_versions_filters_and_respects_seller(self):
        self.accept()
        new = self.order._mys_new_version()
        gateway = self.env['mys.gateway'].with_user(self.seller)
        with patch.object(self.Gateway, '_request', return_value={'eventos': []}):
            trace = gateway._trace_operations(order_id=self.order.id)
            self.assertEqual({o['id'] for o in trace['orders']}, {self.order.id, new.id})
            self.assertTrue(any(e['code'] == 'CREADA' for e in trace['eventos']))
            filtered = gateway._trace_operations(order_id=self.order.id, version=2, event_type='COTIZACION')
            self.assertTrue(filtered['eventos'])
            self.assertTrue(all(e['version'] == 2 for e in filtered['eventos']))
            future = fields.Date.today() + timedelta(days=5)
            self.assertFalse(gateway._trace_operations(order_id=self.order.id, date_from=str(future))['eventos'])
            with self.assertRaises(UserError):
                self.env['mys.gateway'].with_user(self.other)._trace_operations(order_id=self.order.id)
