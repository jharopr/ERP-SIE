"""Configuración de la compuerta, tomada solo de variables de entorno."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os

# Perú no aplica horario de verano desde 1994: UTC-5 fijo, sin depender de tzdata.
LIMA = timezone(timedelta(hours=-5), "America/Lima")


def ahora_lima() -> datetime:
    return datetime.now(LIMA).replace(microsecond=0)


@dataclass(frozen=True)
class Config:
    odoo_url: str
    odoo_db: str
    odoo_user: str
    odoo_password: str
    odoo_timeout: float
    token_ventas: str
    token_gerencia: str
    token_admin: str
    database: str
    company_id: str
    ubicacion_id: str
    hora_cierre_cotizacion: str
    aprobacion_vigencia_horas: int
    prefijo_rep: str
    token_odoo: str = ""
    token_agente: str = ""
    bridge_secret: str = ""

    @classmethod
    def desde_entorno(cls) -> "Config":
        env = os.environ.get
        return cls(
            odoo_url=env("ODOO_URL", "http://odoo:8069"),
            odoo_db=env("ODOO_DB", "mys_demo"),
            odoo_user=env("ODOO_READER_USER", env("ODOO_USER", "admin")),
            odoo_password=env("ODOO_READER_PASSWORD", env("ODOO_PASSWORD", "")),
            odoo_timeout=float(env("ODOO_TIMEOUT", "5")),
            token_ventas=env("TOKEN_VENTAS", ""),
            token_gerencia=env("TOKEN_GERENCIA", ""),
            token_admin=env("TOKEN_ADMIN", ""),
            database=env("COMPUERTA_DB", "/data/compuerta.sqlite3"),
            company_id=env("COMPANY_ID", "MYS-DEMO"),
            ubicacion_id=env("UBICACION_ID", "TIENDA-DEMO"),
            hora_cierre_cotizacion=env("COTIZACION_HORA_CIERRE", "18:00"),
            aprobacion_vigencia_horas=int(env("APROBACION_VIGENCIA_HORAS", "24")),
            prefijo_rep=env("PREFIJO_REP", "REP-PC3"),
            token_odoo=env("TOKEN_ODOO", ""),
            token_agente=env("TOKEN_AGENTE", ""),
            bridge_secret=env("ODOO_BRIDGE_SECRET", ""),
        )
