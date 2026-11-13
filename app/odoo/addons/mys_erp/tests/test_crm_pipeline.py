import json
import uuid
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCrmPipeline(TransactionCase):
    """Pruebas ORM sin servicios externos; todas las operaciones se revierten."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.seller = cls.env['res.users'].create({
            'name': 'Vendedor pruebas CRM', 'login': 'mys-crm-tests',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('mys_erp.group_mys_seller').id])],
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente pruebas CRM', 'mys_identidad_revisada': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Producto pruebas CRM', 'list_price': 400, 'taxes_id': [(5, 0, 0)],
        })

    def setUp(self):
        super().setUp()
        self.lead = self.env['crm.lead'].with_user(self.seller).create({
            'name': 'Oportunidad de pruebas', 'type': 'opportunity',
            'partner_id': self.partner.id, 'user_id': self.seller.id,
        })

    def stage(self, step):
        return self.env.ref('mys_erp.stage_mys_' + step)

    def quote(self):
        return self.env['sale.order'].sudo().create({
            'partner_id': self.partner.id, 'user_id': self.seller.id,
            'opportunity_id': self.lead.id,
            'client_order_ref': 'COT-TEST-%s v1' % uuid.uuid4().hex,
            'validity_date': fields.Date.context_today(self.env.user) + timedelta(days=2),
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 5,
                                   'price_unit': 400, 'tax_id': [(5, 0, 0)]})],
        })

    def evaluate(self, order, status, code, accepted=True):
        if order.state != 'sent':
            order.write({'state': 'sent'})
        request_id = 'SOL-TEST-%s' % order.id
        order.write({
            'mys_status': status, 'mys_response': json.dumps({'respuesta': {'status': status, 'code': code}}),
            'mys_request_id': request_id, 'mys_acceptance_id': 'ACE-TEST' if accepted else False,
            'mys_acceptance_hash': order._mys_hash() if accepted else False,
        })
        vals = {'order_id': order.id, 'user_id': self.seller.id, 'company_id': order.company_id.id,
                'request_id': request_id, 'correlation_id': 'COR-TEST-%s' % order.id,
                'status': status, 'code': code}
        ev = self.env['mys.evaluation'].sudo().search([('request_id', '=', request_id)])
        if ev:
            ev.write(vals)
        else:
            ev = self.env['mys.evaluation'].sudo().create(vals)
        return ev

    def test_conversion_keeps_lead_and_uses_qualified_stage(self):
        lead = self.env['crm.lead'].with_user(self.seller).create({
            'name': 'Consulta inicial', 'type': 'lead', 'partner_id': self.partner.id,
            'description': 'Necesita cinco autoradios', 'user_id': self.seller.id,
        })
        original_id = lead.id
        lead.convert_opportunity(self.partner)
        self.assertEqual(lead.id, original_id)
        self.assertEqual(lead.type, 'opportunity')
        self.assertEqual(lead.stage_id, self.stage('qualified'))
        self.assertIn('cinco autoradios', lead.description)

    def test_pipeline_has_only_five_mys_columns(self):
        columns = self.lead.with_context(mys_commercial_pipeline=True)._read_group_stage_ids(
            self.env['crm.stage'], [('type', '=', 'opportunity')])
        self.assertEqual(columns.mapped('mys_commercial_step'),
                         ['qualified', 'preparing', 'presented', 'review', 'validated'])

    def test_cannot_force_close_from_ui_or_rpc(self):
        attempts = [
            lambda: self.lead.write({'stage_id': self.stage('validated').id}),
            lambda: self.lead.write({'probability': 100}),
            lambda: self.lead.action_set_won(),
            lambda: self.lead.write({'stage_id': self.env.ref('crm.stage_lead4').id}),
            lambda: self.env['crm.lead'].with_user(self.seller).create({
                'name': 'Cierre sin cotización', 'type': 'opportunity', 'probability': 100}),
        ]
        for action in attempts:
            with self.assertRaises(UserError), self.cr.savepoint():
                action()
        self.assertEqual(self.lead.stage_id, self.stage('qualified'))

    def test_quote_preparation_and_presentation(self):
        with self.assertRaises(UserError), self.cr.savepoint():
            self.lead.write({'stage_id': self.stage('presented').id})
        order = self.quote()
        self.assertEqual(self.lead.stage_id, self.stage('preparing'))
        order.write({'state': 'sent'})
        self.assertEqual(self.lead.stage_id, self.stage('presented'))
        order.order_line.write({'price_unit': 450})
        self.assertEqual(self.lead.stage_id, self.stage('preparing'))

    def test_send_action_presents_first_version(self):
        order = self.quote()
        order.write({'client_order_ref': False})
        order.with_user(self.seller).action_mys_send()
        self.assertEqual(self.lead.stage_id, self.stage('presented'))
        self.assertEqual(order.mys_version, 1)

    def test_rejected_and_partial_do_not_lose_opportunity(self):
        order = self.quote()
        self.evaluate(order, 'RECHAZADA', 'DESCUENTO_SIN_APROBACION')
        self.assertEqual(self.lead.stage_id, self.stage('review'))
        self.assertTrue(self.lead.active)
        self.evaluate(order, 'PROMESA_CONDICIONADA', 'DISPONIBILIDAD_PARCIAL')
        self.assertEqual(self.lead.stage_id, self.stage('review'))
        self.assertEqual(self.lead.mys_evaluation_status, 'PROMESA_CONDICIONADA')

    def test_pending_preserves_stage_and_resume_can_close(self):
        order = self.quote()
        order.write({'state': 'sent'})
        self.lead.write({'stage_id': self.stage('review').id})
        self.evaluate(order, 'PENDIENTE', 'DEPENDENCIA_NO_DISPONIBLE')
        self.assertEqual(self.lead.stage_id, self.stage('review'))
        self.assertEqual(self.lead.mys_evaluation_status, 'PENDIENTE')
        self.evaluate(order, 'ACEPTADA', 'VALIDADA')
        self.assertEqual(self.lead.stage_id, self.stage('validated'))
        self.assertTrue(self.lead.stage_id.is_won)
        self.assertEqual(order.state, 'sent')

    def test_current_version_required_and_new_version_reopens(self):
        order = self.quote()
        self.evaluate(order, 'ACEPTADA', 'VALIDADA')
        self.assertEqual(self.lead.stage_id, self.stage('validated'))
        new = order._mys_new_version()
        self.assertEqual(self.lead.mys_current_order_id, new)
        self.assertEqual(self.lead.stage_id, self.stage('preparing'))
        self.assertFalse(new.mys_acceptance_id)
        with self.assertRaises(UserError), self.cr.savepoint():
            self.lead.action_set_won()
        # Una sincronización tardía de la versión anterior no cierra la nueva.
        order.mys_evaluation_ids.write({'message': 'Historial actualizado'})
        self.assertEqual(self.lead.stage_id, self.stage('preparing'))

    def test_acceptance_and_validity_are_required(self):
        order = self.quote()
        self.evaluate(order, 'ACEPTADA', 'VALIDADA', accepted=False)
        with self.assertRaises(UserError), self.cr.savepoint():
            self.lead.action_set_won()
        order.write({'validity_date': fields.Date.context_today(order.with_context(tz='America/Lima')) - timedelta(days=1)})
        self.evaluate(order, 'ACEPTADA', 'VALIDADA')
        with self.assertRaises(UserError), self.cr.savepoint():
            self.lead.action_set_won()
        self.assertNotEqual(self.lead.stage_id, self.stage('validated'))

    def test_sync_does_not_reactivate_lost_opportunity(self):
        order = self.quote()
        self.lead.action_set_lost()
        self.evaluate(order, 'RECHAZADA', 'DESCUENTO_SIN_APROBACION')
        self.assertFalse(self.lead.active)
