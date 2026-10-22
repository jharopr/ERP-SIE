"""Genera SVG nativos, editables y sin dependencias para el bloque de Benjamin.

Ejecutar: python documentos/ep/benjamin/diagramas/generar_diagramas.py
Las fuentes Mermaid paralelas documentan la misma semántica del proceso.
"""

from pathlib import Path
from html import escape

BASE = Path(__file__).resolve().parent
C = {
    "ink": "#15324A", "muted": "#526578", "line": "#4A637A",
    "blue": "#006C87", "pale": "#E8F6FA", "green": "#176447",
    "greenp": "#EAF7EF", "amber": "#87540A", "amberp": "#FFF4DC",
    "gray": "#F1F4F7", "grayline": "#ABB6C2", "red": "#9D3131",
    "redp": "#FFF0EF", "white": "#FFFFFF", "bg": "#FBFCFE",
}


class SVG:
    def __init__(self, title, height=1000):
        self.h = height
        self.a = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" role="img" aria-labelledby="title desc">',
                  f'<title id="title">{escape(title)}</title>',
                  '<desc id="desc">Caso didáctico de IMPORTACIONES MYS HERMANOS S.A.C. Cliente nuevo persona natural, público general y canal físico. Diseño y simulación local; Odoo no desplegado. Datos sintéticos.</desc>',
                  '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="#4A637A"/></marker><marker id="amberarrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="#87540A"/></marker><marker id="grayarrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="#ABB6C2"/></marker></defs>',
                  '<style>text {font-family: "Segoe UI", Arial, sans-serif;} .title {font-weight:700;} </style>',
                  f'<rect width="1600" height="{height}" fill="{C["bg"]}"/>']

    def rect(self, x, y, w, h, fill="white", stroke="grayline", radius=12, width=1.5, dashed=False):
        dash = ' stroke-dasharray="7 6"' if dashed else ''
        self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{C.get(fill, fill)}" stroke="{C.get(stroke, stroke)}" stroke-width="{width}"{dash}/>')

    def text(self, x, y, value, size=20, color="ink", bold=False, anchor="start"):
        self.a.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{C.get(color, color)}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(value)}</text>')

    def lines(self, x, y, values, size=19, step=27, color="ink", bold=False, anchor="start"):
        for i, value in enumerate(values):
            self.text(x, y + i * step, value, size, color, bold, anchor)

    def card(self, x, y, w, h, title, lines=(), fill="white", stroke="blue", size=19, title_size=21):
        self.rect(x, y, w, h, fill, stroke)
        self.text(x + 18, y + 32, title, title_size, stroke, True)
        self.lines(x + 18, y + 61, lines, size=size, step=25)

    def arrow(self, points, color="line", dashed=False, width=2.2, end=True):
        pts = " ".join(f"{x},{y}" for x, y in points)
        marker = "amberarrow" if color == "amber" else "grayarrow" if color == "grayline" else "arrow"
        dash = ' stroke-dasharray="7 6"' if dashed else ''
        arrow = f' marker-end="url(#{marker})"' if end else ''
        self.a.append(f'<polyline points="{pts}" fill="none" stroke="{C.get(color, color)}" stroke-width="{width}" stroke-linejoin="round"{dash}{arrow}/>')

    def header(self, n, title, subtitle):
        self.rect(36, 30, 47, 47, "ink", "ink", radius=10)
        self.text(59, 62, n, 22, "white", True, "middle")
        self.text(102, 61, title, 30, bold=True)
        self.text(41, 106, subtitle, 19, "muted")

    def footer(self):
        self.text(42, self.h - 39, "Diseño / simulación local · Odoo no desplegado · cantidades, precios y stock sintéticos", 17, "muted")
        self.text(42, self.h - 14, "IMPORTACIONES MYS HERMANOS S.A.C. · Público general · Canal físico walk-in · Continuidad PC2 v2.1", 16, "muted")

    def save(self, name):
        self.a.append('</svg>')
        (BASE / name).write_text("\n".join(self.a), encoding="utf-8")


