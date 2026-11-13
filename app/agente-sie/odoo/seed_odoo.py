"""Carga idempotente del escenario sintético PC3 en Odoo 18 y en la base de la compuerta.

Se ejecuta DENTRO del contenedor `compuerta` (tiene red hacia Odoo y acceso al
volumen SQLite):

    docker compose exec compuerta python /seed/seed_odoo.py            # carga o refresca
    docker compose exec compuerta python /seed/seed_odoo.py --reiniciar # además borra solicitudes y bitácora
    docker compose exec compuerta python /seed/seed_odoo.py --crear-v3  # paso del caso E02 tras la aprobación

Idempotente: busca por `ref`, `default_code`, `client_order_ref` o nombre y
actualiza en vez de duplicar. Las vigencias quedan en el día de ejecución.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import xmlrpc.client

sys.path.insert(0, os.environ.get("COMPUERTA_SRC", "/srv"))

from app import escenario as E  # noqa: E402
from app.config import Config, ahora_lima  # noqa: E402
from app.repositorio import Repositorio  # noqa: E402

MODULOS = ["crm", "sale_management", "stock"]


def log(msg):
    print(f"[seed] {msg}", flush=True)


class Odoo:
    def __init__(self, url, db, login, password):
        self.url, self.db, self.login, self.password = url.rstrip("/"), db, login, password
        self.uid = None

    def proxy(self, path):
        return xmlrpc.client.ServerProxy(f"{self.url}{path}", allow_none=True)

    def esperar(self, segundos=300):
        limite = time.time() + segundos
        while True:
            try:
                return self.proxy("/xmlrpc/2/common").version()
            except Exception as exc:  # noqa: BLE001 - se reintenta cualquier falla de arranque
                if time.time() > limite:
                    raise SystemExit(f"Odoo no respondió en {segundos} s: {exc}")
                time.sleep(3)

    def asegurar_base(self, master, idioma):
        dbs = self.proxy("/xmlrpc/2/db").list()
        if self.db in dbs:
            log(f"base '{self.db}' ya existe")
            return
        log(f"creando base '{self.db}' sin datos de demostración (puede tardar 1-3 min)…")
        try:
            self.proxy("/xmlrpc/2/db").create_database(master, self.db, False, idioma, self.password, self.login)
        except xmlrpc.client.Fault as exc:
            raise SystemExit(f"No se pudo crear la base. ¿ODOO_MASTER_PASSWORD coincide? Detalle: {exc.faultString[:300]}")

    def conectar(self):
        self.uid = self.proxy("/xmlrpc/2/common").authenticate(self.db, self.login, self.password, {})
        if not self.uid:
            raise SystemExit("Autenticación rechazada: revise ODOO_USER / ODOO_PASSWORD en .env")

    def x(self, modelo, metodo, *args, **kw):
        kw['context'] = {**kw.get('context', {}), 'mys_seed': True}
        return self.proxy("/xmlrpc/2/object").execute_kw(self.db, self.uid, self.password, modelo, metodo, list(args), kw)

    def buscar(self, modelo, dominio, **kw):
        return self.x(modelo, "search", dominio, context={"active_test": False}, **kw)

    def leer(self, modelo, dominio, campos):
        return self.x(modelo, "search_read", dominio, fields=campos, context={"active_test": False})

    def ref(self, xmlid):
        modulo, nombre = xmlid.split(".")
        r = self.leer("ir.model.data", [("module", "=", modulo), ("name", "=", nombre)], ["res_id"])
        return r[0]["res_id"] if r else None

    def upsert(self, modelo, dominio, valores):
        ids = self.buscar(modelo, dominio)
        if ids:
            self.x(modelo, "write", ids[:1], valores)
            return ids[0], False
        return self.x(modelo, "create", valores), True


def llamar_tolerante(odoo, modelo, metodo, ids, contexto=None):
    """Algunos métodos de botón devuelven acciones (dict) o None; no son errores."""
    try:
        return odoo.x(modelo, metodo, ids, context=contexto or {})
    except xmlrpc.client.Fault as exc:
        if "cannot marshal None" in exc.faultString:
            return None
        raise


def instalar_modulos(odoo):
    pendientes = odoo.leer("ir.module.module", [("name", "in", MODULOS), ("state", "!=", "installed")], ["name"])
    if not pendientes:
        log("módulos crm, sale_management y stock ya instalados")
        return
    log(f"instalando {[m['name'] for m in pendientes]} (puede tardar 2-5 min)…")
    llamar_tolerante(odoo, "ir.module.module", "button_immediate_install", [m["id"] for m in pendientes])
    odoo.conectar()  # el registro se recarga tras instalar


def configurar_empresa(odoo):
    pen = odoo.buscar("res.currency", [("name", "=", "PEN")])
    odoo.x("res.currency", "write", pen, {"active": True})
    empresa = odoo.leer("res.users", [("id", "=", odoo.uid)], ["company_id"])[0]["company_id"][0]
    odoo.x("res.company", "write", [empresa], {"name": "Importaciones MYS Hermanos", "currency_id": pen[0]})
    tarifas = odoo.buscar("product.pricelist", [])
    if tarifas:
        odoo.x("product.pricelist", "write", tarifas, {"currency_id": pen[0]})
    almacen = odoo.leer("stock.warehouse", [("company_id", "=", empresa)], ["lot_stock_id"])[0]
    odoo.x("stock.warehouse", "write", [almacen["id"]], {"name": E.UBICACION_ID})
    return pen[0], almacen["lot_stock_id"][0]


def asegurar_vendedor(odoo):
    grupos = [g for g in (odoo.ref("base.group_user"), odoo.ref("sales_team.group_sale_salesman")) if g]
    campo_grupos = "group_ids" if "group_ids" in odoo.x("res.users", "fields_get", attributes=["type"]) else "groups_id"
    uid, nuevo = odoo.upsert("res.users", [("login", "=", E.VENDEDOR_LOGIN)],
                             {"name": "Vendedor 01", "login": E.VENDEDOR_LOGIN,
                              campo_grupos: [(4, g) for g in grupos]})
    log(f"vendedor {E.VENDEDOR_LOGIN} {'creado' if nuevo else 'actualizado'} (id {uid})")
    return uid


def asegurar_productos(odoo):
    campos = odoo.x("product.template", "fields_get", attributes=["type"])
    almacenable = {"type": "consu", "is_storable": True} if "is_storable" in campos else {"type": "product"}
    ids = {}
    for sku, p in E.PRODUCTOS.items():
        tmpl, _ = odoo.upsert("product.template", [("default_code", "=", sku)],
                              {"name": p["nombre"], "default_code": sku, "list_price": p["precio"], "sale_ok": True,
                               "taxes_id": [(6, 0, [])], "active": True, **almacenable})
        ids[sku] = odoo.buscar("product.product", [("product_tmpl_id", "=", tmpl)])[0]
    log(f"productos {list(ids)} listos ({almacenable})")
    return ids


def asegurar_clientes(odoo):
    ids = {}
    for ref, c in E.CLIENTES.items():
        ids[ref], _ = odoo.upsert("res.partner", [("ref", "=", ref)], {"name": c["nombre"], "ref": ref, "active": True})
    return ids


def fijar_stock(odoo, productos, ubicacion):
    for sku, pid in productos.items():
        objetivo = E.PRODUCTOS[sku]["fisico"]
        quants = odoo.buscar("stock.quant", [("product_id", "=", pid), ("location_id", "=", ubicacion)])
        if quants:
            odoo.x("stock.quant", "write", quants[:1], {"inventory_quantity": objetivo}, context={"inventory_mode": True})
            qid = quants[0]
        else:
            qid = odoo.x("stock.quant", "create", {"product_id": pid, "location_id": ubicacion,
                                                   "inventory_quantity": objetivo}, context={"inventory_mode": True})
        llamar_tolerante(odoo, "stock.quant", "action_apply_inventory", [qid])
    log("stock físico fijado en 10 y 10")


def lineas(productos, lista):
    return [(0, 0, {"product_id": productos[l["sku"]], "product_uom_qty": l["cantidad"],
                    "price_unit": E.PRODUCTOS[l["sku"]]["precio"], "discount": l.get("descuento", 0.0),
                    "tax_id": [(6, 0, [])]}) for l in lista]


def asegurar_reservas(odoo, productos, clientes, vendedor, moneda):
    for r in E.RESERVAS:
        existentes = odoo.leer("sale.order", [("client_order_ref", "=", r["ref"])], ["state"])
        if existentes and existentes[0]["state"] == "sale":
            continue
        if existentes:
            oid = existentes[0]["id"]
        else:
            oid = odoo.x("sale.order", "create", {
                "partner_id": clientes[r["cliente"]], "client_order_ref": r["ref"], "user_id": vendedor,
                "order_line": lineas(productos, [{"sku": r["sku"], "cantidad": r["cantidad"]}])})
        llamar_tolerante(odoo, "sale.order", "action_confirm", [oid])
        entregas = odoo.leer("stock.picking", [("sale_id", "=", oid), ("state", "not in", ["done", "cancel"])], ["state"])
        if entregas:
            llamar_tolerante(odoo, "stock.picking", "action_assign", [p["id"] for p in entregas])
    log("reservas de CLI-DEMO-002 confirmadas (2 × RAD-7BT, 7 × RAD-10X)")


def asegurar_oportunidades(odoo, clientes):
    ids = {}
    reference_field = 'mys_reference' if 'mys_reference' in odoo.x('crm.lead', 'fields_get', attributes=['type']) else 'name'
    for opp, o in E.OPORTUNIDADES.items():
        ids[opp], _ = odoo.upsert("crm.lead", [(reference_field, "=", opp)],
                                  {"name": opp, "type": "opportunity", "partner_id": clientes[o["cliente"]], "active": True})
    return ids


def poner_estado(odoo, oid, estado_actual, objetivo):
    if estado_actual == objetivo:
        return
    if estado_actual == "cancel" and objetivo != "cancel":
        llamar_tolerante(odoo, "sale.order", "action_draft", [oid])
        estado_actual = "draft"
    if objetivo == "sent" and estado_actual == "draft":
        try:
            llamar_tolerante(odoo, "sale.order", "action_quotation_sent", [oid])
        except xmlrpc.client.Fault:
            odoo.x("sale.order", "write", [oid], {"state": "sent"})
    elif objetivo == "cancel":
        llamar_tolerante(odoo, "sale.order", "action_cancel", [oid], {"disable_cancel_warning": True})


def asegurar_cotizacion(odoo, cot, productos, clientes, oportunidades, vendedor, hoy, tiene_opp):
    ref = f"{cot['id']} v{cot['version']}"
    valores = {"partner_id": clientes[cot["cliente"]], "client_order_ref": ref, "user_id": vendedor,
               "validity_date": hoy}
    if tiene_opp:
        valores["opportunity_id"] = oportunidades[cot["oportunidad"]]
    existentes = odoo.leer("sale.order", [("client_order_ref", "=", ref)], ["state", "order_line"])
    if existentes:
        oid, estado = existentes[0]["id"], existentes[0]["state"]
        if estado == "cancel" and cot["estado"] != "cancel":
            llamar_tolerante(odoo, "sale.order", "action_draft", [oid])
            estado = "draft"
        if estado in ("draft", "sent"):
            odoo.x("sale.order", "write", [oid], {**valores, "order_line": [(5, 0, 0), *lineas(productos, cot["lineas"])]})
    else:
        oid = odoo.x("sale.order", "create", {**valores, "order_line": lineas(productos, cot["lineas"])})
        estado = "draft"
    poner_estado(odoo, oid, estado, cot["estado"])
    final = odoo.leer("sale.order", [("id", "=", oid)], ["state", "amount_total", "currency_id"])[0]
    return ref, final


def anular_versiones_extra(odoo, conocidas):
    """Versiones creadas durante una demo anterior (p. ej. COT-DEMO-004 v3) se anulan al refrescar."""
    for base in {c["id"] for c in E.COTIZACIONES}:
        for so in odoo.leer("sale.order", [("client_order_ref", "=like", f"{base} v%")], ["client_order_ref", "state"]):
            if so["client_order_ref"] not in conocidas and so["state"] != "cancel":
                llamar_tolerante(odoo, "sale.order", "action_cancel", [so["id"]], {"disable_cancel_warning": True})
                log(f"anulada versión extra {so['client_order_ref']}")


def verificar(odoo, productos, ubicacion):
    ok = True
    esperado = {"RAD-7BT": (10, 2, 8), "RAD-10X": (10, 7, 3)}
    for sku, pid in productos.items():
        q = odoo.leer("stock.quant", [("product_id", "=", pid), ("location_id", "child_of", ubicacion)],
                      ["quantity", "reserved_quantity"])
        fisico, reservado = sum(x["quantity"] for x in q), sum(x["reserved_quantity"] for x in q)
        fila = (int(fisico), int(reservado), int(fisico - reservado))
        marca = "✓" if fila == esperado[sku] else "✗"
        ok &= fila == esperado[sku]
        log(f"{marca} {sku}: físico {fila[0]}, reservado {fila[1]}, disponible {fila[2]} (esperado {esperado[sku]})")
    return ok


def crear_v3(odoo, repo, productos, clientes, oportunidades, vendedor, hoy, tiene_opp, ahora):
    cot = {"id": "COT-DEMO-004", "version": 3, "oportunidad": "OPP-DEMO-001", "cliente": "CLI-DEMO-001",
           "lineas": [{"sku": "RAD-7BT", "cantidad": 5, "descuento": 10.0}], "estado": "sent"}
    _, final = asegurar_cotizacion(odoo, cot, productos, clientes, oportunidades, vendedor, hoy, tiene_opp)
    total = f"{final['amount_total']:.2f}"
    with repo.conexion() as db:
        db.execute("INSERT INTO aceptaciones VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(acceptance_id) DO NOTHING",
                   ("ACE-PC3-005", E.COMPANY_ID, "COT-DEMO-004", 3, "CLI-DEMO-001", total, ahora.isoformat(), E.VENDEDOR))
    log(f"COT-DEMO-004 v3 enviada (total {total}) y aceptación ACE-PC3-005 registrada")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reiniciar", action="store_true", help="Borra solicitudes, bitácora, REP y aprobaciones")
    parser.add_argument("--crear-v3", action="store_true", help="Crea COT-DEMO-004 v3 (tras la aprobación del dueño)")
    args = parser.parse_args()

    config = Config.desde_entorno()
    master = os.environ.get("ODOO_MASTER_PASSWORD", "")
    if not config.odoo_password or not master:
        raise SystemExit("Faltan ODOO_PASSWORD u ODOO_MASTER_PASSWORD en .env")
    # El seed es administración explícita; el servicio usa otra cuenta solo lectura.
    odoo = Odoo(config.odoo_url, config.odoo_db, os.environ.get("ODOO_USER", "admin"),
                os.environ.get("ODOO_PASSWORD", ""))
    log(f"Odoo {odoo.esperar().get('server_version')} en {config.odoo_url}")
    odoo.asegurar_base(master, os.environ.get("ODOO_IDIOMA", "es_PE"))
    odoo.conectar()
    instalar_modulos(odoo)

    ahora = ahora_lima()
    hoy = ahora.date().isoformat()
    repo = Repositorio(config.database)
    moneda, ubicacion = configurar_empresa(odoo)
    vendedor = asegurar_vendedor(odoo)
    productos = asegurar_productos(odoo)
    clientes = asegurar_clientes(odoo)
    tiene_opp = "opportunity_id" in odoo.x("sale.order", "fields_get", attributes=["type"])
    if not tiene_opp:
        log("AVISO: sale.order no tiene opportunity_id (falta sale_crm); el vínculo cotización-oportunidad no se podrá leer")

    if args.crear_v3:
        oportunidades = asegurar_oportunidades(odoo, clientes)
        crear_v3(odoo, repo, productos, clientes, oportunidades, vendedor, hoy, tiene_opp, ahora)
        return

    fijar_stock(odoo, productos, ubicacion)
    asegurar_reservas(odoo, productos, clientes, vendedor, moneda)
    oportunidades = asegurar_oportunidades(odoo, clientes)
    conocidas = set()
    for cot in E.COTIZACIONES:
        ref, final = asegurar_cotizacion(odoo, cot, productos, clientes, oportunidades, vendedor, hoy, tiene_opp)
        conocidas.add(ref)
        esperado = E.total_cotizacion(cot)
        marca = "✓" if abs(final["amount_total"] - esperado) < 0.005 and final["state"] == cot["estado"] else "✗"
        log(f"{marca} {ref}: estado {final['state']}, total {final['amount_total']:.2f} {final['currency_id'][1]}"
            f" (esperado {esperado:.2f}, {cot['estado']})")
    anular_versiones_extra(odoo, conocidas)

    if args.reiniciar:
        repo.reiniciar_transacciones()
        log("base de la compuerta reiniciada (solicitudes, bitácora, REP, aprobaciones)")
    E.registrar_maestros_locales(repo, ahora, ubicacion)
    log(f"maestros locales registrados; aceptaciones con hora {ahora.isoformat()} − 5 min; "
        f"cotizaciones vigentes hasta {hoy} {config.hora_cierre_cotizacion}")
    if not verificar(odoo, productos, ubicacion):
        raise SystemExit("La verificación de stock no coincide con el escenario")
    log("seed completo")


if __name__ == "__main__":
    main()
