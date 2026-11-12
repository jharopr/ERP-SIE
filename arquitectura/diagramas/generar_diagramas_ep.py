"""Genera SVG con iconos para la arquitectura EP usando solo biblioteca estándar.

Lee evidencia existente de Benjamín; no ejecuta el contrato ni altera sus JSON.
--check verifica coherencia, XML y vigencia de los tres SVG sin escribir archivos.
"""

import argparse
from decimal import Decimal
from html import escape
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVIDENCE = ROOT / "pruebas/ep-benjamin/evidencias"
INK = "#183345"
MUTED = "#526574"
BLUE = "#286d9b"
GREEN = "#267b65"
AMBER = "#a76513"
RED = "#b34043"
NAVY = "#16374c"

# Iconos propios de trazos SVG. No dependen de tipografías ni servicios externos.
ICONS = {
    "store": '<path d="M7 25h63v45H7z M2 24 14 5h49l14 19z M18 9l-3 15 M34 9l-3 15 M50 9l-3 15 M66 9l-3 15 M20 70V43h17v27 M45 40h17v14H45z"/>',
    "contact": '<rect x="3" y="7" width="71" height="58"/><circle cx="22" cy="29" r="9"/><path d="m10 54 5-11h14l7 11 M44 24h21 M44 36h21 M44 48h17"/>',
    "crm": '<circle cx="40.5" cy="11.5" r="11"/><circle cx="11.5" cy="53.5" r="11"/><circle cx="68.5" cy="53.5" r="11"/><path d="M40 24v9H12v9 M40 33h28v9"/>',
    "document": '<path d="M10 3h41l18 18v51H10z M51 3v18h18 M23 33h33 M23 46h33 M23 59h33"/>',
    "control": '<circle cx="39.5" cy="37.5" r="36"/><path d="m21 38 13 13 25-26"/>',
    "stock": '<path d="M4 35h32v31H4z M42 35h32v31H42z M23 0h32v31H23z M20 35v12 M58 35v12 M39 0v12"/>',
    "approval": '<path d="M14 5h50v67H14z m10 47 9 9 22-21"/><circle cx="39.5" cy="25.5" r="9.5"/>',
    "shield": '<path d="m39 0 31 13-5 34-26 25-27-25-5-34z m-17 34 13 13 21-24"/>',
    "database": '<ellipse cx="39.5" cy="13" rx="36.5" ry="11"/><path d="M3 13v46c0 15 73 15 73 0V13 M3 34c0 15 73 15 73 0 M3 49c0 15 73 15 73 0"/>',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases():
    fixtures = read_json(ROOT / "pruebas/ep-benjamin/fixtures/casos.json")["cases"]
    require({case["case_id"] for case in fixtures} == {"EP-N01", "EP-S01", "EP-E01"},
            "Cambió el conjunto de casos EP; revisar el aporte y sus gráficos.")
    cases = {}
    for fixture in fixtures:
        case_id = fixture["case_id"]
        record = read_json(EVIDENCE / f"{case_id}.json")
        source = read_json(EVIDENCE / f"{case_id}-entrada.json")
        request, observed, masters = record["request"], record["observed"], source["masters"]
        require(request == fixture["request"] == source["request"], f"{case_id}: solicitud desalineada.")
        require(record["expected"] == fixture["expected"], f"{case_id}: expectativa desalineada.")
        for key, value in fixture["expected"].items():
            require(observed.get(key) == value, f"{case_id}: observado distinto en {key}.")
        checks = record["checks"]
        require(record["passed"] and checks and all(check["passed"] for check in checks),
                f"{case_id}: hay comprobaciones fallidas o ausentes.")
        require(observed["order_id"] is None, f"{case_id}: el caso no puede crear pedido.")
        require(record["request_count"] == 1 and record["repeated_response"] == observed,
                f"{case_id}: inconsistencia de reintento.")
        opportunity = masters["opportunities"][request["opportunity_id"]]
        customer = masters["customers"][request["customer_id"]]
        lead = masters["leads"][opportunity["lead_id"]]
        require(customer["segment"] == "PUBLICO_GENERAL_NUEVO" and
                opportunity["channel"] == lead["channel"] == "FISICO" and
                opportunity["source"] == lead["source"] == "VISITA_ESPONTANEA",
                f"{case_id}: se alteró el escenario presencial de PC2.")
        quotation = masters["quotations"][request["quotation_id"]]
        require(quotation["version"] == request["quotation_version"], f"{case_id}: versión incoherente.")
        require(len(quotation["lines"]) == 1, f"{case_id}: revisar el diagrama para más líneas.")
        line = quotation["lines"][0]
        base = Decimal(str(line["quantity"])) * Decimal(line["unit_price"])
        total = base * (1 - Decimal(line["discount_pct"]) / 100)
        require(total == Decimal(quotation["total"]), f"{case_id}: total de oferta incorrecto.")
        require(line["quantity"] == 5 and Decimal(line["unit_price"]) == 400,
                f"{case_id}: cambió la base comercial; revisar textos del aporte.")
        stock = masters["availability"]["quantities"][line["sku"]]
        require(stock == fixture["expected_stock"], f"{case_id}: stock de entrada incoherente.")
        signal = record["conceptual_p2p_signal"]
        require(signal == fixture["expected_signal"], f"{case_id}: señal P2P desalineada.")
        if signal:
            require(signal["shortfall_quantity"] == max(0, line["quantity"] - stock),
                    f"{case_id}: déficit incorrecto.")
            require(signal["request_id"] == request["request_id"] and
                    signal["correlation_id"] == request["correlation_id"] and
                    signal["quotation_version"] == request["quotation_version"],
                    f"{case_id}: señal sin trazabilidad.")
            require(not signal["automatic_action"] and
                    all(signal[key] is None for key in ["purchase_order_id", "reservation_id", "promised_date"]),
                    f"{case_id}: señal fuera del alcance conceptual.")
        cases[case_id] = {"record": record, "request": request, "observed": observed,
                          "quotation": quotation, "line": line, "stock": stock, "signal": signal}
    require(sum(len(case["record"]["checks"]) for case in cases.values()) == 112,
            "Cambió el número de comprobaciones reportado; revisar la documentación.")
    return cases


def money(value):
    return f"{Decimal(value):,.0f}"


class SVG:
    def __init__(self, title, height, description):
        self.height = height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1900" height="{height}" '
                      f'viewBox="0 0 1900 {height}" role="img" aria-labelledby="title description">',
                      f'<title id="title">{escape(title)}</title>',
                      f'<desc id="description">{escape(description)}</desc>',
                      f'<rect width="1900" height="{height}" fill="#ffffff"/>']

    def rect(self, x, y, width, height, fill="white", stroke="#c9d6df", radius=16):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
                          f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')

    def text(self, x, y, value, size=29, color=INK, bold=False):
        weight = ' font-weight="700"' if bold else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" fill="{color}"{weight}>'
                          f'{escape(str(value))}</text>')

    def lines(self, x, y, values, size=29, color=INK, gap=36):
        for value in values:
            self.text(x, y, value, size, color)
            y += gap

    def icon(self, name, x, y, color=BLUE, size=65):
        self.parts.append(f'<g transform="translate({x} {y}) scale({size / 80})" fill="none" '
                          f'stroke="{color}" stroke-width="3.3" stroke-linecap="round" '
                          f'stroke-linejoin="round">{ICONS[name]}</g>')

    def arrow(self, points, color="blue", label=None, label_at=None, dashed=False):
        colors = {"blue": BLUE, "green": GREEN, "amber": AMBER, "navy": NAVY}
        if dashed:
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                length = math.hypot(x2 - x1, y2 - y1)
                for start in range(0, math.ceil(length), 28):
                    end = min(start + 15, length)
                    ax, ay = x1 + (x2 - x1) * start / length, y1 + (y2 - y1) * start / length
                    bx, by = x1 + (x2 - x1) * end / length, y1 + (y2 - y1) * end / length
                    self.parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                                      f'stroke="{colors[color]}" stroke-width="4"/>')
        else:
            coords = " ".join(f"{x},{y}" for x, y in points)
            self.parts.append(f'<polyline points="{coords}" fill="none" stroke="{colors[color]}" '
                              f'stroke-width="4" stroke-linejoin="round"/>')
        (ax, ay), (bx, by) = points[-2:]
        angle = math.atan2(by - ay, bx - ax)
        vertices = [(bx, by), (bx - 18 * math.cos(angle - .5), by - 18 * math.sin(angle - .5)),
                    (bx - 18 * math.cos(angle + .5), by - 18 * math.sin(angle + .5))]
        self.parts.append('<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in vertices)
                          + f'" fill="{colors[color]}"/>')
        if label:
            self.text(*label_at, label, 26, colors[color], True)

    def card(self, x, y, width, height, title, lines, icon, color=BLUE, fill="#edf5fa", tag=None, element_id=None):
        if element_id:
            self.parts.append(f'<g id="{element_id}">')
        self.rect(x, y, width, height, fill, color)
        self.icon(icon, x + 22, y + 22, color, 54)
        self.text(x + 100, y + 51, title, 33, color, True)
        self.lines(x + 25, y + 124, lines, 28, gap=34)
        if tag:
            self.text(x + 25, y + height - 17, tag, 24, color, True)
        if element_id:
            self.parts.append('</g>')

    def finish(self):
        return "\n".join(self.parts + ['</svg>', ''])


