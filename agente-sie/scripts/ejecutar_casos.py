"""Ejecuta los 6 casos PC3 contra la compuerta, SIN modelo de lenguaje, y escribe evidencias.

    python scripts/ejecutar_casos.py                 # contra http://localhost:8000 (Docker levantado)
    python scripts/ejecutar_casos.py --caida bandera # F01 con la bandera ADMIN en vez de detener Odoo
    python scripts/ejecutar_casos.py --simulado      # sin Docker: app en proceso + Odoo simulado (etiquetado)

Requisitos: Python 3.10+. Modo real: solo biblioteca estándar y `docker compose`.
Modo simulado: fastapi, httpx y pydantic (compuerta/requirements-dev.txt).
Antes de ejecutar reinicia la base de la compuerta y refresca el seed (vigencias del día).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Consolas de Windows (cp1252) no imprimen «✓»: se fuerza UTF-8 sin abortar.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
EVID = RAIZ / "evidencias"
CASOS = {c["id"]: c for c in json.loads((RAIZ / "datos_prueba" / "casos_pc3.json").read_text(encoding="utf-8"))["casos"]}
SKUS = ["RAD-7BT", "RAD-10X"]


def leer_env():
    archivo = RAIZ / ".env"
    if not archivo.exists():
        raise SystemExit("Falta .env (cp .env.example .env)")
    valores = {}
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if linea.strip() and not linea.lstrip().startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            valores[k.strip()] = v.strip()
    return valores


class Real:
    etiqueta = "Docker: Odoo 18 + compuerta reales"

    def __init__(self, base, tokens, caida):
        self.base, self.tokens, self.caida = base.rstrip("/"), tokens, caida

    def llamar(self, metodo, ruta, rol="VENTAS", json_=None, agente=None, cabeceras=None):
        datos = json.dumps(json_).encode() if json_ is not None else (b"" if metodo == "POST" else None)
        req = urllib.request.Request(self.base + ruta, data=datos, method=metodo)
        req.add_header("Authorization", f"Bearer {self.tokens[rol]}")
        req.add_header("Content-Type", "application/json")
        if agente:
            req.add_header("X-Actor-Type", "AGENTE")
            req.add_header("X-Agent-Tool", agente)
        for k, v in (cabeceras or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            cuerpo = e.read()
            return e.code, json.loads(cuerpo) if cuerpo else None

    def compose(self, *args):
        subprocess.run(["docker", "compose", *args], cwd=RAIZ, check=True)

    def preparar(self):
        print("· reiniciando compuerta y refrescando seed…")
        self.compose("exec", "-T", "compuerta", "python", "/seed/seed_odoo.py", "--reiniciar")

    def odoo_caido(self, caido):
        if self.caida == "bandera":
            self.llamar("POST", "/admin/simulacion", "ADMIN", {"odoo_caido": caido})
            return
        self.compose("stop" if caido else "start", "odoo")
        if not caido:
            for _ in range(60):
                s, b = self.llamar("GET", "/salud")
                if s == 200 and b["odoo"]["disponible"]:
                    return
                time.sleep(3)
            raise SystemExit("Odoo no volvió a estar disponible")


class Simulado:
    etiqueta = "SIMULADO: compuerta en proceso + Odoo simulado en memoria (no reemplaza la ejecución con Docker)"

    def __init__(self):
        import tempfile
        sys.path.insert(0, str(RAIZ / "compuerta"))
        sys.path.insert(0, str(RAIZ / "compuerta" / "tests"))
        from fastapi.testclient import TestClient
        from conftest import TOKENS, UBICACION_ODOO, OdooSimulado
        from app import escenario as E
        from app.config import Config, ahora_lima
        from app.main import crear_app
        from app.repositorio import Repositorio

        ahora = ahora_lima()
        db = str(Path(tempfile.mkdtemp()) / "compuerta.sqlite3")
        config = Config("http://simulado", "mys_demo", "admin", "x", 5, TOKENS["VENTAS"], TOKENS["GERENCIA"],
                        TOKENS["ADMIN"], db, E.COMPANY_ID, E.UBICACION_ID, "23:59", 24, "REP-PC3")
        self.odoo = OdooSimulado(fecha_vigencia=ahora.date().isoformat())
        app = crear_app(config, self.odoo)
        E.registrar_maestros_locales(Repositorio(db), ahora, UBICACION_ODOO)
        self.cliente, self.tokens = TestClient(app), TOKENS

    def llamar(self, metodo, ruta, rol="VENTAS", json_=None, agente=None, cabeceras=None):
        h = {"Authorization": f"Bearer {self.tokens[rol]}", **(cabeceras or {})}
        if agente:
            h.update({"X-Actor-Type": "AGENTE", "X-Agent-Tool": agente})
        r = self.cliente.request(metodo, ruta, headers=h, json=json_)
        return r.status_code, r.json() if r.content else None

    def preparar(self):
        pass

    def odoo_caido(self, caido):
        self.odoo.caido = caido


def stock(t):
    return {sku: t.llamar("GET", f"/disponibilidad/{sku}")[1] for sku in SKUS}


def sin_hora(s):
    return {k: {c: v for c, v in d.items() if c != "observed_at"} for k, d in s.items()}


def bitacora(t, correlation_id):
    return t.llamar("GET", f"/bitacora?correlation_id={correlation_id}")[1]["eventos"]


def comparar(obs, esp, campos=("status", "code", "responsible_role", "total", "order_id", "conditions")):
    return {c: {"esperado": esp[c], "observado": obs.get(c), "ok": obs.get(c) == esp[c]} for c in campos if c in esp}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--simulado", action="store_true")
    ap.add_argument("--caida", choices=["docker", "bandera"], default="docker")
    ap.add_argument("--url", default=None)
    args = ap.parse_args()
    if args.simulado:
        t = Simulado()
    else:
        env = leer_env()
        t = Real(args.url or f"http://localhost:{env.get('COMPUERTA_PORT', '8000')}",
                 {"VENTAS": env["TOKEN_VENTAS"], "GERENCIA": env["TOKEN_GERENCIA"], "ADMIN": env["TOKEN_ADMIN"]}, args.caida)
    t.preparar()
    inicio = datetime.now(timezone.utc).isoformat()
    antes = stock(t)
    resultados = []

    def registrar(caso_id, entrada, respuesta, chequeos, extra=None, correlation=None):
        ok = all(v["ok"] for v in chequeos.values())
        evidencia = {"caso": caso_id, "titulo": CASOS[caso_id]["titulo"], "modo": t.etiqueta,
                     "ejecutado_utc": datetime.now(timezone.utc).isoformat(), "entrada": entrada,
                     "respuesta": respuesta, "chequeos": chequeos, "ok": ok, **(extra or {}),
                     "bitacora": bitacora(t, correlation) if correlation else None}
        (EVID / f"{caso_id}.json").write_text(json.dumps(evidencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        resultados.append((caso_id, chequeos, ok))
        print(f"{'✓' if ok else '✗'} {caso_id}")

    EVID.mkdir(exist_ok=True)
    # PC3-N01
    c = CASOS["PC3-N01"]
    s, r = t.llamar("POST", "/solicitudes", json_=c["solicitud"])
    n01 = r
    registrar("PC3-N01", c["solicitud"], r, {**comparar(r["respuesta"], c["esperado"]),
              "senales": {"esperado": 0, "observado": len(r["senales_reposicion"]), "ok": not r["senales_reposicion"]}},
              correlation="COR-PC3-001")
    # PC3-E01 + escalamiento y decisión del dueño
    c = CASOS["PC3-E01"]
    s, r = t.llamar("POST", "/solicitudes", json_=c["solicitud"])
    senal = (r["senales_reposicion"] or [{}])[0]
    _, esc = t.llamar("POST", "/escalamientos", json_={"tipo": "REPOSICION", "request_id": "SOL-PC3-E01",
                                                         "resumen": "Faltan 2 RAD-10X"}, agente="escalar_al_dueno")
    _, dec = t.llamar("POST", f"/escalamientos/{esc['escalation_id']}/decision", "GERENCIA",
                      {"decision": c["decision_dueno"]["decision"], "motivo": c["decision_dueno"]["motivo"]})
    chequeos = comparar(r["respuesta"], c["esperado"])
    chequeos.update({f"senal.{k}": {"esperado": v, "observado": senal.get(k), "ok": senal.get(k) == v}
                     for k, v in c["esperado"]["senal"].items()})
    chequeos["decision_dueno"] = {"esperado": "OFRECER_PARCIAL", "observado": dec["resultado"]["decision"],
                                  "ok": dec["resultado"]["decision"] == "OFRECER_PARCIAL"}
    registrar("PC3-E01", c["solicitud"], r, chequeos, {"escalamiento": esc, "decision_dueno": dec}, "COR-PC3-002")
    # PC3-E02
    c = CASOS["PC3-E02"]
    s, r = t.llamar("POST", "/solicitudes", json_=c["solicitud"])
    _, esc = t.llamar("POST", "/escalamientos", json_={"tipo": "DESCUENTO", "request_id": "SOL-PC3-E02",
                                                         "resumen": "Cliente pide 10 %"}, agente="escalar_al_dueno")
    eventos = t.llamar("GET", "/bitacora?request_id=SOL-PC3-E02")[1]["eventos"]
    chequeos = comparar(r["respuesta"], c["esperado"])
    sin_i05 = not any(e["interface_id"] == "I05" for e in eventos)
    chequeos["sin_consulta_stock"] = {"esperado": True, "observado": sin_i05, "ok": sin_i05}
    chequeos["aprobacion_aplicaria_a_v3"] = {"esperado": 3, "observado": esc.get("version_aprobacion"),
                                             "ok": esc.get("version_aprobacion") == 3}
    registrar("PC3-E02", c["solicitud"], r, chequeos, {"escalamiento": esc}, "COR-PC3-001")
    # PC3-F01
    c = CASOS["PC3-F01"]
    t.odoo_caido(True)
    try:
        s, r = t.llamar("POST", "/solicitudes", json_=c["solicitud"])
    finally:
        t.odoo_caido(False)
    s2, r2 = t.llamar("POST", "/solicitudes/SOL-PC3-F01/reanudar")
    chequeos = comparar(r["respuesta"], c["esperado"])
    chequeos.update({f"reanudar.{k}": v for k, v in comparar(r2["respuesta"], c["esperado_tras_reanudar"]).items()})
    registrar("PC3-F01", c["solicitud"], r, chequeos, {"modo_caida": "simulado" if args.simulado else args.caida,
                                                       "respuesta_tras_reanudar": r2}, "COR-PC3-004")
    # PC3-I01
    s, r = t.llamar("POST", "/solicitudes", json_=CASOS["PC3-N01"]["solicitud"])
    eventos = t.llamar("GET", "/bitacora?request_id=SOL-PC3-N01")[1]["eventos"]
    recibidas = sum(e["event_type"] == "RECIBIDA" for e in eventos)
    registrar("PC3-I01", CASOS["PC3-N01"]["solicitud"], r, {
        "misma_respuesta": {"esperado": True, "observado": r == n01, "ok": r == n01},
        "evento": {"esperado": "REINTENTO", "observado": eventos[-1]["event_type"], "ok": eventos[-1]["event_type"] == "REINTENTO"},
        "una_sola_solicitud": {"esperado": 1, "observado": recibidas, "ok": recibidas == 1}}, correlation="COR-PC3-001")
    # PC3-A01 (nivel compuerta; la respuesta del modelo se documenta en evidencias/agente_*.md)
    c = CASOS["PC3-A01"]
    s, r = t.llamar("POST", "/aprobaciones", json_=c["intento_con_token_ventas"], agente="escalar_al_dueno",
                    cabeceras={"X-Correlation-Id": "COR-PC3-001"})
    eventos = bitacora(t, "COR-PC3-001")
    denegada = [e for e in eventos if e["event_type"] == "DENEGADA"]
    _, e02 = t.llamar("GET", "/solicitudes/SOL-PC3-E02")
    registrar("PC3-A01", c["intento_con_token_ventas"], {"http": s, "cuerpo": r}, {
        "http_403": {"esperado": 403, "observado": s, "ok": s == 403},
        "evento_denegada": {"esperado": True, "observado": bool(denegada), "ok": bool(denegada)},
        "E02_sigue_rechazada": {"esperado": "DESCUENTO_SIN_APROBACION", "observado": e02["respuesta"]["code"],
                                "ok": e02["respuesta"]["code"] == "DESCUENTO_SIN_APROBACION"}})

    despues = stock(t)
    intacto = sin_hora(antes) == sin_hora(despues)
    ordenes_nulas = all(json.loads((EVID / f"{cid}.json").read_text(encoding="utf-8"))["respuesta"].get("respuesta", {}).get("order_id") is None
                        for cid in ("PC3-N01", "PC3-E01", "PC3-E02", "PC3-F01", "PC3-I01"))
    (EVID / "stock_antes_despues.json").write_text(json.dumps({"antes": antes, "despues": despues, "intacto": intacto},
                                                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_ok = sum(ok for _, _, ok in resultados)
    filas = []
    for cid, chequeos, ok in resultados:
        esperado = "; ".join(f"{k}={json.dumps(v['esperado'], ensure_ascii=False)}" for k, v in chequeos.items())
        observado = "; ".join(f"{k}={json.dumps(v['observado'], ensure_ascii=False)}" for k, v in chequeos.items())
        filas.append(f"| {cid} | {esperado} | {observado} | {'✓' if ok else '✗'} |")
    disponibles = ", ".join(f"{k}: disp. {v['disponible']}" for k, v in despues.items())
    md = ["# Resultados PC3 · esperado vs observado", "",
          f"- **Modo:** {t.etiqueta}", f"- **Ejecución (UTC):** {inicio}",
          f"- **Equipo:** Python {platform.python_version()} · {platform.system()} {platform.release()}",
          f"- **Casos:** {total_ok}/{len(resultados)} ✓",
          f"- **Stock intacto antes/después:** {'✓' if intacto else '✗'} ({disponibles})",
          f"- **order_id null en todas las respuestas:** {'✓' if ordenes_nulas else '✗'}",
          "- Generado por `scripts/ejecutar_casos.py` sin modelo de lenguaje. La conversación del agente está en `agente_*.md`.",
          "", "| Caso | Esperado | Observado | ✓/✗ |", "|---|---|---|---|", *filas, ""]
    (EVID / "resultados.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\n{total_ok}/{len(resultados)} casos ✓ · stock intacto: {intacto} · order_id null: {ordenes_nulas}")
    print(f"Evidencias en {EVID}")
    sys.exit(0 if total_ok == len(resultados) and intacto and ordenes_nulas else 1)


if __name__ == "__main__":
    main()
