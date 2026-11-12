"""El vendedor habla con nombres, no con códigos.

GET  /cotizaciones-buscar?texto=…  → cotizaciones por número de Odoo (S000…), cliente o código COT-…
POST /cotizaciones-validar {cotizacion} → identifica la versión vigente y su aceptación y envía la I03.

Los identificadores de la solicitud (SOL/COR) se DERIVAN DE FORMA FIJA, igual que el botón
«3. Evaluar reglas» de Odoo: validar desde el chat o desde el botón da la misma solicitud, y un
reintento nunca crea otra (idempotencia). Las reglas siguen siendo las del motor R01–R12; aquí
solo se arman las 9 referencias que el vendedor ya no tiene que escribir.
"""
from __future__ import annotations

import json
import uuid

from fastapi import Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .odoo_cliente import DependenciaNoDisponible
from .snapshot import dinero, version_vigente

ESTADOS = {"draft": "borrador", "sent": "enviada al cliente", "sale": "pedido confirmado", "cancel": "anulada"}


class Validar(BaseModel):
    cotizacion: str = Field(min_length=2, max_length=100)


def registrar_lenguaje_natural(app, config, repo, exigir, fuente, ejecutar, con_senales, huella_agente):
    def evaluada(quotation_id, version):
        with repo.conexion() as db:
            fila = db.execute("SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=?",
                              (config.company_id, quotation_id, version)).fetchone()
        return fila["request_id"] if fila else None

    def aceptacion(quotation_id, version):
        with repo.conexion() as db:
            fila = db.execute("SELECT acceptance_id FROM aceptaciones WHERE company_id=? AND quotation_id=? AND quotation_version=?"
                              " ORDER BY accepted_at DESC LIMIT 1", (config.company_id, quotation_id, version)).fetchone()
        return fila["acceptance_id"] if fila else None

    def historial(quotation_id, versiones):
        """Lo ocurrido con la cotización: evaluaciones por versión, decisiones del gerente y aprobaciones."""
        numero = {v["version"]: v["numero_odoo"] for v in versiones}
        with repo.conexion() as db:
            evaluaciones = db.execute("SELECT request_id, quotation_version, response_json FROM requests "
                                      "WHERE company_id=? AND quotation_id=? ORDER BY quotation_version",
                                      (config.company_id, quotation_id)).fetchall()
            decisiones = db.execute("SELECT escalation_id, tipo, quotation_version, estado, decision, created_at, decided_at "
                                    "FROM escalamientos WHERE company_id=? AND quotation_id=? ORDER BY created_at",
                                    (config.company_id, quotation_id)).fetchall()
            aprobaciones = db.execute("SELECT quotation_version, status, total, approved_at, valid_until, motivo "
                                      "FROM aprobaciones WHERE company_id=? AND quotation_id=? ORDER BY approved_at",
                                      (config.company_id, quotation_id)).fetchall()
        def resultado(fila):
            try:
                r = json.loads(fila["response_json"])
                return f"{r['status']} / {r['code']}", r.get("correlation_id")
            except (ValueError, KeyError, TypeError):
                return None, None
        return {
            "evaluaciones": [{"version": e["quotation_version"], "numero_odoo": numero.get(e["quotation_version"]),
                              "resultado": resultado(e)[0], "correlation_id": resultado(e)[1]} for e in evaluaciones],
            "decisiones_del_gerente": [{"escalation_id": d["escalation_id"], "tipo": d["tipo"],
                                        "sobre_version": d["quotation_version"], "estado": d["estado"],
                                        "decision": d["decision"], "solicitada": d["created_at"], "decidida": d["decided_at"]}
                                       for d in decisiones],
            "aprobaciones_de_descuento": [{"para_version": a["quotation_version"], "numero_odoo": numero.get(a["quotation_version"]),
                                           "estado": a["status"], "total": a["total"], "aprobada": a["approved_at"],
                                           "vale_hasta": a["valid_until"], "motivo": a["motivo"]} for a in aprobaciones],
        }

    def familias(texto):
        if not hasattr(fuente, "buscar_cotizaciones"):
            raise HTTPException(503, "La búsqueda por nombre requiere Odoo.")
        try:
            encontradas = fuente.buscar_cotizaciones(texto)
        except DependenciaNoDisponible:
            raise HTTPException(503, "Odoo no responde; no se pudo buscar la cotización.")
        resumen = []
        for f in encontradas:
            vigente = version_vigente([{**v, "state": v["state"]} for v in f["versiones"]])
            if not vigente:
                continue
            q, v = f["cotizacion"], vigente["version"]
            resumen.append({
                "cotizacion": q, "version_vigente": v, "numero_odoo": vigente["numero_odoo"],
                "cliente": vigente["cliente"], "cliente_ref": vigente["cliente_ref"], "oportunidad": vigente["oportunidad"],
                "vendedor": vigente["vendedor"], "total": dinero(vigente["total"]),
                "estado": ESTADOS.get(vigente["state"], vigente["state"]), "productos": vigente["productos"],
                "aceptacion_registrada": aceptacion(q, v), "ya_evaluada": bool(evaluada(q, v)),
                "versiones": [{"version": x["version"], "numero_odoo": x["numero_odoo"],
                               "estado": ESTADOS.get(x["state"], x["state"]), "total": dinero(x["total"])} for x in f["versiones"]],
                "historial": historial(q, f["versiones"]),
                "_company_odoo_id": vigente["company_odoo_id"]})
        return resumen

    def publico(c):
        return {k: v for k, v in c.items() if not k.startswith("_")}

    @app.get("/cotizaciones-buscar")
    def buscar(request: Request, texto: str = Query(min_length=2, max_length=100),
               quien=Depends(exigir("VENTAS", "GERENCIA"))):
        resultado = [publico(c) for c in familias(texto)]
        huella_agente(request, quien, texto.encode(), None)
        return {"coincidencias": len(resultado), "cotizaciones": resultado,
                "nota": "Datos leídos de Odoo. Para validar una, use validar_cotizacion con su número de Odoo o código."}

    @app.post("/cotizaciones-validar")
    def validar(datos: Validar, request: Request, quien=Depends(exigir("VENTAS"))):
        candidatas = familias(datos.cotizacion)
        if not candidatas:
            raise HTTPException(404, f"No encontré una cotización para «{datos.cotizacion}». Pruebe con el número de Odoo (S000…) o el nombre del cliente.")
        if len(candidatas) > 1:
            return {"necesita_elegir": True, "mensaje": "Hay varias cotizaciones; pregunte al vendedor cuál.",
                    "opciones": [publico(c) for c in candidatas]}
        c = candidatas[0]
        q, v = c["cotizacion"], c["version_vigente"]
        previa = evaluada(q, v)
        if previa:  # ya validada (por botón o por chat): se devuelve la respuesta guardada, sin repetir
            guardada = repo.respuesta(config.company_id, previa)
            huella_agente(request, quien, datos.cotizacion.encode(), guardada["respuesta"]["correlation_id"], previa)
            return {"identificada": publico(c), "ya_estaba_validada": True, **con_senales(guardada["respuesta"])}
        if not c["aceptacion_registrada"]:
            return {"identificada": publico(c), "sin_aceptacion": True,
                    "mensaje": "El cliente aún no tiene aceptación registrada para esta versión. El vendedor debe "
                               "registrarla en Odoo (botón «2. Registrar aceptación») antes de validar."}
        # Misma derivación que mys_erp (Order.action_mys_evaluate): una sola solicitud por versión.
        operacion = uuid.uuid5(uuid.NAMESPACE_URL, "mys-evaluation/%s/%s/%s" % (c["_company_odoo_id"], q, v)).hex[:24]
        payload = {"contract_version": "1.0", "company_id": config.company_id,
                   "request_id": "SOL-" + operacion, "correlation_id": "COR-" + operacion,
                   "opportunity_id": c["oportunidad"], "customer_id": c["cliente_ref"],
                   "quotation_id": q, "quotation_version": v, "acceptance_id": c["aceptacion_registrada"]}
        respuesta = ejecutar(payload, quien)
        huella_agente(request, quien, datos.cotizacion.encode(), respuesta.get("correlation_id"), respuesta.get("request_id"))
        return {"identificada": publico(c), **con_senales(respuesta)}
