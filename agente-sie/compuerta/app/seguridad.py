"""Tokens por rol. El rol y la identidad salen del token, nunca del cuerpo."""

from __future__ import annotations

from dataclasses import dataclass
import hmac

from .config import Config

# Identidad fija asociada a cada token en el escenario sintético.
ACTOR_POR_ROL = {"VENTAS": "VEN-DEMO-01", "GERENCIA": "GER-DEMO-01", "ADMIN": "ADM-DEMO-01"}
TIPOS_ACTOR = {"HUMANO", "AGENTE"}


@dataclass(frozen=True)
class Identidad:
    rol: str
    actor_id: str
    actor_type: str  # HUMANO | AGENTE (la compuerta registra SISTEMA para sus propias consultas)


def identificar(config: Config, authorization: str | None, tipo_declarado: str | None) -> Identidad | None:
    """Devuelve la identidad del token o None. Tokens vacíos nunca autentican."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[len("Bearer "):].strip()
    candidatos = {"VENTAS": config.token_ventas, "GERENCIA": config.token_gerencia, "ADMIN": config.token_admin}
    for rol, esperado in candidatos.items():
        if esperado and hmac.compare_digest(token.encode(), esperado.encode()):
            # X-Actor-Type solo etiqueta la bitácora; no otorga permisos.
            tipo = (tipo_declarado or "HUMANO").upper()
            if rol != "VENTAS" or tipo not in TIPOS_ACTOR:
                tipo = "HUMANO"
            return Identidad(rol, ACTOR_POR_ROL[rol], tipo)
    return None