def mapa_corporativo():
    s = SVG("Mapa corporativo de procesos — IMPORTACIONES MYS HERMANOS S.A.C.")
    s.header("01", "Mapa corporativo · nivel 1", "Comercialización de autoradios: procesos estratégicos, misionales y de soporte. Propuesta analítica del caso.")
    s.text(52, 157, "PROCESOS ESTRATÉGICOS", 20, bold=True)
    for x, title, lines in [
        (55, "Dirección del negocio", ["Objetivos comerciales", "y seguimiento del desempeño"]),
        (435, "Gestión comercial", ["Precios, descuentos", "y propuesta de valor"]),
        (815, "Planificación de compras", ["Proveedores, reposición", "y disponibilidad objetivo"]),
        (1195, "Control y mejora", ["Indicadores, riesgos", "y experiencia del cliente"]),
    ]:
        s.card(x, 180, 350, 120, title, lines, "gray", "line", size=19, title_size=21)

    s.rect(210, 335, 1160, 245, "pale", "blue", width=2)
    s.text(232, 370, "PROCESOS MISIONALES / CORE", 21, "blue", True)
    s.card(235, 398, 340, 138, "O2C · venta al cliente", ["Consulta → cotización →", "solicitud y respuesta ERP", "Resto O2C: contexto fuera EP"], "white", "blue")
    s.card(625, 398, 340, 138, "Inventario comercial", ["Consulta de disponibilidad", "y control de existencias", "Sin reserva en la demo EP"], "white", "blue")
    s.card(1015, 398, 330, 138, "P2P · abastecimiento", ["Necesidad → compra →", "recepción y pago proveedor", "En EP: señal y evaluación"], "white", "blue")
    s.arrow([(575, 468), (625, 468)])
    s.arrow([(965, 468), (1015, 468)], "amber", dashed=True)
    s.text(805, 564, "Interacciones entre procesos; no representa una secuencia de producción", 17, "muted", anchor="middle")
    s.card(28, 401, 157, 156, "Entrada", ["Necesidad del", "cliente nuevo", "público general", "Canal físico"], "greenp", "green", size=16, title_size=20)
    s.arrow([(185, 469), (210, 469)])
    s.card(1398, 401, 175, 156, "Valor esperado", ["Cotización clara", "y respuesta", "trazable para", "decidir la compra"], "greenp", "green", size=17, title_size=19)
    s.arrow([(1370, 469), (1398, 469)])

    s.text(52, 635, "PROCESOS DE SOPORTE", 20, bold=True)
    for x, title, lines in [
        (55, "Administración y finanzas", ["Caja, registros y control", "de obligaciones"]),
        (435, "Sistemas y datos", ["Catálogo, clientes, versiones", "y trazabilidad documental"]),
        (815, "Gestión de personas", ["Roles, responsabilidades", "y capacidades comerciales"]),
        (1195, "Cumplimiento y archivo", ["Documentos, autorizaciones", "y evidencias del proceso"]),
    ]:
        s.card(x, 658, 350, 120, title, lines, "gray", "line", size=18, title_size=20)
    s.rect(55, 817, 1490, 82, "amberp", "amber")
    s.lines(77, 848, ["Alcance seleccionado: O2C presencial de cliente persona natural NUEVA, desde consulta hasta respuesta a solicitud ERP.", "Empresa comercializadora: el mapa no incorpora manufactura. Los procesos de soporte y P2P se incluyen como contexto."], 19, 27, "amber")
    s.footer()
    s.save("01-mapa-corporativo.svg")