def architecture(cases):
    normal, partial = cases["EP-N01"], cases["EP-S01"]
    request, signal = normal["request"], partial["signal"]
    s = SVG("Arquitectura lógica EP de Odoo para cliente nuevo en tienda física", 2040,
            "Módulos C01 a C08 e interfaces I01 a I07. Cliente presencial nuevo, registros comerciales, "
            "controles y respuesta sin pedido. Señal conceptual P2P fuera del contrato. Odoo no desplegado.")
    s.icon("store", 35, 25, NAVY, 80)
    s.text(140, 60, "Cliente nuevo en tienda física", 45, NAVY, True)
    s.text(140, 108, "Público general · visita espontánea · registro humano del vendedor", 29, MUTED)
    s.rect(20, 230, 1860, 1460, "#fafcfe")
    s.text(55, 277, "ODOO PROPUESTO  /  RESPONSABILIDADES LÓGICAS", 30, NAVY, True)
    s.arrow([(1270, 140), (1270, 290), (950, 290), (950, 315)],
            label="Atención presencial", label_at=(1300, 190))
    s.card(65, 315, 530, 235, "C02  Contactos", ["Cliente único", request["customer_id"], "Datos mínimos autorizados"],
           "contact", tag="Módulo estándar propuesto", element_id="C02")
    s.card(685, 315, 530, 235, "C01  CRM", ["Lead y oportunidad", request["opportunity_id"], "Origen y seguimiento"],
           "crm", tag="Módulo estándar propuesto", element_id="C01")
    s.card(1305, 315, 530, 235, "C03  Ventas", [request["quotation_id"], "Versión v1 y aceptación",
           f'5 unidades · S/ {money(normal["quotation"]["total"])}'], "document",
           tag="Versionado y aceptación por extender", element_id="C03")
    s.arrow([(685, 430), (595, 430)], label="I01", label_at=(604, 403))
    s.arrow([(1215, 430), (1305, 430)], label="I02", label_at=(1224, 403))
    s.arrow([(950, 550), (950, 765)], label="I03 · solicitar", label_at=(720, 655))
    s.arrow([(1125, 765), (1125, 625), (1570, 625), (1570, 550)],
            label="I04 · versión aceptada", label_at=(1260, 603))
    s.card(65, 765, 530, 235, "C06  Autorización", ["Dueño decide excepciones", "Regla didáctica del 5 %",
           "Aprobación por versión"], "approval", AMBER, "#fff7e9", "Extensión propuesta", "C06")
    s.card(685, 765, 530, 235, "C04  Transición", ["Evalúa solicitud y reglas", request["request_id"],
           "Conserva decisión y motivo"], "control", GREEN, "#eef8f3", "Extensión propuesta", "C04")
    s.card(1305, 765, 530, 235, "C05  Inventario", ["SKU y ubicación", "Disponibilidad y hora", "Consulta sin reserva"],
           "stock", tag="Módulo estándar consultado", element_id="C05")
    s.arrow([(685, 880), (595, 880)], "amber", "I06", (604, 853))
    s.arrow([(1215, 880), (1305, 880)], label="I05", label_at=(1224, 853))
    s.arrow([(950, 1000), (950, 1070)], "green")
    s.rect(320, 1070, 1260, 145, "#f1f8f5", GREEN)
    s.text(350, 1105, "RESPUESTA A VENTAS Y CRM", 31, GREEN, True)
    s.text(350, 1150, "ACEPTADA / código VALIDADA · RECHAZADA", 29)
    s.text(350, 1190, "PROMESA_CONDICIONADA · PENDIENTE  |  order_id = null", 29)
    s.arrow([(950, 1215), (950, 1300)], "navy", "I07 · autorización y eventos", (995, 1272))
    s.card(65, 1300, 1770, 155, "C07  Seguridad y bitácora",
           [f'Actor · permisos · compañía · {request["correlation_id"]} · evento y fecha'],
           "shield", NAVY, "#eef2f6", element_id="C07")
    s.arrow([(950, 1455), (950, 1515)], "green")
    s.parts.append('<g id="C08">')
    s.icon("database", 440, 1530, GREEN, 90)
    s.text(555, 1553, "C08  Persistencia Odoo y PostgreSQL", 34, GREEN, True)
    s.text(555, 1603, "C01–C07 acceden mediante ORM; diseño por implementar", 28, MUTED)
    s.text(555, 1648, "La prueba local utiliza JSON y SQLite", 28, MUTED)
    s.parts.append('</g>')
    s.card(65, 1725, 855, 185, "UBLHUB  Continuidad de PC1", ["Emisión electrónica futura", "Fuera del tramo evaluado"],
           "document", MUTED, "#f3f5f7")
    s.card(1010, 1725, 825, 185, "P2P  Abastecimiento", [f'Faltante {signal["shortfall_quantity"]} → {signal["signal_id"]}',
           "Dueño evalúa; sin compra automática"], "stock", AMBER, "#fff9ef")
    s.arrow([(1580, 1140), (1860, 1140), (1860, 1810), (1835, 1810)], "amber", dashed=True)
    s.lines(1605, 1202, ["Tras respuesta parcial:", "arnés documenta señal", "fuera del contrato 1.0"], 23, AMBER, 29)
    s.text(65, 1948, "Flecha continua: intercambio lógico · Trazo discontinuo: dependencia conceptual", 26, MUTED)
    s.text(65, 1988, "Ficha: identidad · Documento: cotización · Cajas: inventario · Escudo: seguridad · Cilindro: datos", 25, MUTED)
    s.text(65, 2024, "Diseño y datos sintéticos · Odoo no desplegado · Sin pedido, reserva ni compras ejecutadas", 25, MUTED)
    return s.finish()


