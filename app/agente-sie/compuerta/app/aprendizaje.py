"""Aprendizaje del Agente SIE a partir de resultados CONFIRMADOS por personas.

No reentrena el modelo ni cambia reglas. Acumula conocimiento auditable:
  - Precedentes del gerente: cada decisión registrada (descuento o reposición) con el descuento
    pedido, el nivel del cliente, las categorías y el motivo. Sirve como contexto, nunca decide.
  - Alias de productos: frases del vendedor («el kit grande») → SKU, aprendidas SOLO de propuestas
    que el vendedor aplicó en Odoo (confirmación humana).
  - Desempeño: herramientas más usadas, propuestas aplicadas vs descartadas, tasa de aprobación.

GET /aprendizaje/precedentes?tipo=&descuento=&cliente=  casos parecidos y qué decidió el gerente
GET /aprendizaje/resumen                                  qué aprendió el agente hasta hoy
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import threading
import time
import unicodedata

from fastapi import Depends, HTTPException, Query

from .odoo_cliente import DependenciaNoDisponible

DDL = """
CREATE TABLE IF NOT EXISTS conocimiento_casos (
    escalation_id TEXT PRIMARY KEY, tipo TEXT NOT NULL, quotation_id TEXT, version INTEGER,
    cliente_ref TEXT, nivel TEXT, descuento_max REAL, total TEXT, categorias TEXT,
    decision TEXT NOT NULL, motivo TEXT, decidido_en TEXT, aprendido_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alias_productos (
    texto TEXT PRIMARY KEY, sku TEXT NOT NULL, confirmaciones INTEGER NOT NULL DEFAULT 1, ultimo_uso TEXT NOT NULL
);
"""
NIVELES = {"nuevo": "Nuevo", "ocasional": "Ocasional", "frecuente": "Frecuente", "mayorista": "Mayorista"}


def normalizar(texto):
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower()) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.split())


def _categorias_catalogo():
    ruta = Path(os.environ.get("CATALOGO_PATH", "/catalogo/productos.json"))
    try:
        return {p["sku"]: p["categoria"] for p in json.loads(ruta.read_text(encoding="utf-8"))["productos"]}
    except (OSError, ValueError, KeyError):
        return {}


class Aprendizaje:
    """Conocimiento acumulado. Se sincroniza de forma incremental y como máximo cada 30 s."""

    def __init__(self, config, repo, fuente, reloj):
        self.config, self.repo, self.fuente, self.reloj = config, repo, fuente, reloj
        self._ultima = 0.0
        self._lock = threading.Lock()
        with repo.conexion() as db:
            db.executescript(DDL)

    # ------------------------------------------------------------ alias (frases → SKU)
    def alias(self, texto):
        clave = normalizar(texto)
        with self.repo.conexion() as db:
            f = db.execute("SELECT sku FROM alias_productos WHERE texto=?", (clave,)).fetchone()
            if f:
                db.execute("UPDATE alias_productos SET ultimo_uso=? WHERE texto=?", (self.reloj().isoformat(), clave))
        return f["sku"] if f else None

    def confirmar_alias(self, pares):
        """pares: [(texto dicho por el vendedor, sku)] de una propuesta APLICADA por una persona."""
        ahora = self.reloj().isoformat()
        with self.repo.conexion() as db:
            for texto, sku in pares:
                clave = normalizar(texto)
                if not clave or clave == normalizar(sku):
                    continue
                db.execute("INSERT INTO alias_productos(texto,sku,ultimo_uso) VALUES(?,?,?) ON CONFLICT(texto) DO UPDATE SET "
                           "confirmaciones = CASE WHEN alias_productos.sku = excluded.sku THEN alias_productos.confirmaciones + 1 ELSE 1 END, "
                           "sku = excluded.sku, ultimo_uso = excluded.ultimo_uso", (clave, sku, ahora))

    # ------------------------------------------------------------ precedentes
    def sincronizar(self, forzar=False):
        """Incorpora las decisiones nuevas del gerente con su contexto (descuento, nivel, categorías)."""
        if not forzar and time.monotonic() - self._ultima < 30:
            return
        with self._lock:
            self._ultima = time.monotonic()
            with self.repo.conexion() as db:
                nuevos = db.execute(
                    "SELECT e.* FROM escalamientos e LEFT JOIN conocimiento_casos c ON c.escalation_id = e.escalation_id "
                    "WHERE e.estado='DECIDIDO' AND e.company_id=? AND c.escalation_id IS NULL", (self.config.company_id,)).fetchall()
            if not nuevos:
                return
            categorias = _categorias_catalogo()
            niveles = {}
            for e in nuevos:
                descuento, cliente, cats = None, None, []
                try:
                    versiones = self.fuente.versiones_cotizacion(e["quotation_id"]) if e["quotation_id"] else []
                    v = next((x for x in versiones if x["version"] == e["quotation_version"]), None)
                    if v:
                        descuento = max((l["discount_pct"] for l in v["lines"]), default=0.0)
                        cliente = v["customer_ref"]
                        cats = sorted({categorias.get(l["sku"], "Otros") for l in v["lines"] if l["sku"]})
                    if cliente and cliente not in niveles and hasattr(self.fuente, "perfil_cliente"):
                        perfil = self.fuente.perfil_cliente(cliente)
                        niveles[cliente] = perfil[0]["mys_nivel"] if perfil else None
                except DependenciaNoDisponible:
                    return  # se reintenta en la próxima consulta
                with self.repo.conexion() as db:
                    if e["tipo"] == "DESCUENTO":
                        m = db.execute("SELECT motivo FROM aprobaciones WHERE quotation_id=? AND quotation_version=? "
                                       "ORDER BY approval_id DESC LIMIT 1", (e["quotation_id"], e["version_aprobacion"])).fetchone()
                    else:
                        m = db.execute("SELECT motivo FROM decisiones_reposicion WHERE signal_id=? ORDER BY decision_id DESC LIMIT 1",
                                       (e["signal_id"],)).fetchone()
                    db.execute("INSERT OR IGNORE INTO conocimiento_casos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               (e["escalation_id"], e["tipo"], e["quotation_id"], e["quotation_version"], cliente,
                                niveles.get(cliente), descuento, e["total"], ", ".join(cats), e["decision"],
                                m["motivo"] if m else None, e["decided_at"], self.reloj().isoformat()))

    def precedentes(self, tipo="DESCUENTO", descuento=None, nivel=None, limite=5):
        self.sincronizar()
        with self.repo.conexion() as db:
            filas = [dict(f) for f in db.execute("SELECT * FROM conocimiento_casos WHERE tipo=? ORDER BY decidido_en DESC",
                                                 (tipo,)).fetchall()]
        criterio, similares = [], filas
        if descuento is not None:
            similares = [f for f in similares if f["descuento_max"] is not None and abs(f["descuento_max"] - descuento) <= 2.5]
            criterio.append(f"descuento entre {max(0, descuento - 2.5):g} % y {descuento + 2.5:g} %")
        if nivel:
            con_nivel = [f for f in similares if f["nivel"] == nivel]
            if len(con_nivel) >= 2:
                similares = con_nivel
                criterio.append(f"cliente {NIVELES.get(nivel, nivel).lower()}")
            else:
                criterio.append(f"(pocos casos de cliente {NIVELES.get(nivel, nivel).lower()}: se amplió a todos los niveles)")
        decisiones = Counter(f["decision"] for f in similares)
        aprobados = [f["descuento_max"] for f in similares if f["decision"] == "APROBADA" and f["descuento_max"] is not None]
        return {"tipo": tipo, "criterio": ", ".join(criterio) or "todos los casos", "casos_parecidos": len(similares),
                "decisiones": dict(decisiones),
                "tasa_aprobacion_pct": round(decisiones.get("APROBADA", 0) / len(similares) * 100, 1)
                if similares and tipo == "DESCUENTO" else None,
                "descuento_promedio_aprobado": round(sum(aprobados) / len(aprobados), 1) if aprobados else None,
                "ejemplos": [{"cotizacion": f"{f['quotation_id']} v{f['version']}", "cliente": f["cliente_ref"],
                              "nivel": NIVELES.get(f["nivel"], f["nivel"]), "descuento": f["descuento_max"],
                              "categorias": f["categorias"], "decision": f["decision"], "motivo": f["motivo"],
                              "fecha": (f["decidido_en"] or "")[:10]} for f in similares[:limite]],
                "nota": "Precedentes reales del gerente. Son contexto para decidir; no autorizan nada."}

    def resumen(self):
        self.sincronizar()
        with self.repo.conexion() as db:
            casos = [dict(f) for f in db.execute("SELECT * FROM conocimiento_casos").fetchall()]
            alias = [dict(f) for f in db.execute("SELECT texto, sku, confirmaciones FROM alias_productos "
                                                  "ORDER BY confirmaciones DESC, ultimo_uso DESC LIMIT 10").fetchall()]
            propuestas = Counter(f["estado"] for f in db.execute("SELECT estado FROM propuestas_cambio").fetchall()) \
                if db.execute("SELECT name FROM sqlite_master WHERE name='propuestas_cambio'").fetchone() else Counter()
            herramientas = Counter(f["code"] for f in db.execute(
                "SELECT code FROM audit WHERE event_type='HERRAMIENTA_AGENTE'").fetchall())
        por_nivel = defaultdict(Counter)
        por_banda = defaultdict(Counter)
        for c in casos:
            if c["tipo"] != "DESCUENTO":
                continue
            por_nivel[NIVELES.get(c["nivel"], "Sin perfil")][c["decision"]] += 1
            d = c["descuento_max"] or 0
            banda = "hasta 8 %" if d <= 8 else ("8 % a 12 %" if d <= 12 else "más de 12 %")
            por_banda[banda][c["decision"]] += 1
        resueltas = propuestas.get("APLICADA", 0) + propuestas.get("DESCARTADA", 0)
        return {"casos_aprendidos": len(casos),
                "descuentos_por_nivel": {k: dict(v) for k, v in por_nivel.items()},
                "descuentos_por_banda": {k: dict(v) for k, v in por_banda.items()},
                "reposicion": dict(Counter(c["decision"] for c in casos if c["tipo"] == "REPOSICION")),
                "propuestas": dict(propuestas),
                "propuestas_aplicadas_pct": round(propuestas.get("APLICADA", 0) / resueltas * 100, 1) if resueltas else None,
                "alias_aprendidos": alias, "herramientas_mas_usadas": dict(herramientas.most_common(8))}


def registrar_aprendizaje(app, config, repo, exigir, fuente, reloj):
    motor = Aprendizaje(config, repo, fuente, reloj)
    app.state.aprendizaje = motor

    @app.get("/aprendizaje/precedentes")
    def precedentes(tipo: str = Query(default="DESCUENTO", pattern=r"^(DESCUENTO|REPOSICION)$"),
                    descuento: float | None = Query(default=None, ge=0, le=100),
                    cliente: str | None = Query(default=None, max_length=100),
                    quien=Depends(exigir("VENTAS", "GERENCIA"))):
        nivel = None
        if cliente and hasattr(fuente, "perfil_cliente"):
            try:
                perfil = fuente.perfil_cliente(cliente)
            except DependenciaNoDisponible:
                raise HTTPException(503, "Odoo no responde; no se pudo leer el perfil del cliente.")
            nivel = perfil[0]["mys_nivel"] if perfil else None
        respuesta = motor.precedentes(tipo, descuento, nivel)
        if cliente:
            respuesta["nivel_del_cliente"] = NIVELES.get(nivel, nivel) if nivel else "sin perfil"
        return respuesta

    @app.get("/aprendizaje/resumen")
    def resumen(quien=Depends(exigir("VENTAS", "GERENCIA", "ADMIN"))):
        return motor.resumen()

    return motor
