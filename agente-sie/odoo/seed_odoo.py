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
import csv
import json
import os
from pathlib import Path
import sys
import time
import xmlrpc.client

sys.path.insert(0, os.environ.get("COMPUERTA_SRC", "/srv"))

from app import escenario as E  # noqa: E402
from app.config import Config, ahora_lima  # noqa: E402
from app.repositorio import Repositorio  # noqa: E402

MODULOS = ["crm", "sale_management", "stock"]
DIR_DATOS = Path(__file__).resolve().parent


def cargar_catalogo():
    """odoo/catalogo.csv: catálogo de la tienda (scripts/importar_catalogo.py lo genera desde el Excel de la empresa).

    Columnas obligatorias: sku, nombre, categoria, precio_pen, stock_fisico.
    Opcionales: subcategoria, unidad (unidad|par|kit|metro|servicio), tipo (producto|servicio), codigo_barras.
    Debe incluir los SKU de los casos PC3 con su precio y stock.
    """
    cat = {}
    with open(DIR_DATOS / "catalogo.csv", encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            cat[fila["sku"].strip()] = {"nombre": fila["nombre"].strip(), "categoria": fila["categoria"].strip(),
                                        "subcategoria": (fila.get("subcategoria") or "").strip(),
                                        "unidad": (fila.get("unidad") or "unidad").strip(),
                                        "tipo": (fila.get("tipo") or "producto").strip(),
                                        "barras": (fila.get("codigo_barras") or "").strip(),
                                        "precio": float(fila["precio_pen"]), "fisico": int(fila["stock_fisico"])}
    for sku, prod in E.PRODUCTOS.items():  # los casos PC3 dependen de estos valores exactos
        if sku not in cat or cat[sku]["precio"] != prod["precio"] or cat[sku]["fisico"] != prod["fisico"]:
            raise SystemExit(f"catalogo.csv debe mantener {sku} con precio {prod['precio']} y stock {prod['fisico']} (casos PC3)")
    return cat


def cargar_extra():
    archivo = DIR_DATOS / "escenario_extra.json"
    if not archivo.exists():
        return {"clientes": {}, "leads": [], "ventas_confirmadas": [], "oportunidades": {}, "cotizaciones": []}
    return {"leads": [], **json.loads(archivo.read_text(encoding="utf-8"))}


CAT = cargar_catalogo()
EXTRA = cargar_extra()
CLIENTES = {**{k: {"nombre": v["nombre"]} for k, v in E.CLIENTES.items()}, **EXTRA["clientes"]}
OPORTUNIDADES = {**E.OPORTUNIDADES, **EXTRA["oportunidades"]}
RESERVAS = [{"ref": r["ref"], "cliente": r["cliente"], "lineas": [{"sku": r["sku"], "cantidad": r["cantidad"]}]}
            for r in E.RESERVAS] + EXTRA["ventas_confirmadas"]
COTIZACIONES = E.COTIZACIONES + EXTRA["cotizaciones"]


def total_esperado(cot):
    return round(sum(round(CAT[l["sku"]]["precio"] * l["cantidad"] * (1 - l.get("descuento", 0) / 100), 2)
                     for l in cot["lineas"]), 2)


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
    odoo.x("res.company", "write", [empresa], {"name": "MYS Demo (datos sintéticos)", "currency_id": pen[0]})
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
                             {"name": "Vendedor Demo 01 (sintético)", "login": E.VENDEDOR_LOGIN,
                              campo_grupos: [(4, g) for g in grupos]})
    log(f"vendedor {E.VENDEDOR_LOGIN} {'creado' if nuevo else 'actualizado'} (id {uid})")
    return uid


