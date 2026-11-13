import os
import uuid
import hashlib
import hmac
import time
import requests
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, UserError
from werkzeug.exceptions import Forbidden, BadRequest

_AGENT_CACHE = {}
_PROVIDER_MESSAGES = {
    'CUOTA_AGOTADA': 'Sin cuota: Gemini agotó el límite de generación de la cuenta. La clave es válida. '
                    'Espere a que el proveedor restablezca la cuota; las reglas y módulos de Odoo siguen disponibles.',
    'API_KEY_RECHAZADA': 'Gemini rechazó la API key o sus permisos. Actualice GEMINI_API_KEY en app/.env.',
    'MODELO_NO_DISPONIBLE': 'Gemini no pudo generar la respuesta. Revise el modelo y su disponibilidad.'}


def _provider_failure(code):
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    model = os.environ.get('GEMINI_MODEL', 'models/gemini-3.5-flash-lite')
    failure = {'configured': bool(key), 'enabled': False, 'model': model, 'code': code, 'message': _PROVIDER_MESSAGES[code]}
    cache_key = hashlib.sha256((key + model).encode()).hexdigest()
    _AGENT_CACHE[cache_key] = (time.monotonic() + (3600 if code == 'CUOTA_AGOTADA' else 60), failure)
    return failure


class Sistema(http.Controller):
    @http.route('/mys/agent/provider-error', type='http', auth='none', methods=['POST'], csrf=False)
    def provider_error(self):
        expected = os.environ.get('N8N_WEBHOOK_SECRET', '')
        supplied = request.httprequest.headers.get('X-MYS-Webhook', '')
        if not expected or not hmac.compare_digest(expected.encode(), supplied.encode()):
            raise Forbidden()
        data = request.httprequest.get_json(silent=True) or {}
        if data.get('code') not in _PROVIDER_MESSAGES:
            raise BadRequest()
        _provider_failure(data['code'])
        return request.make_json_response({'recorded': True})

    @http.route('/mys/session', type='json', auth='user')
    def session(self):
        gateway = request.env['mys.gateway']
        role = gateway._role()
        return {'name': request.env.user.name, 'role': role, 'uid': request.env.uid,
                'agent': self._agent_status()}

    def _agent_status(self):
        key = os.environ.get('GEMINI_API_KEY', '').strip()
        model = os.environ.get('GEMINI_MODEL', 'models/gemini-3.5-flash-lite')
        result = {'configured': bool(key), 'enabled': False, 'model': model, 'code': 'SIN_API_KEY',
                  'message': 'Deshabilitado: falta GEMINI_API_KEY en app/.env.'}
        if not key:
            return result
        cache_key = hashlib.sha256((key + model).encode()).hexdigest()
        cached = _AGENT_CACHE.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        try:
            response = requests.get('https://generativelanguage.googleapis.com/v1beta/models',
                                    headers={'x-goog-api-key': key}, timeout=8)
            if response.ok:
                models = response.json().get('models', [])
                available = any(m['name'] == model and 'generateContent' in m.get('supportedGenerationMethods', []) for m in models)
                result.update(enabled=available, code='HABILITADO' if available else 'MODELO_NO_DISPONIBLE',
                    message='API key verificada. Agente disponible.' if available else 'API key válida; el modelo configurado no está disponible para esta cuenta.')
            elif response.status_code in (400, 401, 403):
                result.update(code='API_KEY_RECHAZADA', message='Deshabilitado: Gemini rechazó la API key o sus permisos. Actualice GEMINI_API_KEY en app/.env.')
            elif response.status_code == 429:
                result.update(code='CUOTA_AGOTADA', message='Gemini no tiene cuota disponible. Reintente después o revise la cuota de la cuenta.')
            else:
                result.update(code='SIN_CONEXION', message='No se pudo verificar Gemini. Reintente en un minuto.')
        except (requests.RequestException, ValueError):
            result.update(code='SIN_CONEXION', message='No se pudo conectar con Gemini. Reintente en un minuto.')
        _AGENT_CACHE.clear()
        _AGENT_CACHE[cache_key] = (time.monotonic() + 60, result)
        return result

    def _sync(self, data):
        """Refleja también evaluaciones/escalamientos creados con las herramientas del chat."""
        env = request.env
        env.cr.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ['mys-sync-%s' % env.company.id])
        Eval = env['mys.evaluation'].sudo()
        Decision = env['mys.decision'].sudo()
        for r in data['solicitudes']:
            order = env['sale.order'].search([('mys_quotation_id', '=', r['quotation_id']),
                                               ('mys_version', '=', r['quotation_version']),
                                               ('company_id', '=', env.company.id)], limit=1)
            if not order:
                continue
            rec = Eval.search([('request_id', '=', r['request_id'])], limit=1)
            import json
            values = {'order_id': order.id, 'user_id': order.user_id.id, 'company_id': order.company_id.id,
                      'request_id': r['request_id'], 'correlation_id': r['correlation_id'], 'status': r['status'],
                      'code': r['code'], 'message': r['message'], 'required_action': r.get('required_action'),
                      'response_json': json.dumps(r, ensure_ascii=False, indent=2)}
            rec.write(values) if rec else Eval.create(values)
            order.sudo().write({'mys_locked': True, 'mys_request_id': r['request_id'],
                                'mys_correlation_id': r['correlation_id'], 'mys_status': r['status']})
        for esc in data['escalamientos']:
            evaluation = Eval.search([('request_id', '=', esc['request_id'])], limit=1)
            if not evaluation:
                continue
            values = {'evaluation_id': evaluation.id, 'user_id': evaluation.user_id.id,
                      'company_id': evaluation.company_id.id, 'escalation_id': esc['escalation_id'],
                      'tipo': esc['tipo'], 'state': esc['estado'], 'total': esc['total'],
                      'target_version': esc['version_aprobacion'], 'deadline': esc['plazo_hasta']}
            rec = Decision.search([('escalation_id', '=', esc['escalation_id'])], limit=1)
            if rec:
                rec.write({k: v for k, v in values.items() if k != 'state' or rec.state != 'DECIDIDO'})
            else:
                Decision.create(values)

    @http.route('/mys/workspace', type='json', auth='user')
    def workspace(self):
        env = request.env
        gateway = env['mys.gateway']
        role = gateway._role()
        warning = False
        try:
            data = gateway._request('GET', '/integracion/resumen')
            self._sync(data)
        except UserError as exc:
            warning = str(exc)
            data = {'politica': {}}
        return {'role': role, 'agent': self._agent_status(), 'warning': warning,
                'counts': {'contacts': env['res.partner'].search_count([('mys_demo', '=', True)]),
                           'leads': env['crm.lead'].search_count([('type', '=', 'lead')]),
                           'opportunities': env['crm.lead'].search_count([('type', '=', 'opportunity')]),
                           'products': env['product.template'].search_count([('mys_catalogo', '=', True)]),
                           'quotes': env['sale.order'].search_count(['|', ('client_order_ref', '=like', 'COT-%'), ('client_order_ref', '=', False), ('state', '!=', 'sale'), ('mys_confirmed_at', '=', False)]),
                           'sales': env['sale.order'].search_count([('client_order_ref', '=like', 'COT-%'), '|', ('state', '=', 'sale'), ('mys_confirmed_at', '!=', False)]),
                           'evaluations': env['mys.evaluation'].search_count([]),
                           'decisions': env['mys.decision'].search_count([('state', '=', 'ESPERANDO_DECISION')])},
                'policy': data['politica'],
                'evaluations': env['mys.evaluation'].search_read([], ['request_id', 'order_id', 'status', 'code',
                                                                      'message', 'correlation_id'], limit=20)}

    @http.route('/mys/trace', type='json', auth='user')
    def trace(self, **filters):
        allowed = {'query', 'order_id', 'correlation_id', 'partner_id', 'user_id', 'date_from',
                   'date_to', 'version', 'event_type', 'actor_id'}
        return request.env['mys.gateway']._trace_operations(**{k: v for k, v in filters.items() if k in allowed})

    @http.route('/mys/agent/status', type='json', auth='user')
    def agent_status(self):
        request.env['mys.gateway']._role()
        return self._agent_status()

    @http.route('/mys/agent/chat', type='json', auth='user')
    def chat(self, message, conversation=None):
        gateway = request.env['mys.gateway']
        headers = gateway._headers()
        status = self._agent_status()
        if not status['enabled']:
            return {'ok': False, 'code': status['code'], 'message': status['message']}
        if not isinstance(message, str) or not message.strip() or len(message) > 4000:
            raise UserError('Escriba un mensaje de 1 a 4000 caracteres.')
        import re
        if not isinstance(conversation, str) or not re.fullmatch(r'[a-f0-9]{32}', conversation):
            conversation = uuid.uuid4().hex
        # Memoria separada por usuario y conversación. Ninguna credencial llega al navegador.
        body = {'chatInput': message.strip(), 'sessionId': 'odoo-%s-%s' % (request.env.uid, conversation),
                'mys_context': headers['X-MYS-Context']}
        try:
            r = requests.post(os.environ.get('N8N_INTERNAL_URL', 'http://n8n:5678') + '/webhook/mys-agente-integrado',
                              json=body, headers={'X-MYS-Webhook': os.environ.get('N8N_WEBHOOK_SECRET', '')}, timeout=100)
            data = r.json()
            if isinstance(data, list):
                data = data[0] if data else {}
            output = data.get('output')
            if r.ok and output:
                # Las evaluaciones y escalamientos del chat aparecen en los módulos nativos
                # al terminar la respuesta, sin esperar una visita al tablero.
                try:
                    self._sync(gateway._request('GET', '/integracion/resumen'))
                except UserError:
                    pass
                return {'ok': True, 'message': str(output), 'conversation': conversation}
            code = data.get('code')
            if code in _PROVIDER_MESSAGES:
                failure = _provider_failure(code)
                return {'ok': False, 'code': code, 'message': failure['message'], 'conversation': conversation}
        except (requests.RequestException, ValueError):
            pass
        # El workflow de error de n8n publica el estado con cabecera privada, sin
        # devolver descripciones del proveedor que puedan contener información interna.
        for attempt in range(4):
            status = self._agent_status()
            if not status['enabled']:
                return {'ok': False, 'code': status['code'], 'message': status['message'], 'conversation': conversation}
            if attempt < 3:
                time.sleep(0.2)
        return {'ok': False, 'code': 'MODELO_NO_DISPONIBLE', 'conversation': conversation,
                'message': 'La API key está configurada, pero el agente no pudo responder. Revise validez de la clave, '
                           'cuota, modelo y servicio n8n. Las reglas comerciales siguen disponibles en Odoo.'}
