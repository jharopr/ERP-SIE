"""Análisis comercial de solo lectura para el agente y el gerente.

GET /analisis/rotacion   productos con menor (o mayor) rotación: vendidas, stock, días sin venta, cobertura
GET /analisis/clientes   cartera segmentada por capacidad de compra y afinidad con una categoría o producto

Las cifras las calcula Odoo con reglas fijas (ventas confirmadas, stock, perfil diario del cliente);
aquí solo se filtran, ordenan y agrupan. Nada se escribe en Odoo. Un vendedor ve únicamente los
clientes que tiene asignados; el gerente ve toda la cartera.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Query, Request

from .catalogo import coincide, terminos
from .odoo_cliente import DependenciaNoDisponible
from .snapshot import dinero

# Capacidad de compra según el monto comprado en los últimos 6 meses (S/). ALTA coincide con el
# umbral de cliente mayorista del perfil; las reglas están documentadas en docs/ANALISIS_COMERCIAL.md.
CAPACIDAD = (("ALTA", 5000.0), ("MEDIA", 1000.0), ("BAJA", 0.01))
NIVELES = {"nuevo": "Nuevo", "ocasional": "Ocasional", "frecuente": "Frecuente", "mayorista": "Mayorista"}
CLASES = {"sin_movimiento": "Sin ventas en el periodo", "baja": "Rotación baja", "media": "Rotación media",
          "alta": "Rotación alta", "agotado": "Sin stock disponible"}


def capacidad(monto: float) -> str:
    for nombre, minimo in CAPACIDAD:
        if monto >= minimo:
            return nombre
    return "SIN_COMPRAS"


def registrar_analisis(app, config, repo, exigir, fuente, huella_agente):

    @app.get("/analisis/rotacion")
    def rotacion(request: Request, orden: str = Query(default="menor", pattern="^(menor|mayor)$"),
                 dias: int = Query(default=90, ge=7, le=365), categoria: str = Query(default="", max_length=80),
                 limite: int = Query(default=10, ge=1, le=30), quien=Depends(exigir("VENTAS", "GERENCIA"))):
        if not hasattr(fuente, "rotacion"):
            raise HTTPException(503, "La rotación requiere Odoo.")
        ubicacion = repo.mapa("ubicacion", config.ubicacion_id)
        try:
            datos = fuente.rotacion(dias, int(ubicacion) if ubicacion else None)
        except DependenciaNoDisponible:
            raise HTTPException(503, "Odoo no responde; no se pudo calcular la rotación.")
        huella_agente(request, quien, f"{orden}|{dias}|{categoria}".encode(), None)
        buscados = terminos(categoria)
        productos = [p for p in datos["productos"]
                     if coincide(buscados, f"{p['categoria']} {p['nombre']} {p['sku']}")]
        resumen = {CLASES[c]: sum(1 for p in productos if p["clasificacion"] == c) for c in CLASES}
        inmovilizado = sum(p["disponible"] * p["precio"] for p in productos if p["clasificacion"] == "sin_movimiento")

        if orden == "menor":
            # Lo que más conviene mover: con stock, menos vendido, más tiempo sin venderse y más dinero parado.
            candidatos = [p for p in productos if p["disponible"] > 0]
            candidatos.sort(key=lambda p: (p["vendidas"], -(p["dias_sin_venta"] if p["dias_sin_venta"] is not False else 10**6),
                                           -p["disponible"] * p["precio"]))
        else:
            candidatos = sorted((p for p in productos if p["vendidas"] > 0), key=lambda p: -p["vendidas"])

        def fila(p):
            return {"sku": p["sku"], "producto": p["nombre"], "categoria": p["categoria"],
                    "precio": dinero(p["precio"]), "vendidas_en_periodo": p["vendidas"], "unidad": p["unidad"],
                    "pedidos_en_periodo": p["pedidos"], "ultima_venta": p["ultima_venta"] or "nunca vendido",
                    "dias_sin_venta": p["dias_sin_venta"] if p["dias_sin_venta"] is not False else None,
                    "stock_disponible": p["disponible"],
                    "dias_de_cobertura": p["cobertura_dias"] if p["cobertura_dias"] is not False else None,
                    "valor_en_stock": dinero(p["disponible"] * p["precio"]),
                    "rotacion": CLASES[p["clasificacion"]]}

        return {"periodo_dias": datos["dias"], "desde": datos["desde"], "orden": orden,
                "categoria": categoria or "todas", "productos_evaluados": len(productos),
                "resumen": resumen, "valor_en_stock_sin_ventas": dinero(inmovilizado),
                "productos": [fila(p) for p in candidatos[:limite]],
                "nota": "Calculado por Odoo con ventas confirmadas y stock actual de la tienda (precio de lista). "
                        "Cobertura = días que dura el stock al ritmo de venta del periodo. Datos de demostración."}

    @app.get("/analisis/clientes")
    def clientes(request: Request, categoria: str = Query(default="", max_length=80),
                 capacidad_minima: str = Query(default="", pattern="^(|ALTA|MEDIA|BAJA)$"),
                 limite: int = Query(default=10, ge=1, le=30), quien=Depends(exigir("VENTAS", "GERENCIA"))):
        if not hasattr(fuente, "clientes_segmentacion"):
            raise HTTPException(503, "La segmentación requiere Odoo.")
        # Un vendedor con sesión de Odoo solo ve su cartera; el gerente, toda la empresa.
        propia = quien.rol == "VENTAS" and quien.odoo_uid
        try:
            filas = fuente.clientes_segmentacion(quien.odoo_uid if propia else None)
        except DependenciaNoDisponible:
            raise HTTPException(503, "Odoo no responde; no se pudo leer la cartera.")
        huella_agente(request, quien, f"{categoria}|{capacidad_minima}".encode(), None)

        buscados = terminos(categoria)
        orden_cap = ["ALTA", "MEDIA", "BAJA", "SIN_COMPRAS"]
        tope = orden_cap.index(capacidad_minima) if capacidad_minima else len(orden_cap) - 1
        clientes_ = []
        for f in filas:
            cap = capacidad(f["mys_monto_6m"] or 0.0)
            if orden_cap.index(cap) > tope:
                continue
            afinidad = None
            if buscados:
                if coincide(buscados, f"{f['mys_categorias_top'] or ''} {f['mys_productos_top'] or ''}"):
                    afinidad = "ya compra esta categoría"
                elif coincide(buscados, f["mys_sugerencias"] or ""):
                    afinidad = "complemento sugerido de lo que compra"
                else:
                    continue
            compro = (f["mys_compras_6m"] or 0) > 0 or bool(f["mys_ultima_compra"])
            clientes_.append({
                "cliente": f["name"], "codigo": f["ref"], "capacidad_de_compra": cap,
                "nivel": NIVELES.get(f["mys_nivel"], f["mys_nivel"]), "monto_6_meses": dinero(f["mys_monto_6m"] or 0),
                "compras_6_meses": f["mys_compras_6m"], "ticket_promedio": dinero(f["mys_ticket_promedio"] or 0),
                "ultima_compra": f["mys_ultima_compra"] or None,
                "dias_sin_comprar": f["mys_dias_sin_compra"] if compro else None,
                "inactivo": bool(f["mys_inactivo"]), "categorias_que_compra": f["mys_categorias_top"] or None,
                "complementos_sugeridos": f["mys_sugerencias"] or None,
                **({"afinidad": afinidad} if afinidad else {}),
                "_monto": f["mys_monto_6m"] or 0.0})
        clientes_.sort(key=lambda c: (c.get("afinidad") != "ya compra esta categoría", orden_cap.index(c["capacidad_de_compra"]),
                                      -c["_monto"]))
        segmentos = {s: {"clientes": 0, "monto_6_meses": 0.0} for s in orden_cap}
        for c in clientes_:
            segmentos[c["capacidad_de_compra"]]["clientes"] += 1
            segmentos[c["capacidad_de_compra"]]["monto_6_meses"] += c["_monto"]
        return {"alcance": "clientes asignados a este vendedor" if propia else "toda la cartera",
                "categoria": categoria or "todas", "clientes_evaluados": len(clientes_),
                "segmentos": {s: {"clientes": v["clientes"], "monto_6_meses": dinero(v["monto_6_meses"])}
                              for s, v in segmentos.items() if v["clientes"]},
                "clientes": [{k: v for k, v in c.items() if k != "_monto"} for c in clientes_[:limite]],
                "reglas": "Capacidad por monto comprado en 6 meses: ALTA desde S/ 5 000, MEDIA desde S/ 1 000, "
                          "BAJA con alguna compra, SIN_COMPRAS sin compras confirmadas. Perfil calculado por Odoo cada día.",
                "nota": "Es una sugerencia para el vendedor; no autoriza descuentos ni cambia los topes."}
