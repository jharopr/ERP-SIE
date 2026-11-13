import json
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from odoo.tools import file_open


class ContactoMYS(models.Model):
    _inherit = 'res.partner'

    mys_demo = fields.Boolean('Datos de prueba MYS', index=True)
    mys_segmento = fields.Selection([('nuevo', 'Público general nuevo'), ('recurrente', 'Cliente recurrente'),
                                     ('proveedor', 'Proveedor de demostración')], string='Segmento comercial')
    mys_identidad_revisada = fields.Boolean('Identidad sintética revisada')
    mys_documento_demo = fields.Char('Documento de ejemplo', copy=False,
                                    help='Identificador ficticio para la demostración. No es un documento fiscal.')
    mys_canal_preferido = fields.Selection([
        ('whatsapp', 'WhatsApp'), ('telefono', 'Llamada telefónica'),
        ('correo', 'Correo electrónico'), ('tienda', 'Atención en tienda'),
    ], string='Canal preferido')

    @api.model
    def action_mys_prepare_demo_contacts(self):
        """Permite al seed sincronizar las fichas sin reiniciar operaciones."""
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Solo el administrador puede preparar los contactos de demostración.'))
        return self._mys_prepare_demo_contacts()

    @api.model
    def _mys_prepare_demo_contacts(self):
        """Actualiza por referencia: conserva IDs, cotizaciones e historial.

        Los contactos manuales (como Benja) quedan fuera de esta carga. Solo se
        archivan los registros automáticos reconocidos por su nombre y referencia.
        """
        with file_open('mys_erp/demo/contactos_demo.json', 'r') as source:
            contacts = json.load(source)
        partners = self.with_context(active_test=False, tracking_disable=True,
                                     mail_create_nosubscribe=True)
        country = self.env.ref('base.pe')
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id), ('code', '=', '15'),
        ], limit=1)
        seller = self.env['res.users'].search([('login', '=', 'vendedor01')], limit=1)
        ids = []
        for contact in contacts:
            values = dict(contact, country_id=country.id, state_id=state.id,
                          mys_demo=True, mys_identidad_revisada=True,
                          customer_rank=1, active=True, is_company=False,
                          type='contact', lang='es_PE', tz='America/Lima')
            if seller:
                values['user_id'] = seller.id
            partner = partners.search([('ref', '=', contact['ref'])], limit=1)
            if partner:
                # Evita mensajes y escrituras innecesarias en cada arranque.
                changes = {key: value for key, value in values.items()
                           if (partner[key].id if partner._fields[key].type == 'many2one'
                               else partner[key]) != value}
                if changes:
                    partner.write(changes)
            else:
                partner = partners.create(values)
            ids.append(partner.id)
            # CRM conserva sus nombres/códigos y recibe los datos visibles del contacto.
            leads = self.env['crm.lead'].with_context(active_test=False, tracking_disable=True).search([
                ('partner_id', '=', partner.id),
            ])
            for lead in leads:
                details = {'contact_name': partner.name, 'email_from': partner.email,
                           'phone': partner.phone, 'mobile': partner.mobile,
                           'street': partner.street, 'street2': partner.street2,
                           'city': partner.city, 'zip': partner.zip,
                           'state_id': partner.state_id.id, 'country_id': partner.country_id.id}
                changes = {key: value for key, value in details.items()
                           if (lead[key].id if lead._fields[key].type == 'many2one'
                               else lead[key]) != value}
                if changes:
                    lead.write(changes)
        generated = partners.search([
            ('mys_demo', '=', True), ('supplier_rank', '=', 0),
            ('name', '=like', 'Cliente prueba nativa %'), ('id', 'not in', ids),
        ]).filtered(lambda p: re.fullmatch(r'Cliente prueba nativa [0-9a-f]{8}', p.name)
                    and p.ref == 'CLI-MYS-%s' % p.id and p.active)
        generated.write({'active': False})
        return ids