def case_diagram(cases):
    s = SVG("Casos EP y controles de arquitectura", 1160,
            "Tres variantes independientes del cliente nuevo presencial: normal, faltante y descuento sin autorización. "
            "Respuestas leídas de las evidencias de Benjamín; no son operaciones reales en Odoo.")
    normal = cases["EP-N01"]
    s.text(30, 60, "Un mismo caso comercial y tres respuestas controladas", 43, NAVY, True)
    steps = [("contact", "Cliente nuevo", normal["request"]["customer_id"]),
             ("crm", "Oportunidad", normal["request"]["opportunity_id"]),
             ("document", "Cotización", normal["request"]["quotation_id"]),
             ("control", "Evaluación", "SOL y COR")]
    for i, (symbol, title, value) in enumerate(steps):
        x = 30 + i * 470
        s.rect(x, 100, 420, 205, "#edf5fa", BLUE)
        s.icon(symbol, x + 20, 120, BLUE, 65)
        s.text(x + 110, 159, title, 31, BLUE, True)
        s.text(x + 20, 252, value, 30)
        if i < 3:
            s.arrow([(x + 420, 200), (x + 470, 200)])
    s.text(30, 365, "5 autoradios × S/ 400 = S/ 2,000 · Persona natural · Tienda física · Visita espontánea", 29, MUTED)
    config = [("EP-N01", "Caso normal", "control", GREEN, "#eef8f3"),
              ("EP-S01", "Faltante", "stock", AMBER, "#fff7e9"),
              ("EP-E01", "Excepción", "approval", RED, "#fcf0f0")]
    for i, (case_id, title, symbol, color, fill) in enumerate(config):
        case = cases[case_id]
        y = 410 + i * 205
        s.parts.append(f'<g id="{case_id}">')
        s.rect(30, y, 1840, 180, fill, color)
        s.icon(symbol, 55, y + 40, color, 65)
        s.text(150, y + 49, f"{case_id}  {title}", 34, color, True)
        discount = Decimal(case["line"]["discount_pct"])
        s.text(150, y + 100, f'{discount:.0f} % de descuento propuesto → S/ {money(case["quotation"]["total"])}', 28)
        if case_id == "EP-S01":
            detail = f'Disponibilidad {case["stock"]} → faltan {case["signal"]["shortfall_quantity"]}'
        elif case_id == "EP-E01":
            detail = "Sin aprobación válida del dueño; cotización v2"
        else:
            detail = f'Disponibilidad de evaluación: {case["stock"]}; cotización v1'
        s.text(150, y + 140, detail, 28)
        s.text(1010, y + 56, case["observed"]["status"], 31, color, True)
        s.text(1010, y + 102, case["observed"]["code"], 27, color)
        notes = {"EP-N01": "Solicitud validada; sin pedido ni reserva.",
                 "EP-S01": "REP-EP-001: evaluación conceptual P2P.",
                 "EP-E01": "Se rechaza la transición; el vendedor escala."}
        s.text(1010, y + 145, notes[case_id], 27)
        s.parts.append('</g>')
    s.text(30, 1072, "Casos independientes de Benjamín · Datos sintéticos · order_id = null en los tres casos", 29, MUTED)
    s.text(30, 1114, "La respuesta rechazada conserva total = null; S/ 1,800 corresponde a la oferta propuesta.", 28, MUTED)
    return s.finish()


