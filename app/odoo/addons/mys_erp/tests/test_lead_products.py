from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLeadProducts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.seller = cls.env['res.users'].create({
            'name': 'Vendedor prueba productos', 'login': 'mys-lead-products-tests',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('mys_erp.group_mys_seller').id])],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente productos lead'})
        cls.product = cls.env['product.product'].create({
            'name': 'Autoradio prueba lead', 'list_price': 400, 'taxes_id': [(5, 0, 0)],
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Instalación prueba lead', 'type': 'service', 'list_price': 50, 'taxes_id': [(5, 0, 0)],
        })
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Tarifa prueba lead', 'currency_id': cls.env.company.currency_id.id,
            'item_ids': [(0, 0, {'applied_on': '0_product_variant', 'product_id': cls.product.id,
                                 'compute_price': 'fixed', 'fixed_price': 360, 'min_quantity': 5})],
        })
        cls.partner.property_product_pricelist = cls.pricelist

    def lead(self, **extra):
        vals = {'name': 'Consulta de cinco autoradios', 'type': 'lead',
                'partner_id': self.partner.id, 'user_id': self.seller.id,
                'mys_product_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 5})]}
        vals.update(extra)
        return self.env['crm.lead'].with_user(self.seller).create(vals)

    def test_product_selection_and_quantity_use_customer_pricelist(self):
        lead = self.lead()
        self.assertEqual(lead.mys_pricelist_id, self.pricelist)
        self.assertAlmostEqual(lead.mys_product_line_ids.price_unit, 360)
        self.assertAlmostEqual(lead.mys_estimated_untaxed, 1800)
        self.assertAlmostEqual(lead.expected_revenue, 1800)
        self.assertFalse(lead.order_ids)
        lead.mys_product_line_ids.write({'quantity': 2})
        self.assertAlmostEqual(lead.mys_product_line_ids.price_unit, 400)
        self.assertAlmostEqual(lead.expected_revenue, 800)

    def test_form_onchange_prices_unsaved_line(self):
        view = self.env.ref('crm.crm_lead_view_form')
        with Form(self.env['crm.lead'].with_user(self.seller).with_context(
                default_type='lead', default_partner_id=self.partner.id), view=view) as form:
            form.name = 'Consulta desde formulario'
            with form.mys_product_line_ids.new() as line:
                line.product_id = self.product
                line.quantity = 5
                self.assertAlmostEqual(line.price_unit, 360)
                self.assertAlmostEqual(line.price_subtotal, 1800)
            self.assertAlmostEqual(form.mys_estimated_untaxed, 1800)

    def test_conversion_creates_one_linked_draft_with_all_products(self):
        lead = self.lead(mys_product_line_ids=[
            (0, 0, {'product_id': self.product.id, 'quantity': 5}),
            (0, 0, {'product_id': self.other_product.id, 'quantity': 2}),
        ])
        lead.convert_opportunity(self.partner)
        order = lead.order_ids
        self.assertEqual(len(order), 1)
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.partner_id, self.partner)
        self.assertEqual(order.user_id, self.seller)
        self.assertEqual(order.pricelist_id, self.pricelist)
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(order.mys_version, 1)
        self.assertAlmostEqual(order.amount_untaxed, 1900)
        self.assertAlmostEqual(lead.expected_revenue, 1900)
        self.assertEqual(lead.stage_id.mys_commercial_step, 'preparing')
        self.assertFalse(order.picking_ids)
        self.assertFalse(order.mys_acceptance_id)
        lead.convert_opportunity(self.partner)
        lead.action_mys_initial_quotation()
        self.assertEqual(lead.order_ids, order)

    def test_existing_opportunity_can_receive_initial_products(self):
        lead = self.lead(type='opportunity', mys_product_line_ids=[])
        lead.write({'mys_product_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 5})]})
        self.assertEqual(len(lead.order_ids), 1)
        self.assertAlmostEqual(lead.expected_revenue, lead.order_ids.amount_untaxed)

    def test_offer_changes_update_revenue_without_altering_initial_need(self):
        lead = self.lead()
        lead.convert_opportunity(self.partner)
        order = lead.order_ids.sudo()
        order.order_line.write({'discount': 5})
        self.assertAlmostEqual(order.amount_untaxed, 1710)
        self.assertAlmostEqual(lead.expected_revenue, 1710)
        self.assertAlmostEqual(lead.mys_estimated_untaxed, 1800)
        with self.assertRaises(UserError), self.cr.savepoint():
            lead.mys_product_line_ids.write({'quantity': 8})
        lead.write({'expected_revenue': 999999})
        self.assertAlmostEqual(lead.expected_revenue, 1710)
        new_order = order._mys_new_version()
        new_order.order_line.write({'price_unit': 300})
        self.assertAlmostEqual(lead.expected_revenue, new_order.amount_untaxed)
        self.assertEqual(lead.mys_current_order_id, new_order)

    def test_included_taxes_are_not_counted_as_expected_revenue(self):
        if not self.env.company.account_fiscal_country_id:
            self.env.company.account_fiscal_country_id = self.env.ref('base.pe')
        group = self.env['account.tax.group'].create({'name': 'IGV prueba lead'})
        tax = self.env['account.tax'].create({
            'name': 'IGV incluido prueba', 'amount': 18, 'amount_type': 'percent',
            'type_tax_use': 'sale', 'price_include_override': 'tax_included',
            'tax_group_id': group.id,
        })
        self.product.taxes_id = tax
        lead = self.lead()
        estimate = lead.mys_estimated_untaxed
        self.assertLess(estimate, 1800)
        lead.convert_opportunity(self.partner)
        self.assertAlmostEqual(lead.order_ids.amount_untaxed, estimate, places=2)
        self.assertAlmostEqual(lead.expected_revenue, estimate, places=2)
        self.assertAlmostEqual(lead.order_ids.amount_total, 1800, places=2)

    def test_foreign_currency_is_converted_to_company_currency(self):
        currency = self.env.ref('base.USD')
        if currency == self.env.company.currency_id:
            currency = self.env.ref('base.PEN')
        currency.active = True
        self.env['res.currency.rate'].create({
            'currency_id': currency.id, 'company_id': self.env.company.id,
            'name': fields.Date.context_today(self.env.user.with_context(tz='America/Lima')), 'rate': 2,
        })
        self.pricelist.currency_id = currency
        lead = self.lead()
        lead.convert_opportunity(self.partner)
        order = lead.order_ids
        expected = currency._convert(order.amount_untaxed, self.env.company.currency_id, self.env.company,
                                      fields.Date.context_today(lead.with_context(tz='America/Lima')))
        self.assertEqual(order.currency_id, currency)
        self.assertAlmostEqual(lead.expected_revenue, expected)

    def test_prices_cannot_be_supplied_by_rpc(self):
        lead = self.lead()
        with self.assertRaises(AccessError), self.cr.savepoint():
            lead.mys_product_line_ids.write({'price_unit': 1})
        with self.assertRaises(AccessError), self.cr.savepoint():
            lead.write({'mys_product_line_ids': [(0, 0, {
                'product_id': self.product.id, 'quantity': 5, 'price_unit': 1})]})

    def test_other_seller_cannot_modify_lead_lines(self):
        lead = self.lead()
        other = self.env['res.users'].create({
            'name': 'Otro vendedor', 'login': 'mys-other-products-test',
            'groups_id': [(6, 0, self.seller.groups_id.ids)],
        })
        with self.assertRaises(AccessError), self.cr.savepoint():
            lead.mys_product_line_ids.with_user(other).write({'quantity': 10})
