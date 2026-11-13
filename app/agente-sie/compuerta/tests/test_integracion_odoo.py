"""Seguridad de la identidad Odoo y del agente, independiente de la interfaz."""
import base64
from dataclasses import replace
import hashlib
import hmac
import json
import time
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import crear_app
from app.seguridad import identificar


def firma(config, **changes):
    datos = {'uid': 6, 'actor_id': 'VEN-DEMO-01', 'rol': 'VENTAS', 'company_id': 'MYS-DEMO', 'exp': int(time.time())+600}
    datos.update(changes)
    raw = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip('=')
    return raw + '.' + hmac.new(config.bridge_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def config(entorno):
    return replace(entorno.config, token_odoo='privado-odoo', token_agente='privado-agente', bridge_secret='firma-prueba')


def test_contexto_firmado_vencido_alterado_y_compania(entorno):
    c = config(entorno)
    assert identificar(c, 'Bearer privado-odoo', None, firma(c)).odoo_uid == 6
    assert identificar(c, 'Bearer privado-odoo', None, firma(c, exp=int(time.time())-1)) is None
    assert identificar(c, 'Bearer privado-odoo', None, firma(c, company_id='OTRA')) is None
    assert identificar(c, 'Bearer privado-odoo', None, firma(c)+'x') is None
    assert identificar(c, 'Bearer privado-odoo', None, None) is None
    assert identificar(c, 'Bearer privado-odoo', None, 'roto') is None


def test_agente_con_contexto_dueno_no_puede_aprobar(entorno):
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    headers = {'Authorization': 'Bearer privado-agente', 'X-MYS-Context': firma(c, rol='GERENCIA', actor_id='GER-DEMO-01')}
    r = client.post('/aprobaciones', headers=headers, json={'quotation_id': 'COT-DEMO-004', 'version': 3,
                   'total': '1800.00', 'decision': 'APROBADA', 'motivo': 'No autorizado'})
    assert r.status_code == 403


def test_navegador_no_puede_inventar_identidad_o_registrar_otro_vendedor(entorno):
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    body = {'opportunity_id': 'OPP-TEST', 'customer_id': 'CLI-DEMO-001', 'seller_uid': 99, 'identidad_revisada': True}
    headers = {'Authorization': 'Bearer privado-odoo', 'X-MYS-Context': firma(c)}
    assert client.post('/integracion/contexto', headers=headers, json=body).status_code == 403
    body['seller_uid'] = 6
    assert client.post('/integracion/contexto', headers=headers, json=body).status_code == 200
    headers['Authorization'] = 'Bearer privado-agente'
    assert client.post('/integracion/contexto', headers=headers, json=body).status_code == 403


def test_portal_retirado_por_defecto(entorno, monkeypatch):
    monkeypatch.delenv('ENABLE_LEGACY_PORTAL', raising=False)
    client = TestClient(crear_app(config(entorno), entorno.odoo, entorno.reloj))
    assert client.get('/panel/resumen').status_code == 404


def test_escalamiento_vencido_admite_nuevo_seguimiento(entorno, casos):
    payload = casos['PC3-E02']['solicitud']
    entorno.llamar('POST', '/solicitudes', json=payload)
    body = {'tipo': 'DESCUENTO', 'request_id': payload['request_id'], 'resumen': 'Revisar excepción comercial'}
    first = entorno.llamar('POST', '/escalamientos', json=body).json()
    entorno.reloj.hora += timedelta(minutes=11)
    second = entorno.llamar('POST', '/escalamientos', json=body).json()
    assert first['escalation_id'] != second['escalation_id']
    assert segundo_estado(entorno, first['escalation_id']) == 'SIN_DECISION'


def segundo_estado(entorno, escalation_id):
    return entorno.llamar('GET', '/escalamientos/'+escalation_id).json()['estado']


def test_revalidar_venta_usa_stock_fresco_y_conserva_evaluacion(entorno, casos):
    payload = casos['PC3-N01']['solicitud']
    first = entorno.llamar('POST', '/solicitudes', json=payload).json()['respuesta']
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    headers = {'Authorization': 'Bearer privado-odoo', 'X-MYS-Context': firma(c)}
    path = '/solicitudes/' + payload['request_id'] + '/validar-confirmacion'
    assert client.post(path, headers=headers).json()['respuesta']['code'] == 'VALIDADA'
    entorno.odoo.reservado['RAD-7BT'] = entorno.odoo.fisico['RAD-7BT']
    result = client.post(path, headers=headers)
    assert result.status_code == 200
    assert result.json()['respuesta']['code'] == 'DISPONIBILIDAD_PARCIAL'
    assert entorno.repo.respuesta(c.company_id, payload['request_id'])['respuesta'] == first
    assert not entorno.repo.senales_de(payload['request_id'])
    assert any(e['event_type'] == 'REVALIDACION_VENTA' for e in entorno.repo.bitacora(request_id=payload['request_id']))


def test_revalidar_venta_rechaza_agente_y_token_sin_sesion_odoo(entorno, casos):
    payload = casos['PC3-N01']['solicitud']
    entorno.llamar('POST', '/solicitudes', json=payload)
    path = '/solicitudes/' + payload['request_id'] + '/validar-confirmacion'
    assert entorno.llamar('POST', path).status_code == 403
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    headers = {'Authorization': 'Bearer privado-agente', 'X-MYS-Context': firma(c)}
    assert client.post(path, headers=headers).status_code == 403
    headers = {'Authorization': 'Bearer privado-odoo', 'X-MYS-Context': firma(c, actor_id='VEN-OTRO')}
    assert client.post(path, headers=headers).status_code == 403


def test_revalidar_venta_detecta_vencimiento_y_caida(entorno, casos):
    payload = casos['PC3-N01']['solicitud']
    entorno.llamar('POST', '/solicitudes', json=payload)
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    headers = {'Authorization': 'Bearer privado-odoo', 'X-MYS-Context': firma(c)}
    path = '/solicitudes/' + payload['request_id'] + '/validar-confirmacion'
    entorno.odoo.caido = True
    assert client.post(path, headers=headers).json()['respuesta']['status'] == 'PENDIENTE'
    entorno.odoo.caido = False
    entorno.reloj.hora += timedelta(days=2)
    assert client.post(path, headers=headers).json()['respuesta']['code'] == 'COTIZACION_VENCIDA'


def test_bitacora_por_cotizacion_incluye_aceptacion_sin_correlacion(entorno, casos):
    payload = casos['PC3-N01']['solicitud']
    entorno.llamar('POST', '/solicitudes', json=payload)
    result = entorno.llamar('POST', '/aceptaciones', json={
        'acceptance_id': 'ACE-TRACE-TEST', 'quotation_id': payload['quotation_id'],
        'version': payload['quotation_version']})
    assert result.status_code == 200
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    headers = {'Authorization': 'Bearer privado-odoo', 'X-MYS-Context': firma(c)}
    r = client.get('/bitacora', params={'quotation_id': payload['quotation_id']}, headers=headers)
    assert r.status_code == 200
    events = r.json()['eventos']
    assert any(e['event_type'] == 'ACEPTACION' and e['correlation_id'] is None for e in events)
    assert any(e['code'] == 'VALIDADA' for e in events)
    headers['X-MYS-Context'] = firma(c, actor_id='VEN-OTRO')
    assert client.get('/bitacora', params={'quotation_id': payload['quotation_id']}, headers=headers).status_code == 403
