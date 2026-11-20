"""El agente aprende solo de resultados confirmados por personas; los precedentes no deciden."""


def test_alias_se_aprende_y_se_reutiliza(entorno):
    motor = entorno.app.state.aprendizaje
    assert motor.alias("el autorradio de siete") is None
    motor.confirmar_alias([("El autorradio de SIETE", "RAD-7BT")])
    assert motor.alias("el autorradio de siete") == "RAD-7BT"      # sin tildes ni mayúsculas
    # La propuesta usa el alias aprendido sin preguntar.
    r = entorno.llamar("POST", "/propuestas", agente="proponer_cambio_cotizacion",
                       json={"cotizacion": "COT-DEMO-001", "cambios": [{"producto": "el autorradio de siete", "cantidad": 7}]})
    assert r.status_code == 200, r.text
    assert r.json()["cambios"][0]["sku"] == "RAD-7BT"


def test_alias_no_se_aprende_de_lo_mismo_que_el_sku(entorno):
    motor = entorno.app.state.aprendizaje
    motor.confirmar_alias([("rad-7bt", "RAD-7BT"), ("", "RAD-7BT")])
    assert motor.alias("rad-7bt") is None


def test_precedentes_filtran_por_descuento_y_nivel(entorno):
    motor = entorno.app.state.aprendizaje
    filas = [("E1", 10.0, "mayorista", "APROBADA"), ("E2", 9.0, "mayorista", "APROBADA"), ("E3", 11.0, "mayorista", "RECHAZADA"),
             ("E4", 10.0, "nuevo", "RECHAZADA"), ("E5", 20.0, "mayorista", "RECHAZADA")]
    with entorno.repo.conexion() as db:
        for eid, d, nivel, dec in filas:
            db.execute("INSERT INTO conocimiento_casos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (eid, "DESCUENTO", "COT-X", 1, "CLI-X", nivel, d, "100.00", "Audio", dec, "motivo", "2026-11-20", "2026-11-20"))
    r = motor.precedentes("DESCUENTO", descuento=10, nivel="mayorista")
    assert r["casos_parecidos"] == 3 and r["decisiones"] == {"APROBADA": 2, "RECHAZADA": 1}
    assert r["tasa_aprobacion_pct"] == 66.7 and r["descuento_promedio_aprobado"] == 9.5
    assert "no autorizan" in r["nota"]
    # Sin casos suficientes del nivel, amplía a todos los niveles y lo dice.
    r2 = motor.precedentes("DESCUENTO", descuento=10, nivel="frecuente")
    assert r2["casos_parecidos"] == 4 and "se amplió" in r2["criterio"]


def test_endpoints_de_aprendizaje(entorno):
    assert entorno.llamar("GET", "/aprendizaje/resumen").status_code == 200
    r = entorno.llamar("GET", "/aprendizaje/precedentes?tipo=DESCUENTO&descuento=10")
    assert r.status_code == 200 and "casos_parecidos" in r.json()