def asegurar_productos(odoo):
    campos = odoo.x("product.template", "fields_get", attributes=["type"])
    almacenable = {"type": "consu", "is_storable": True} if "is_storable" in campos else {"type": "product"}
    servicio = {"type": "service", **({"is_storable": False} if "is_storable" in campos else {})}
    uom = {"unidad": odoo.ref("uom.product_uom_unit"), "metro": odoo.ref("uom.product_uom_meter")}
    # Categorías de dos niveles (categoría / subcategoría), como en la lista de la empresa.
    categorias = {}
    for nombre in sorted({p["categoria"] for p in CAT.values()}):
        categorias[nombre], _ = odoo.upsert("product.category", [("name", "=", nombre), ("parent_id", "=", False)],
                                            {"name": nombre})
    for padre, sub in sorted({(p["categoria"], p["subcategoria"]) for p in CAT.values() if p["subcategoria"]}):
        categorias[(padre, sub)], _ = odoo.upsert("product.category", [("name", "=", sub), ("parent_id", "=", categorias[padre])],
                                                  {"name": sub, "parent_id": categorias[padre]})
    existentes = {t["default_code"]: t["id"] for t in odoo.leer("product.template", [("default_code", "in", list(CAT))],
                                                                ["default_code"])}
    nuevos = 0
    for sku, p in CAT.items():
        unidad = uom["metro"] if p["unidad"] == "metro" and uom["metro"] else uom["unidad"]
        valores = {"name": p["nombre"], "default_code": sku, "list_price": p["precio"], "sale_ok": True,
                   "categ_id": categorias[(p["categoria"], p["subcategoria"])] if p["subcategoria"] else categorias[p["categoria"]],
                   "uom_id": unidad, "uom_po_id": unidad, "barcode": p["barras"] or False,
                   "taxes_id": [(6, 0, [])], "active": True, **(servicio if p["tipo"] == "servicio" else almacenable)}
        if sku in existentes:
            odoo.x("product.template", "write", [existentes[sku]], valores)
        else:
            existentes[sku] = odoo.x("product.template", "create", valores)
            nuevos += 1
    fuera = odoo.buscar("product.template", [("default_code", "!=", False), ("default_code", "not in", list(CAT)),
                                             ("active", "=", True)])
    if fuera:  # productos de un catálogo anterior: se archivan (no se borran: pueden tener historial)
        odoo.x("product.template", "write", fuera, {"active": False})
        log(f"{len(fuera)} productos que ya no están en el catálogo fueron archivados")
    ids = {v["default_code"]: v["id"] for v in odoo.leer("product.product", [("default_code", "in", list(CAT))], ["default_code"])}
    log(f"{len(ids)} productos del catálogo listos ({nuevos} nuevos, {len(categorias)} categorías)")
    return ids


def asegurar_clientes(odoo):
    ids = {}
    for ref, c in CLIENTES.items():
        ids[ref], _ = odoo.upsert("res.partner", [("ref", "=", ref)], {"name": c["nombre"], "ref": ref, "active": True})
    return ids


def con_stock(productos):
    return {sku: pid for sku, pid in productos.items() if CAT[sku]["tipo"] != "servicio"}


def fijar_stock(odoo, productos, ubicacion):
    """Ajuste de inventario agrupado: solo toca los productos cuyo físico difiere del catálogo."""
    almacenables = con_stock(productos)
    quants = {}
    for q in odoo.leer("stock.quant", [("product_id", "in", list(almacenables.values())), ("location_id", "=", ubicacion)],
                       ["product_id", "quantity"]):
        quants.setdefault(q["product_id"][0], q)
    modo = {"inventory_mode": True}
    por_aplicar = []
    for sku, pid in almacenables.items():
        objetivo = CAT[sku]["fisico"]
        q = quants.get(pid)
        if q and int(q["quantity"]) == objetivo:
            continue
        if q:
            odoo.x("stock.quant", "write", [q["id"]], {"inventory_quantity": objetivo}, context=modo)
            por_aplicar.append(q["id"])
        else:
            por_aplicar.append(odoo.x("stock.quant", "create", {"product_id": pid, "location_id": ubicacion,
                                                                "inventory_quantity": objetivo}, context=modo))
    if por_aplicar:
        llamar_tolerante(odoo, "stock.quant", "action_apply_inventory", por_aplicar)
    log(f"stock físico fijado para {len(almacenables)} productos ({len(por_aplicar)} ajustados)")