def event_diagram(cases):
    """Vista de eventos, responsables y respuestas, alineada con la evidencia."""
    s = SVG("Eventos de la arquitectura integrada CRM ERP", 1840,
            "La aceptación de la cotización precede a la solicitud. C04 registra recepción y decisión. "
            "Tres variantes independientes: validación, disponibilidad parcial y descuento sin aprobación. "
            "El arnés documenta REP-EP-001 como señal conceptual hacia P2P. El reintento recupera la respuesta original.")
    s.text(55, 65, "Eventos de la arquitectura integrada", 48, NAVY, True)
    s.text(55, 112, "Cliente nuevo en tienda física · Odoo propuesto · solicitud y respuesta", 30, MUTED)

    def event_card(x, y, width, height, title, lines, icon, color, fill, tag):
        s.rect(x, y, width, height, fill, color)
        s.icon(icon, x + 22, y + 20, color, 54)
        s.text(x + 100, y + 51, title, 33, color, True)
        s.lines(x + 25, y + 97, lines, 28, gap=34)
        s.text(x + 25, y + height - 18, tag, 24, color, True)

    event_card(340, 155, 1220, 160, "E01  Cotización aceptada por el cliente",
           ["Cliente / Ventas C03 → vendedor en CRM C01"], "document", BLUE, "#edf5fa",
           "Antecedente sintético · misma cotización y versión")
    s.arrow([(950, 315), (950, 405)], label="I03 · Ventas solicita la evaluación", label_at=(985, 369))
    event_card(340, 405, 1220, 160, "E02  Solicitud recibida",
           ["CRM C01 → Control C04 · bitácora RECIBIDA"], "crm", BLUE, "#edf5fa",
           "Permisos e idempotencia antes de evaluar")
    s.arrow([(950, 565), (950, 630)])
    s.rect(340, 630, 1220, 130, "#f3f5f7", NAVY)
    s.text(375, 675, "C04 coordina los controles", 35, NAVY, True)
    s.text(375, 724, "I04 oferta · I06 autorización · I05 stock si procede", 32)
    # Ramas de casos independientes; no son etapas sucesivas.
    for x in (340, 950, 1560):
        s.arrow([(950, 760), (950, 800), (x, 800), (x, 850)], "navy") if x != 950 else s.arrow([(950, 760), (950, 850)], "navy")
    branch = [
        (65, "E03  Validación", GREEN, "#eef8f3", ["C04 → CRM / Ventas", "ACEPTADA", "código VALIDADA", "EP-N01 · sin pedido"]),
        (675, "E04  Stock parcial", AMBER, "#fff7e9", ["C05 informa; C04 decide", "PROMESA_CONDICIONADA", "DISPONIBILIDAD_PARCIAL", "EP-S01 · 5 − 3 = 2"]),
        (1285, "E05  Sin aprobación", RED, "#fcf0f0", ["C06 se consulta; C04 decide", "RECHAZADA", "DESCUENTO_SIN_APROBACION", "EP-E01 · sin consulta de stock"]),
    ]
    for x, title, color, fill, lines in branch:
        s.rect(x, 850, 550, 245, fill, color)
        s.text(x + 22, 897, title, 35, color, True)
        s.lines(x + 22, 946, lines, 27, gap=37)
    s.text(65, 1143, "Tres variantes independientes", 29, MUTED)
    for x in (340, 950, 1560):
        s.arrow([(x, 1095), (x, 1175), (950, 1175), (950, 1230)], "navy") if x != 950 else s.arrow([(950, 1095), (950, 1230)], "navy")
    event_card(65, 1230, 1770, 160, "C07  Decisión registrada y respuesta a CRM / Ventas",
           ["I07 · DECISION + código · actor, fecha, SOL y COR · order_id = null"], "shield", NAVY, "#eef2f6",
           "Registro técnico en la simulación · diseño por implementar en Odoo")
    s.arrow([(450, 1390), (450, 1495)], "green", "Misma solicitud final y contenido", (80, 1445))
    event_card(65, 1495, 850, 195, "E07  Reintento recibido",
           ["CRM C01 → C04 por I03", "Recupera la respuesta original"], "control", GREEN, "#eef8f3",
           "REINTENTO · una sola decisión persistida")
    s.arrow([(1150, 1095), (1150, 1205), (1865, 1205), (1865, 1470), (1430, 1470), (1430, 1495)], "amber", dashed=True)
    event_card(1015, 1495, 820, 195, "E06  Necesidad de abastecer",
           [f'Arnés → dueño / abastecimiento · {cases["EP-S01"]["signal"]["signal_id"]}',
            "Solo tras respuesta parcial · brecha 2"], "stock", AMBER, "#fff7e9",
           "Señal conceptual O2C–P2P · fuera del contrato")
    s.text(65, 1747, "Línea continua: interacción interna · Discontinua: señal conceptual sin compra automática", 28, MUTED)
    s.text(65, 1795, "E01: narrativa previa · E02–E05 y E07: bitácora local · E06: arnés de evidencia", 28, MUTED)
    return s.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verificar vigencia y coherencia sin escribir")
    args = parser.parse_args()
    cases = load_cases()
    generated = {"componentes-crm-erp-ep.svg": architecture(cases),
                 "casos-arquitectura-ep.svg": case_diagram(cases),
                 "eventos-crm-erp-ep.svg": event_diagram(cases)}
    for name, content in generated.items():
        root = ET.fromstring(content)
        require(root.find("{http://www.w3.org/2000/svg}title") is not None, f"{name}: falta título accesible.")
        if args.check:
            path = HERE / name
            require(path.exists() and path.read_text(encoding="utf-8") == content,
                    f"{name}: gráfico ausente o desactualizado; regenerar y revisar.")
        else:
            (HERE / name).write_text(content, encoding="utf-8", newline="\n")
    print("OK: 3 casos existentes coherentes, 112 comprobaciones registradas y 3 SVG "
          + ("vigentes; sin modificaciones." if args.check else "generados."))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
