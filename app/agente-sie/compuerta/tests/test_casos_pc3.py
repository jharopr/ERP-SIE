"""Seis casos PC3 contra la compuerta con Odoo simulado, más permisos y bitácora."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA = Path(__file__).resolve().parents[1] / "app" / "contrato" / "respuesta-pedido-v1.schema.json"


def validar_schema(respuesta):
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(respuesta, json.loads(SCHEMA.read_text(encoding="utf-8")))


def enviar(ent, solicitud, agente=False):
    r = ent.llamar("POST", "/solicitudes", agente="enviar_solicitud_i03" if agente else False, json=solicitud)
    assert r.status_code == 200, r.text
    return r.json()


def comparar(respuesta, esperado):
    for campo in ("status", "code", "responsible_role", "total", "order_id", "conditions"):
        if campo in esperado:
            assert respuesta[campo] == esperado[campo], campo


def test_pc3_n01_normal(entorno, casos):
    caso = casos["PC3-N01"]
    antes = dict(entorno.odoo.reservado)
    datos = enviar(entorno, caso["solicitud"], agente=True)
    comparar(datos["respuesta"], caso["esperado"])
    validar_schema(datos["respuesta"])
    assert datos["senales_reposicion"] == []
    assert entorno.odoo.reservado == antes  # stock intacto: no se reserva nada


def test_pc3_e01_faltante_crea_rep_y_dueno_decide(entorno, casos):
    caso = casos["PC3-E01"]
    datos = enviar(entorno, caso["solicitud"])
    comparar(datos["respuesta"], caso["esperado"])
    validar_schema(datos["respuesta"])
    senal = datos["senales_reposicion"][0]
    for k, v in caso["esperado"]["senal"].items():
        assert senal[k] == v
    # VENTAS no puede decidir la reposición
    assert entorno.llamar("POST", "/decisiones-reposicion", json=caso["decision_dueno"]).status_code == 403
    r = entorno.llamar("POST", "/decisiones-reposicion", rol="GERENCIA", json=caso["decision_dueno"])
    assert r.status_code == 200 and r.json()["decidido_por"] == "GER-DEMO-01"
    eventos = entorno.llamar("GET", "/bitacora", params={"correlation_id": "COR-PC3-002"}).json()["eventos"]
    secuencia = [e["event_type"] for e in eventos]
    assert secuencia == ["RECIBIDA", "CONSULTA", "CONSULTA", "CONSULTA", "SENAL_REP", "DECISION", "DECISION_DUENO"]
    assert eventos[-1]["actor_type"] == "HUMANO" and eventos[-1]["actor_id"] == "GER-DEMO-01"


def test_pc3_e02_descuento_sin_aprobacion_y_flujo_v3(entorno, casos):
    caso = casos["PC3-E02"]
    datos = enviar(entorno, caso["solicitud"])
    comparar(datos["respuesta"], caso["esperado"])
    eventos = entorno.llamar("GET", "/bitacora", params={"request_id": "SOL-PC3-E02"}).json()["eventos"]
    assert not any(e["interface_id"] == "I05" for e in eventos)  # sin consulta de stock
    # El dueño aprueba para la v3 (nueva versión). La v2 sigue rechazada.
    r = entorno.llamar("POST", "/aprobaciones", rol="GERENCIA", json={
        "quotation_id": "COT-DEMO-004", "version": 3, "total": "1800.00", "decision": "APROBADA",
        "motivo": "Cliente recurrente; volumen justifica 10 %", "correlation_id": "COR-PC3-001"})
    assert r.status_code == 200 and r.json()["approver_id"] == "GER-DEMO-01"
    entorno.odoo.cotizaciones.append({"id": "COT-DEMO-004", "version": 3, "oportunidad": "OPP-DEMO-001",
                                      "cliente": "CLI-DEMO-001", "estado": "sent",
                                      "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 10.0}]})
    a = entorno.llamar("POST", "/aceptaciones", json={"acceptance_id": "ACE-PC3-005", "quotation_id": "COT-DEMO-004", "version": 3})
    assert a.status_code == 200 and a.json()["total"] == "1800.00"
    v3 = enviar(entorno, {**caso["solicitud"], "request_id": "SOL-PC3-E02-V3", "quotation_version": 3,
                          "acceptance_id": "ACE-PC3-005"})["respuesta"]
    assert (v3["status"], v3["code"], v3["total"], v3["order_id"]) == ("ACEPTADA", "VALIDADA", "1800.00", None)
    # La aprobación de la v3 no rescata la v2 (ya obsoleta)
    assert entorno.llamar("GET", "/solicitudes/SOL-PC3-E02").json()["respuesta"]["code"] == "DESCUENTO_SIN_APROBACION"


@pytest.mark.parametrize("modo", ["odoo_caido", "bandera_admin"])
def test_pc3_f01_dependencia_caida_y_reanudar(entorno, casos, modo):
    caso = casos["PC3-F01"]
    if modo == "odoo_caido":
        entorno.odoo.caido = True
    else:
        assert entorno.llamar("POST", "/admin/simulacion", rol="ADMIN", json={"odoo_caido": True}).status_code == 200
    datos = enviar(entorno, caso["solicitud"])
    comparar(datos["respuesta"], caso["esperado"])
    validar_schema(datos["respuesta"])
    assert entorno.llamar("GET", "/disponibilidad/RAD-7BT").status_code == 503
    # Reintento mientras sigue caído: misma respuesta PENDIENTE, sin duplicar
    assert enviar(entorno, caso["solicitud"])["respuesta"] == datos["respuesta"]
    entorno.odoo.caido = False
    entorno.llamar("POST", "/admin/simulacion", rol="ADMIN", json={"odoo_caido": False})
    r = entorno.llamar("POST", "/solicitudes/SOL-PC3-F01/reanudar")
    assert r.status_code == 200, r.text
    comparar(r.json()["respuesta"], caso["esperado_tras_reanudar"])
    # Una solicitud ya resuelta no se reanuda
    assert entorno.llamar("POST", "/solicitudes/SOL-PC3-F01/reanudar").status_code == 409


def test_pc3_i01_reintento_identico(entorno, casos):
    caso = casos["PC3-N01"]
    primera = enviar(entorno, caso["solicitud"])
    segunda = enviar(entorno, caso["solicitud"])
    assert primera == segunda
    with entorno.repo.conexion() as db:
        assert db.execute("SELECT COUNT(*) FROM requests WHERE request_id='SOL-PC3-N01'").fetchone()[0] == 1
    eventos = entorno.llamar("GET", "/bitacora", params={"request_id": "SOL-PC3-N01"}).json()["eventos"]
    assert eventos[-1]["event_type"] == "REINTENTO"
    # Misma clave con otro payload: conflicto, no sobrescribe
    otro = {**caso["solicitud"], "acceptance_id": "ACE-PC3-004"}
    assert enviar(entorno, otro)["respuesta"]["code"] == "IDEMPOTENCIA_CONFLICTO"


def test_pc3_a01_ventas_no_puede_aprobar(entorno, casos):
    caso = casos["PC3-A01"]
    enviar(entorno, casos["PC3-E02"]["solicitud"])
    r = entorno.llamar("POST", "/aprobaciones", agente="escalar_al_dueno", json=caso["intento_con_token_ventas"],
                       headers={"X-Correlation-Id": "COR-PC3-001"})
    assert r.status_code == caso["esperado"]["http_aprobacion_con_token_ventas"]
    eventos = entorno.llamar("GET", "/bitacora", params={"correlation_id": "COR-PC3-001"}).json()["eventos"]
    assert eventos[-1]["event_type"] == "DENEGADA" and eventos[-1]["actor_type"] == "AGENTE"
    with entorno.repo.conexion() as db:
        assert db.execute("SELECT COUNT(*) FROM aprobaciones").fetchone()[0] == 0
    # Reenviar E02 sigue rechazada (reintento): nada cambió
    assert enviar(entorno, casos["PC3-E02"]["solicitud"])["respuesta"]["code"] == caso["esperado"]["estado_E02"]


def test_payload_no_puede_traer_rol_ni_precios(entorno, casos):
    solicitud = {**casos["PC3-N01"]["solicitud"], "role": "GERENCIA", "total": "1.00"}
    assert enviar(entorno, solicitud)["respuesta"]["code"] == "CONTRATO_INVALIDO"


def test_tokens(entorno):
    assert entorno.cliente.get("/clientes/CLI-DEMO-001").status_code == 401
    assert entorno.cliente.get("/clientes/CLI-DEMO-001", headers={"Authorization": "Bearer otro"}).status_code == 401
    r = entorno.llamar("GET", "/clientes/CLI-DEMO-001")
    assert r.json() == {"customer_id": "CLI-DEMO-001", "activo": True, "identidad_revisada": True, "segmento": "CONSUMIDOR_FINAL"}
    assert entorno.llamar("POST", "/admin/reiniciar").status_code == 403


def test_consultas_de_lectura(entorno):
    d = entorno.llamar("GET", "/disponibilidad/RAD-10X").json()
    assert (d["fisico"], d["reservado"], d["disponible"]) == (10, 7, 3)
    c = entorno.llamar("GET", "/cotizaciones/COT-DEMO-004/1").json()
    assert (c["estado"], c["version_vigente"], c["total"]) == ("cancel", 2, "1900.00")
    assert entorno.llamar("GET", "/salud").json()["odoo"]["disponible"] is True


def test_cotizacion_vencida_tras_hora_de_cierre(entorno, casos):
    from datetime import datetime
    from app.config import LIMA
    entorno.reloj.hora = datetime(2026, 11, 13, 18, 30, tzinfo=LIMA)
    assert enviar(entorno, casos["PC3-N01"]["solicitud"])["respuesta"]["code"] == "COTIZACION_VENCIDA"


def test_huella_del_agente_sin_texto(entorno, casos):
    enviar(entorno, casos["PC3-N01"]["solicitud"], agente=True)
    eventos = entorno.llamar("GET", "/bitacora", params={"correlation_id": "COR-PC3-001"}).json()["eventos"]
    huella = [e for e in eventos if e["event_type"] == "HERRAMIENTA_AGENTE"]
    assert huella and huella[0]["code"] == "enviar_solicitud_i03" and len(huella[0]["detalle"]["input_hash"]) == 64
    texto = json.dumps(eventos, ensure_ascii=False)
    assert "Cliente Demo" not in texto  # nunca nombres en la bitácora


def test_escalamiento_reposicion_y_descuento(entorno, casos):
    enviar(entorno, casos["PC3-E01"]["solicitud"])
    enviar(entorno, casos["PC3-E02"]["solicitud"])
    rep = entorno.llamar("POST", "/escalamientos", agente="escalar_al_dueno",
                         json={"tipo": "REPOSICION", "request_id": "SOL-PC3-E01", "resumen": "Faltan 2 RAD-10X"}).json()
    assert (rep["escalation_id"], rep["signal_id"], rep["destinatario"]) == ("ESC-PC3-001", "REP-PC3-001", "DUENO_Y_ABASTECIMIENTO")
    # idempotente: escalar de nuevo devuelve el mismo
    assert entorno.llamar("POST", "/escalamientos", json={"tipo": "REPOSICION", "request_id": "SOL-PC3-E01",
                                                          "resumen": "otra vez"}).json()["escalation_id"] == "ESC-PC3-001"
    desc = entorno.llamar("POST", "/escalamientos", json={"tipo": "DESCUENTO", "request_id": "SOL-PC3-E02",
                                                          "resumen": "Cliente pide 10 %"}).json()
    assert (desc["version_aprobacion"], desc["total"], desc["destinatario"]) == (3, "1800.00", "DUENO")
    # tipo que no corresponde al código
    assert entorno.llamar("POST", "/escalamientos", json={"tipo": "DESCUENTO", "request_id": "SOL-PC3-E01",
                                                          "resumen": "x" * 5}).status_code == 409
    entorno.llamar("POST", "/decisiones-reposicion", rol="GERENCIA", json=casos["PC3-E01"]["decision_dueno"])
    entorno.llamar("POST", "/aprobaciones", rol="GERENCIA", json={"quotation_id": "COT-DEMO-004", "version": 3,
                   "total": "1800.00", "decision": "RECHAZADA", "motivo": "Margen insuficiente"})
    assert entorno.llamar("GET", "/escalamientos/ESC-PC3-001").json()["decision"] == "OFRECER_PARCIAL"
    assert entorno.llamar("GET", "/escalamientos/ESC-PC3-002").json()["estado"] == "DECIDIDO"


def test_escalamiento_sin_decision_en_10_minutos(entorno, casos):
    from datetime import timedelta
    enviar(entorno, casos["PC3-E01"]["solicitud"])
    entorno.llamar("POST", "/escalamientos", json={"tipo": "REPOSICION", "request_id": "SOL-PC3-E01", "resumen": "Faltan 2"})
    entorno.reloj.hora += timedelta(minutes=11)
    r = entorno.llamar("GET", "/escalamientos/ESC-PC3-001").json()
    assert r["estado"] == "SIN_DECISION" and "seguimiento" in r["mensaje"]


def test_decision_por_escalamiento_desde_formulario(entorno, casos):
    enviar(entorno, casos["PC3-E02"]["solicitud"])
    entorno.llamar("POST", "/escalamientos", json={"tipo": "DESCUENTO", "request_id": "SOL-PC3-E02", "resumen": "Pide 10 %"})
    cuerpo = {"decision": "APROBADA", "motivo": "Volumen justifica"}
    assert entorno.llamar("POST", "/escalamientos/ESC-PC3-001/decision", json=cuerpo).status_code == 403  # VENTAS no
    assert entorno.llamar("POST", "/escalamientos/ESC-PC3-001/decision", rol="GERENCIA",
                          json={"decision": "OFRECER_PARCIAL", "motivo": "no aplica"}).status_code == 422
    r = entorno.llamar("POST", "/escalamientos/ESC-PC3-001/decision", rol="GERENCIA", json=cuerpo).json()
    assert (r["resultado"]["version"], r["resultado"]["total"], r["resultado"]["approver_id"]) == (3, "1800.00", "GER-DEMO-01")
    assert entorno.llamar("POST", "/escalamientos/ESC-PC3-001/decision", rol="GERENCIA", json=cuerpo).status_code == 409