def mapa_integrado():
    s = SVG("Mapa integrado O2C y P2P — alcance del examen parcial")
    s.header("02", "Mapa integrado · O2C y su enlace con P2P", "Una vista: bloque comercial EP, señal de reposición y contexto corporativo. Sin pedido, reserva ni compra ejecutada.")
    s.text(46, 148, "O2C · RECORRIDO EVALUADO EN EL EXAMEN PARCIAL", 20, "blue", True)
    cards = [
        (50, "01 · Consulta física", ["Cliente nuevo walk-in", "5 autoradios familiares", "09:45"]),
        (350, "02 · Cliente + lead", ["CLI-DEMO-001", "LEAD-EP-001", "09:46"]),
        (650, "03 · Oportunidad", ["OPP-DEMO-001", "Público general / físico", "09:48"]),
        (950, "04 · Stock referencial", ["Caso base: 8 disponibles", "Consulta; sin reserva", "09:50"]),
        (1250, "05 · Cotización v1", ["COT-DEMO-001 · S/ 1 900", "5 × S/ 400; descuento 5%", "09:52"]),
    ]
    for x, title, lines in cards:
        s.card(x, 175, 250, 130, title, lines, "pale", "blue", size=16, title_size=18)
    for x in [300, 600, 900, 1200]:
        s.arrow([(x, 240), (x + 50, 240)])
    for x, title, lines, fill, stroke in [
        (1250, "06 · Aceptación exacta", ["ACE-EP-001 → versión 1", "Acepta términos cotizados", "09:54"], "pale", "blue"),
        (950, "07 · Solicitud a ERP", ["SOL-EP-N01 / COR-EP-001", "Vendedor envía datos", "09:55"], "pale", "blue"),
        (650, "08 · Evaluación lógica", ["Cliente, precio y versión", "Descuento autorizado", "Reglas de disponibilidad"], "pale", "blue"),
        (350, "09 · Respuesta", ["ACEPTADA / VALIDADA", "order_id: null", "09:55:01"], "greenp", "green"),
        (50, "CORTE DEL EP", ["Solicitud validada", "Sin pedido ni reserva", "No hay venta concluida"], "redp", "red"),
    ]:
        s.card(x, 355, 250, 130, title, lines, fill, stroke, size=16, title_size=18)
    s.arrow([(1375, 305), (1375, 355)])
    for x in [1250, 950, 650, 350]:
        s.arrow([(x, 420), (x - 50, 420)])

    s.arrow([(775, 485), (775, 517), (750, 517), (750, 550)], "amber", dashed=True)
    s.text(795, 533, "Tras controles conformes", 16, "amber")
    s.card(605, 550, 290, 100, "PROMESA_CONDICIONADA", ["EP-S01: disponible 3; déficit 2", "Evaluación de disponibilidad"], "amberp", "amber", size=16, title_size=17)
    s.card(965, 550, 260, 100, "Necesidad de reposición", ["REP-EP-001 · enlace P2P", "Sin OC ni fecha prometida"], "amberp", "amber", size=16, title_size=18)
    s.card(1265, 550, 290, 100, "Dueño / compras evalúa", ["Factibilidad de abastecimiento", "Sin orden de compra ni fecha"], "amberp", "amber", size=16, title_size=18)
    s.arrow([(895, 595), (965, 595)], "amber", dashed=True)
    s.arrow([(1225, 595), (1265, 595)], "amber", dashed=True)
    s.text(45, 598, "Caso base: 8 ≥ 5; no activa reposición.", 18, "muted")
    s.text(45, 625, "EP-S01: stock parcial; sin promesa firme.", 17, "muted")

    s.rect(42, 673, 1516, 172, "gray", "grayline", dashed=True)
    s.text(62, 701, "P2P COMPLETO · SOLO CONTEXTO / NO EJECUTADO EN LA DEMOSTRACIÓN EP", 18, "muted", True)
    labels = [("Selección proveedor", "Cotizar / evaluar"), ("Orden de compra", "Aprobar / emitir OC"),
              ("Recepción", "Conformidad de bienes"), ("Factura proveedor", "Validación / cuenta por pagar"),
              ("Pago proveedor", "Programación y desembolso"), ("Cierre P2P", "Aplicación / conciliación")]
    for i, (title, line) in enumerate(labels):
        x = 62 + i * 250
        s.card(x, 717, 225, 70, title, [line], "white", "grayline", size=14, title_size=16)
        if i < 5:
            s.arrow([(x + 225, 753), (x + 250, 753)], "grayline", dashed=True)
    s.arrow([(1410, 650), (1410, 657), (30, 657), (30, 753), (62, 753)], "grayline", dashed=True)
    s.arrow([(675, 787), (675, 810), (830, 810)], "grayline", dashed=True)
    s.text(842, 817, "Retorno a stock futuro tras recepción; no modifica el stock de esta demo", 17, "muted")

    s.rect(42, 869, 1516, 53, "gray", "grayline")
    s.text(62, 901, "O2C posterior · CONTEXTO FUERA DEL EP: pedido → reserva → facturación / entrega → cobro aplicado", 20, "muted")
    s.footer()
    s.save("02-mapa-integrado-o2c-p2p.svg")


