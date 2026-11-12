"""Tokens por rol. El rol y la identidad salen del token, nunca del cuerpo."""

from __future__ import annotations

from dataclasses import dataclass
import hmac
import base64
import hashlib
import json
import time

from .config import Config

# Identidad fija asociada a cada token en el escenario sintético.
ACTOR_POR_ROL = {"VENTAS": "VEN-DEMO-01", "GERENCIA": "GER-DEMO-01", "ADMIN": "ADM-DEMO-01"}
TIPOS_ACTOR = {"HUMANO", "AGENTE"}


@dataclass(frozen=True)
class Identidad:
    rol: str
    actor_id: str
    actor_type: str  # HUMANO | AGENTE (la compuerta registra SISTEMA para sus propias consultas)
    odoo_uid: int | None = None


def identificar(config: Config, authorization: str | None, tipo_declarado: str | None,
                contexto: str | None = None) -> Identidad | None:
    """Devuelve la identidad del token o None. Tokens vacíos nunca autentican."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[len("Bearer "):].strip()
    for esperado, tipo in ((config.token_odoo, "HUMANO"), (config.token_agente, "AGENTE")):
        if esperado and hmac.compare_digest(token.encode(), esperado.encode()):
            try:
                contenido, firma = contexto.split(".")
                calculada = hmac.new(config.bridge_secret.encode(), contenido.encode(), hashlib.sha256).hexdigest()
                if not config.bridge_secret or not hmac.compare_digest(firma, calculada):
                    return None
                datos = json.loads(base64.urlsafe_b64decode(contenido + "=" * (-len(contenido) % 4)))
                if (datos['exp'] < time.time() or datos['exp'] > time.time() + 900
                        or datos['company_id'] != config.company_id
                        or datos['rol'] not in ('VENTAS', 'GERENCIA') or not isinstance(datos['uid'], int)
                        or not datos['actor_id'].startswith(('VEN-', 'GER-'))):
                    return None
                return Identidad(datos['rol'], datos['actor_id'], tipo, datos['uid'])
            except (ValueError, KeyError, TypeError, AttributeError):
                return None
    candidatos = {"VENTAS": config.token_ventas, "GERENCIA": config.token_gerencia, "ADMIN": config.token_admin}
    for rol, esperado in candidatos.items():
        if esperado and hmac.compare_digest(token.encode(), esperado.encode()):
            # X-Actor-Type solo etiqueta la bitácora; no otorga permisos.
            tipo = (tipo_declarado or "HUMANO").upper()
            if rol != "VENTAS" or tipo not in TIPOS_ACTOR:
                tipo = "HUMANO"
            return Identidad(rol, ACTOR_POR_ROL[rol], tipo)
    return None