def lineas(productos, lista):
    return [(0, 0, {"product_id": productos[l["sku"]], "product_uom_qty": l["cantidad"],
                    "price_unit": CAT[l["sku"]]["precio"], "discount": l.get("descuento", 0.0),
                    "tax_id": [(6, 0, [])]}) for l in lista]


def asegurar_reservas(odoo, productos, clientes, vendedor, moneda):
    for r in RESERVAS:
        existentes = odoo.leer("sale.order", [("client_order_ref", "=", r["ref"])], ["state", "order_line"])
        if existentes and existentes[0]["state"] == "sale":
            actuales = sorted((l["product_id"][0], int(l["product_uom_qty"])) for l in
                              odoo.leer("sale.order.line", [("order_id", "=", existentes[0]["id"])], ["product_id", "product_uom_qty"]))
            deseadas = sorted((productos[l["sku"]], l["cantidad"]) for l in r["lineas"])
            if actuales == deseadas:
                continue
            # El catálogo cambió: se anula la venta anterior (libera su reserva) y se crea otra con el contenido nuevo.
            llamar_tolerante(odoo, "sale.order", "action_cancel", [existentes[0]["id"]], {"disable_cancel_warning": True})
            odoo.x("sale.order", "write", [existentes[0]["id"]], {"client_order_ref": f"{r['ref']} (anulada por cambio de catálogo)"})
            existentes = []
        if existentes:
            oid = existentes[0]["id"]
        else:
            oid = odoo.x("sale.order", "create", {
                "partner_id": clientes[r["cliente"]], "client_order_ref": r["ref"], "user_id": vendedor,
                "order_line": lineas(productos, r["lineas"])})
        llamar_tolerante(odoo, "sale.order", "action_confirm", [oid])
        entregas = odoo.leer("stock.picking", [("sale_id", "=", oid), ("state", "not in", ["done", "cancel"])], ["state"])
        if entregas:
            llamar_tolerante(odoo, "stock.picking", "action_assign", [p["id"] for p in entregas])
    log(f"{len(RESERVAS)} ventas confirmadas (generan las reservas de stock)")


def asegurar_oportunidades(odoo, clientes):
    ids = {}
    for opp, o in OPORTUNIDADES.items():
        ids[opp], _ = odoo.upsert("crm.lead", [("name", "=", opp)],
                                  {"name": opp, "type": "opportunity", "partner_id": clientes[o["cliente"]], "active": True})
    for lead in EXTRA["leads"]:  # leads aún sin convertir: muestran el paso «lead → oportunidad» en el CRM
        existentes = odoo.leer("crm.lead", [("name", "=", lead["nombre"])], ["type"])
        if not existentes:
            odoo.x("crm.lead", "create", {"name": lead["nombre"], "type": "lead", "contact_name": lead["contacto"]})
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
    for base in {c["id"] for c in COTIZACIONES}:
        for so in odoo.leer("sale.order", [("client_order_ref", "=like", f"{base} v%")], ["client_order_ref", "state"]):
            if so["client_order_ref"] not in conocidas and so["state"] != "cancel":
                llamar_tolerante(odoo, "sale.order", "action_cancel", [so["id"]], {"disable_cancel_warning": True})
                log(f"anulada versión extra {so['client_order_ref']}")


