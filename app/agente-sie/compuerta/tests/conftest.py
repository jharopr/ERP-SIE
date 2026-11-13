"""Odoo simulado (en memoria) con el escenario PC3 y fábrica de la app de prueba."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PAQUETE = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from app import escenario as E  # noqa: E402
from app.config import LIMA, Config  # noqa: E402
from app.main import crear_app  # noqa: E402
from app.odoo_cliente import DependenciaNoDisponible  # noqa: E402
from app.repositorio import Repositorio  # noqa: E402

UBICACION_ODOO = 8
HORA = datetime(2026, 11, 13, 10, 0, tzinfo=LIMA)
TOKENS = {"VENTAS": "tok-ventas-prueba", "GERENCIA": "tok-gerencia-prueba", "ADMIN": "tok-admin-prueba"}


class OdooSimulado:
    """Implementa la misma interfaz de lectura que OdooCliente."""

    def __init__(self, fecha_vigencia="2026-11-13"):
        self.caido = False
        self.fecha_vigencia = fecha_vigencia
        self.cotizaciones = [dict(c) for c in E.COTIZACIONES]
        self.fisico = {sku: float(p["fisico"]) for sku, p in E.PRODUCTOS.items()}
        self.reservado = {sku: 0.0 for sku in E.PRODUCTOS}
        for r in E.RESERVAS:
            self.reservado[r["sku"]] += r["cantidad"]

    def _ok(self):
        if self.caido:
            raise DependenciaNoDisponible("ConnectionRefusedError")

    def ping(self):
        self._ok()
        return {"server_version": "18.0-simulado"}

    def cliente(self, ref):
        self._ok()
        return {"ref": ref, "active": True} if ref in E.CLIENTES else None

    def oportunidad(self, opp_id):
        self._ok()
        o = E.OPORTUNIDADES.get(opp_id)
        return {"opportunity_id": opp_id, "type": "opportunity", "active": True, "customer_ref": o["cliente"]} if o else None

    def versiones_cotizacion(self, quotation_id):
        self._ok()
        return [{"version": c["version"], "state": c["estado"], "currency": "PEN", "validity_date": self.fecha_vigencia,
                 "seller_login": E.VENDEDOR_LOGIN, "customer_ref": c["cliente"], "opportunity_id": c["oportunidad"],
                 "amount_total": E.total_cotizacion(c),
                 "lines": [{"sku": l["sku"], "quantity": float(l["cantidad"]), "unit_price": E.PRODUCTOS[l["sku"]]["precio"],
                            "discount_pct": l["descuento"]} for l in c["lineas"]]}
                for c in self.cotizaciones if c["id"] == quotation_id]

    def productos(self, skus):
        self._ok()
        return {s: {"active": True, "list_price": E.PRODUCTOS[s]["precio"], "currency": "PEN"} for s in skus if s in E.PRODUCTOS}

    def stock(self, skus, ubicacion_odoo_id):
        self._ok()
        assert ubicacion_odoo_id == UBICACION_ODOO
        return {s: {"fisico": self.fisico.get(s, 0.0), "reservado": self.reservado.get(s, 0.0)} for s in skus}


class Reloj:
    def __init__(self, hora=HORA):
        self.hora = hora

    def __call__(self):
        return self.hora


@pytest.fixture
def entorno(tmp_path):
    from fastapi.testclient import TestClient

    config = Config(odoo_url="http://simulado", odoo_db="mys_demo", odoo_user="admin", odoo_password="x",
                    odoo_timeout=5, token_ventas=TOKENS["VENTAS"], token_gerencia=TOKENS["GERENCIA"],
                    token_admin=TOKENS["ADMIN"], database=str(tmp_path / "compuerta.sqlite3"), company_id=E.COMPANY_ID,
                    ubicacion_id=E.UBICACION_ID, hora_cierre_cotizacion="18:00", aprobacion_vigencia_horas=24,
                    prefijo_rep="REP-PC3")
    odoo, reloj = OdooSimulado(), Reloj()
    app = crear_app(config, odoo, reloj)
    E.registrar_maestros_locales(Repositorio(config.database), reloj(), UBICACION_ODOO)
    cliente = TestClient(app)

    def llamar(metodo, ruta, rol="VENTAS", agente=False, **kw):
        cabeceras = {"Authorization": f"Bearer {TOKENS[rol]}", **kw.pop("headers", {})}
        if agente:
            cabeceras.update({"X-Actor-Type": "AGENTE", "X-Agent-Tool": agente, "X-Agent-Version": "w1-1.0",
                              "X-Prompt-Version": "p-1.0"})
        return cliente.request(metodo, ruta, headers=cabeceras, **kw)

    class Entorno:
        pass

    ent = Entorno()
    ent.cliente, ent.llamar, ent.odoo, ent.reloj, ent.config, ent.app = cliente, llamar, odoo, reloj, config, app
    ent.repo = app.state.repo
    return ent


@pytest.fixture(scope="session")
def casos():
    datos = json.loads((PAQUETE / "datos_prueba" / "casos_pc3.json").read_text(encoding="utf-8"))
    return {c["id"]: c for c in datos["casos"]}
