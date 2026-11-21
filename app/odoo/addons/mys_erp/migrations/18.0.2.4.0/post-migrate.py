from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Conserva las ofertas existentes; solo sincroniza sus ingresos esperados.
    env['crm.lead'].with_context(active_test=False).search([
        ('type', '=', 'opportunity'), ('order_ids', '!=', False),
    ])._mys_sync_expected_revenue()
