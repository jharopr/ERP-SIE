"""Escenario sintético PC3 (fuente única para el seed de Odoo y las pruebas).

NO son datos reales de Importaciones MYS Hermanos. Moneda PEN, precio final
académico sin desglose de IGV. Disponible = físico − reservado.
"""

from __future__ import annotations

COMPANY_ID = "MYS-DEMO"
UBICACION_ID = "TIENDA-DEMO"
VENDEDOR = "VEN-DEMO-01"
VENDEDOR_LOGIN = "ven-demo-01"
DUENO = "GER-DEMO-01"
ADMIN = "ADM-DEMO-01"
TOPE_DESCUENTO_VENDEDOR = "5.00"

PRODUCTOS = {
    "RAD-7BT": {"nombre": 'Autoradio Bluetooth 7" (genérico)', "precio": 400.0, "fisico": 10},
    "RAD-10X": {"nombre": 'Autoradio pantalla 10" (genérico)', "precio": 520.0, "fisico": 10},
}

CLIENTES = {
    "CLI-DEMO-001": {"nombre": "Cliente Demo 001 (sintético)", "segmento": "CONSUMIDOR_FINAL", "identidad_revisada": True},
    "CLI-DEMO-002": {"nombre": "Cliente Demo 002 (sintético)", "segmento": "RECURRENTE", "identidad_revisada": True},
}

# Pedidos confirmados de OTRO cliente: generan la reserva (2 y 7 unidades).
RESERVAS = [
    {"ref": "RES-DEMO-001", "cliente": "CLI-DEMO-002", "sku": "RAD-7BT", "cantidad": 2},
    {"ref": "RES-DEMO-002", "cliente": "CLI-DEMO-002", "sku": "RAD-10X", "cantidad": 7},
]

OPORTUNIDADES = {
    "OPP-DEMO-001": {"cliente": "CLI-DEMO-001"},
    "OPP-DEMO-002": {"cliente": "CLI-DEMO-001"},
}

# Cada versión es un sale.order distinto con client_order_ref "<id> v<n>".
# COT-DEMO-004: v1 (5 %) anulada; v2 (10 %) vigente → caso PC3-E02.
COTIZACIONES = [
    {"id": "COT-DEMO-001", "version": 1, "oportunidad": "OPP-DEMO-001", "cliente": "CLI-DEMO-001",
     "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 5.0}], "estado": "sent"},
    {"id": "COT-DEMO-002", "version": 1, "oportunidad": "OPP-DEMO-002", "cliente": "CLI-DEMO-001",
     "lineas": [{"sku": "RAD-10X", "cantidad": 5, "descuento": 5.0}], "estado": "sent"},
    {"id": "COT-DEMO-003", "version": 1, "oportunidad": "OPP-DEMO-001", "cliente": "CLI-DEMO-001",
     "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 5.0}], "estado": "sent"},
    {"id": "COT-DEMO-004", "version": 1, "oportunidad": "OPP-DEMO-001", "cliente": "CLI-DEMO-001",
     "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 5.0}], "estado": "cancel"},
    {"id": "COT-DEMO-004", "version": 2, "oportunidad": "OPP-DEMO-001", "cliente": "CLI-DEMO-001",
     "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 10.0}], "estado": "sent"},
]

# Aceptación del cliente ligada a la versión exacta (registrada con hora = ahora − 5 min).
ACEPTACIONES = {
    "ACE-PC3-001": {"cotizacion": "COT-DEMO-001", "version": 1},
    "ACE-PC3-002": {"cotizacion": "COT-DEMO-002", "version": 1},
    "ACE-PC3-003": {"cotizacion": "COT-DEMO-004", "version": 2},
    "ACE-PC3-004": {"cotizacion": "COT-DEMO-003", "version": 1},
}

ACTORES = {
    VENDEDOR: {"rol": "VENTAS", "oportunidades": ["OPP-DEMO-001", "OPP-DEMO-002"]},
    DUENO: {"rol": "GERENCIA", "oportunidades": []},
    ADMIN: {"rol": "ADMIN", "oportunidades": []},
}


def total_linea(sku: str, cantidad: int, descuento: float) -> float:
    return round(PRODUCTOS[sku]["precio"] * cantidad * (1 - descuento / 100), 2)


def total_cotizacion(cot: dict) -> float:
    return round(sum(total_linea(l["sku"], l["cantidad"], l["descuento"]) for l in cot["lineas"]), 2)


def registrar_maestros_locales(repo, ahora, ubicacion_odoo_id) -> None:
    """Actores, política, clientes, mapa de IDs y aceptaciones en la base de la compuerta (idempotente)."""
    from datetime import timedelta
    import json

    aceptado = (ahora - timedelta(minutes=5)).isoformat()
    with repo.conexion() as db:
        for actor_id, a in ACTORES.items():
            db.execute("INSERT INTO actores(actor_id,rol,company_id,opportunities_json) VALUES(?,?,?,?)"
                       " ON CONFLICT(actor_id) DO UPDATE SET rol=excluded.rol, company_id=excluded.company_id,"
                       " opportunities_json=excluded.opportunities_json",
                       (actor_id, a["rol"], COMPANY_ID, json.dumps(a["oportunidades"])))
        db.execute("INSERT INTO politica(clave,valor) VALUES('max_seller_discount',?)"
                   " ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", (TOPE_DESCUENTO_VENDEDOR,))
        for ref, c in CLIENTES.items():
            db.execute("INSERT INTO clientes_ext(ref,identity_reviewed,segmento) VALUES(?,?,?)"
                       " ON CONFLICT(ref) DO UPDATE SET identity_reviewed=excluded.identity_reviewed,"
                       " segmento=excluded.segmento", (ref, int(c["identidad_revisada"]), c["segmento"]))
        for tipo, externo, odoo in (("usuario", VENDEDOR, VENDEDOR_LOGIN), ("ubicacion", UBICACION_ID, str(ubicacion_odoo_id))):
            db.execute("INSERT INTO mapa_ids(tipo,externo,odoo) VALUES(?,?,?)"
                       " ON CONFLICT(tipo,externo) DO UPDATE SET odoo=excluded.odoo", (tipo, externo, odoo))
        cotizaciones = {(c["id"], c["version"]): c for c in COTIZACIONES}
        for ace_id, a in ACEPTACIONES.items():
            cot = cotizaciones[(a["cotizacion"], a["version"])]
            db.execute("INSERT INTO aceptaciones VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(acceptance_id) DO UPDATE SET"
                       " quotation_id=excluded.quotation_id, quotation_version=excluded.quotation_version,"
                       " customer_id=excluded.customer_id, total=excluded.total, accepted_at=excluded.accepted_at",
                       (ace_id, COMPANY_ID, a["cotizacion"], a["version"], cot["cliente"],
                        f"{total_cotizacion(cot):.2f}", aceptado, "SEED"))
