"""Compuerta CRM–ERP v1.0 para el Agente SIE (FastAPI).

Las reglas R01-R12 viven en el motor probado; aquí solo hay transporte,
permisos por token, snapshot desde Odoo y extensiones de bitácora.
"""

from __future__ import annotations

from datetime import timedelta
import hashlib
import json
import re
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import snapshot
from .config import Config, ahora_lima
from .motor import evaluar
from .odoo_cliente import DependenciaNoDisponible, OdooCliente
from .repositorio import Repositorio
from .seguridad import Identidad, identificar

VERSION_COMPUERTA = "1.0.0"
ID = r"^[A-Za-z0-9_-]{1,64}$"


class Aprobacion(BaseModel):
    quotation_id: str = Field(pattern=ID)
    version: int = Field(ge=1)
    total: str = Field(pattern=r"^[0-9]+\.[0-9]{2}$")
    decision: Literal["APROBADA", "RECHAZADA"]
    motivo: str = Field(min_length=3, max_length=280)
    correlation_id: str | None = Field(default=None, pattern=ID)


class DecisionReposicion(BaseModel):
    signal_id: str = Field(pattern=ID)
    decision: Literal["OFRECER_PARCIAL", "EVALUAR_REPOSICION", "DESCARTAR"]
    motivo: str = Field(min_length=3, max_length=280)


class Aceptacion(BaseModel):
    acceptance_id: str = Field(pattern=ID)
    quotation_id: str = Field(pattern=ID)
    version: int = Field(ge=1)


class EventoAgente(BaseModel):
    correlation_id: str = Field(pattern=ID)
    tool: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    agent_version: str = Field(max_length=32)
    prompt_version: str = Field(max_length=32)
    input_hash: str = Field(pattern=r"^[a-f0-9]{16,128}$")
    request_id: str | None = Field(default=None, pattern=ID)


class SimulacionCaida(BaseModel):
    odoo_caido: bool


class Escalamiento(BaseModel):
    tipo: Literal["DESCUENTO", "REPOSICION", "DEPENDENCIA", "IDEMPOTENCIA"]
    request_id: str = Field(pattern=ID)
    resumen: str = Field(min_length=3, max_length=500)


class DecisionDueno(BaseModel):
    decision: Literal["APROBADA", "RECHAZADA", "OFRECER_PARCIAL", "EVALUAR_REPOSICION", "DESCARTAR"]
    motivo: str = Field(min_length=3, max_length=280)


# Tipo de escalamiento →(código de respuesta que lo justifica, destinatario)
ESCALAMIENTOS = {
    "DESCUENTO": ("DESCUENTO_SIN_APROBACION", "DUENO"),
    "REPOSICION": ("DISPONIBILIDAD_PARCIAL", "DUENO_Y_ABASTECIMIENTO"),
    "DEPENDENCIA": ("DEPENDENCIA_NO_DISPONIBLE", "ADMINISTRADOR"),
    "IDEMPOTENCIA": (None, "ADMINISTRADOR_Y_VENTAS"),
}
PLAZO_DECISION = timedelta(minutes=10)


