from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDemoPresentation(TransactionCase):
    def test_title_change_preserves_reference_and_copy_gets_new_reference(self):
        lead = self.env['crm.lead'].create({'name': 'OPP-DEMO-TEST', 'type': 'lead'})
        lead.write({'name': 'Autoradio para José Quispe'})
        self.assertEqual(lead.mys_reference, 'OPP-DEMO-TEST')
        copied = lead.copy()
        self.assertEqual(copied.mys_reference, 'OPP-MYS-%s' % copied.id)

    def test_humanization_keeps_historical_customer_and_operation(self):
        partner = self.env['res.partner'].create({
            'name': 'Cliente prueba nativa ffeedd12', 'mys_demo': True, 'active': False})
        partner.ref = 'CLI-MYS-%s' % partner.id
        lead = self.env['crm.lead'].create({'name': 'Venta desde Odoo ffeedd12',
                                          'type': 'opportunity', 'partner_id': partner.id})
        product = self.env['product.product'].create({'name': 'Pantalla Android', 'list_price': 450})
        order = self.env['sale.order'].create({'partner_id': partner.id, 'opportunity_id': lead.id,
            'client_order_ref': 'COT-DEMO-PRESENTATION v1',
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 5})]})
        before = (partner.ref, lead.mys_reference, order.partner_id.id, order.opportunity_id.id,
                  order.amount_total, order.client_order_ref, lead.stage_id.id)
        self.env['crm.lead']._mys_prepare_demo_presentation()
        self.assertNotIn('prueba nativa', partner.name)
        self.assertFalse(partner.active)
        self.assertIn('5 × Pantalla Android', lead.name)
        self.assertIn(partner.name, lead.name)
        self.assertEqual(before, (partner.ref, lead.mys_reference, order.partner_id.id,
            order.opportunity_id.id, order.amount_total, order.client_order_ref, lead.stage_id.id))
        after = (partner.name, lead.name)
        self.env['crm.lead']._mys_prepare_demo_presentation()
        self.assertEqual(after, (partner.name, lead.name))

    def test_summary_follows_products_and_quantity(self):
        partner = self.env['res.partner'].create({'name': 'Cliente resumen'})
        product = self.env['product.product'].create({'name': 'Autoradio Bluetooth'})
        order = self.env['sale.order'].create({'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 2})]})
        self.assertEqual(order.mys_subject, '2 × Autoradio Bluetooth')
        order.order_line.product_uom_qty = 3
        self.assertEqual(order.mys_subject, '3 × Autoradio Bluetooth')