def verificar(odoo, productos, ubicacion):
    ok = True
    reservado = {}
    for r in RESERVAS:
        for l in r["lineas"]:
            reservado[l["sku"]] = reservado.get(l["sku"], 0) + l["cantidad"]
    esperado = {sku: (p["fisico"], reservado.get(sku, 0), p["fisico"] - reservado.get(sku, 0)) for sku, p in CAT.items()}
    almacenables = con_stock(productos)
    totales = {pid: [0.0, 0.0] for pid in almacenables.values()}
    for q in odoo.leer("stock.quant", [("product_id", "in", list(totales)), ("location_id", "child_of", ubicacion)],
                       ["product_id", "quantity", "reserved_quantity"]):
        totales[q["product_id"][0]][0] += q["quantity"]
        totales[q["product_id"][0]][1] += q["reserved_quantity"]
    errores = 0
    for sku, pid in almacenables.items():
        fisico, reservado_odoo = totales[pid]
        fila = (int(fisico), int(reservado_odoo), int(fisico - reservado_odoo))
        if fila != esperado[sku]:
            errores += 1
            log(f"✗ {sku}: físico {fila[0]}, reservado {fila[1]}, disponible {fila[2]} (esperado {esperado[sku]})")
        elif esperado[sku][1] or sku in E.PRODUCTOS:  # se muestran solo los que tienen reservas
            log(f"✓ {sku}: físico {fila[0]}, reservado {fila[1]}, disponible {fila[2]}")
    log(f"stock verificado: {len(almacenables) - errores}/{len(almacenables)} productos coinciden con el catálogo")
    return ok and not errores


def registrar_extra_local(repo, ahora, totales):
    """Clientes, oportunidades del vendedor y aceptaciones del escenario extra en la base de la compuerta."""
    from datetime import timedelta
    aceptado = (ahora - timedelta(minutes=5)).isoformat()
    with repo.conexion() as db:
        for ref, c in EXTRA["clientes"].items():
            db.execute("INSERT INTO clientes_ext(ref,identity_reviewed,segmento) VALUES(?,1,?)"
                       " ON CONFLICT(ref) DO UPDATE SET identity_reviewed=1, segmento=excluded.segmento",
                       (ref, c["segmento"]))
        fila = db.execute("SELECT opportunities_json FROM actores WHERE actor_id=?", (E.VENDEDOR,)).fetchone()
        opps = sorted(set(json.loads(fila[0]) if fila else []) | set(EXTRA["oportunidades"]))
        db.execute("UPDATE actores SET opportunities_json=? WHERE actor_id=?", (json.dumps(opps), E.VENDEDOR))
        for cot in EXTRA["cotizaciones"]:
            if not cot.get("aceptacion"):
                continue
            total = "%.2f" % totales[f"{cot['id']} v{cot['version']}"]
            db.execute("INSERT INTO aceptaciones VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(acceptance_id) DO UPDATE SET"
                       " total=excluded.total, accepted_at=excluded.accepted_at",
                       (cot["aceptacion"], E.COMPANY_ID, cot["id"], cot["version"], cot["cliente"], total, aceptado, "SEED"))
    n = sum(1 for c in EXTRA["cotizaciones"] if c.get("aceptacion"))
    log(f"escenario extra: {len(EXTRA['clientes'])} clientes, {len(EXTRA['oportunidades'])} oportunidades, {n} aceptaciones")


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
    odoo = Odoo(config.odoo_url, config.odoo_db, config.odoo_user, config.odoo_password)
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
    totales = {}
    for cot in COTIZACIONES:
        ref, final = asegurar_cotizacion(odoo, cot, productos, clientes, oportunidades, vendedor, hoy, tiene_opp)
        conocidas.add(ref)
        totales[ref] = final["amount_total"]
        esperado = total_esperado(cot)
        marca = "✓" if abs(final["amount_total"] - esperado) < 0.005 and final["state"] == cot["estado"] else "✗"
        log(f"{marca} {ref}: estado {final['state']}, total {final['amount_total']:.2f} {final['currency_id'][1]}"
            f" (esperado {esperado:.2f}, {cot['estado']})")
    anular_versiones_extra(odoo, conocidas)

    if args.reiniciar:
        repo.reiniciar_transacciones()
        log("base de la compuerta reiniciada (solicitudes, bitácora, REP, aprobaciones)")
    E.registrar_maestros_locales(repo, ahora, ubicacion)
    registrar_extra_local(repo, ahora, totales)
    log(f"maestros locales registrados; aceptaciones con hora {ahora.isoformat()} − 5 min; "
        f"cotizaciones vigentes hasta {hoy} {config.hora_cierre_cotizacion}")
    if not verificar(odoo, productos, ubicacion):
        raise SystemExit("La verificación de stock no coincide con el escenario")
    log("seed completo")


if __name__ == "__main__":
    main()
