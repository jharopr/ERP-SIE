"""Lectura de Odoo 18 por XML-RPC. Esta capa NO escribe en Odoo.

Devuelve diccionarios normalizados para que `snapshot.py` arme `masters`.
Cualquier falla de red, autenticación o tiempo (> timeout) se traduce en
`DependenciaNoDisponible`, que la compuerta convierte en PENDIENTE.
"""

from __future__ import annotations

import http.client
import re
import socket
import threading
import time
import unicodedata
import xmlrpc.client


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes: «María» y «maria» se tratan igual."""
    return "".join(c for c in unicodedata.normalize("NFD", (texto or "").lower()) if unicodedata.category(c) != "Mn")


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
        self._clientes = (0.0, [])          # (vence, [(id, texto normalizado)])
        self._candado = threading.Lock()

    CACHE_CLIENTES_S = 60   # la lista de clientes cambia poco; precios y stock NUNCA se cachean

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

    def _leer_anidado(self, modelo, dominio, especificacion, contexto=None):
        """Una sola llamada con relaciones anidadas (web_search_read de Odoo 17+): pedido + líneas +
        cliente + oportunidad en un viaje, en lugar de uno por modelo."""
        uid = self._uid_actual()
        kwargs = {"specification": especificacion, "context": {"active_test": False, **(contexto or {})}}
        r = self._call(lambda: self._proxy("/xmlrpc/2/object").execute_kw(
            self.db, uid, self.password, modelo, "web_search_read", [dominio], kwargs))
        return r["records"]

    def _politica_descuento(self, ids):
        if not ids:
            return {}
        uid = self._uid_actual()
        return self._call(lambda: self._proxy('/xmlrpc/2/object').execute_kw(
            self.db, uid, self.password, 'sale.order', 'mys_analyze_discount', [ids]))

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
        filas = self._leer("crm.lead", [("mys_reference", "=", opp_id)], ["name", "mys_reference", "type", "partner_id", "active"])
        if len(filas) != 1:
            return None
        f = filas[0]
        return {"opportunity_id": f["mys_reference"], "type": f["type"], "active": bool(f["active"]),
                "customer_ref": self._ref_partner(_id(f["partner_id"]))}

    _SPEC_LINEAS = {"fields": {"display_type": {}, "product_id": {"fields": {"default_code": {}, "display_name": {}}},
                               "product_uom_qty": {}, "price_unit": {}, "discount": {}}}

    @staticmethod
    def _rel(valor, campo="id"):
        """Valor de una relación many2one leída con web_search_read (dict o False)."""
        return valor.get(campo) if isinstance(valor, dict) else None

    def versiones_cotizacion(self, quotation_id: str) -> list[dict]:
        patron = re.compile(rf"^{re.escape(quotation_id)} v([1-9][0-9]*)$")
        pedidos = self._leer_anidado("sale.order", [("client_order_ref", "=like", f"{quotation_id} v%")], {
            "name": {}, "client_order_ref": {}, "state": {}, "validity_date": {}, "amount_total": {},
            "currency_id": {"fields": {"display_name": {}}}, "user_id": {"fields": {}},
            "partner_id": {"fields": {"ref": {}}}, "opportunity_id": {"fields": {"mys_reference": {}}},
            "order_line": self._SPEC_LINEAS})
        pedidos = [(p, m) for p in pedidos if (m := patron.match(p["client_order_ref"] or ""))]
        if not pedidos:
            return []
        rel = self._rel
        policy_reports = self._politica_descuento([p['id'] for p, _ in pedidos])
        return [{
            "version": int(m.group(1)), "numero_odoo": p["name"], "state": p["state"], "currency": rel(p["currency_id"], "display_name"),
            "validity_date": p["validity_date"] or None,
            "seller_login": None, "seller_odoo_id": rel(p["user_id"]),
            "customer_ref": rel(p["partner_id"], "ref") or None,
            "opportunity_id": rel(p["opportunity_id"], "mys_reference") or None,
            "amount_total": p["amount_total"],
            "policy_report": policy_reports.get(str(p['id'])),
            "lines": [{"sku": rel(l["product_id"], "default_code") or None, "quantity": l["product_uom_qty"],
                       "unit_price": l["price_unit"], "discount_pct": l["discount"]}
                      for l in p["order_line"] if not l["display_type"]],
        } for p, m in pedidos]

    CAMPOS_PERFIL = ["name", "ref", "mys_nivel", "mys_nivel_motivo", "mys_compras_6m", "mys_monto_6m",
                     "mys_unidades_6m", "mys_ticket_promedio", "mys_ultima_compra", "mys_dias_sin_compra",
                     "mys_inactivo", "mys_descuento_promedio", "mys_conversion", "mys_categorias_top",
                     "mys_productos_top", "mys_sugerencias", "mys_perfil_fecha"]

    def clientes_por_texto(self, texto: str) -> list[int]:
        """Clientes cuyo nombre o código contiene TODAS las palabras dichas, sin importar tildes,
        mayúsculas ni orden («Maria Flores» encuentra a «María Fernanda Flores Rojas»)."""
        palabras = [w for w in _normalizar(texto).replace(",", " ").split() if len(w) > 1]
        if not palabras:
            return []
        with self._candado:
            vence, clientes = self._clientes
            if vence < time.monotonic():
                filas = self._leer("res.partner", ["|", ("customer_rank", ">", 0), ("mys_nivel", "!=", False)], ["name", "ref"])
                clientes = [(f["id"], _normalizar(f"{f['name']} {f['ref'] or ''}")) for f in filas]
                self._clientes = (time.monotonic() + self.CACHE_CLIENTES_S, clientes)
        return [i for i, texto in clientes if all(w in texto for w in palabras)]

    def perfil_cliente(self, texto: str, limite: int = 3) -> list[dict]:
        """Perfil comercial (calculado por reglas en Odoo) de los clientes cuyo nombre o código coincide."""
        ids = self.clientes_por_texto(texto)
        if not ids:
            return []
        filas = self._leer("res.partner", [("id", "in", ids), ("mys_nivel", "!=", False)], self.CAMPOS_PERFIL)
        return filas[:limite]

    def clientes_segmentacion(self, vendedor_uid: int | None = None) -> list[dict]:
        """Perfiles de toda la cartera (o solo los clientes asignados a un vendedor). Solo lectura."""
        dominio = [("mys_nivel", "!=", False), ("active", "=", True), ("ref", "not like", "CARGA-%")]
        if vendedor_uid:
            dominio.append(("user_id", "=", vendedor_uid))
        return self._leer("res.partner", dominio, self.CAMPOS_PERFIL + ["user_id"],
                          contexto={"active_test": True})

    def rotacion(self, dias: int, ubicacion_odoo_id: int | None = None) -> dict:
        """Totales de venta confirmada y stock por SKU, calculados en Odoo (product.product.mys_rotacion)."""
        uid = self._uid_actual()
        return self._call(lambda: self._proxy("/xmlrpc/2/object").execute_kw(
            self.db, uid, self.password, "product.product", "mys_rotacion", [],
            {"dias": int(dias), "ubicacion_id": ubicacion_odoo_id or False}))

    def buscar_cotizaciones(self, texto: str, limite: int = 5) -> list[dict]:
        """Cotizaciones SIE por número de Odoo (S000…), código COT-…, nombre o código del cliente.

        Devuelve una entrada por familia (COT-…) con todas sus versiones, para que el vendedor
        hable con nombres y no con códigos. Solo lectura.
        """
        t = texto.strip()
        dominio = [("client_order_ref", "=like", "COT-%"), "|", "|", "|",
                   ("name", "ilike", t), ("client_order_ref", "ilike", t),
                   ("partner_id.name", "ilike", t), ("partner_id.ref", "ilike", t)]
        coincidencias = self._leer("sale.order", dominio, ["client_order_ref"])
        if not coincidencias:  # nombre del cliente dicho de otra forma (sin tildes, incompleto, otro orden)
            ids = self.clientes_por_texto(t)
            if ids:
                coincidencias = self._leer("sale.order", [("client_order_ref", "=like", "COT-%"), ("partner_id", "in", ids)],
                                           ["client_order_ref"])
        familias = []
        for f in coincidencias:
            m = re.match(r"^(COT-[A-Za-z0-9_-]+) v[1-9][0-9]*$", f["client_order_ref"] or "")
            if m and m.group(1) not in familias:
                familias.append(m.group(1))
        familias = familias[:limite]
        if not familias:
            return []
        dominio = ["|"] * (len(familias) - 1) + [("client_order_ref", "=like", f"{q} v%") for q in familias]
        pedidos = self._leer_anidado("sale.order", dominio, {
            "name": {}, "client_order_ref": {}, "state": {}, "amount_total": {}, "company_id": {"fields": {}},
            "partner_id": {"fields": {"display_name": {}, "ref": {}}}, "opportunity_id": {"fields": {"mys_reference": {}}},
            "user_id": {"fields": {"display_name": {}}}, "order_line": self._SPEC_LINEAS})
        rel = self._rel
        resultado = []
        policy_reports = self._politica_descuento([p['id'] for p in pedidos])
        for q in familias:
            versiones = []
            for p in pedidos:
                m = re.match(rf"^{re.escape(q)} v([1-9][0-9]*)$", p["client_order_ref"] or "")
                if not m:
                    continue
                propias = [l for l in p["order_line"] if not l["display_type"]]
                versiones.append({
                    "version": int(m.group(1)), "numero_odoo": p["name"], "state": p["state"],
                    "company_odoo_id": rel(p["company_id"]), "cliente": rel(p["partner_id"], "display_name"),
                    "cliente_ref": rel(p["partner_id"], "ref") or None,
                    "oportunidad": rel(p["opportunity_id"], "mys_reference") or None,
                    "vendedor": rel(p["user_id"], "display_name"), "total": p["amount_total"],
                    "analisis_comercial": policy_reports.get(str(p['id'])),
                    "productos": "; ".join(f"{l['product_uom_qty']:g} × {rel(l['product_id'], 'display_name')} ({l['discount']:g} %)"
                                           for l in propias)})
            resultado.append({"cotizacion": q, "versiones": sorted(versiones, key=lambda v: v["version"])})
        return resultado

    def productos(self, skus: list[str]) -> dict:
        filas = self._leer("product.product", [("default_code", "in", list(skus))],
                           ["name", "default_code", "active", "list_price", "currency_id"])
        return {f["default_code"]: {"name": f["name"], "active": bool(f["active"]), "list_price": f["list_price"],
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
