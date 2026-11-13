"""Integración app/: seguridad del panel y consulta de inventario tras R08."""
from datetime import timedelta
from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def compatibilidad_portal_historico(monkeypatch):
    monkeypatch.setenv('ENABLE_LEGACY_PORTAL', 'true')


def login(entorno, monkeypatch, rol='VENTAS'):
    monkeypatch.setenv('ODOO_SELLER_PASSWORD', 'clave-vendedor-prueba')
    monkeypatch.setenv('ODOO_OWNER_PASSWORD', 'clave-dueno-prueba')
    password = 'clave-vendedor-prueba' if rol == 'VENTAS' else 'clave-dueno-prueba'
    return entorno.cliente.post('/panel/sesion', json={'rol': rol, 'password': password})


def test_rechazo_r08_no_invoca_proveedor_stock(entorno, casos):
    original = entorno.odoo.stock
    entorno.odoo.stock = Mock(side_effect=original)
    r = entorno.llamar('POST', '/solicitudes', json=casos['PC3-E02']['solicitud'])
    assert r.json()['respuesta']['code'] == 'DESCUENTO_SIN_APROBACION'
    entorno.odoo.stock.assert_not_called()


def test_reintento_no_reconsulta_stock(entorno, casos):
    entorno.odoo.stock = Mock(side_effect=entorno.odoo.stock)
    payload = casos['PC3-N01']['solicitud']
    first = entorno.llamar('POST', '/solicitudes', json=payload)
    assert entorno.odoo.stock.call_count == 1
    entorno.odoo.stock.reset_mock()
    again = entorno.llamar('POST', '/solicitudes', json=payload)
    assert first.json() == again.json()
    entorno.odoo.stock.assert_not_called()


def test_panel_requiere_sesion(entorno):
    assert entorno.cliente.get('/panel/resumen').status_code == 401
    assert entorno.cliente.get('/panel/casos').status_code == 401


def test_login_cookie_http_only_y_logout(entorno, monkeypatch):
    result = login(entorno, monkeypatch)
    assert result.status_code == 200
    assert 'HttpOnly' in result.headers['set-cookie']
    assert 'SameSite=strict' in result.headers['set-cookie']
    assert entorno.cliente.get('/panel/resumen').json()['rol'] == 'VENTAS'
    assert entorno.cliente.delete('/panel/sesion').status_code == 200
    assert entorno.cliente.get('/panel/resumen').status_code == 401


def test_login_no_revela_tokens(entorno, monkeypatch):
    monkeypatch.setenv('ODOO_SELLER_PASSWORD', 'clave-vendedor-prueba')
    r = entorno.cliente.post('/panel/sesion', json={'rol': 'VENTAS', 'password': 'incorrecta'})
    assert r.status_code == 401
    assert 'TOKEN_' not in r.text


def test_panel_ventas_no_aprueba(entorno, monkeypatch):
    login(entorno, monkeypatch)
    r = entorno.cliente.post('/panel/escalamientos/ESC-PC3-001/decision', json={'decision':'APROBADA','motivo':'demo'})
    assert r.status_code == 403


def test_panel_dueno_no_envia_solicitud_ventas(entorno, monkeypatch):
    login(entorno, monkeypatch, 'GERENCIA')
    assert entorno.cliente.post('/panel/casos/PC3-N01/evaluar').status_code == 403


def test_panel_origen_externo_bloqueado(entorno, monkeypatch):
    login(entorno, monkeypatch)
    r = entorno.cliente.post('/panel/casos/PC3-N01/evaluar', headers={'Origin':'https://otro-sitio.example'})
    assert r.status_code == 403


def test_panel_caso_real_y_escalamiento(entorno, monkeypatch):
    login(entorno, monkeypatch)
    response = entorno.cliente.post('/panel/casos/PC3-E01/evaluar')
    assert response.status_code == 200, response.text
    assert response.json()['respuesta']['status'] == 'PROMESA_CONDICIONADA'
    request_id = response.json()['respuesta']['request_id']
    esc = entorno.cliente.post(f'/panel/solicitudes/{request_id}/escalar')
    assert esc.status_code == 200, esc.text
    assert esc.json()['estado'] == 'ESPERANDO_DECISION'


def test_dueno_no_decide_tras_vencimiento(entorno, casos):
    entorno.llamar('POST', '/solicitudes', json=casos['PC3-E01']['solicitud'])
    esc = entorno.llamar('POST', '/escalamientos', json={'tipo':'REPOSICION','request_id':'SOL-PC3-E01','resumen':'Prueba del plazo'}).json()
    entorno.reloj.hora += timedelta(minutes=11)
    r = entorno.llamar('POST', f'/escalamientos/{esc["escalation_id"]}/decision', rol='GERENCIA',
                       json={'decision':'EVALUAR_REPOSICION','motivo':'Demasiado tarde'})
    assert r.status_code == 409
