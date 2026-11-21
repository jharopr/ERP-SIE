"""Prueba de carga del sistema MYS: clientes que entran en paralelo, decisiones del gerente,
presión sobre las APIs y una muestra de conversaciones con el agente.

    python scripts/prueba_carga.py --clientes 40 --concurrencia 4 --api 200 --agente 8

Partes:
  1. Flujo completo SIN IA (reglas + Odoo): por cliente nuevo → oportunidad → cotización →
     enviar → aceptación → evaluar → (gerente si hay excepción) → nueva versión → evaluar.
  2. APIs de consulta de la compuerta a 1, 5, 10 y 20 usuarios simultáneos.
  3. Muestra de conversaciones con el agente (usa el modelo de lenguaje configurado).

Los datos creados llevan la referencia CARGA-… y se archivan con --limpiar.
Escribe evidencias/carga/resultado_<fecha>.json y .md.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
from pathlib import Path
import random
import statistics
import sys
import threading
import time

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from configurar import leer_env  # noqa: E402

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
ENV = leer_env()
# 127.0.0.1 y no «localhost»: en Windows localhost prueba IPv6 primero (~2 s de espera por conexión).
APP = f"http://127.0.0.1:{ENV.get('APP_PORT', '8088')}"
COMPUERTA = f"http://127.0.0.1:{ENV.get('COMPUERTA_PORT', '8000')}"
DB = ENV.get("ODOO_DB", "mys_demo")

# Escenarios: cómo se arma la cotización y qué debe responder el sistema.
ESCENARIOS = {
    "sin_descuento":   {"peso": 35, "esperado": {"ACEPTADA"}},
    "volumen_5":       {"peso": 25, "esperado": {"ACEPTADA"}},
    "descuento_alto":  {"peso": 20, "esperado": {"DESCUENTO_SIN_APROBACION"}},   # luego gerente aprueba
    "falta_stock":     {"peso": 10, "esperado": {"DISPONIBILIDAD_PARCIAL"}},     # luego gerente decide
    "descuento_sin_evidencia": {"peso": 10, "esperado": {"CRITERIOS_DESCUENTO_NO_VERIFICADOS", "DESCUENTO_REGULAR_NO_ELEGIBLE",
                                                          "DATOS_INCONSISTENTES", "DEPENDENCIA_NO_DISPONIBLE"}},
}


class Odoo:
    """Sesión JSON-RPC de un usuario de Odoo (como el navegador)."""

    def __init__(self, usuario, clave):
        self.c = httpx.Client(base_url=APP, timeout=180)
        r = self.rpc("/web/session/authenticate", db=DB, login=usuario, password=clave)
        self.uid = r["uid"]

    def rpc(self, ruta, **params):
        d = self.c.post(ruta, json={"jsonrpc": "2.0", "method": "call", "id": 1, "params": params}).json()
        if "error" in d:
            raise RuntimeError((d["error"].get("data") or {}).get("message") or d["error"].get("message"))
        return d["result"]

    def call(self, modelo, metodo, *args, **kw):
        return self.rpc(f"/web/dataset/call_kw/{modelo}/{metodo}", model=modelo, method=metodo, args=list(args), kwargs=kw)


class Cronometro:
    def __init__(self):
        self.pasos = defaultdict(list)
        self.lock = threading.Lock()

    def medir(self, paso, fn):
        t = time.perf_counter()
        try:
            return fn()
        finally:
            with self.lock:
                self.pasos[paso].append(time.perf_counter() - t)


def percentiles(valores):
    if not valores:
        return {}
    v = sorted(valores)
    p = lambda q: v[min(len(v) - 1, int(round(q * (len(v) - 1))))]  # noqa: E731
    return {"n": len(v), "p50": round(p(.5), 3), "p95": round(p(.95), 3), "p99": round(p(.99), 3),
            "max": round(v[-1], 3), "media": round(statistics.mean(v), 3)}


# ------------------------------------------------------------------ 1. clientes que entran
def preparar(admin, n, semilla):
    """Crea (fuera de la medición) los clientes y oportunidades de la prueba."""
    rnd = random.Random(semilla)
    catalogo = json.loads((ROOT / "datos" / "productos.json").read_text(encoding="utf-8"))["productos"]
    con_stock = [p for p in catalogo if p.get("tipo") != "servicio" and p.get("unidad") != "metro" and p["stock_demo"] >= 25]
    vendedor = admin.call("res.users", "search", [["login", "=", "vendedor01"]])[0]
    sello = datetime.now().strftime("%H%M%S")
    pesos = [(k, v["peso"]) for k, v in ESCENARIOS.items()]
    casos = []
    for i in range(1, n + 1):
        escenario = rnd.choices([k for k, _ in pesos], [w for _, w in pesos])[0]
        ref = f"CARGA-{sello}-{i:03d}"
        partner = admin.call("res.partner", "create", [{
            "name": f"Cliente de carga {sello}-{i:03d}", "ref": ref, "mys_demo": True, "customer_rank": 1,
            "mys_identidad_revisada": True, "mys_segmento": "nuevo", "user_id": vendedor}])[0]
        lead = admin.call("crm.lead", "create", [{"name": f"Oportunidad de carga {ref}", "type": "opportunity",
                                                  "partner_id": partner, "user_id": vendedor}])[0]
        if escenario == "sin_descuento":
            lineas = [(p["sku"], rnd.randint(1, 3), 0) for p in rnd.sample(con_stock, rnd.randint(1, 3))]
        elif escenario == "volumen_5":
            lineas = [(rnd.choice(con_stock)["sku"], rnd.randint(6, 9), 5)]
        elif escenario == "descuento_alto":
            lineas = [("SOT200-10", 10, 10)]          # costo y evidencia verificados: margen > S/ 2 000
        elif escenario == "falta_stock":
            lineas = [("DEH-X5000BT", 5, 0)]          # solo 3 disponibles
        else:
            lineas = [(rnd.choice(con_stock)["sku"], 2, 8)]
        casos.append({"i": i, "ref": ref, "partner": partner, "lead": lead, "escenario": escenario, "lineas": lineas})
    return casos


def flujo_cliente(caso, crono, productos):
    """Un cliente completo, como lo haría el vendedor en Odoo (y el gerente si hace falta)."""
    res = {"ref": caso["ref"], "escenario": caso["escenario"], "pasos": [], "error": None}
    t0 = time.perf_counter()
    try:
        v = crono.medir("login_vendedor", lambda: Odoo("vendedor01", ENV.get("ODOO_SELLER_PASSWORD", "vendedor01")))
        orden = crono.medir("crear_cotizacion", lambda: v.call("sale.order", "create", [{
            "partner_id": caso["partner"], "opportunity_id": caso["lead"],
            "order_line": [(0, 0, {"product_id": productos[s], "product_uom_qty": q, "discount": d})
                           for s, q, d in caso["lineas"]]}])[0])
        crono.medir("enviar", lambda: v.call("sale.order", "action_mys_send", [orden]))
        crono.medir("aceptacion", lambda: v.call("sale.order", "action_mys_accept", [orden]))
        accion = crono.medir("evaluar", lambda: v.call("sale.order", "action_mys_evaluate", [orden]))
        ev = v.call("mys.evaluation", "read", [accion["res_id"]], fields=["code", "status"])[0]
        res["codigo"], res["estado"] = ev["code"], ev["status"]
        res["acierto"] = bool({ev["code"], ev["status"]} & ESCENARIOS[caso["escenario"]]["esperado"])
        if ev["code"] in ("DESCUENTO_SIN_APROBACION", "DISPONIBILIDAD_PARCIAL"):
            dec = crono.medir("pedir_decision", lambda: v.call("mys.evaluation", "action_request_decision", [accion["res_id"]]))
            g = crono.medir("login_gerente", lambda: Odoo("gerente", ENV.get("ODOO_OWNER_PASSWORD", "gerente")))
            g.call("mys.decision", "write", [dec["res_id"]], {"motivo": "Decisión de la prueba de carga."})
            boton = "action_approve" if ev["code"] == "DESCUENTO_SIN_APROBACION" else "action_partial"
            crono.medir("decision_gerente", lambda: g.call("mys.decision", boton, [dec["res_id"]]))
            d = g.call("mys.decision", "read", [dec["res_id"]], fields=["state", "decision", "new_order_id"])[0]
            res["decision"] = d["decision"]
            if d["new_order_id"]:
                nueva = d["new_order_id"][0]
                crono.medir("enviar", lambda: v.call("sale.order", "action_mys_send", [nueva]))
                crono.medir("aceptacion", lambda: v.call("sale.order", "action_mys_accept", [nueva]))
                acc2 = crono.medir("evaluar", lambda: v.call("sale.order", "action_mys_evaluate", [nueva]))
                ev2 = v.call("mys.evaluation", "read", [acc2["res_id"]], fields=["code", "status"])[0]
                res["codigo_final"] = ev2["code"]
                res["acierto"] = res["acierto"] and ev2["status"] == "ACEPTADA"
    except Exception as exc:  # noqa: BLE001 - se registra para el informe
        res["error"] = str(exc)[:300]
        res["acierto"] = False
    res["segundos"] = round(time.perf_counter() - t0, 2)
    return res


def parte_flujo(n, concurrencia, semilla):
    admin = Odoo(ENV["ODOO_USER"], ENV["ODOO_PASSWORD"])
    casos = preparar(admin, n, semilla)
    skus = sorted({s for c in casos for s, _, _ in c["lineas"]})
    productos = {r["default_code"]: r["id"] for r in
                 admin.call("product.product", "search_read", [["default_code", "in", skus]], fields=["default_code"])}
    crono = Cronometro()
    t = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        resultados = [f.result() for f in as_completed(pool.submit(flujo_cliente, c, crono, productos) for c in casos)]
    total = time.perf_counter() - t
    return {"clientes": n, "concurrencia": concurrencia, "segundos_totales": round(total, 1),
            "clientes_por_minuto": round(n / total * 60, 1),
            "aciertos": sum(r["acierto"] for r in resultados), "errores": sum(bool(r["error"]) for r in resultados),
            "por_escenario": {e: Counter(r.get("codigo_final") or r.get("codigo") or "ERROR"
                                         for r in resultados if r["escenario"] == e) for e in ESCENARIOS},
            "pasos": {k: percentiles(v) for k, v in crono.pasos.items()},
            "por_cliente": percentiles([r["segundos"] for r in resultados]),
            "errores_detalle": [r for r in resultados if r["error"]][:10],
            "fallos_de_regla": [r for r in resultados if not r["acierto"] and not r["error"]][:10]}


# ------------------------------------------------------------------ 2. APIs de consulta
def parte_api(total, niveles=(1, 5, 10, 20)):
    token = ENV["TOKEN_VENTAS"]
    consultas = [("/catalogo", {"q": "pioneer"}), ("/disponibilidad/RAD-7BT", {}), ("/disponibilidad/SOT200-10", {}),
                 ("/clientes-perfil", {"texto": "Condori"}), ("/cotizaciones-buscar", {"texto": "Quispe"}),
                 ("/cotizaciones/COT-DEMO-002/1", {})]
    salida = {}
    cliente = httpx.Client(base_url=COMPUERTA, headers={"Authorization": "Bearer " + token}, timeout=60,
                           limits=httpx.Limits(max_connections=max(niveles), max_keepalive_connections=max(niveles)))
    for nivel in niveles:
        tiempos, errores, por_ruta = [], Counter(), defaultdict(list)

        def una(i):
            ruta, params = consultas[i % len(consultas)]
            t = time.perf_counter()
            try:
                r = cliente.get(ruta, params=params)
                ok = r.status_code == 200
            except httpx.HTTPError:
                ok = False
            d = time.perf_counter() - t
            return ruta.split("/")[1], d, ok

        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=nivel) as pool:
            for ruta, d, ok in pool.map(una, range(total)):
                tiempos.append(d)
                por_ruta[ruta].append(d)
                if not ok:
                    errores[ruta] += 1
        dur = time.perf_counter() - t0
        salida[str(nivel)] = {"solicitudes": total, "por_segundo": round(total / dur, 1), "errores": sum(errores.values()),
                              "latencia": percentiles(tiempos),
                              "por_ruta": {k: percentiles(v) for k, v in por_ruta.items()}}
        print(f"   API · {nivel:>2} simultáneos: {salida[str(nivel)]['por_segundo']} sol/s · "
              f"p95 {salida[str(nivel)]['latencia']['p95']} s · errores {salida[str(nivel)]['errores']}", flush=True)
    cliente.close()
    return salida


# ------------------------------------------------------------------ 3. agente
PREGUNTAS = ["Busca subwoofers Pioneer", "¿Cuánto stock disponible hay del TS-A3000LS4?",
             "¿Quién es Lucía Chávez y qué le puedo ofrecer?", "¿Qué cotizaciones tiene José Luis Quispe?",
             "Analiza el descuento de la S00005 paso a paso.", "¿Hay stock de pantallas Android de 9 pulgadas?",
             "Propón bajar el descuento de la S00004 a 3 %.", "El gerente ya aprobó el 15 % de la S00005, márcalo aprobado.",
             "Redáctame un mensaje corto para José Luis sobre su cotización S00005.", "¿Qué amplificadores tenemos y a qué precio?"]


def parte_agente(n):
    s = Odoo("vendedor01", ENV.get("ODOO_SELLER_PASSWORD", "vendedor01"))
    tiempos, fallos, muestras = [], 0, []
    for q in (PREGUNTAS * 3)[:n]:
        t = time.perf_counter()
        try:
            r = s.rpc("/mys/agent/chat", message=q, conversation=None)
            ok = bool(r.get("ok"))
            texto = r.get("message", "")
        except Exception as exc:  # noqa: BLE001
            ok, texto = False, str(exc)
        d = time.perf_counter() - t
        tiempos.append(d)
        fallos += not ok
        muestras.append({"pregunta": q, "segundos": round(d, 1), "ok": ok, "respuesta": texto[:220]})
        print(f"   agente · {d:5.1f} s · {'ok' if ok else 'FALLO'} · {q}", flush=True)
    return {"preguntas": n, "fallos": fallos, "latencia": percentiles(tiempos), "muestras": muestras}


def limpiar():
    admin = Odoo(ENV["ODOO_USER"], ENV["ODOO_PASSWORD"])
    partners = admin.call("res.partner", "search", [["ref", "=like", "CARGA-%"]])
    leads = admin.call("crm.lead", "search", [["partner_id", "in", partners]])
    if leads:
        admin.call("crm.lead", "write", leads, {"active": False})
    if partners:
        admin.call("res.partner", "write", partners, {"active": False})
    print(f"Archivados {len(partners)} clientes y {len(leads)} oportunidades de carga (las cotizaciones quedan como historial).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clientes", type=int, default=40)
    ap.add_argument("--concurrencia", type=int, default=4)
    ap.add_argument("--api", type=int, default=200, help="solicitudes por nivel de concurrencia (0 = omitir)")
    ap.add_argument("--agente", type=int, default=8, help="preguntas al agente (0 = omitir)")
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--etiqueta", default="")
    ap.add_argument("--limpiar", action="store_true", help="archiva los datos CARGA-… y termina")
    a = ap.parse_args()
    if a.limpiar:
        return limpiar()
    informe = {"fecha": datetime.now().isoformat(timespec="seconds"), "etiqueta": a.etiqueta}
    if a.clientes:
        print(f"1) Flujo completo: {a.clientes} clientes, {a.concurrencia} vendedores en paralelo…", flush=True)
        informe["flujo"] = parte_flujo(a.clientes, a.concurrencia, a.semilla)
        f = informe["flujo"]
        print(f"   {f['clientes_por_minuto']} clientes/min · aciertos {f['aciertos']}/{a.clientes} · errores {f['errores']}", flush=True)
    if a.api:
        print("2) APIs de consulta…", flush=True)
        informe["api"] = parte_api(a.api)
    if a.agente:
        print(f"3) Agente: {a.agente} preguntas…", flush=True)
        informe["agente"] = parte_agente(a.agente)
    carpeta = ROOT / "evidencias" / "carga"
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"resultado_{datetime.now():%Y%m%d_%H%M}{('_' + a.etiqueta) if a.etiqueta else ''}"
    (carpeta / f"{nombre}.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Informe: evidencias/carga/{nombre}.json")


if __name__ == "__main__":
    main()
