"""Propuestas de cambio: el agente propone con vista previa; solo el vendedor desde Odoo las aplica."""


def proponer(ent, cambios, cotizacion="COT-DEMO-001", agente="proponer_cambio_cotizacion"):
    return ent.llamar("POST", "/propuestas", agente=agente,
                      json={"cotizacion": cotizacion, "cambios": cambios, "motivo": "Prueba"})


def test_cambiar_descuento_calcula_vista_previa_y_avisa_tope(entorno):
    r = proponer(entorno, [{"producto": "RAD-7BT", "descuento": 10}])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["estado"] == "PENDIENTE" and d["propuesta_id"].startswith("PRO-")
    assert d["cambios"] == [{"accion": "modificar", "sku": "RAD-7BT", "texto": "RAD-7BT", "descuento": 10.0}]
    assert d["vista_previa"]["total_actual"] == "1900.00"      # 5 × 400 con 5 %
    assert d["vista_previa"]["total_propuesto"] == "1800.00"   # 5 × 400 con 10 %
    assert d["vista_previa"]["supera_tope"] is True
    assert "gerente" in d["mensaje"]


def test_agregar_producto_y_cambiar_cantidad_desde_texto_json(entorno):
    import json
    r = proponer(entorno, json.dumps([{"producto": "RAD-7BT", "cantidad": 6}, {"producto": "RAD-10X", "cantidad": 1}]))
    assert r.status_code == 200, r.text
    v = r.json()["vista_previa"]
    assert v["total_propuesto"] == "2800.00"   # 6 × 400 × 0,95 = 2280 + 1 × 520
    assert v["supera_tope"] is False
    assert [c["accion"] for c in r.json()["cambios"]] == ["modificar", "agregar"]


def test_validaciones(entorno):
    assert proponer(entorno, [{"producto": "RAD-7BT", "descuento": 150}]).status_code == 422
    assert proponer(entorno, [{"producto": "RAD-7BT", "accion": "quitar"}]).status_code == 422   # quedaría vacía
    assert proponer(entorno, [{"producto": "NO-EXISTE", "cantidad": 1}]).status_code == 404
    assert proponer(entorno, []).status_code == 422


def test_el_agente_no_puede_aplicar_su_propia_propuesta(entorno):
    pid = proponer(entorno, [{"producto": "RAD-7BT", "descuento": 3}]).json()["propuesta_id"]
    r = entorno.llamar("POST", f"/propuestas/{pid}/resolver", agente="aplicar", json={"accion": "APLICADA", "nueva_version": 2})
    assert r.status_code == 403
    assert entorno.llamar("GET", f"/propuestas/{pid}").json()["estado"] == "PENDIENTE"


def test_queda_en_bitacora(entorno):
    pid = proponer(entorno, [{"producto": "RAD-7BT", "cantidad": 4}]).json()["propuesta_id"]
    eventos = entorno.llamar("GET", f"/bitacora?correlation_id={pid}", rol="ADMIN").json()
    lista = eventos.get("eventos", eventos) if isinstance(eventos, dict) else eventos
    assert any(e.get("code") == "PROPUESTA_REGISTRADA" for e in lista)
