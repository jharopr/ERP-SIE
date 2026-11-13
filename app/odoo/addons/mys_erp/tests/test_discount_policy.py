from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiscountPolicy(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Cliente ficticio política'})
        self.product = self.env['product.product'].create({
            'name': 'Audio ficticio política', 'type': 'consu', 'is_storable': True,
            'list_price': 500, 'standard_price': 50, 'taxes_id': [(5, 0, 0)],
            'mys_origen_mercaderia': 'domestic', 'mys_costo_verificado': True,
            'mys_evidencia_comercial': 'Fixture sintético de prueba'})
        self.order = self.env['sale.order'].create({'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 5,
                                   'price_unit': 500, 'discount': 5, 'tax_id': [(5, 0, 0)]})]})

    def report(self):
        return self.order._mys_discount_report()

    def test_regular_five_is_not_more_than_five_and_six_is(self):
        self.assertEqual(self.report()['blocking_code'], 'DESCUENTO_REGULAR_NO_ELEGIBLE')
        self.order.order_line.product_uom_qty = 6
        self.assertFalse(self.report()['blocking_code'])

    def test_same_product_split_lines_are_aggregated(self):
        self.order.order_line.product_uom_qty = 3
        self.order.write({'order_line': [(0, 0, {'product_id': self.product.id,
            'product_uom_qty': 3, 'price_unit': 500, 'discount': 5})]})
        self.assertFalse(self.report()['blocking_code'])
        self.assertEqual(self.report()['regular'][0]['quantity'], 6)

    def test_imported_twenty_is_eligible_twenty_one_is_not(self):
        self.product.mys_origen_mercaderia = 'imported'
        location = self.order.warehouse_id.lot_stock_id
        self.env['stock.quant']._update_available_quantity(self.product, location, 20)
        self.assertFalse(self.report()['blocking_code'])
        self.env['stock.quant']._update_available_quantity(self.product, location, 1)
        self.assertEqual(self.report()['blocking_code'], 'DESCUENTO_REGULAR_NO_ELEGIBLE')

    def test_missing_origin_is_not_invented(self):
        self.product.mys_origen_mercaderia = 'unknown'
        self.assertTrue(self.report()['pending'])
        self.assertEqual(self.report()['regular'][0]['eligible'], None)

    def test_margin_two_thousand_is_not_above_two_thousand(self):
        self.order.order_line.discount = 10
        self.assertIs(self.report()['criteria']['margin_above_2000_pen'], False)
        self.product.standard_price = 49
        self.assertIs(self.report()['criteria']['margin_above_2000_pen'], True)
        self.assertFalse(self.report()['blocking_code'])
        self.assertTrue(self.report()['requires_manager'])

    def test_missing_cost_can_qualify_only_through_another_proven_criterion(self):
        self.order.order_line.discount = 10
        self.product.mys_costo_verificado = False
        self.assertIsNone(self.report()['exceptional_eligible'])
        self.assertTrue(self.report()['pending'])
        self.product.mys_sin_rotacion_desde = fields.Date.today() - relativedelta(months=7)
        self.assertTrue(self.report()['exceptional_eligible'])
        self.assertFalse(self.report()['blocking_code'])

    def test_exact_six_months_is_not_older_than_six_months(self):
        self.order.order_line.discount = 10
        self.product.mys_sin_rotacion_desde = fields.Date.today() - relativedelta(months=6)
        self.assertFalse(self.report()['criteria']['liquidation_over_6_months'])
        self.product.mys_sin_rotacion_desde -= relativedelta(days=1)
        self.assertTrue(self.report()['criteria']['liquidation_over_6_months'])

    def history(self, quantity, months_ago=1, state='sale'):
        date = fields.Date.today().replace(day=1) - relativedelta(months=months_ago)
        order = self.env['sale.order'].create({'partner_id': self.partner.id, 'state': state,
            'date_order': datetime.combine(date, datetime.min.time()).replace(hour=12),
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': quantity,
                                   'price_unit': 500, 'tax_id': [(5, 0, 0)]})]})
        # Fixture transaccional; no es una entrega real ni queda en la base.
        order.order_line.write({'qty_delivered': quantity})
        return order

    def test_ten_delivered_units_is_not_eleven_cancelled_orders_do_not_count(self):
        self.order.order_line.discount = 10
        self.history(50, state='cancel')
        self.history(10)
        self.assertFalse(self.report()['criteria']['loyalty_above_10_units'])
        self.history(1)
        self.assertTrue(self.report()['criteria']['loyalty_above_10_units'])
        self.assertEqual(self.report()['criteria']['delivered_units'], 11)

    def test_monthly_requires_each_of_the_three_complete_previous_months(self):
        self.order.order_line.discount = 10
        self.history(1, 1)
        self.history(1, 3)
        self.assertFalse(self.report()['criteria']['monthly_last_3_complete_months'])
        self.history(1, 2)
        self.assertTrue(self.report()['criteria']['monthly_last_3_complete_months'])
        self.assertTrue(self.report()['exceptional_eligible'])

    def test_seller_cannot_forge_policy_evidence(self):
        seller = self.env['res.users'].create({'name': 'Vendedor reglas', 'login': 'test-reglas-seller',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('mys_erp.group_mys_seller').id])]})
        with self.assertRaises(AccessError):
            self.product.product_tmpl_id.with_user(seller).write({'mys_origen_mercaderia': 'imported'})
        with self.assertRaises(UserError):
            self.order._mys_check_discount_policy()
