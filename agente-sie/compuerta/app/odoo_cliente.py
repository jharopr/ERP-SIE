"""Lectura de Odoo 18 por XML-RPC. Esta capa NO escribe en Odoo.

Devuelve diccionarios normalizados para que `snapshot.py` arme `masters`.
Cualquier falla de red, autenticación o tiempo (> timeout) se traduce en
`DependenciaNoDisponible`, que la compuerta convierte en PENDIENTE.
"""

from __future__ import annotations

import http.client
import re
import socket
import xmlrpc.client


class DependenciaNoDisponible(Exception):
    """Odoo no respondió a tiempo o no se pudo leer de forma confiable."""


class _TransporteConTimeout(xmlrpc.client.Transport):
    def __init__(self, timeout: float, https: bool = False):
        super().__init__()
        self._timeout = timeout
        self._https = https

    def make_connection(self, host):
        cls = http.client.HTTPSConnection if self._https else http.client.HTTPConnection
        chost, self._extra_headers, _ = self.get_host_info(host)
        self._connection = host, cls(chost, timeout=self._timeout)
        return self._connection[1]


def _nombre(m2o):
    """Odoo devuelve many2one como [id, nombre] o False."""
    return m2o[1] if m2o else None


def _id(m2o):
    return m2o[0] if m2o else None


class OdooCliente:
    def __init__(self, url: str, db: str, user: str, password: str, timeout: float = 5.0):
        self.url, self.db, self.user, self.password, self.timeout = url.rstrip("/"), db, user, password, timeout
        self._uid = None

    def _proxy(self, path):
        return xmlrpc.client.ServerProxy(f"{self.url}{path}", allow_none=True,
                                         transport=_TransporteConTimeout(self.timeout, self.url.startswith("https")))

    def _call(self, fn):
        try:
            return fn()
        except (OSError, socket.timeout, http.client.HTTPException, xmlrpc.client.ProtocolError, xmlrpc.client.Fault) as exc:
            self._uid = None
            raise DependenciaNoDisponible(type(exc).__name__) from exc

    def _uid_actual(self):
        if self._uid is None:
            uid = self._call(lambda: self._proxy("/xmlrpc/2/common").authenticate(self.db, self.user, self.password, {}))
            if not uid:
                raise DependenciaNoDisponible("Autenticación rechazada por Odoo")
            self._uid = uid
        return self._uid

    def _leer(self, modelo, dominio, campos, contexto=None):
        uid = self._uid_actual()
        kwargs = {"fields": campos, "context": {"active_test": False, **(contexto or {})}}
        return self._call(lambda: self._proxy("/xmlrpc/2/object").execute_kw(
            self.db, uid, self.password, modelo, "search_read", [dominio], kwargs))

    # ---- interfaz usada por snapshot.py -------------------------------------------------
    def ping(self) -> dict:
        version = self._call(lambda: self._proxy("/xmlrpc/2/common").version())
        self._uid_actual()
        return {"server_version": version.get("server_version")}

    def cliente(self, ref: str) -> dict | None:
        filas = self._leer("res.partner", [("ref", "=", ref)], ["id", "ref", "active"])
        return {"ref": filas[0]["ref"], "active": bool(filas[0]["active"])} if len(filas) == 1 else None

    def _ref_partner(self, partner_id):
        if not partner_id:
            return None
        filas = self._leer("res.partner", [("id", "=", partner_id)], ["ref"])
        return filas[0]["ref"] or None if filas else None

    def oportunidad(self, opp_id: str) -> dict | None:
        filas = self._leer("crm.lead", [("name", "=", opp_id)], ["name", "type", "partner_id", "active"])
        if len(filas) != 1:
            return None
        f = filas[0]
        return {"opportunity_id": f["name"], "type": f["type"], "active": bool(f["active"]),
                "customer_ref": self._ref_partner(_id(f["partner_id"]))}

    def versiones_cotizacion(self, quotation_id: str) -> list[dict]:
        patron = re.compile(rf"^{re.escape(quotation_id)} v([1-9][0-9]*)$")
        pedidos = self._leer("sale.order", [("client_order_ref", "=like", f"{quotation_id} v%")],
                             ["client_order_ref", "state", "currency_id", "validity_date", "user_id",
                              "partner_id", "opportunity_id", "amount_total", "order_line"])
        pedidos = [(p, m) for p in pedidos if (m := patron.match(p["client_order_ref"] or ""))]
        if not pedidos:
            return []
        # Lecturas agrupadas (una por modelo, no una por versión): menos viajes a Odoo, misma información.
        todas = self._leer("sale.order.line", [("order_id", "in", [p["id"] for p, _ in pedidos]),
                                               ("display_type", "=", False)],
                           ["order_id", "product_id", "product_uom_qty", "price_unit", "discount"])
        ids_producto = sorted({_id(l["product_id"]) for l in todas if l["product_id"]})
        codigos = {f["id"]: f["default_code"] for f in
                   self._leer("product.product", [("id", "in", ids_producto)], ["default_code"])} if ids_producto else {}
        ids_usuario = sorted({_id(p["user_id"]) for p, _ in pedidos if p["user_id"]})
        logins = {f["id"]: f["login"] for f in
                  self._leer("res.users", [("id", "in", ids_usuario)], ["login"])} if ids_usuario else {}
        ids_cliente = sorted({_id(p["partner_id"]) for p, _ in pedidos if p["partner_id"]})
        refs = {f["id"]: f["ref"] or None for f in
                self._leer("res.partner", [("id", "in", ids_cliente)], ["ref"])} if ids_cliente else {}
        resultado = []
        for p, m in pedidos:
            lineas = [l for l in todas if _id(l["order_id"]) == p["id"]]
            oportunidad = _nombre(p["opportunity_id"]) if p.get("opportunity_id") else None
            resultado.append({
                "version": int(m.group(1)), "state": p["state"], "currency": _nombre(p["currency_id"]),
                "validity_date": p["validity_date"] or None, "seller_login": logins.get(_id(p["user_id"])),
                "customer_ref": refs.get(_id(p["partner_id"])), "opportunity_id": oportunidad,
                "amount_total": p["amount_total"],
                "lines": [{"sku": codigos.get(_id(l["product_id"])), "quantity": l["product_uom_qty"],
                           "unit_price": l["price_unit"], "discount_pct": l["discount"]} for l in lineas],
            })
        return resultado

    def productos(self, skus: list[str]) -> dict:
        filas = self._leer("product.product", [("default_code", "in", list(skus))],
                           ["default_code", "active", "list_price", "currency_id"])
        return {f["default_code"]: {"active": bool(f["active"]), "list_price": f["list_price"],
                                    "currency": _nombre(f["currency_id"])} for f in filas}

    def stock(self, skus: list[str], ubicacion_odoo_id: int) -> dict:
        """Físico y reservado por SKU dentro de la ubicación interna de la tienda."""
        codigos = {f["id"]: f["default_code"] for f in
                   self._leer("product.product", [("default_code", "in", list(skus))], ["default_code"])}
        filas = self._leer("stock.quant", [("product_id", "in", list(codigos)),
                                           ("location_id", "child_of", ubicacion_odoo_id)],
                           ["product_id", "quantity", "reserved_quantity"]) if codigos else []
        resultado = {sku: {"fisico": 0.0, "reservado": 0.0} for sku in skus}
        for f in filas:
            sku = codigos.get(_id(f["product_id"]))
            if sku in resultado:
                resultado[sku]["fisico"] += f["quantity"]
                resultado[sku]["reservado"] += f["reserved_quantity"]
        return resultado
