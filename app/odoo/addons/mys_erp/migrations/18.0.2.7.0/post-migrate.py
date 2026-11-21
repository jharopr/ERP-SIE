from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['sale.order'].search([])._compute_mys_subject()
    env['crm.lead']._mys_prepare_demo_presentation()
    env['sale.order'].search([])._compute_mys_discount_state()
