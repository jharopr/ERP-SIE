from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestContactosDemo(TransactionCase):
    def test_repeat_keeps_contact_ids_and_quotation(self):
        partners = self.env['res.partner']
        ids = partners._mys_prepare_demo_contacts()
        customer = partners.browse(ids[0])
        order = self.env['sale.order'].create({'partner_id': customer.id})
        before = (order.partner_id.id, order.state, order.amount_total)
        self.assertEqual(ids, partners._mys_prepare_demo_contacts())
        self.assertEqual(before, (order.partner_id.id, order.state, order.amount_total))
        self.assertEqual(len(ids), 10)
        for partner in partners.browse(ids):
            for field in ('name', 'phone', 'mobile', 'email', 'street', 'street2',
                          'city', 'zip', 'country_id', 'state_id', 'function',
                          'mys_documento_demo', 'mys_segmento', 'mys_canal_preferido', 'comment'):
                self.assertTrue(partner[field], '%s: %s' % (partner.ref, field))
            self.assertTrue(partner.email.endswith('@example.com'))
            self.assertTrue(partner.mys_documento_demo.startswith('DEMO-'))

    def test_archives_only_identifiable_automatic_fixtures(self):
        partners = self.env['res.partner']
        generated = partners.create({'name': 'Cliente prueba nativa abcdef12', 'mys_demo': True})
        generated.ref = 'CLI-MYS-%s' % generated.id
        manual = partners.create({'name': 'Benja', 'mys_demo': True, 'phone': '999111222'})
        similar = partners.create({'name': 'Cliente prueba nativa abcdef12', 'mys_demo': True,
                                   'ref': 'REFERENCIA-MANUAL'})
        partners._mys_prepare_demo_contacts()
        self.assertFalse(generated.active)
        self.assertTrue(generated.exists())
        self.assertTrue(manual.active)
        self.assertEqual(manual.phone, '999111222')
        self.assertTrue(similar.active)

    def test_seller_cannot_reset_demo_contacts(self):
        seller = self.env['res.users'].create({
            'name': 'Prueba carga contactos', 'login': 'mys-contactos-demo-tests',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('mys_erp.group_mys_seller').id])],
        })
        with self.assertRaises(AccessError):
            self.env['res.partner'].with_user(seller).action_mys_prepare_demo_contacts()
