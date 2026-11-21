"""Historial de versiones y pedidos, con alcance comercial y filtros comunes."""
from datetime import datetime, time

import pytz

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class Gateway(models.AbstractModel):
    _inherit = 'mys.gateway'

    def _trace_operations(self, query='', order_id=False, correlation_id='', partner_id=False,
                          user_id=False, date_from=False, date_to=False, version=False,
                          event_type='', actor_id=''):
        role = self._role()
        if not isinstance(query, str) or len(query) > 160:
            raise UserError(_('La búsqueda admite hasta 160 caracteres.'))
        query = (query or correlation_id or '').strip()
        Order = self.env['sale.order']
        base = [('company_id', '=', self.env.company.id)]
        if role == 'VENTAS':
            base += [('user_id', '=', self.env.uid)]
        for name, value in [('partner_id', partner_id), ('user_id', user_id)]:
            if value:
                base += [(name, '=', int(value))]
        domain = expression.AND([base, ['|', ('client_order_ref', '=like', 'COT-%'), ('opportunity_id', '!=', False)]])
        anchor = Order.search(expression.AND([base, [('id', '=', int(order_id))]]), limit=1) if order_id else Order.browse()
        if order_id and not anchor:
            raise UserError(_('No tiene acceso a esta operación.'))
        if not anchor and query:
            anchor = Order.search(expression.AND([domain, [('name', '=ilike', query)]]), limit=1)
        if anchor:
            related = [('opportunity_id', '=', anchor.opportunity_id.id)] if anchor.opportunity_id else [
                ('mys_quotation_id', '=', anchor.mys_quotation_id)] if anchor.mys_quotation_id else [('id', '=', anchor.id)]
            domain = expression.AND([base, related])
        elif query:
            evs = self.env['mys.evaluation'].search(['|', ('correlation_id', '=', query), ('request_id', '=', query)])
            domain = expression.AND([domain, expression.OR([
                [(name, 'ilike', query)] for name in ('name', 'client_order_ref', 'partner_id.name',
                                                     'opportunity_id.name', 'opportunity_id.mys_reference')
            ] + [[('id', 'in', evs.order_id.ids)]])])
        orders = Order.search(domain, order='id desc', limit=201)
        warning = _('Se muestran hasta 200 registros. Precise la búsqueda para consultar más operaciones.') if len(orders) > 200 else False
        orders = orders[:200]
        local = self.env['mys.operation.event'].search([('order_id', 'in', orders.ids)])
        evaluations = self.env['mys.evaluation'].search([('order_id', 'in', orders.ids)])
        decisions = self.env['mys.decision'].search([('order_id', 'in', orders.ids)])
        events = []

        def append(order, event_id, occurred_at, kind, code, actor, actor_type='HUMANO', detail='', interface='ODOO'):
            events.append({'event_id': event_id, 'occurred_at': occurred_at, 'event_type': kind, 'code': code,
                           'actor_id': actor, 'actor_type': actor_type, 'interface_id': interface,
                           'detail': detail, 'order_id': order.id, 'order_name': order.name,
                           'version': order.mys_version, 'quotation_id': order.mys_quotation_id or '',
                           'customer': order.partner_id.display_name, 'seller': order.user_id.display_name})

        def local_time(value):
            return pytz.UTC.localize(fields.Datetime.to_datetime(value)).astimezone(pytz.timezone('America/Lima')).isoformat()

        def describe(detail):
            labels = {'motivo': 'Motivo', 'mensaje': 'Resultado', 'diagnostico': 'Diagnóstico',
                      'siguiente_paso': 'Siguiente paso', 'quotation_id': 'Cotización', 'version': 'Versión',
                      'total': 'Total verificado', 'sku': 'Producto', 'faltante': 'Cantidad faltante',
                      'escalation_id': 'Solicitud al dueño'}
            lines = ['%s: %s' % (label, detail[key]) for key, label in labels.items() if detail.get(key)]
            for condition in detail.get('condiciones', []):
                lines.append('%s: solicitado %s, disponible %s' % (condition.get('sku', ''),
                             condition.get('requested_quantity', ''), condition.get('available_quantity', '')))
            return '\n'.join(lines)

        for event in local:
            append(event.order_id, 'odoo-%s' % event.id, local_time(event.occurred_at), event.event_type,
                   event.code, event.user_id.display_name, detail=event.detail or '')
        created = local.filtered(lambda e: e.code == 'CREADA').order_id
        for order in orders - created:
            append(order, 'created-%s' % order.id, local_time(order.create_date), 'COTIZACION', 'CREADA',
                   order.create_uid.display_name, detail=_('Registro histórico de creación de la cotización.'))
        for decision in decisions.filtered('decision'):
            detail = decision.motivo or ''
            if decision.new_order_id:
                detail += '\n' + _('Nueva versión: %s') % decision.new_order_id.name
            if not decision.mys_decided_at:
                detail += '\n' + _('Registro histórico: se muestra la fecha de última actualización en Odoo.')
            append(decision.order_id, 'decision-%s' % decision.id,
                   local_time(decision.mys_decided_at or decision.write_date),
                   'APROBACION' if decision.tipo == 'DESCUENTO' else 'DECISION_DUENO',
                   decision.decision, decision.approver_id.display_name or _('Dueño'), detail=detail)
        remote_requests = set()
        by_request = {e.request_id: e.order_id for e in evaluations}
        families = set(orders.mapped('mys_quotation_id')) - {False, ''}
        for family in sorted(families):
            try:
                remote = self._request('GET', '/bitacora?quotation_id=' + family)['eventos']
            except UserError:
                warning = _('La compuerta no respondió: se muestra el historial guardado en Odoo. Reintente para ver todos los eventos de reglas.')
                break
            for event in remote:
                detail = event.get('detalle') or {}
                if event['event_type'] == 'ACEPTACION' and local.filtered(lambda e:
                        e.event_type == 'ACEPTACION' and e.order_id.mys_quotation_id == detail.get('quotation_id')
                        and e.order_id.mys_version == detail.get('version')):
                    continue
                if event['event_type'] == 'APROBACION' and decisions.filtered(lambda d:
                        d.tipo == 'DESCUENTO' and d.order_id.mys_quotation_id == detail.get('quotation_id')
                        and d.target_version == detail.get('version') and d.decision == event['code']):
                    continue
                order = by_request.get(event.get('request_id'))
                if event.get('request_id') and not order:
                    continue
                if not order:
                    if detail.get('quotation_id'):
                        order = orders.filtered(lambda o: o.mys_quotation_id == detail['quotation_id'] and
                                                o.mys_version == detail.get('version', detail.get('quotation_version')))[:1]
                if not order or order not in orders:
                    continue
                if event.get('request_id'):
                    remote_requests.add(event['request_id'])
                if event['event_type'] == 'DECISION':
                    ev = evaluations.filtered(lambda e: e.request_id == event.get('request_id'))[:1]
                    detail = {**detail, 'diagnostico': ev.message or '', 'siguiente_paso': ev.required_action or ''}
                append(order, 'gateway-%s' % event['event_id'], event['occurred_at'], event['event_type'],
                       event['code'], event['actor_id'], event.get('actor_type', 'SISTEMA'),
                       describe(detail), event['interface_id'])
        for ev in evaluations.filtered(lambda e: e.request_id not in remote_requests):
            append(ev.order_id, 'evaluation-%s' % ev.id, local_time(ev.write_date), 'EVALUACION', ev.code,
                   ev.user_id.display_name, 'SISTEMA', '\n'.join(filter(None, [ev.message, ev.required_action])))

        def parse_time(value):
            parsed = datetime.fromisoformat(value)
            return parsed.replace(tzinfo=pytz.UTC) if parsed.tzinfo is None else parsed

        events.sort(key=lambda e: (parse_time(e['occurred_at']), e['event_id']))
        options = {
            'customers': [{'id': p.id, 'name': p.display_name} for p in orders.partner_id.sorted('name')],
            'sellers': [{'id': u.id, 'name': u.display_name} for u in orders.user_id.sorted('name')],
            'versions': sorted(set(orders.mapped('mys_version')) - {0}),
            'types': sorted({e['event_type'] for e in events}), 'actors': sorted({e['actor_id'] for e in events}),
        }
        lima = pytz.timezone('America/Lima')
        try:
            start = lima.localize(datetime.combine(fields.Date.to_date(date_from), time.min)) if date_from else None
            end = lima.localize(datetime.combine(fields.Date.to_date(date_to), time.max)) if date_to else None
        except (ValueError, TypeError):
            raise UserError(_('Seleccione fechas válidas.')) from None
        if start and end and start > end:
            raise UserError(_('La fecha inicial debe ser anterior a la fecha final.'))
        events = [e for e in events if (not version or e['version'] == int(version))
                  and (not event_type or e['event_type'] == event_type)
                  and (not actor_id or e['actor_id'] == actor_id)
                  and (not start or parse_time(e['occurred_at']) >= start)
                  and (not end or parse_time(e['occurred_at']) <= end)]
        return {'eventos': events, 'options': options, 'warning': warning,
                'orders': [{'id': o.id, 'name': o.name, 'version': o.mys_version, 'state': o.state,
                            'customer': o.partner_id.display_name, 'reference': o.mys_quotation_id or '',
                            'evaluation': o.mys_status or 'Sin evaluar'} for o in orders.sorted('id')]}
