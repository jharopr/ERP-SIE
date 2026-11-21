"""Análisis comercial (rotación y segmentación), sinónimos del catálogo y mejoras de las propuestas."""
from fastapi.testclient import TestClient

from app.catalogo import coincide, terminos
from app.main import crear_app
from test_integracion_odoo import config, firma


def test_rotacion_menor_prioriza_lo_estancado_con_mas_dinero_parado(entorno):
    r = entorno.llamar("GET", "/analisis/rotacion?orden=menor&dias=90", agente="rotacion_productos")
    assert r.status_code == 200, r.text
    d = r.json()
    skus = [p["sku"] for p in d["productos"]]
    assert skus[:2] == ["AMP-650", "AMP-1200"]       # 0 vendidas: primero el que NUNCA se vendió, luego 200 días sin venta
    assert "CAB-4GA" not in skus                      # sin stock: no hay nada que mover
    assert d["productos"][0]["ultima_venta"] == "nunca vendido"
    assert d["productos"][1]["valor_en_stock"] == "55200.00" and d["productos"][1]["dias_sin_venta"] == 200
    assert d["valor_en_stock_sin_ventas"] == "69500.00"
    assert d["resumen"]["Sin ventas en el periodo"] == 2


def test_rotacion_mayor_y_filtro_por_categoria(entorno):
    d = entorno.llamar("GET", "/analisis/rotacion?orden=mayor").json()
    assert [p["sku"] for p in d["productos"]] == ["RAD-7BT", "CAB-4GA"]
    d = entorno.llamar("GET", "/analisis/rotacion?orden=menor&categoria=amplificadores").json()
    assert {p["sku"] for p in d["productos"]} == {"AMP-1200", "AMP-650"}


def test_segmentacion_por_capacidad_de_compra(entorno):
    d = entorno.llamar("GET", "/analisis/clientes", agente="segmentar_clientes").json()
    capacidad = {c["codigo"]: c["capacidad_de_compra"] for c in d["clientes"]}
    assert capacidad == {"CLI-DEMO-002": "ALTA", "CLI-OTRO-001": "MEDIA", "CLI-DEMO-001": "BAJA", "CLI-DEMO-009": "SIN_COMPRAS"}
    assert d["segmentos"]["ALTA"] == {"clientes": 1, "monto_6_meses": "5750.00"}
    nuevo = next(c for c in d["clientes"] if c["codigo"] == "CLI-DEMO-009")
    assert nuevo["dias_sin_comprar"] is None          # nunca compró: no es «0 días sin comprar»


def test_segmentacion_por_afinidad_con_una_categoria(entorno):
    d = entorno.llamar("GET", "/analisis/clientes?categoria=amplificador").json()
    afinidad = {c["codigo"]: c["afinidad"] for c in d["clientes"]}
    assert afinidad == {"CLI-DEMO-002": "ya compra esta categoría", "CLI-OTRO-001": "ya compra esta categoría",
                        "CLI-DEMO-001": "complemento sugerido de lo que compra"}
    assert [c["codigo"] for c in d["clientes"]][-1] == "CLI-DEMO-001"   # primero los que ya compran
    assert entorno.llamar("GET", "/analisis/clientes?capacidad_minima=MEDIA").json()["clientes_evaluados"] == 2


def test_vendedor_ve_solo_su_cartera_y_el_gerente_toda(entorno):
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    vendedor = {"Authorization": "Bearer privado-agente", "X-MYS-Context": firma(c)}
    d = client.get("/analisis/clientes", headers=vendedor).json()
    assert d["alcance"] == "clientes asignados a este vendedor"
    assert "CLI-OTRO-001" not in {x["codigo"] for x in d["clientes"]}
    gerente = {"Authorization": "Bearer privado-agente", "X-MYS-Context": firma(c, rol="GERENCIA", actor_id="GER-DEMO-01")}
    d = client.get("/analisis/clientes", headers=gerente).json()
    assert d["alcance"] == "toda la cartera" and d["clientes_evaluados"] == 4


def test_analisis_sin_odoo_responde_503(entorno):
    entorno.odoo.caido = True
    assert entorno.llamar("GET", "/analisis/rotacion").status_code == 503
    assert entorno.llamar("GET", "/analisis/clientes").status_code == 503


def test_sinonimos_y_numeros_en_la_busqueda():
    kit = "KIT DE INSTALACIÓN PARA AMPLIFICADOR CALIBRE 4 1000W"
    assert coincide(terminos("kit de 4 gauge"), kit)
    assert not coincide(terminos("kit de 4 gauge"), "Kit Strata Cobra-4GX 5000W")
    assert not coincide(terminos("kit 4 gauge"), "Kit calibre 8 1400W")       # «4» no coincide dentro de «1400»
    assert coincide(terminos("subwoofers pioneer"), "Subwoofer Pioneer TS-W")


