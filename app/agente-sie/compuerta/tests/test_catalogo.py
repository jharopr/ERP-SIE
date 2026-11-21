import json
from fastapi.testclient import TestClient
from app.main import crear_app


def client_with_catalog(entorno, tmp_path, monkeypatch):
    path=tmp_path/'catalogo.json'
    path.write_text(json.dumps({'productos':[{'sku':'RAD-7BT','nombre':'Pantalla de catálogo',
                                             'codigo_original':'RAD-7BT','categoria':'Radios y Pantallas'}]}),encoding='utf-8')
    monkeypatch.setenv('CATALOGO_PATH',str(path))
    app=crear_app(entorno.config,entorno.odoo,entorno.reloj)
    return TestClient(app), {'Authorization':'Bearer '+entorno.config.token_ventas}


def test_busqueda_sin_calcular_precio(entorno,tmp_path,monkeypatch):
    client,headers=client_with_catalog(entorno,tmp_path,monkeypatch)
    response=client.get('/catalogo?q=PANTÁLLA',headers=headers)
    assert response.status_code==200
    assert response.json()['productos'][0]['precio']=='400.00'
    assert response.json()['productos'][0]['sku']=='RAD-7BT'
    assert client.get('/catalogo?q=inexistente',headers=headers).json()['productos']==[]


def test_fuente_caida_no_fabrica_precio(entorno,tmp_path,monkeypatch):
    client,headers=client_with_catalog(entorno,tmp_path,monkeypatch)
    entorno.odoo.caido=True
    assert client.get('/catalogo',headers=headers).status_code==503
    assert client.get('/catalogo').status_code==401
