"""Propuestas de cambio a una cotización: el agente PROPONE, el vendedor APLICA en Odoo.

POST /propuestas                      el agente (o el vendedor) registra una propuesta con vista previa
GET  /propuestas?quotation_id=&estado= propuestas de una cotización
GET  /propuestas/{id}                 una propuesta
POST /propuestas/{id}/resolver        SOLO desde Odoo con sesión humana: APLICADA (con la nueva versión) o DESCARTADA

La propuesta no modifica Odoo. El cambio real lo hace el vendedor con el botón «Aplicar como nueva
versión», que crea una versión nueva con su propio usuario. Después siguen las reglas de siempre
(enviar, aceptación del cliente, evaluar y, si pasa el tope, decisión del gerente).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json
import os
from pathlib import Path
import re
import unicodedata

from fastapi import Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .odoo_cliente import DependenciaNoDisponible
from .snapshot import dinero, version_vigente

DDL = """
CREATE TABLE IF NOT EXISTS propuestas_cambio (
    proposal_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, quotation_id TEXT NOT NULL, version INTEGER NOT NULL,
    cambios_json TEXT NOT NULL, vista_previa_json TEXT NOT NULL, motivo TEXT NOT NULL,
    actor_id TEXT NOT NULL, actor_type TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'PENDIENTE',
    created_at TEXT NOT NULL, resuelta_por TEXT, resuelta_at TEXT, nueva_version INTEGER
);
"""
COT = re.compile(r"^COT-[A-Za-z0-9_-]+$")
CENT = Decimal("0.01")


class Propuesta(BaseModel):
    cotizacion: str = Field(min_length=2, max_length=100)
    cambios: list | str
    motivo: str = Field(default="Cambio solicitado por el vendedor", max_length=300)


class Resolucion(BaseModel):
    accion: str = Field(pattern=r"^(APLICADA|DESCARTADA)$")
    nueva_version: int | None = Field(default=None, ge=1)


def _norm(texto):
    return "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower()) if unicodedata.category(c) != "Mn")


def _catalogo():
    from .catalogo import cargar_catalogo   # mismo caché por mtime que /catalogo
    try:
        return (cargar_catalogo() or {}).get("productos", [])
    except (OSError, ValueError, KeyError):
        return []


def registrar_propuestas(app, config, repo, exigir, fuente, huella_agente, reloj, aprendizaje=None):
    with repo.conexion() as db:
        db.executescript(DDL)

    def fila_a_dict(f):
        return {"propuesta_id": f["proposal_id"], "cotizacion": f["quotation_id"], "version_base": f["version"],
                "cambios": json.loads(f["cambios_json"]), "vista_previa": json.loads(f["vista_previa_json"]),
                "motivo": f["motivo"], "propuesta_por": f["actor_id"], "tipo_actor": f["actor_type"],
                "estado": f["estado"], "creada": f["created_at"], "resuelta_por": f["resuelta_por"],
                "resuelta": f["resuelta_at"], "nueva_version": f["nueva_version"]}

    def identificar(texto):
        """Cotización por código COT-…, número de Odoo (S000…) o cliente. Devuelve (quotation_id, opciones)."""
        t = texto.strip()
        if COT.match(t):
            return t, []
        if not hasattr(fuente, "buscar_cotizaciones"):
            raise HTTPException(404, "Indique el código de la cotización (COT-…).")
        try:
            familias = fuente.buscar_cotizaciones(t)
        except DependenciaNoDisponible:
            raise HTTPException(503, "Odoo no responde; no se pudo identificar la cotización.")
        if len(familias) == 1:
            return familias[0]["cotizacion"], []
        opciones = []
        for f in familias:
            v = max((x for x in f["versiones"] if x["state"] != "cancel"), key=lambda x: x["version"], default=None)
            if v:
                opciones.append({"numero_odoo": v["numero_odoo"], "cliente": v["cliente"], "productos": v["productos"],
                                 "total": dinero(v["total"])})
        return None, opciones

    def resolver_producto(texto, lineas_actuales, nombres):
        """SKU exacto o nombre (palabras, sin tildes): primero entre las líneas de la cotización, luego en el catálogo."""
        t = str(texto or "").strip()
        if not t:
            raise HTTPException(422, "Cada cambio debe indicar el producto (SKU o nombre).")
        for sku in lineas_actuales:
            if sku.lower() == t.lower():
                return sku
        catalogo = _catalogo()
        for p in catalogo:
            if p["sku"].lower() == t.lower() or p.get("codigo_original", "").lower() == t.lower():
                return p["sku"]
        aprendido = aprendizaje.alias(t) if aprendizaje else None
        if aprendido:  # frase confirmada antes por un vendedor al aplicar una propuesta
            return aprendido
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{1,40}", t) and " " not in t:
            # SKU que existe en Odoo aunque no esté en el archivo del catálogo (p. ej. los genéricos de la PC3).
            try:
                if t.upper() in fuente.productos([t.upper()]):
                    return t.upper()
            except DependenciaNoDisponible:
                pass
        from .catalogo import coincide, terminos   # mismas reglas de búsqueda (plurales, sinónimos) que /catalogo
        buscados = terminos(t)
        en_cotizacion = [s for s in lineas_actuales if coincide(buscados, f"{s} {nombres.get(s, '')}")]
        if len(en_cotizacion) == 1:   # lo que ya está en la cotización tiene prioridad sobre el catálogo
            return en_cotizacion[0]
        candidatos = en_cotizacion or [p["sku"] for p in catalogo
                                       if coincide(buscados, f"{p['sku']} {p['nombre']}")]
        if len(candidatos) == 1:
            return candidatos[0]
        if not candidatos:
            raise HTTPException(404, f"No encontré el producto «{t}». Pruebe con el SKU o un nombre más exacto.")
        raise HTTPException(409, f"«{t}» coincide con varios productos: {', '.join(candidatos[:6])}. Indique el SKU.")

    @app.post("/propuestas")
    def proponer(datos: Propuesta, request: Request, quien=Depends(exigir("VENTAS"))):
        quotation_id, opciones = identificar(datos.cotizacion)
        if not quotation_id:
            if not opciones:
                raise HTTPException(404, f"No encontré una cotización para «{datos.cotizacion}».")
            return {"necesita_elegir": True, "mensaje": "Hay varias cotizaciones; pregunte al vendedor cuál.", "opciones": opciones}
        try:
            cambios = json.loads(datos.cambios) if isinstance(datos.cambios, str) else datos.cambios
        except ValueError:
            raise HTTPException(422, "Los cambios deben ser una lista: [{producto, cantidad, descuento}].")
        if isinstance(cambios, dict):
            cambios = [cambios]
        if not isinstance(cambios, list) or not cambios or len(cambios) > 20:
            raise HTTPException(422, "Indique entre 1 y 20 cambios.")
        try:
            vigente = version_vigente(fuente.versiones_cotizacion(quotation_id))
        except DependenciaNoDisponible:
            raise HTTPException(503, "Odoo no responde; no se pudo leer la cotización.")
        if not vigente:
            raise HTTPException(404, f"La cotización {quotation_id} no tiene una versión vigente.")
        if quien.odoo_uid and quien.rol == "VENTAS" and vigente.get("seller_odoo_id") not in (None, quien.odoo_uid):
            raise HTTPException(403, "Esa cotización pertenece a otro vendedor; solo su vendedor puede proponer cambios.")

        lineas = {}  # sku → {cantidad, precio, descuento}
        for l in vigente["lines"]:
            if l["sku"]:
                lineas[l["sku"]] = {"cantidad": Decimal(str(l["quantity"])), "precio": Decimal(str(l["unit_price"])),
                                    "descuento": Decimal(str(l["discount_pct"]))}
        try:
            info = fuente.productos(sorted(lineas))
        except DependenciaNoDisponible:
            info = {}
        nombres = {s: v.get("name", "") for s, v in info.items()}
        antes = {s: dict(v) for s, v in lineas.items()}

        normalizados = []
        for c in cambios:
            if not isinstance(c, dict):
                raise HTTPException(422, "Cada cambio debe ser un objeto {producto, cantidad, descuento}.")
            texto_original = str(c.get("producto") or c.get("sku") or "").strip()
            sku = resolver_producto(texto_original, list(lineas), nombres)
            accion = str(c.get("accion") or "").lower()
            cantidad = c.get("cantidad")
            descuento = c.get("descuento")
            sumar = c.get("sumar")
            try:
                cantidad = None if cantidad in (None, "") else Decimal(str(cantidad))
                descuento = None if descuento in (None, "") else Decimal(str(descuento))
                sumar = None if sumar in (None, "") else Decimal(str(sumar))
            except ArithmeticError:
                raise HTTPException(422, "Cantidad y descuento deben ser números.")
            if sumar is not None:   # «agrega 1 más», «quita 2»: relativo a la cantidad actual de la línea
                if cantidad is not None:
                    raise HTTPException(422, "Indique la cantidad final o cuánto sumar, no ambas.")
                cantidad = (lineas[sku]["cantidad"] if sku in lineas else Decimal("0")) + sumar
                if cantidad < 0:
                    raise HTTPException(422, f"No se pueden quitar más unidades de {sku} de las que tiene la cotización.")
            if descuento is not None and not Decimal("0") <= descuento <= Decimal("100"):
                raise HTTPException(422, "El descuento debe estar entre 0 y 100 %.")
            if cantidad is not None and not Decimal("0") <= cantidad <= Decimal("10000"):
                raise HTTPException(422, "La cantidad debe estar entre 0 y 10 000.")
            if accion == "quitar" or cantidad == 0:
                if sku not in lineas:
                    raise HTTPException(422, f"{sku} no está en la cotización; no se puede quitar.")
                del lineas[sku]
                normalizados.append({"accion": "quitar", "sku": sku, "texto": texto_original})
                continue
            if sku in lineas:
                if cantidad is None and descuento is None:
                    raise HTTPException(422, f"Indique la nueva cantidad o el descuento de {sku}.")
                if cantidad is not None:
                    lineas[sku]["cantidad"] = cantidad
                if descuento is not None:
                    lineas[sku]["descuento"] = descuento
                normalizados.append({"accion": "modificar", "sku": sku, "texto": texto_original,
                                     **({"cantidad": float(cantidad)} if cantidad is not None else {}),
                                     **({"descuento": float(descuento)} if descuento is not None else {})})
            else:
                try:
                    precio = fuente.productos([sku]).get(sku)
                except DependenciaNoDisponible:
                    raise HTTPException(503, "Odoo no responde; no se pudo leer el precio del producto.")
                if not precio or not precio.get("active", True):
                    raise HTTPException(404, f"{sku} no está activo en Odoo.")
                nombres[sku] = precio.get("name", "")
                lineas[sku] = {"cantidad": cantidad or Decimal("1"), "precio": Decimal(str(precio["list_price"])),
                               "descuento": descuento or Decimal("0")}
                normalizados.append({"accion": "agregar", "sku": sku, "texto": texto_original,
                                     "cantidad": float(lineas[sku]["cantidad"]),
                                     "descuento": float(lineas[sku]["descuento"])})
        if not lineas:
            raise HTTPException(422, "La cotización no puede quedar sin productos.")

        def subtotal(v):
            return (v["precio"] * v["cantidad"] * (1 - v["descuento"] / 100)).quantize(CENT, rounding=ROUND_HALF_UP)

        tope = Decimal(str(repo.politica().get("max_seller_discount", "5")))
        def cambio(s, v):
            a = antes.get(s)
            if not a:
                return f"nuevo: {float(v['cantidad']):g} unidad(es)"
            partes = []
            if v["cantidad"] != a["cantidad"]:
                partes.append(f"cantidad {'sube' if v['cantidad'] > a['cantidad'] else 'baja'} de {float(a['cantidad']):g} a {float(v['cantidad']):g}")
            if v["descuento"] != a["descuento"]:
                partes.append(f"descuento {'sube' if v['descuento'] > a['descuento'] else 'baja'} de {float(a['descuento']):g} % a {float(v['descuento']):g} %")
            return "; ".join(partes) or "sin cambio"

        detalle = [{"sku": s, "producto": nombres.get(s, ""), "cantidad": float(v["cantidad"]), "precio": dinero(v["precio"]),
                    "descuento": float(v["descuento"]), "subtotal": dinero(subtotal(v)),
                    "cambio": cambio(s, v), "supera_tope": v["descuento"] > tope} for s, v in lineas.items()]
        detalle += [{"sku": s, "producto": nombres.get(s, ""), "cantidad": 0.0, "precio": dinero(a["precio"]),
                     "descuento": float(a["descuento"]), "subtotal": "0.00", "cambio": f"se quita (tenía {float(a['cantidad']):g})",
                     "supera_tope": False} for s, a in antes.items() if s not in lineas]
        total_antes = sum((subtotal(v) for v in antes.values()), Decimal("0"))
        total_nuevo = sum((subtotal(v) for v in lineas.values()), Decimal("0"))
        maximo = max((v["descuento"] for v in lineas.values()), default=Decimal("0"))
        vista = {"lineas": detalle, "total_actual": dinero(total_antes), "total_propuesto": dinero(total_nuevo),
                 "descuento_maximo": float(maximo), "tope_vendedor": float(tope), "supera_tope": maximo > tope}

        ahora = reloj().isoformat()
        with repo.conexion(exclusiva=True) as db:
            n = db.execute("SELECT COUNT(*) FROM propuestas_cambio").fetchone()[0] + 1
            proposal_id = f"PRO-{n:04d}"
            db.execute("INSERT INTO propuestas_cambio(proposal_id,company_id,quotation_id,version,cambios_json,"
                       "vista_previa_json,motivo,actor_id,actor_type,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (proposal_id, config.company_id, quotation_id, vigente["version"],
                        json.dumps(normalizados, ensure_ascii=False), json.dumps(vista, ensure_ascii=False),
                        datos.motivo.strip(), quien.actor_id, quien.actor_type, ahora))
            repo.registrar_evento(db, company_id=config.company_id, request_id=None, correlation_id=proposal_id,
                                  actor_id=quien.actor_id, actor_type=quien.actor_type, interface_id="AGENTE",
                                  event_type="PROPUESTA", code="PROPUESTA_REGISTRADA", occurred_at=ahora,
                                  detalle={"quotation_id": quotation_id, "version": vigente["version"],
                                           "cambios": len(normalizados), "supera_tope": vista["supera_tope"]})
        huella_agente(request, quien, json.dumps(normalizados).encode(), proposal_id)
        # Texto exacto para el vendedor: el modelo lo repite y no reescribe cifras (evita totales mal copiados).
        advertencias = [f"Atención: en {l['sku']} la {l['cambio']}; revise que eso sea lo que pidió el cliente."
                        for l in detalle if " baja de " in l["cambio"] and "cantidad" in l["cambio"]]
        advertencias += [f"Atención: {l['sku']} {l['cambio']}." for l in detalle if l["cambio"].startswith("se quita")]
        if vista["supera_tope"]:
            advertencias.append(f"Un descuento pasa el tope de {float(tope):g} %: al evaluar la nueva versión decidirá el gerente.")
        sentido = "sube" if total_nuevo > total_antes else "baja" if total_nuevo < total_antes else "no cambia"
        numero = vigente.get("numero_odoo") or f"{quotation_id} v{vigente['version']}"
        resumen = "\n".join([f"Propuesta {proposal_id} para {numero}:",
                             f"- Total actual: S/ {dinero(total_antes)}",
                             f"- Total propuesto: S/ {dinero(total_nuevo)} (el total {sentido})",
                             *[f"- {l['sku']}: {l['cambio']}" for l in detalle if l["cambio"] != "sin cambio"],
                             *[f"- {a}" for a in advertencias],
                             "La cotización todavía NO cambió: ábrala en Odoo y pulse «Aplicar como nueva versión» o «Descartar»."])
        return {"resumen_para_el_vendedor": resumen, "advertencias": advertencias,
                "propuesta_id": proposal_id, "estado": "PENDIENTE", "cotizacion": quotation_id,
                "version_base": vigente["version"], "cambios": normalizados, "vista_previa": vista,
                "mensaje": ("Propuesta registrada. Todavía NO cambia la cotización: el vendedor debe abrirla en Odoo y "
                            "pulsar «Aplicar como nueva versión». "
                            + ("Como un descuento pasa el tope del vendedor, al evaluar la nueva versión se necesitará "
                               "la decisión del gerente." if vista["supera_tope"] else ""))}

    @app.get("/propuestas")
    def listar(quotation_id: str = Query(pattern=r"^[A-Za-z0-9_-]{1,64}$"), estado: str | None = None,
               quien=Depends(exigir("VENTAS", "GERENCIA"))):
        consulta = "SELECT * FROM propuestas_cambio WHERE company_id=? AND quotation_id=?"
        params = [config.company_id, quotation_id]
        if estado:
            consulta += " AND estado=?"
            params.append(estado)
        with repo.conexion() as db:
            filas = db.execute(consulta + " ORDER BY created_at DESC", params).fetchall()
        return {"propuestas": [fila_a_dict(f) for f in filas]}

    @app.get("/propuestas/{proposal_id}")
    def ver(proposal_id: str, quien=Depends(exigir("VENTAS", "GERENCIA"))):
        with repo.conexion() as db:
            f = db.execute("SELECT * FROM propuestas_cambio WHERE proposal_id=? AND company_id=?",
                           (proposal_id, config.company_id)).fetchone()
        if not f:
            raise HTTPException(404, "Propuesta no encontrada.")
        return fila_a_dict(f)

    @app.post("/propuestas/{proposal_id}/resolver")
    def resolver(proposal_id: str, datos: Resolucion, quien=Depends(exigir("VENTAS"))):
        # Solo una persona desde Odoo: el agente nunca aplica ni descarta sus propias propuestas.
        if not quien.odoo_uid or quien.actor_type != "HUMANO":
            raise HTTPException(403, "Solo el vendedor desde Odoo puede aplicar o descartar una propuesta.")
        ahora = reloj().isoformat()
        with repo.conexion() as db:
            f = db.execute("SELECT * FROM propuestas_cambio WHERE proposal_id=? AND company_id=?",
                           (proposal_id, config.company_id)).fetchone()
            if not f:
                raise HTTPException(404, "Propuesta no encontrada.")
            if f["estado"] != "PENDIENTE":
                raise HTTPException(409, f"La propuesta ya está {f['estado']}.")
            db.execute("UPDATE propuestas_cambio SET estado=?, resuelta_por=?, resuelta_at=?, nueva_version=? "
                       "WHERE proposal_id=?", (datos.accion, quien.actor_id, ahora, datos.nueva_version, proposal_id))
            repo.registrar_evento(db, company_id=config.company_id, request_id=None, correlation_id=proposal_id,
                                  actor_id=quien.actor_id, actor_type="HUMANO", interface_id="ODOO",
                                  event_type="PROPUESTA", code=f"PROPUESTA_{datos.accion}", occurred_at=ahora,
                                  detalle={"quotation_id": f["quotation_id"], "nueva_version": datos.nueva_version})
        if datos.accion == "APLICADA" and aprendizaje:
            # Aprende solo de lo que una persona confirmó: la frase dicha → el SKU aplicado.
            aprendizaje.confirmar_alias([(c.get("texto"), c["sku"]) for c in json.loads(f["cambios_json"]) if c.get("texto")])
        return {"propuesta_id": proposal_id, "estado": datos.accion, "nueva_version": datos.nueva_version}
