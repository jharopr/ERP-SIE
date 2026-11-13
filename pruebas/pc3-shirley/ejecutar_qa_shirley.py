"""QA PC3 de Shirley Carrión: instalación limpia, caso normal, stock/servicio y coherencia.

Qué hace, sin servicios externos ni credenciales:

1. Comprueba si el checkout contiene el paquete del Agente SIE (`agente-sie/`) y
   el sistema Odoo (`app/`). Si faltan, registra la prueba como BLOQUEADA.
2. Copia a un directorio temporal el simulador del contrato (`pruebas/pc2`),
   el arnés EP (`pruebas/ep-benjamin`) y los esquemas, y los ejecuta desde cero
   ("instalación limpia" del prototipo disponible). No modifica las evidencias
   versionadas del repositorio.
3. Calcula los indicadores de inventario y servicio de la sección 5B a partir de
   las respuestas OBSERVADAS (datos sintéticos, no métricas de la empresa).
4. Revisa la coherencia entre el informe PC3 y los documentos previos con reglas
   explícitas y registra los defectos encontrados.

Uso, desde la raíz del repositorio y con Python 3.10+ (solo biblioteca estándar):

    python pruebas/pc3-shirley/ejecutar_qa_shirley.py
    python pruebas/pc3-shirley/ejecutar_qa_shirley.py --output pruebas/pc3-shirley/evidencias/revalidacion

Código de salida: 0 si todo pasa; 1 si quedan defectos abiertos de prioridad ALTA
o la prueba del agente está bloqueada; 2 si falla la ejecución del prototipo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIMA = timezone(timedelta(hours=-5), "America/Lima")

COPIAR = ["pruebas/pc2", "pruebas/ep-benjamin", "arquitectura/contratos"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leer(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Paquete del agente y del sistema Odoo
# ---------------------------------------------------------------------------
def revisar_paquete_agente() -> dict:
    agente = ROOT / "agente-sie"
    odoo = ROOT / "app"
    presente = {"agente-sie/": agente.is_dir(), "app/": odoo.is_dir()}
    guia = [p for p in (agente / "README.md", odoo / "README.md") if p.exists()]
    estado = "DISPONIBLE" if all(presente.values()) else "BLOQUEADA"
    return {
        "prueba": "SHI-U01 Instalación limpia del Agente SIE y del sistema Odoo",
        "presente": presente,
        "guias_encontradas": [p.relative_to(ROOT).as_posix() for p in guia],
        "estado": estado,
        "motivo": None if estado == "DISPONIBLE" else (
            "El checkout no contiene el paquete del agente ni el sistema Odoo. Según la ficha QA de "
            "Adrián, están en las ramas origin/pc3/agente-sie (commit 8cfbf84) y origin/sistema-agente "
            "(commit 587eabb). Ejecutar esta prueba sobre el ZIP GE703_PC3_Agente_G7 cuando Ballack lo entregue."),
    }


# ---------------------------------------------------------------------------
# 2. Instalación limpia del prototipo de contrato disponible
# ---------------------------------------------------------------------------
def ejecutar_prototipo(temporal: Path) -> dict:
    for rel in COPIAR:
        origen = ROOT / rel
        if not origen.exists():
            return {"estado": "ERROR", "motivo": f"Falta {rel} en el checkout"}
        destino = temporal / rel
        shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("evidencias", "*.sqlite3", "__pycache__"))
    pasos = []
    for nombre, script in [("PC2: pruebas del contrato", "pruebas/pc2/generar_evidencias.py"),
                           ("EP: casos normal, stock parcial y descuento", "pruebas/ep-benjamin/generar_evidencias.py")]:
        inicio = time.perf_counter()
        proc = subprocess.run([sys.executable, script], cwd=temporal, capture_output=True, text=True)
        pasos.append({"paso": nombre, "comando": f"python {script}", "codigo_salida": proc.returncode,
                      "segundos": round(time.perf_counter() - inicio, 3),
                      "salida": proc.stdout.strip().splitlines()[-4:],
                      "errores": proc.stderr.strip().splitlines()[-5:]})
    estado = "CONFORME" if all(p["codigo_salida"] == 0 for p in pasos) else "NO_CONFORME"
    return {"prueba": "SHI-U02 Instalación limpia del prototipo de contrato incluido en el repositorio",
            "estado": estado, "pasos": pasos}


# ---------------------------------------------------------------------------
# 3. Indicadores de inventario y servicio (sección 5B)
# ---------------------------------------------------------------------------
def pct(num: float, den: float):
    return None if den == 0 else round(num * 100 / den, 2)


def calcular_indicadores(temporal: Path) -> dict:
    evid = temporal / "pruebas/ep-benjamin/evidencias"
    casos = leer(temporal / "pruebas/ep-benjamin/fixtures/casos.json")["cases"]
    filas, revisiones = [], []
    for caso in casos:
        cid = caso["case_id"]
        datos = leer(evid / f"{cid}.json")
        entrada = leer(evid / f"{cid}-entrada.json").get("masters", {})
        obs = datos["observed"]
        cotizacion = entrada.get("quotations", {}).get(obs["quotation_id"])
        if cotizacion and cotizacion.get("version") != obs["quotation_version"]:
            cotizacion = None
        lineas = (cotizacion or {}).get("lines") or []
        sku = lineas[0]["sku"] if lineas else "RAD-7BT"
        solicitado = sum(l["quantity"] for l in lineas) if lineas else None
        disponible = entrada.get("availability", {}).get("quantities", {}).get(sku)
        evaluado_stock = obs["code"] != "DESCUENTO_SIN_APROBACION"
        if evaluado_stock and solicitado is not None and disponible is not None:
            atendible = min(solicitado, disponible)
            faltante = solicitado - atendible
        else:
            atendible = faltante = None
        senal = datos.get("conceptual_p2p_signal")
        fila = {
            "caso": cid, "estado": obs["status"], "codigo": obs["code"], "sku": sku,
            "unidades_solicitadas": solicitado, "disponible_snapshot": disponible,
            "evaluado_en_stock": evaluado_stock, "unidades_atendibles": atendible,
            "faltante": faltante,
            "pedido_completo": None if not evaluado_stock else faltante == 0,
            "promised_date": [c.get("promised_date") for c in obs.get("conditions", [])] or None,
            "order_id": obs["order_id"], "senal_reposicion": senal["signal_id"] if senal else None,
        }
        filas.append(fila)
        # Comprobaciones de interpretación stock/servicio que el agente y el sistema deben respetar
        revisiones += [
            {"caso": cid, "control": "Sin pedido operativo (order_id null)", "ok": obs["order_id"] is None},
            {"caso": cid, "control": "Comprobaciones del arnés superadas", "ok": bool(datos.get("passed"))},
        ]
        if obs["code"] == "DISPONIBILIDAD_PARCIAL":
            revisiones += [
                {"caso": cid, "control": "Parcial sin fecha prometida", "ok": all(c.get("promised_date") is None for c in obs["conditions"])},
                {"caso": cid, "control": "Parcial requiere nueva aceptación del cliente", "ok": all(c.get("requires_customer_acceptance") for c in obs["conditions"])},
                {"caso": cid, "control": "Señal de reposición sin compra ni reserva automática",
                 "ok": bool(senal) and senal.get("purchase_order_id") is None and senal.get("reservation_id") is None and senal.get("automatic_action") is False},
                {"caso": cid, "control": "Faltante de la señal = solicitado − disponible",
                 "ok": bool(senal) and senal.get("shortfall_quantity") == faltante},
            ]
        if obs["code"] == "DESCUENTO_SIN_APROBACION":
            codigos = [e.get("code") for e in datos.get("audit", [])]
            revisiones.append({"caso": cid, "control": "Rechazo sin evento de disponibilidad en bitácora",
                               "ok": "DISPONIBILIDAD" not in codigos})
    ev = [f for f in filas if f["evaluado_en_stock"] and f["unidades_solicitadas"] is not None]
    sol = sum(f["unidades_solicitadas"] for f in ev)
    ate = sum(f["unidades_atendibles"] for f in ev)
    completos = sum(1 for f in ev if f["pedido_completo"])
    agregados = {
        "aviso": ("Indicadores calculados sobre corridas sintéticas e independientes del arnés EP. "
                  "Sirven para comprobar fórmulas y lectura del agente; NO son nivel de servicio de MYS Hermanos."),
        "solicitudes_evaluadas_en_stock": len(ev),
        "solicitudes_excluidas": [f["caso"] for f in filas if not f["evaluado_en_stock"]],
        "tasa_cumplimiento_unidades_pct": pct(ate, sol),
        "formula_tasa_unidades": f"{ate} atendibles ÷ {sol} solicitadas × 100",
        "solicitudes_completas_pct": pct(completos, len(ev)),
        "formula_solicitudes_completas": f"{completos} completas ÷ {len(ev)} evaluadas × 100",
        "solicitudes_con_quiebre_pct": pct(len(ev) - completos, len(ev)),
        "senales_reposicion_sustentadas_pct": pct(
            sum(1 for f in filas if f["senal_reposicion"]), sum(1 for f in ev if f["faltante"])),
        "promesas_con_fecha_sin_validar": sum(1 for f in filas for d in (f["promised_date"] or []) if d is not None),
    }
    return {"prueba": "SHI-U04 Interpretación de stock y servicio", "por_caso": filas,
            "agregados": agregados, "controles": revisiones,
            "estado": "CONFORME" if all(r["ok"] for r in revisiones) else "NO_CONFORME"}


# ---------------------------------------------------------------------------
# 4. Coherencia documental entre informe PC3 y entregas previas
# ---------------------------------------------------------------------------
REGLAS = [
    {"id": "SHI-PC3-002", "prioridad": "ALTA", "tema": "Ubicación de la empresa",
     "patron": r"San Juan de Lurigancho|Jr\. Las Mimosas",
     "archivos": ["GE703_EP_G7_CONSOLIDADO_COMPLETO.md"],
     "esperado": "PC3 sitúa las tiendas en Naranjal «La 50», Independencia, y el almacén en Carabayllo (5A, EMP-01/03)",
     "accion": "No copiar la ubicación del parcial al informe PC3; confirmar con Adrián y retirar la dirección completa por privacidad"},
    {"id": "SHI-PC3-003", "prioridad": "MEDIA", "tema": "Código de almacén en la señal de reposición",
     "patron": r"ALM-SJL-01",
     "archivos": ["GE703_EP_G7_CONSOLIDADO_COMPLETO.md"],
     "esperado": "La evidencia ejecutada usa location_id TIENDA-DEMO; PC3 propone ubicaciones Carabayllo N1/N2 y tiendas",
     "accion": "Usar en el informe el código que muestra la evidencia o la tabla de ubicaciones de 5B"},
    {"id": "SHI-PC3-004", "prioridad": "ALTA", "tema": "Inmutabilidad de la bitácora",
     "patron": r"inmutab|no repudio",
     "archivos": ["GE703_EP_G7_CONSOLIDADO_COMPLETO.md"],
     "esperado": "La ficha de Adrián indica que la bitácora del prototipo NO acredita inmutabilidad fuerte",
     "accion": "En PC3 decir «bitácora con huella SHA-256 que permite detectar cambios», no «inmutable»"},
]


def revisar_coherencia() -> list[dict]:
    hallazgos = []
    for regla in REGLAS:
        ocurrencias = []
        for rel in regla["archivos"]:
            path = ROOT / rel
            if not path.exists():
                continue
            for n, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(regla["patron"], linea, re.IGNORECASE):
                    ocurrencias.append({"archivo": rel, "linea": n})
        hallazgos.append({**{k: v for k, v in regla.items() if k != "patron"},
                          "ocurrencias": ocurrencias[:10], "total_ocurrencias": len(ocurrencias),
                          "estado": "ABIERTO" if ocurrencias else "NO_DETECTADO"})
    # El informe PC3 no debe repetir esas afirmaciones
    informe = ROOT / "documentos/pc3/shirley/informe_pc3_consolidado.md"
    if informe.exists():
        texto = informe.read_text(encoding="utf-8")
        prohibido = [p for p in ("San Juan de Lurigancho", "inmutable", "ALM-SJL-01") if p in texto]
        hallazgos.append({"id": "SHI-PC3-005", "prioridad": "ALTA", "tema": "Informe PC3 libre de afirmaciones heredadas",
                          "esperado": "El informe no repite ubicación, código ni inmutabilidad del parcial",
                          "ocurrencias": prohibido, "total_ocurrencias": len(prohibido),
                          "estado": "ABIERTO" if prohibido else "CONFORME", "archivos": [informe.relative_to(ROOT).as_posix()],
                          "accion": "Corregir antes de exportar el PDF"})
    return hallazgos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=HERE / "evidencias")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    meta = {"ejecutado_lima": datetime.now(LIMA).isoformat(timespec="seconds"),
            "qa_asignado": "Shirley Carrión Oré",
            "python": platform.python_version(), "sistema": platform.platform(),
            "modo": "Simulador local del contrato + arnés EP en directorio temporal; sin Odoo, n8n, LLM ni red",
            "ejecucion": "Ejecutada por Shirley Carrión Oré con su script de QA (preparado con apoyo de IA)"}
    paquete = revisar_paquete_agente()
    with TemporaryDirectory(prefix="pc3-shirley-") as tmp:
        temporal = Path(tmp)
        prototipo = ejecutar_prototipo(temporal)
        if prototipo["estado"] != "CONFORME":
            resultado = {**meta, "paquete_agente": paquete, "prototipo": prototipo}
            (args.output / "resultado_qa_shirley.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
            print("ERROR: el prototipo no se ejecutó limpiamente; ver resultado_qa_shirley.json")
            return 2
        indicadores = calcular_indicadores(temporal)
    coherencia = revisar_coherencia()
    resultado = {**meta, "paquete_agente": paquete, "prototipo": prototipo,
                 "indicadores": indicadores, "coherencia": coherencia}
    salida = args.output / "resultado_qa_shirley.json"
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "indicadores_servicio.json").write_text(
        json.dumps({**meta, **indicadores}, ensure_ascii=False, indent=2), encoding="utf-8")
    resumen = {**meta, "archivos_sha256": {p.name: sha256(p) for p in sorted(args.output.glob("*.json")) if p.name != "resumen_shirley.json"}}
    (args.output / "resumen_shirley.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"SHI-U01 agente/sistema: {paquete['estado']}")
    print(f"SHI-U02 prototipo limpio: {prototipo['estado']} ({', '.join(str(p['segundos']) + ' s' for p in prototipo['pasos'])})")
    for f in indicadores["por_caso"]:
        print(f"  {f['caso']}: {f['estado']}/{f['codigo']} solicitadas={f['unidades_solicitadas']} "
              f"snapshot={f['disponible_snapshot']} atendibles={f['unidades_atendibles']} faltante={f['faltante']}")
    a = indicadores["agregados"]
    print(f"SHI-U04 stock/servicio: {indicadores['estado']} · cumplimiento unidades {a['tasa_cumplimiento_unidades_pct']} % "
          f"· solicitudes completas {a['solicitudes_completas_pct']} % (sintético)")
    for h in coherencia:
        print(f"{h['id']} [{h['prioridad']}] {h['tema']}: {h['estado']} ({h['total_ocurrencias']})")
    print(f"Evidencia: {salida.relative_to(ROOT).as_posix() if salida.is_relative_to(ROOT) else salida}")
    altos = [h for h in coherencia if h["prioridad"] == "ALTA" and h["estado"] == "ABIERTO"]
    return 1 if altos or paquete["estado"] == "BLOQUEADA" or indicadores["estado"] != "CONFORME" else 0


if __name__ == "__main__":
    sys.exit(main())
