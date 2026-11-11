"""Arma el dict `masters` con la misma forma que `pruebas/pc2/fixtures/maestros.json`.

Datos comerciales, catálogo y stock vienen de Odoo (solo lectura). Actores,
política, aceptaciones, aprobaciones e identidad revisada vienen de la base local.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from .config import Config
from .odoo_cliente import DependenciaNoDisponible
from .repositorio import Repositorio

LLAVES = ("company_id", "customer_id", "opportunity_id", "quotation_id")


def dinero(valor) -> str:
    return format(Decimal(str(valor)).quantize(Decimal("0.01")), "f")


def entero_si_exacto(valor):
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor


def vigencia(fecha: str | None, config: Config) -> str:
    # Sin fecha de vigencia la cotización se trata como vencida (nunca como vigente).
    if not fecha:
        return "1970-01-01T00:00:00-05:00"
    return f"{fecha}T{config.hora_cierre_cotizacion}:00-05:00"


def version_vigente(versiones: list[dict]) -> dict | None:
    """La vigente es la mayor versión no anulada. Las anteriores quedan obsoletas."""
    activas = [v for v in versiones if v["state"] != "cancel"]
    return max(activas, key=lambda v: v["version"]) if activas else None


def cotizacion_normalizada(v: dict, config: Config, repo: Repositorio) -> dict:
    return {
        "company_id": config.company_id,
        "opportunity_id": v["opportunity_id"],
        "customer_id": v["customer_ref"],
        "version": v["version"],
        "state": v["state"],
        "currency": v["currency"],
        "valid_until": vigencia(v["validity_date"], config),
        "seller_id": repo.externo_por_odoo("usuario", v["seller_login"]) if v["seller_login"] else None,
        "lines": [{"sku": l["sku"], "quantity": entero_si_exacto(l["quantity"]),
                   "unit_price": dinero(l["unit_price"]), "discount_pct": dinero(l["discount_pct"])}
                  for l in v["lines"]],
        "total": dinero(v["amount_total"]),
    }


def disponibilidad(fuente, repo: Repositorio, config: Config, skus) -> dict:
    """Disponible = físico − reservado. Ante cualquier duda devuelve available=false."""
    ubicacion = repo.mapa("ubicacion", config.ubicacion_id)
    if repo.simular_caida() or not ubicacion:
        return {"available": False}
    try:
        stock = fuente.stock(sorted(skus), int(ubicacion))
    except DependenciaNoDisponible:
        return {"available": False}
    cantidades = {}
    for sku, s in stock.items():
        libre = s["fisico"] - s["reservado"]
        cantidades[sku] = int(libre) if float(libre).is_integer() else libre  # no entero → el motor lo rechaza
    return {"available": True, "company_id": config.company_id, "location_id": config.ubicacion_id,
            "quantities": cantidades}


def construir(request, fuente, repo: Repositorio, config: Config, ahora: datetime) -> tuple[dict, bool]:
    """Devuelve (masters, comercial_disponible)."""
    masters = {
        "business_time": ahora.isoformat(),
        "company_id": config.company_id,
        "policy": repo.politica(),
        "actors": repo.actores(),
        "customers": {}, "opportunities": {}, "products": {}, "quotations": {},
        "acceptances": repo.aceptaciones(config.company_id),
        "approvals": repo.aprobaciones(config.company_id),
        "availability": {"available": False},
    }
    if not isinstance(request, dict) or not all(isinstance(request.get(k), str) for k in LLAVES):
        return masters, True  # el motor rechazará por contrato; no hace falta leer Odoo
    if repo.simular_caida():
        return masters, False
    try:
        cliente = fuente.cliente(request["customer_id"])
        if cliente:
            ext = repo.cliente_ext(cliente["ref"]) or {}
            masters["customers"][cliente["ref"]] = {"company_id": config.company_id, "active": cliente["active"],
                                                    "identity_reviewed": bool(ext.get("identity_reviewed"))}
        opp = fuente.oportunidad(request["opportunity_id"])
        if opp and opp["active"]:
            masters["opportunities"][opp["opportunity_id"]] = {"company_id": config.company_id,
                                                               "customer_id": opp["customer_ref"], "type": opp["type"]}
        vigente = version_vigente(fuente.versiones_cotizacion(request["quotation_id"]))
        skus = set()
        if vigente:
            masters["quotations"][request["quotation_id"]] = cotizacion_normalizada(vigente, config, repo)
            skus = {l["sku"] for l in vigente["lines"] if l["sku"]}
        for sku, p in fuente.productos(sorted(skus)).items():
            masters["products"][sku] = {"company_id": config.company_id, "active": p["active"],
                                        "unit_price": dinero(p["list_price"]), "currency": p["currency"]}
    except DependenciaNoDisponible:
        return masters, False
    masters["availability"] = disponibilidad(fuente, repo, config, skus)
    return masters, True
