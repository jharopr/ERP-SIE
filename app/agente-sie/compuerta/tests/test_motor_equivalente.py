"""La envoltura no cambia ninguna decisión del motor probado en PC2.

Nota: los casos EP-N01/S01/E01 mencionados en las instrucciones no están en el
repositorio; se usan los cuatro casos PC2 que sí existen (N01, E01, P01, T01).
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from app.motor import Compuerta
from app.motor_base.simulador import TransitionSimulator

FIX = Path(__file__).parent / "fixtures_pc2"
ORIGINAL = Path(__file__).resolve().parents[4] / "pruebas" / "pc2" / "simulador.py"
COPIA = Path(__file__).resolve().parents[1] / "app" / "motor_base" / "simulador.py"


def cargar(nombre):
    return json.loads((FIX / nombre).read_text(encoding="utf-8"))


CASOS = [
    ("PC2-N01", "solicitud-normal.json", None, "ACEPTADA", "VALIDADA"),
    ("PC2-E01", "solicitud-excepcion.json", None, "RECHAZADA", "DESCUENTO_SIN_APROBACION"),
    ("PC2-P01", "solicitud-normal.json", "parcial", "PROMESA_CONDICIONADA", "DISPONIBILIDAD_PARCIAL"),
    ("PC2-T01", "solicitud-normal.json", "caido", "PENDIENTE", "DEPENDENCIA_NO_DISPONIBLE"),
]


def masters_para(variante):
    m = cargar("maestros.json")
    if variante == "parcial":
        m["availability"]["quantities"]["AUT-DEMO-001"] = 3
    if variante == "caido":
        m["availability"]["available"] = False
    return m


@pytest.mark.skipif(not ORIGINAL.exists(), reason="Fuera del repositorio ERP-SIE no hay original para comparar")
def test_motor_es_copia_exacta():
    assert hashlib.sha256(COPIA.read_bytes()).hexdigest() == hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()


@pytest.mark.parametrize("caso,archivo,variante,status,code", CASOS)
def test_misma_respuesta_y_bitacora_que_el_original(tmp_path, caso, archivo, variante, status, code):
    solicitud = cargar(archivo)
    original = TransitionSimulator(masters_para(variante))
    envuelto = Compuerta(masters_para(variante), str(tmp_path / "c.sqlite3"))
    try:
        r1, r2 = original.submit(deepcopy(solicitud)), envuelto.submit(deepcopy(solicitud))
        assert r1 == r2
        assert (r2["status"], r2["code"], r2["order_id"]) == (status, code, None)
        columnas = "request_id,correlation_id,actor_id,interface_id,event_type,code"
        a1 = [tuple(f) for f in original.db.execute(f"SELECT {columnas} FROM audit ORDER BY event_id")]
        a2 = [tuple(f) for f in envuelto.db.execute(f"SELECT {columnas} FROM audit WHERE interface_id != 'REP' ORDER BY event_id")]
        assert a1 == a2
        # reintento idéntico: misma respuesta en ambos
        assert original.submit(deepcopy(solicitud)) == envuelto.submit(deepcopy(solicitud))
    finally:
        original.close()
        envuelto.close()


def test_promesa_condicionada_crea_rep_en_la_misma_transaccion(tmp_path):
    db = str(tmp_path / "c.sqlite3")
    motor = Compuerta(masters_para("parcial"), db)
    try:
        r = motor.submit(cargar("solicitud-normal.json"))
    finally:
        motor.close()
    con = sqlite3.connect(db)
    fila = con.execute("SELECT signal_id, sku, requested, available, faltante, automatic_action FROM senales_rep").fetchone()
    con.close()
    assert r["status"] == "PROMESA_CONDICIONADA"
    assert fila == ("REP-PC3-001", "AUT-DEMO-001", 5, 3, 2, 0)


def test_actor_type_por_evento(tmp_path):
    db = str(tmp_path / "c.sqlite3")
    motor = Compuerta(masters_para(None), db, actor_type="AGENTE")
    try:
        motor.submit(cargar("solicitud-normal.json"))
        tipos = [tuple(f) for f in motor.db.execute("SELECT a.event_type, e.actor_type FROM audit a"
                                                    " JOIN audit_ext e USING(event_id) ORDER BY a.event_id")]
    finally:
        motor.close()
    assert tipos[0] == ("RECIBIDA", "AGENTE")
    assert all(t == "SISTEMA" for ev, t in tipos if ev in ("CONSULTA", "DECISION"))
