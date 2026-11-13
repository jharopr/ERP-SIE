def post_init_hook(env):
    env['crm.lead']._mys_migrate_pipeline()
    env['res.partner']._mys_prepare_demo_contacts()
    env['crm.lead']._mys_prepare_demo_presentation()