def flujo_roles():
    s = SVG("Flujo por roles y reglas de la solicitud comercial del examen parcial")
    s.header("03", "Flujo por roles · validación y excepciones", "Representación funcional por responsabilidades. Odoo es un rol lógico simulado; la aceptación comercial no crea un pedido.")
    for i, (title, sub) in enumerate([
        ("Cliente", "Persona natural nueva"), ("Vendedor", "Atención presencial"),
        ("Odoo · rol lógico", "Validación local simulada"), ("Dueño / abastecimiento", "Autorización y reposición"),
    ]):
        x = 35 + i * 390
        s.rect(x, 135, 365, 765, "white" if i % 2 == 0 else "gray", "grayline", radius=10)
        s.rect(x, 135, 365, 75, "ink", "ink", radius=10)
        s.text(x + 18, 165, title, 23, "white", True)
        s.text(x + 18, 192, sub, 17, "white")
    s.card(55, 230, 325, 99, "Consulta física", ["5 autoradios para vehículos", "familiares · walk-in"], "pale", "blue", size=18, title_size=20)
    s.card(445, 230, 325, 99, "Identificar + registrar", ["CLI-DEMO-001 / LEAD-EP-001", "Sin campaña atribuida"], "pale", "blue", size=17, title_size=20)
    s.arrow([(380, 274), (445, 274)])
    s.card(445, 345, 325, 81, "Crear oportunidad", ["OPP-DEMO-001 · solicitar stock"], "pale", "blue", size=17, title_size=20)
    s.arrow([(607, 329), (607, 345)])
    s.card(835, 345, 325, 81, "Consultar disponibilidad", ["Stock referencial: 8; sin reserva"], "pale", "blue", size=17, title_size=20)
    s.arrow([(770, 385), (835, 385)])
    s.card(1225, 345, 325, 150, "P2P conceptual [1]", ["EP-S01: disponible 3; déficit 2", "PROMESA_CONDICIONADA", "REP-EP-001 · sin OC ni fecha", "Tras controles conformes; sin compra"], "amberp", "amber", size=16, title_size=20)
    s.card(445, 465, 325, 94, "Cotizar versión 1", ["S/ 2 000 − S/ 100 = S/ 1 900", "Stock parcial: promesa condicionada"], "pale", "blue", size=16, title_size=20)
    s.arrow([(997, 426), (997, 447), (607, 447), (607, 465)])
    s.card(55, 465, 325, 94, "Aceptar términos exactos", ["ACE-EP-001 acepta COT-DEMO-001", "Versión 1 y monto S/ 1 900"], "pale", "blue", size=16, title_size=20)
    s.arrow([(445, 512), (380, 512)])
    s.card(445, 604, 325, 120, "Enviar solicitud al ERP", ["Referencias CLI / OPP / COT", "Versión / ACE / SOL / COR", "Importes: snapshot de cotización"], "pale", "blue", size=17, title_size=20)
    s.arrow([(217, 559), (217, 657), (445, 657)])
    s.card(835, 604, 325, 120, "Validar reglas [1]", ["Cliente y aceptación coherentes", "Precio y versión vigentes", "5% permitido; stock informado"], "pale", "blue", size=17, title_size=20)
    s.arrow([(770, 657), (835, 657)])
    s.card(1225, 604, 325, 120, "Excepción de descuento", ["10% exige aprobación del dueño", "Si no existe: RECHAZADA", "No se crea pedido ni reserva"], "redp", "red", size=17, title_size=20)
    s.arrow([(1160, 657), (1225, 657)], "amber", dashed=True)
    s.card(835, 777, 325, 92, "Resultado caso base", ["Estado ACEPTADA · código VALIDADA", "order_id: null"], "greenp", "green", size=16, title_size=20)
    s.arrow([(997, 724), (997, 777)])
    s.lines(1012, 739, ["5% y datos", "conformes"], 16, 22, "green")
    s.card(445, 777, 325, 92, "Recibir y explicar respuesta", ["09:55:01 · solicitud validada", "No equivale a una venta cerrada"], "greenp", "green", size=17, title_size=20)
    s.arrow([(835, 823), (770, 823)])
    s.rect(40, 914, 1510, 33, "redp", "red", radius=7)
    s.text(795, 937, "FIN DEL BLOQUE EP · Detener antes de crear pedido, reservar stock o ejecutar procesos posteriores del O2C", 18, "red", True, "middle")
    s.footer()
    s.save("03-flujo-roles-validacion.svg")