def proponer(ent, cambios, cotizacion="COT-DEMO-001"):
    return ent.llamar("POST", "/propuestas", agente="proponer_cambio_cotizacion",
                      json={"cotizacion": cotizacion, "cambios": cambios, "motivo": "Prueba"})


def test_sumar_es_relativo_y_cada_linea_dice_si_sube_o_baja(entorno):
    d = proponer(entorno, [{"producto": "RAD-7BT", "sumar": 1}]).json()
    linea = d["vista_previa"]["lineas"][0]
    assert linea["cantidad"] == 6.0 and linea["cambio"] == "cantidad sube de 5 a 6"
    d = proponer(entorno, [{"producto": "RAD-7BT", "cantidad": 2}]).json()
    assert d["vista_previa"]["lineas"][0]["cambio"] == "cantidad baja de 5 a 2"
    r = proponer(entorno, [{"producto": "RAD-7BT", "sumar": -9}])
    assert r.status_code == 422
    r = proponer(entorno, [{"producto": "RAD-7BT", "sumar": 1, "cantidad": 3}])
    assert r.status_code == 422


def test_quitar_una_linea_aparece_en_la_vista_previa(entorno):
    d = proponer(entorno, [{"producto": "RAD-10X", "cantidad": 1}]).json()
    assert d["vista_previa"]["lineas"][-1]["cambio"] == "nuevo: 1 unidad(es)"


def test_vendedor_no_propone_sobre_cotizacion_de_otro(entorno, monkeypatch):
    c = config(entorno)
    client = TestClient(crear_app(c, entorno.odoo, entorno.reloj))
    original = entorno.odoo.versiones_cotizacion
    monkeypatch.setattr(entorno.odoo, "versiones_cotizacion",
                        lambda q: [dict(v, seller_odoo_id=9) for v in original(q)])
    headers = {"Authorization": "Bearer privado-agente", "X-MYS-Context": firma(c), "X-Actor-Type": "AGENTE"}
    r = client.post("/propuestas", headers=headers,
                    json={"cotizacion": "COT-DEMO-001", "cambios": [{"producto": "RAD-7BT", "cantidad": 6}]})
    assert r.status_code == 403
    monkeypatch.setattr(entorno.odoo, "versiones_cotizacion",
                        lambda q: [dict(v, seller_odoo_id=6) for v in original(q)])
    r = client.post("/propuestas", headers=headers,
                    json={"cotizacion": "COT-DEMO-001", "cambios": [{"producto": "RAD-7BT", "cantidad": 6}]})
    assert r.status_code == 200, r.text


def test_resumen_exacto_y_advertencia_cuando_la_cantidad_baja(entorno):
    d = proponer(entorno, [{"producto": "RAD-7BT", "cantidad": 2}]).json()
    assert "Total actual: S/ 1900.00" in d["resumen_para_el_vendedor"]
    assert "Total propuesto: S/ 760.00 (el total baja)" in d["resumen_para_el_vendedor"]
    assert d["advertencias"] == ["Atención: en RAD-7BT la cantidad baja de 5 a 2; revise que eso sea lo que pidió el cliente."]
    d = proponer(entorno, [{"producto": "RAD-7BT", "sumar": 1}]).json()
    assert d["advertencias"] == [] and "(el total sube)" in d["resumen_para_el_vendedor"]


def test_aprobacion_vencida_se_marca_como_vencida(entorno, monkeypatch):
    version = {"version": 2, "numero_odoo": "S00054", "state": "draft", "company_odoo_id": 1, "cliente": "Cliente",
               "cliente_ref": "CLI-DEMO-001", "oportunidad": "OPP-DEMO-001", "vendedor": "Vendedor 01", "total": 1800.0,
               "analisis_comercial": None, "productos": "5 × RAD-7BT (10 %)"}
    monkeypatch.setattr(entorno.odoo, "buscar_cotizaciones",
                        lambda t, limite=5: [{"cotizacion": "COT-DEMO-009", "versiones": [version]}], raising=False)
    with entorno.repo.conexion() as db:
        for hasta in ("2026-11-12T18:00:00-05:00", "2026-11-14T18:00:00-05:00"):   # el reloj de prueba marca 13/11 10:00
            db.execute("INSERT INTO aprobaciones(company_id,quotation_id,quotation_version,total,status,approver_id,"
                       "approved_at,valid_until,motivo) VALUES(?,?,?,?,?,?,?,?,?)",
                       (entorno.config.company_id, "COT-DEMO-009", 2, "1800.00", "APROBADA", "GER-DEMO-01",
                        "2026-11-11T10:00:00-05:00", hasta, "Cliente frecuente"))
    d = entorno.llamar("GET", "/cotizaciones-buscar?texto=S00054").json()
    situaciones = [a["situacion_hoy"] for a in d["cotizaciones"][0]["historial"]["aprobaciones_de_descuento"]]
    assert situaciones[0].startswith("VENCIDA") and situaciones[1] == "vigente"