def crear_app(config: Config | None = None, fuente=None, reloj=ahora_lima) -> FastAPI:
    config = config or Config.desde_entorno()
    repo = Repositorio(config.database)
    fuente = fuente or OdooCliente(config.odoo_url, config.odoo_db, config.odoo_user,
                                   config.odoo_password, config.odoo_timeout)
    app = FastAPI(title="Compuerta CRM–ERP · Agente SIE · MYS (datos sintéticos)", version=VERSION_COMPUERTA)
    app.state.repo, app.state.config, app.state.fuente = repo, config, fuente

    def evento(**kw):
        with repo.conexion() as db:
            repo.registrar_evento(db, company_id=config.company_id, occurred_at=reloj().isoformat(), **kw)

    def identidad(request: Request, authorization: str | None = Header(default=None),
                  x_actor_type: str | None = Header(default=None)) -> Identidad:
        quien = identificar(config, authorization, x_actor_type)
        if quien is None:
            raise HTTPException(401, "Token ausente o inválido.")
        # Huella de cada llamada del agente: herramienta + hash del cuerpo, nunca el texto.
        herramienta = request.headers.get("x-agent-tool")
        if quien.actor_type == "AGENTE" and herramienta and re.fullmatch(r"[a-z0-9_]{1,64}", herramienta):
            request.state.herramienta = herramienta
        return quien

    def exigir(*roles):
        def dependencia(request: Request, quien: Identidad = Depends(identidad)) -> Identidad:
            if quien.rol not in roles:
                evento(request_id=None, correlation_id=_correlacion(request), actor_id=quien.actor_id,
                       actor_type=quien.actor_type, interface_id="API", event_type="DENEGADA", code="ROL_NO_PERMITIDO",
                       detalle={"ruta": request.url.path, "rol": quien.rol})
                raise HTTPException(403, f"El rol {quien.rol} no puede usar esta operación.")
            return quien
        return dependencia

    def _correlacion(request: Request):
        valor = request.query_params.get("correlation_id") or request.headers.get("x-correlation-id")
        return valor if valor and re.fullmatch(ID, valor) else None

    def huella_agente(request: Request, quien: Identidad, cuerpo: bytes, correlation_id, request_id=None):
        herramienta = getattr(request.state, "herramienta", None)
        if herramienta:
            evento(request_id=request_id, correlation_id=correlation_id, actor_id=quien.actor_id,
                   actor_type="AGENTE", interface_id="AGENTE", event_type="HERRAMIENTA_AGENTE", code=herramienta,
                   detalle={"input_hash": hashlib.sha256(cuerpo).hexdigest(),
                            "agent_version": request.headers.get("x-agent-version", "")[:32],
                            "prompt_version": request.headers.get("x-prompt-version", "")[:32]})

    def ejecutar(payload, quien: Identidad, resume=False):
        masters, comercial_ok = snapshot.construir(payload, fuente, repo, config, reloj())
        respuesta = evaluar(masters, config.database, payload, quien.actor_id, actor_type=quien.actor_type,
                            prefijo_rep=config.prefijo_rep, comercial_disponible=comercial_ok, resume=resume)
        return respuesta

    def con_senales(respuesta: dict) -> dict:
        senales = repo.senales_de(respuesta["request_id"]) if respuesta.get("request_id") else []
        return {"respuesta": respuesta,
                "senales_reposicion": [{k: s[k] for k in ("signal_id", "sku", "requested", "available", "faltante",
                                                         "automatic_action", "estado")} for s in senales]}

    # ---------------------------------------------------------------------------------------
    @app.get("/vivo")
    def vivo():
        """Liveness para el healthcheck de Docker: no consulta Odoo."""
        return {"compuerta": "ok"}

    @app.get("/salud")
    def salud():
        try:
            odoo = {"disponible": not repo.simular_caida(), **({} if repo.simular_caida() else fuente.ping())}
        except DependenciaNoDisponible as exc:
            odoo = {"disponible": False, "motivo": str(exc)}
        return {"compuerta": "ok", "version": VERSION_COMPUERTA, "contrato": "1.0", "odoo": odoo,
                "hora_lima": reloj().isoformat()}

    @app.get("/clientes/{ref}")
    def cliente(ref: str, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        if not re.fullmatch(ID, ref):
            raise HTTPException(422, "Referencia inválida.")
        try:
            if repo.simular_caida():
                raise DependenciaNoDisponible("simulada")
            datos = fuente.cliente(ref)
        except DependenciaNoDisponible:
            return JSONResponse(status_code=503, content={"code": "DEPENDENCIA_NO_DISPONIBLE",
                                                          "message": "Odoo no responde; no se puede verificar el cliente."})
        huella_agente(request, quien, ref.encode(), _correlacion(request))
        if not datos:
            raise HTTPException(404, "Cliente no encontrado.")
        ext = repo.cliente_ext(ref) or {}
        # Sin nombres, documentos ni teléfonos: solo estado.
        return {"customer_id": ref, "activo": datos["active"], "identidad_revisada": bool(ext.get("identity_reviewed")),
                "segmento": ext.get("segmento")}

    @app.get("/cotizaciones/{quotation_id}/{version}")
    def cotizacion(quotation_id: str, version: int, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        if not re.fullmatch(ID, quotation_id) or version < 1:
            raise HTTPException(422, "Referencia inválida.")
        try:
            if repo.simular_caida():
                raise DependenciaNoDisponible("simulada")
            versiones = fuente.versiones_cotizacion(quotation_id)
        except DependenciaNoDisponible:
            return JSONResponse(status_code=503, content={"code": "DEPENDENCIA_NO_DISPONIBLE",
                                                          "message": "Odoo no responde; no se puede leer la cotización."})
        huella_agente(request, quien, f"{quotation_id}/{version}".encode(), _correlacion(request))
        pedida = next((v for v in versiones if v["version"] == version), None)
        if pedida is None:
            raise HTTPException(404, "Versión de cotización no encontrada.")
        vigente = snapshot.version_vigente(versiones)
        datos = snapshot.cotizacion_normalizada(pedida, config, repo)
        return {"quotation_id": quotation_id, "version": version,
                "version_vigente": vigente["version"] if vigente else None,
                "estado": pedida["state"], "moneda": datos["currency"], "lineas": datos["lines"],
                "total": datos["total"], "vigente_hasta": datos["valid_until"],
                "oportunidad": datos["opportunity_id"], "cliente": datos["customer_id"],
                "aceptaciones": repo.aceptacion_de(quotation_id, version),
                "nota": "Total calculado por Odoo; el agente no recalcula montos."}

    @app.get("/disponibilidad/{sku}")
    def disponibilidad(sku: str, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        if not re.fullmatch(ID, sku):
            raise HTTPException(422, "SKU inválido.")
        ubicacion = repo.mapa("ubicacion", config.ubicacion_id)
        try:
            if repo.simular_caida() or not ubicacion:
                raise DependenciaNoDisponible("simulada o sin ubicación")
            stock = fuente.stock([sku], int(ubicacion))[sku]
        except DependenciaNoDisponible:
            return JSONResponse(status_code=503, content={
                "code": "DEPENDENCIA_NO_DISPONIBLE",
                "message": "No hay lectura confiable de stock. Esto NO significa que no haya stock."})
        huella_agente(request, quien, sku.encode(), _correlacion(request))
        e = snapshot.entero_si_exacto
        return {"sku": sku, "fisico": e(float(stock["fisico"])), "reservado": e(float(stock["reservado"])),
                "disponible": e(float(stock["fisico"] - stock["reservado"])), "ubicacion": config.ubicacion_id,
                "observed_at": reloj().isoformat()}

    @app.post("/solicitudes")
    async def solicitudes(request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        cuerpo = await request.body()
        try:
            payload = json.loads(cuerpo)
        except (ValueError, UnicodeDecodeError):
            payload = None  # el motor responde CONTRATO_INVALIDO
        respuesta = ejecutar(payload, quien)
        huella_agente(request, quien, cuerpo, respuesta.get("correlation_id"), respuesta.get("request_id"))
        return con_senales(respuesta)

    @app.post("/solicitudes/{request_id}/reanudar")
    async def reanudar(request_id: str, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        payload = repo.payload(config.company_id, request_id) if re.fullmatch(ID, request_id) else None
        guardada = repo.respuesta(config.company_id, request_id) if payload else None
        if not guardada:
            raise HTTPException(404, "Solicitud no encontrada.")
        if guardada["respuesta"]["status"] != "PENDIENTE":
            raise HTTPException(409, "Solo se reanudan solicitudes en estado PENDIENTE.")
        respuesta = ejecutar(payload, quien, resume=True)
        huella_agente(request, quien, request_id.encode(), respuesta.get("correlation_id"), request_id)
        return con_senales(respuesta)

    @app.get("/solicitudes/{request_id}")
    def consultar_solicitud(request_id: str, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        guardada = repo.respuesta(config.company_id, request_id) if re.fullmatch(ID, request_id) else None
        if not guardada:
            raise HTTPException(404, "Solicitud no encontrada.")
        actor = repo.actores().get(quien.actor_id, {})
        if guardada["opportunity_id"] not in actor.get("opportunities", []):
            raise HTTPException(403, "Sin acceso al resultado de la solicitud.")
        huella_agente(request, quien, request_id.encode(), guardada["respuesta"]["correlation_id"], request_id)
        return con_senales(guardada["respuesta"])

    @app.post("/aceptaciones")
    def aceptaciones(datos: Aceptacion, quien: Identidad = Depends(exigir("VENTAS"))):
        """Extensión C03: registra la aceptación con el total que calcula Odoo, no el del cuerpo."""
        try:
            versiones = fuente.versiones_cotizacion(datos.quotation_id)
        except DependenciaNoDisponible:
            return JSONResponse(status_code=503, content={"code": "DEPENDENCIA_NO_DISPONIBLE",
                                                          "message": "Odoo no responde."})
        v = next((x for x in versiones if x["version"] == datos.version and x["state"] == "sent"), None)
        if v is None:
            raise HTTPException(409, "La versión no existe o no está en estado enviado.")
        ahora = reloj().isoformat()
        with repo.conexion() as db:
            if db.execute("SELECT 1 FROM aceptaciones WHERE acceptance_id=?", (datos.acceptance_id,)).fetchone():
                raise HTTPException(409, "La aceptación ya existe.")
            db.execute("INSERT INTO aceptaciones VALUES(?,?,?,?,?,?,?,?)",
                       (datos.acceptance_id, config.company_id, datos.quotation_id, datos.version, v["customer_ref"],
                        snapshot.dinero(v["amount_total"]), ahora, quien.actor_id))
            repo.registrar_evento(db, company_id=config.company_id, request_id=None, correlation_id=None,
                                  actor_id=quien.actor_id, actor_type=quien.actor_type, interface_id="C03",
                                  event_type="ACEPTACION", code="REGISTRADA", occurred_at=ahora,
                                  detalle={"acceptance_id": datos.acceptance_id, "quotation_id": datos.quotation_id,
                                           "version": datos.version})
        return {"acceptance_id": datos.acceptance_id, "total": snapshot.dinero(v["amount_total"]), "accepted_at": ahora}

    @app.post("/aprobaciones")
    def aprobaciones(datos: Aprobacion, quien: Identidad = Depends(exigir("GERENCIA"))):
        """C06: solo GERENCIA. approver_id sale del token y debe ser distinto del vendedor."""
        if quien.actor_id.startswith("VEN-"):
            raise HTTPException(403, "El aprobador no puede ser el vendedor.")
        ahora = reloj()
        with repo.conexion() as db:
            cur = db.execute(
                "INSERT INTO aprobaciones(company_id,quotation_id,quotation_version,total,status,approver_id,"
                "approved_at,valid_until,motivo,correlation_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (config.company_id, datos.quotation_id, datos.version, datos.total, datos.decision, quien.actor_id,
                 ahora.isoformat(), (ahora + timedelta(hours=config.aprobacion_vigencia_horas)).isoformat(),
                 datos.motivo, datos.correlation_id))
            repo.registrar_evento(db, company_id=config.company_id, request_id=None, correlation_id=datos.correlation_id,
                                  actor_id=quien.actor_id, actor_type="HUMANO", interface_id="C06",
                                  event_type="APROBACION", code=datos.decision, occurred_at=ahora.isoformat(),
                                  detalle={"quotation_id": datos.quotation_id, "version": datos.version,
                                           "total": datos.total, "approval_id": cur.lastrowid})
            repo.cerrar_escalamientos(db, decision=datos.decision, decided_at=ahora.isoformat(),
                                      quotation_id=datos.quotation_id, version_aprobacion=datos.version)
        return {"approval_id": cur.lastrowid, "status": datos.decision, "approver_id": quien.actor_id,
                "quotation_id": datos.quotation_id, "version": datos.version, "total": datos.total,
                "nota": "La aprobación vale solo para esa versión y ese total; requiere nueva aceptación y solicitud."}

    @app.post("/decisiones-reposicion")
    def decisiones_reposicion(datos: DecisionReposicion, quien: Identidad = Depends(exigir("GERENCIA"))):
        senal = repo.senal(datos.signal_id)
        if not senal:
            raise HTTPException(404, "Señal de reposición no encontrada.")
        ahora = reloj().isoformat()
        with repo.conexion() as db:
            db.execute("INSERT INTO decisiones_reposicion(signal_id,decision,motivo,actor_id,decided_at) VALUES(?,?,?,?,?)",
                       (datos.signal_id, datos.decision, datos.motivo, quien.actor_id, ahora))
            db.execute("UPDATE senales_rep SET estado=? WHERE signal_id=?", (f"DECIDIDA_{datos.decision}", datos.signal_id))
            repo.registrar_evento(db, company_id=config.company_id, request_id=senal["request_id"],
                                  correlation_id=senal["correlation_id"], actor_id=quien.actor_id, actor_type="HUMANO",
                                  interface_id="REP", event_type="DECISION_DUENO", code=datos.decision,
                                  occurred_at=ahora, detalle={"signal_id": datos.signal_id})
            repo.cerrar_escalamientos(db, decision=datos.decision, decided_at=ahora, signal_id=datos.signal_id)
        return {"signal_id": datos.signal_id, "decision": datos.decision, "decidido_por": quien.actor_id,
                "decided_at": ahora, "automatic_action": False,
                "nota": "La decisión no crea pedidos ni reservas; el vendedor comunica al cliente sin fechas."}

    @app.post("/escalamientos")
    def escalar(datos: Escalamiento, request: Request, quien: Identidad = Depends(exigir("VENTAS"))):
        """Registra que la excepción espera a un humano. No decide nada."""
        guardada = repo.respuesta(config.company_id, datos.request_id)
        if not guardada:
            raise HTTPException(404, "Solicitud no encontrada.")
        r = guardada["respuesta"]
        codigo, destinatario = ESCALAMIENTOS[datos.tipo]
        if codigo and r["code"] != codigo:
            raise HTTPException(409, f"La solicitud tiene código {r['code']}; no corresponde escalar {datos.tipo}.")
        with repo.conexion() as db:
            abierto = db.execute("SELECT escalation_id FROM escalamientos WHERE request_id=? AND tipo=?"
                                 " AND estado='ESPERANDO_DECISION'", (datos.request_id, datos.tipo)).fetchone()
        if abierto:
            return repo.escalamiento(abierto["escalation_id"])
        total, version_aprobacion, signal_id = r["total"], None, None
        if datos.tipo == "DESCUENTO":
            # La aprobación vale solo para una versión NUEVA (la rechazada no se reutiliza).
            version_aprobacion = r["quotation_version"] + 1
            try:
                v = next((x for x in fuente.versiones_cotizacion(r["quotation_id"])
                          if x["version"] == r["quotation_version"]), None)
                total = snapshot.dinero(v["amount_total"]) if v else None
            except DependenciaNoDisponible:
                total = None
        if datos.tipo == "REPOSICION":
            senales = repo.senales_de(datos.request_id)
            signal_id = senales[0]["signal_id"] if senales else None
        ahora = reloj()
        with repo.conexion() as db:
            n = db.execute("SELECT COUNT(*) FROM escalamientos").fetchone()[0]
            escalation_id = f"ESC-PC3-{n + 1:03d}"
            db.execute("INSERT INTO escalamientos(escalation_id,company_id,tipo,request_id,correlation_id,quotation_id,"
                       "quotation_version,version_aprobacion,total,signal_id,destinatario,resumen_hash,created_at,"
                       "plazo_hasta) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (escalation_id, config.company_id, datos.tipo, datos.request_id, r["correlation_id"],
                        r["quotation_id"], r["quotation_version"], version_aprobacion, total, signal_id, destinatario,
                        hashlib.sha256(datos.resumen.encode()).hexdigest(), ahora.isoformat(),
                        (ahora + PLAZO_DECISION).isoformat()))
            repo.registrar_evento(db, company_id=config.company_id, request_id=datos.request_id,
                                  correlation_id=r["correlation_id"], actor_id=quien.actor_id,
                                  actor_type=quien.actor_type, interface_id="ESC", event_type="ESCALADO",
                                  code=datos.tipo, occurred_at=ahora.isoformat(),
                                  detalle={"escalation_id": escalation_id, "destinatario": destinatario})
        huella_agente(request, quien, datos.model_dump_json().encode(), r["correlation_id"], datos.request_id)
        return repo.escalamiento(escalation_id)

    @app.post("/escalamientos/{escalation_id}/decision")
    def decidir_escalamiento(escalation_id: str, datos: DecisionDueno, quien: Identidad = Depends(exigir("GERENCIA"))):
        """Formulario del dueño (W2). Versión, total y señal salen del escalamiento, no del formulario."""
        esc = repo.escalamiento(escalation_id) if re.fullmatch(ID, escalation_id) else None
        if not esc:
            raise HTTPException(404, "Escalamiento no encontrado.")
        if esc["estado"] != "ESPERANDO_DECISION":
            raise HTTPException(409, f"El escalamiento ya está en estado {esc['estado']}.")
        validas = {"DESCUENTO": {"APROBADA", "RECHAZADA"},
                   "REPOSICION": {"OFRECER_PARCIAL", "EVALUAR_REPOSICION", "DESCARTAR"}}.get(esc["tipo"], set())
        if datos.decision not in validas:
            raise HTTPException(422, f"Para {esc['tipo']} las decisiones válidas son: {', '.join(sorted(validas)) or 'ninguna (lo atiende el administrador)'}.")
        if esc["tipo"] == "DESCUENTO":
            if not esc["total"]:
                raise HTTPException(409, "Sin total verificado en Odoo; reintente cuando Odoo esté disponible.")
            resultado = aprobaciones(Aprobacion(quotation_id=esc["quotation_id"], version=esc["version_aprobacion"],
                                                total=esc["total"], decision=datos.decision, motivo=datos.motivo,
                                                correlation_id=esc["correlation_id"]), quien)
        else:
            resultado = decisiones_reposicion(DecisionReposicion(signal_id=esc["signal_id"], decision=datos.decision,
                                                                 motivo=datos.motivo), quien)
        return {"escalation_id": escalation_id, "tipo": esc["tipo"], "resultado": resultado}

    @app.get("/escalamientos/{escalation_id}")
    def estado_escalamiento(escalation_id: str, request: Request, quien: Identidad = Depends(exigir("VENTAS", "ADMIN"))):
        esc = repo.escalamiento(escalation_id) if re.fullmatch(ID, escalation_id) else None
        if not esc:
            raise HTTPException(404, "Escalamiento no encontrado.")
        if esc["estado"] == "ESPERANDO_DECISION" and reloj().isoformat() > esc["plazo_hasta"]:
            with repo.conexion() as db:
                db.execute("UPDATE escalamientos SET estado='SIN_DECISION' WHERE escalation_id=?", (escalation_id,))
                repo.registrar_evento(db, company_id=config.company_id, request_id=esc["request_id"],
                                      correlation_id=esc["correlation_id"], actor_id="COMPUERTA", actor_type="SISTEMA",
                                      interface_id="ESC", event_type="PLAZO_VENCIDO", code="SIN_DECISION",
                                      occurred_at=reloj().isoformat(), detalle={"escalation_id": escalation_id})
            esc = repo.escalamiento(escalation_id)
        huella_agente(request, quien, escalation_id.encode(), esc["correlation_id"], esc["request_id"])
        mensajes = {"ESPERANDO_DECISION": "Esperando decisión del dueño.",
                    "DECIDIDO": f"El dueño decidió: {esc['decision']}.",
                    "SIN_DECISION": "Sin decisión: la oportunidad queda en seguimiento."}
        return {**esc, "mensaje": mensajes[esc["estado"]]}

    @app.get("/bitacora")
    def bitacora(correlation_id: str | None = None, request_id: str | None = None,
                 quien: Identidad = Depends(exigir("VENTAS", "ADMIN"))):
        if not correlation_id and not request_id:
            raise HTTPException(422, "Indique correlation_id o request_id.")
        for valor in (correlation_id, request_id):
            if valor and not re.fullmatch(ID, valor):
                raise HTTPException(422, "Identificador inválido.")
        return {"correlation_id": correlation_id, "request_id": request_id,
                "eventos": repo.bitacora(correlation_id, request_id)}

    @app.post("/eventos-agente")
    def eventos_agente(datos: EventoAgente, quien: Identidad = Depends(exigir("VENTAS"))):
        evento(request_id=datos.request_id, correlation_id=datos.correlation_id, actor_id=quien.actor_id,
               actor_type="AGENTE", interface_id="AGENTE", event_type="HERRAMIENTA_AGENTE", code=datos.tool,
               detalle={"input_hash": datos.input_hash, "agent_version": datos.agent_version,
                        "prompt_version": datos.prompt_version})
        return {"registrado": True}

    @app.post("/admin/simulacion")
    def simulacion(datos: SimulacionCaida, quien: Identidad = Depends(exigir("ADMIN"))):
        """Bandera documentada para PC3-F01 cuando no se puede detener el contenedor de Odoo."""
        repo.fijar_simulacion(datos.odoo_caido)
        evento(request_id=None, correlation_id=None, actor_id=quien.actor_id, actor_type="HUMANO", interface_id="ADMIN",
               event_type="SIMULACION", code="ODOO_CAIDO" if datos.odoo_caido else "ODOO_RESTABLECIDO")
        return {"odoo_caido_simulado": datos.odoo_caido}

    @app.post("/admin/reiniciar")
    def reiniciar(quien: Identidad = Depends(exigir("ADMIN"))):
        repo.reiniciar_transacciones()
        return {"reiniciado": True, "siguiente": "Ejecutar el seed para registrar aceptaciones y vigencias del día."}

    return app


def app_desde_entorno() -> FastAPI:
    """Fábrica para uvicorn (`--factory`). Falla al arrancar si faltan tokens."""
    config = Config.desde_entorno()
    faltan = [n for n, v in (("TOKEN_VENTAS", config.token_ventas), ("TOKEN_GERENCIA", config.token_gerencia),
                             ("TOKEN_ADMIN", config.token_admin)) if not v]
    if faltan:
        raise RuntimeError(f"Faltan variables de entorno: {', '.join(faltan)}")
    if len({config.token_ventas, config.token_gerencia, config.token_admin}) != 3:
        raise RuntimeError("Los tokens de VENTAS, GERENCIA y ADMIN deben ser distintos.")
    return crear_app(config)
