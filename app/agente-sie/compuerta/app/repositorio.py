"""Base local de la compuerta (SQLite).

Comparte archivo con las tablas del motor (`requests`, `audit`) y añade las
extensiones del informe: aceptaciones (C03 ext.), aprobaciones (C06), actores,
política, mapa de IDs, señales REP, decisiones del dueño y eventos del agente.
La bitácora nunca guarda nombres, DNI ni teléfonos: solo identificadores.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import sqlite3

# Misma definición que crea el motor; se repite para poder escribir eventos propios
# en la misma tabla y mantener un solo orden (event_id) en la bitácora.
DDL = """
CREATE TABLE IF NOT EXISTS requests (
    company_id TEXT NOT NULL, request_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL, quotation_id TEXT NOT NULL,
    quotation_version INTEGER NOT NULL, opportunity_id TEXT NOT NULL,
    response_json TEXT NOT NULL,
    PRIMARY KEY (company_id, request_id),
    UNIQUE (company_id, quotation_id, quotation_version)
);
CREATE TABLE IF NOT EXISTS audit (
    event_id INTEGER PRIMARY KEY, company_id TEXT, request_id TEXT, correlation_id TEXT,
    actor_id TEXT NOT NULL, interface_id TEXT NOT NULL,
    event_type TEXT NOT NULL, code TEXT NOT NULL, occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_ext (
    event_id INTEGER PRIMARY KEY REFERENCES audit(event_id),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('HUMANO','AGENTE','SISTEMA')),
    detalle TEXT
);
CREATE TABLE IF NOT EXISTS solicitudes_payload (
    company_id TEXT NOT NULL, request_id TEXT NOT NULL, payload_json TEXT NOT NULL,
    PRIMARY KEY (company_id, request_id)
);
CREATE TABLE IF NOT EXISTS actores (
    actor_id TEXT PRIMARY KEY, rol TEXT NOT NULL, company_id TEXT NOT NULL,
    opportunities_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS politica (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS clientes_ext (
    ref TEXT PRIMARY KEY, identity_reviewed INTEGER NOT NULL, segmento TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mapa_ids (
    tipo TEXT NOT NULL, externo TEXT NOT NULL, odoo TEXT NOT NULL,
    PRIMARY KEY (tipo, externo)
);
CREATE TABLE IF NOT EXISTS aceptaciones (
    acceptance_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, quotation_id TEXT NOT NULL,
    quotation_version INTEGER NOT NULL, customer_id TEXT NOT NULL, total TEXT NOT NULL,
    accepted_at TEXT NOT NULL, registrada_por TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS aprobaciones (
    approval_id INTEGER PRIMARY KEY, company_id TEXT NOT NULL, quotation_id TEXT NOT NULL,
    quotation_version INTEGER NOT NULL, total TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('APROBADA','RECHAZADA')),
    approver_id TEXT NOT NULL, approved_at TEXT NOT NULL, valid_until TEXT NOT NULL,
    motivo TEXT NOT NULL, correlation_id TEXT
);
CREATE TABLE IF NOT EXISTS senales_rep (
    signal_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL, sku TEXT NOT NULL, requested INTEGER NOT NULL,
    available INTEGER NOT NULL, faltante INTEGER NOT NULL,
    automatic_action INTEGER NOT NULL DEFAULT 0 CHECK (automatic_action = 0),
    estado TEXT NOT NULL DEFAULT 'ABIERTA', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisiones_reposicion (
    decision_id INTEGER PRIMARY KEY, signal_id TEXT NOT NULL REFERENCES senales_rep(signal_id),
    decision TEXT NOT NULL, motivo TEXT NOT NULL, actor_id TEXT NOT NULL, decided_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS escalamientos (
    escalation_id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('DESCUENTO','REPOSICION','DEPENDENCIA','IDEMPOTENCIA')),
    request_id TEXT, correlation_id TEXT NOT NULL, quotation_id TEXT, quotation_version INTEGER,
    version_aprobacion INTEGER, total TEXT, signal_id TEXT, destinatario TEXT NOT NULL,
    resumen_hash TEXT NOT NULL, created_at TEXT NOT NULL, plazo_hasta TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ESPERANDO_DECISION', decision TEXT, decided_at TEXT
);
CREATE TABLE IF NOT EXISTS simulacion (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
"""


class Repositorio:
    def __init__(self, database: str):
        self.database = database
        with self.conexion() as db:
            db.executescript(DDL)

    @contextmanager
    def conexion(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ---- eventos fuera del motor (misma tabla audit) ------------------------------------
    @staticmethod
    def registrar_evento(db, *, company_id, request_id, correlation_id, actor_id, actor_type,
                         interface_id, event_type, code, occurred_at, detalle=None):
        cur = db.execute(
            "INSERT INTO audit(company_id,request_id,correlation_id,actor_id,interface_id,event_type,code,occurred_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (company_id, request_id, correlation_id, actor_id, interface_id, event_type, code, occurred_at))
        db.execute("INSERT INTO audit_ext(event_id,actor_type,detalle) VALUES(?,?,?)",
                   (cur.lastrowid, actor_type, json.dumps(detalle, ensure_ascii=False, sort_keys=True) if detalle else None))
        return cur.lastrowid

    def bitacora(self, correlation_id: str | None = None, request_id: str | None = None) -> list[dict]:
        consulta = ("SELECT a.event_id, a.occurred_at, a.correlation_id, a.request_id, a.interface_id, a.event_type,"
                    " a.code, a.actor_id, COALESCE(e.actor_type,'SISTEMA') AS actor_type, e.detalle"
                    " FROM audit a LEFT JOIN audit_ext e ON e.event_id = a.event_id WHERE 1=1")
        params = []
        if correlation_id:
            consulta += " AND a.correlation_id = ?"
            params.append(correlation_id)
        if request_id:
            consulta += " AND a.request_id = ?"
            params.append(request_id)
        with self.conexion() as db:
            filas = db.execute(consulta + " ORDER BY a.event_id", params).fetchall()
        return [{**dict(f), "detalle": json.loads(f["detalle"]) if f["detalle"] else None} for f in filas]

    # ---- maestros locales ---------------------------------------------------------------
    def actores(self) -> dict:
        with self.conexion() as db:
            filas = db.execute("SELECT * FROM actores").fetchall()
        return {f["actor_id"]: {"role": f["rol"], "company_id": f["company_id"],
                                "opportunities": json.loads(f["opportunities_json"])} for f in filas}

    def politica(self) -> dict:
        with self.conexion() as db:
            filas = db.execute("SELECT clave, valor FROM politica").fetchall()
        return {f["clave"]: f["valor"] for f in filas}

    def cliente_ext(self, ref: str) -> dict | None:
        with self.conexion() as db:
            f = db.execute("SELECT * FROM clientes_ext WHERE ref=?", (ref,)).fetchone()
        return dict(f) if f else None

    def mapa(self, tipo: str, externo: str) -> str | None:
        with self.conexion() as db:
            f = db.execute("SELECT odoo FROM mapa_ids WHERE tipo=? AND externo=?", (tipo, externo)).fetchone()
        return f["odoo"] if f else None

    def externo_por_odoo(self, tipo: str, odoo: str) -> str | None:
        with self.conexion() as db:
            f = db.execute("SELECT externo FROM mapa_ids WHERE tipo=? AND odoo=?", (tipo, str(odoo))).fetchone()
        return f["externo"] if f else None

    def aceptaciones(self, company_id: str) -> dict:
        with self.conexion() as db:
            filas = db.execute("SELECT * FROM aceptaciones WHERE company_id=?", (company_id,)).fetchall()
        return {f["acceptance_id"]: {"company_id": f["company_id"], "quotation_id": f["quotation_id"],
                                     "quotation_version": f["quotation_version"], "customer_id": f["customer_id"],
                                     "total": f["total"], "accepted_at": f["accepted_at"]} for f in filas}

    def aceptacion_de(self, quotation_id: str, version: int) -> list[str]:
        with self.conexion() as db:
            filas = db.execute("SELECT acceptance_id FROM aceptaciones WHERE quotation_id=? AND quotation_version=?",
                               (quotation_id, version)).fetchall()
        return [f["acceptance_id"] for f in filas]

    def aprobaciones(self, company_id: str) -> list[dict]:
        with self.conexion() as db:
            filas = db.execute("SELECT * FROM aprobaciones WHERE company_id=? ORDER BY approval_id", (company_id,)).fetchall()
        return [{"company_id": f["company_id"], "quotation_id": f["quotation_id"],
                 "quotation_version": f["quotation_version"], "total": f["total"], "status": f["status"],
                 "approver_id": f["approver_id"], "approved_at": f["approved_at"], "valid_until": f["valid_until"]}
                for f in filas]

    def senal(self, signal_id: str) -> dict | None:
        with self.conexion() as db:
            f = db.execute("SELECT * FROM senales_rep WHERE signal_id=?", (signal_id,)).fetchone()
        return dict(f) if f else None

    def senales_de(self, request_id: str) -> list[dict]:
        with self.conexion() as db:
            filas = db.execute("SELECT * FROM senales_rep WHERE request_id=? ORDER BY signal_id", (request_id,)).fetchall()
        return [dict(f) for f in filas]

    def payload(self, company_id: str, request_id: str) -> dict | None:
        with self.conexion() as db:
            f = db.execute("SELECT payload_json FROM solicitudes_payload WHERE company_id=? AND request_id=?",
                           (company_id, request_id)).fetchone()
        return json.loads(f["payload_json"]) if f else None

    def respuesta(self, company_id: str, request_id: str) -> dict | None:
        with self.conexion() as db:
            f = db.execute("SELECT response_json, opportunity_id FROM requests WHERE company_id=? AND request_id=?",
                           (company_id, request_id)).fetchone()
        return {"respuesta": json.loads(f["response_json"]), "opportunity_id": f["opportunity_id"]} if f else None

    def escalamiento(self, escalation_id: str) -> dict | None:
        with self.conexion() as db:
            f = db.execute("SELECT * FROM escalamientos WHERE escalation_id=?", (escalation_id,)).fetchone()
        return dict(f) if f else None

    @staticmethod
    def cerrar_escalamientos(db, *, decision, decided_at, signal_id=None, quotation_id=None, version_aprobacion=None):
        """Marca como decididos los escalamientos abiertos que corresponden a la decisión del dueño."""
        if signal_id:
            filtro, params = "signal_id=?", (signal_id,)
        else:
            filtro, params = "quotation_id=? AND version_aprobacion=?", (quotation_id, version_aprobacion)
        db.execute(f"UPDATE escalamientos SET estado='DECIDIDO', decision=?, decided_at=?"
                   f" WHERE estado='ESPERANDO_DECISION' AND {filtro}", (decision, decided_at, *params))

    # ---- simulación de caída (bandera documentada para PC3-F01 sin Docker) -----------------
    def simular_caida(self) -> bool:
        with self.conexion() as db:
            f = db.execute("SELECT valor FROM simulacion WHERE clave='odoo_caido'").fetchone()
        return bool(f and f["valor"] == "1")

    def fijar_simulacion(self, caido: bool):
        with self.conexion() as db:
            db.execute("INSERT INTO simulacion(clave,valor) VALUES('odoo_caido',?)"
                       " ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", ("1" if caido else "0",))

    def reiniciar_transacciones(self):
        """Borra solicitudes, bitácora, aceptaciones, aprobaciones, REP y decisiones.

        Actores, política, clientes y mapa de IDs se conservan; el seed vuelve a
        registrar las aceptaciones con la hora actual.
        """
        with self.conexion() as db:
            for tabla in ("audit_ext", "audit", "requests", "solicitudes_payload", "decisiones_reposicion",
                          "senales_rep", "aprobaciones", "aceptaciones", "escalamientos", "simulacion"):
                db.execute(f"DELETE FROM {tabla}")