def linea_tiempo():
    s = SVG("Línea de tiempo y trazabilidad de la demostración comercial", height=900)
    s.header("04", "Línea de tiempo · una operación correlacionada", "Fecha lógica didáctica: 24/10/2026 · zona horaria UTC−05:00 · COR-EP-001 · Cliente nuevo / público general / canal físico")
    s.text(45, 148, "Lectura: fila superior de izquierda a derecha; continúa por la fila inferior de derecha a izquierda.", 19, "muted")
    events = [
        (50, 180, "09:45", "1 · Consulta física", ["5 autoradios para vehículos", "familiares. Cliente nuevo", "persona natural, walk-in."]),
        (435, 180, "09:46", "2 · Cliente + lead", ["CLI-DEMO-001", "LEAD-EP-001", "Canal físico; sin campaña."]),
        (820, 180, "09:48", "3 · Oportunidad", ["OPP-DEMO-001", "Necesidad comercial trazada", "al lead y al cliente."]),
        (1205, 180, "09:50", "4 · Consulta de stock", ["8 unidades referenciales", "para una solicitud de 5.", "Sin reserva ni reposición."]),
        (1205, 505, "09:52", "5 · Cotización v1", ["COT-DEMO-001 · versión 1", "5 × S/ 400 = S/ 2 000", "5% = S/ 100 → S/ 1 900"]),
        (820, 505, "09:54", "6 · Aceptación", ["ACE-EP-001", "Acepta exactamente v1", "y el monto S/ 1 900."]),
        (435, 505, "09:55", "7 · Envío solicitud", ["SOL-EP-N01", "Solicitud comercial a ERP", "Correlación COR-EP-001."]),
        (50, 505, "09:55:01", "8 · Respuesta lógica", ["Estado: ACEPTADA", "Código: VALIDADA", "order_id: null"]),
    ]
    for x, y, time, title, lines in events:
        final = title.startswith("8")
        s.rect(x, y, 330, 227, "greenp" if final else "pale", "green" if final else "blue", width=2)
        s.text(x + 20, y + 43, time, 31, "green" if final else "blue", True)
        s.text(x + 20, y + 87, title, 23, bold=True)
        s.lines(x + 20, y + 126, lines, size=19, step=29)
        s.text(x + 20, y + 207, "COR-EP-001", 16, "muted")
    for x in [380, 765, 1150]:
        s.arrow([(x, 292), (x + 55, 292)])
    s.arrow([(1535, 292), (1565, 292), (1565, 618), (1535, 618)])
    for x in [1205, 820, 435]:
        s.arrow([(x, 618), (x - 55, 618)])
    s.rect(50, 775, 1485, 56, "redp", "red")
    s.text(792, 809, "CORTE: aceptación de la solicitud, sin pedido creado, sin reserva y sin ejecución de factura, entrega o cobro.", 20, "red", True, "middle")
    s.footer()
    s.save("04-linea-tiempo-trazabilidad.svg")


if __name__ == "__main__":
    mapa_corporativo()
    mapa_integrado()
    flujo_roles()
    linea_tiempo()
    print("Generados 4 diagramas SVG en", BASE)
