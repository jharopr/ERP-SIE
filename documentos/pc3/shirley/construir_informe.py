"""Genera el informe PC3 en Word sobre la plantilla oficial y lo exporta a PDF.

Fuente única: `informe_pc3_consolidado.md`, ordenado con las diez secciones de
`GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx`. Cada marcador
`<!-- INCLUIR: ruta.md -->` se reemplaza por el archivo indicado (5A y 5C de
Adrián, 5B-II de Shirley); `PENDIENTE_...` deja un aviso visible.

La plantilla conserva estilos, tamaño de página y portada; el cuerpo se
reconstruye con los mismos estilos (Heading1–4, TableGrid, encabezado de tabla
sombreado EAEAEA). Se eliminan las instrucciones y «[Completar por el grupo]».

Uso (solo biblioteca estándar; LibreOffice opcional para el PDF):

    python documentos/pc3/shirley/construir_informe.py --plantilla ruta/plantilla.docx
    python documentos/pc3/shirley/construir_informe.py --plantilla ruta/plantilla.docx --salida output/pc3
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FUENTE = HERE / "informe_pc3_consolidado.md"
NOMBRE = "GE703_PC3_Informe_G7_MYS_Hermanos"
MARCA = re.compile(r"^<!-- INCLUIR: (.+?) -->\s*$")
ANCHO = 8640  # ancho útil de la plantilla: 12240 − 2 × 1800 twips

PENDIENTES = {
    "PENDIENTE_5B_BENJAMIN": (
        "### 5B-I. Cadena de suministro: flujo, proveedores, demanda y capacidad\n\n"
        "> **Pendiente de incorporar: aporte de Benjamín Arancibia.** Debe usar las unidades de 5B.0 "
        "(unidades por referencia y ubicación, horas de apertura, semana de seis días) y partir de la "
        "red operativa de 5C.2.\n"),
}


# ---------------------------------------------------------------------------
# Ensamblado del Markdown
# ---------------------------------------------------------------------------
def bajar_encabezados(texto: str, niveles: int) -> str:
    salida, en_codigo = [], False
    for linea in texto.splitlines():
        if linea.startswith(("```", "~~~")):
            en_codigo = not en_codigo
        if not en_codigo and re.match(r"^#{1,4} ", linea):
            linea = "#" * niveles + linea
        salida.append(linea)
    return "\n".join(salida)


def enlaces_a_texto(texto: str, base: Path) -> str:
    def cambiar(m):
        etiqueta, destino = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:)", destino):
            return f"{etiqueta} ({destino})"
        if destino.startswith("#"):
            return etiqueta
        ruta = (base / destino.split("#")[0]).resolve()
        try:
            return f"{etiqueta} (`{ruta.relative_to(ROOT).as_posix()}`)"
        except ValueError:
            return etiqueta
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", cambiar, texto)


def ensamblar() -> str:
    partes, saltar = [], False
    for linea in FUENTE.read_text(encoding="utf-8").splitlines():
        if saltar:
            saltar = False
            if linea.startswith("*"):
                continue
        m = MARCA.match(linea)
        if not m:
            partes.append(linea)
            continue
        objetivo, saltar = m.group(1).strip(), True
        if objetivo in PENDIENTES:
            partes.append(PENDIENTES[objetivo])
            continue
        ruta = (HERE / objetivo).resolve()
        contenido = enlaces_a_texto(ruta.read_text(encoding="utf-8"), ruta.parent)
        partes.append(bajar_encabezados(contenido, 2))  # H1 del aporte → nivel 3 (Heading2)
    texto = enlaces_a_texto("\n".join(partes), HERE)
    texto = re.sub(r"^# .*\n", "", texto, count=1)                     # título: va en la portada
    texto = re.sub(r"^> Fuente editable del informe.*\n", "", texto, count=1, flags=re.M)  # nota interna
    return texto


# ---------------------------------------------------------------------------
# Markdown → WordprocessingML con los estilos de la plantilla
# ---------------------------------------------------------------------------
INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))")


def runs(texto: str, size: int | None = None, bold_base: bool = False) -> str:
    out = []
    for trozo in INLINE.split(texto):
        if not trozo:
            continue
        b, i, mono = bold_base, False, False
        if trozo.startswith("**") and trozo.endswith("**") and len(trozo) > 4:
            trozo, b = trozo[2:-2], True
        elif trozo.startswith("`") and trozo.endswith("`"):
            trozo, mono = trozo[1:-1], True
        elif trozo.startswith("*") and trozo.endswith("*") and len(trozo) > 2:
            trozo, i = trozo[1:-1], True
        props = ""
        if mono:
            props += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
        if b:
            props += "<w:b/>"
        if i:
            props += "<w:i/>"
        if size:
            props += f'<w:sz w:val="{size - 1 if mono else size}"/>'
        rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
        out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(trozo)}</w:t></w:r>')
    return "".join(out)


def parrafo(texto: str, estilo: str | None = None, extra_ppr: str = "", size: int | None = None) -> str:
    ppr = (f'<w:pStyle w:val="{estilo}"/>' if estilo else "") + extra_ppr
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{runs(texto, size)}</w:p>"


def celdas(linea: str) -> list[str]:
    linea = linea.strip().strip("|")
    partes, actual, en_code = [], "", False
    for ch in linea:
        if ch == "`":
            en_code = not en_code
        if ch == "|" and not en_code:
            partes.append(actual.strip())
            actual = ""
        else:
            actual += ch
    partes.append(actual.strip())
    return partes


def anchos(filas: list[list[str]]) -> list[int]:
    n = len(filas[0])
    peso, minimo = [], []
    for c in range(n):
        textos = [re.sub(r"[*`]", "", f[c]) if c < len(f) else "" for f in filas]
        largos = [len(t) for t in textos]
        palabra = max((len(w) for t in textos for w in t.split()), default=4)
        peso.append(max(6, min(60, sum(largos) / len(largos))) ** 0.8)
        minimo.append(min(2400, 150 + palabra * (110 if n <= 3 else 95)))
    total = sum(peso)
    w = [int(ANCHO * p / total) for p in peso]
    for _ in range(5):  # garantizar el ancho de la palabra más larga y repartir el resto
        faltan = [c for c in range(n) if w[c] < minimo[c]]
        if not faltan:
            break
        for c in faltan:
            w[c] = minimo[c]
        libres = [c for c in range(n) if c not in faltan]
        resto = ANCHO - sum(w[c] for c in faltan)
        pl = sum(peso[c] for c in libres) or 1
        for c in libres:
            w[c] = max(minimo[c], int(resto * peso[c] / pl))
    w[-1] += ANCHO - sum(w)
    return w


def tabla(filas: list[list[str]]) -> str:
    n = max(len(f) for f in filas)
    filas = [f + [""] * (n - len(f)) for f in filas]
    w = anchos(filas)
    size = 19 if n <= 3 else (17 if n == 4 else 16)
    grid = "".join(f'<w:gridCol w:w="{x}"/>' for x in w)
    xml = [('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
            f'<w:tblW w:type="dxa" w:w="{ANCHO}"/><w:tblLayout w:type="fixed"/>'
            '<w:tblLook w:firstColumn="1" w:firstRow="1" w:lastColumn="0" w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/>'
            f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>')]
    for k, fila in enumerate(filas):
        cab = k == 0
        trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if cab else "<w:trPr><w:cantSplit/></w:trPr>"
        tcs = []
        for c, txt in enumerate(fila):
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="EAEAEA"/>' if cab else ""
            ppr = "<w:pPr>" + ("<w:keepNext/>" if cab else "") + '<w:spacing w:before="20" w:after="20"/></w:pPr>'
            tcs.append(f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w[c]}"/>{shd}</w:tcPr>'
                       f'<w:p>{ppr}{runs(txt.replace("<br>", " "), size, bold_base=cab)}</w:p></w:tc>')
        xml.append(f"<w:tr>{trpr}{''.join(tcs)}</w:tr>")
    xml.append("</w:tbl>")
    xml.append('<w:p><w:pPr><w:spacing w:before="0" w:after="60"/></w:pPr></w:p>')
    return "".join(xml)


ESTILO_TITULO = {2: "Heading1", 3: "Heading2", 4: "Heading3", 5: "Heading4", 6: "Heading4"}


def md_a_xml(md: str) -> str:
    lineas = md.splitlines()
    out, i = [], 0
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
            continue
        m = re.match(r"^(#{2,6}) (.*)", l)
        if m:
            out.append(parrafo(m.group(2).strip(), ESTILO_TITULO[len(m.group(1))]))
            i += 1
            continue
        if l.startswith(("```", "~~~")):
            cerca, i, bloque = l[:3], i + 1, []
            while i < len(lineas) and not lineas[i].startswith(cerca):
                bloque.append(lineas[i])
                i += 1
            i += 1
            for b in bloque:
                out.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:ind w:left="284"/></w:pPr>'
                           f'<w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="16"/></w:rPr>'
                           f'<w:t xml:space="preserve">{escape(b)}</w:t></w:r></w:p>')
            out.append('<w:p><w:pPr><w:spacing w:before="0" w:after="60"/></w:pPr></w:p>')
            continue
        if l.lstrip().startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                if not re.match(r"^\s*\|?\s*:?-{3,}", lineas[i]):
                    filas.append(celdas(lineas[i]))
                i += 1
            out.append(tabla(filas))
            continue
        if l.startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith(">"):
                bloque.append(lineas[i].lstrip(">").strip())
                i += 1
            out.append(parrafo(" ".join(x for x in bloque if x), "Quote"))
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.) (.*)", l)
        if m:
            while i < len(lineas):
                m = re.match(r"^(\s*)([-*]|\d+\.) (.*)", lineas[i])
                if not m:
                    break
                texto, i = m.group(3), i + 1
                while i < len(lineas) and lineas[i].startswith("  ") and lineas[i].strip() and not re.match(r"^\s*([-*]|\d+\.) ", lineas[i]):
                    texto += " " + lineas[i].strip()
                    i += 1
                marca = "–" if m.group(2) in "-*" else m.group(2)
                sangria = 360 + 360 * (len(m.group(1)) // 2)
                out.append(parrafo(f"{marca} {texto}", None,
                                   f'<w:spacing w:before="0" w:after="60"/><w:ind w:left="{sangria}" w:hanging="284"/>'))
            continue
        bloque = []
        while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#{2,6} |\||>|```|~~~|\s*([-*]|\d+\.) )", lineas[i]):
            bloque.append(lineas[i].strip())
            i += 1
        out.append(parrafo(" ".join(bloque)))
    return "".join(out)


# ---------------------------------------------------------------------------
# Inserción en la plantilla
# ---------------------------------------------------------------------------
PORTADA = [
    ("UNI · FIIS", None),
    ("Informe PC3 · Grupo 7", "Title"),
    ("GE703 · Sistemas Integrados Empresariales · 2026-2", None),
    ("Importaciones MYS Hermanos S.A.C. · Activos y mantenimiento, cadena de suministro parte I y Agente SIE. "
     "Consolidación: Shirley Carrión Oré. Versión 1.0-borrador, 12/11/2026.", None),
]


def construir_docx(plantilla: Path, destino: Path, cuerpo_md: str) -> None:
    with zipfile.ZipFile(plantilla) as z:
        archivos = {n: z.read(n) for n in z.namelist()}
    doc = archivos["word/document.xml"].decode("utf-8")
    inicio = doc.index("<w:body>") + len("<w:body>")
    sect = doc.index("<w:sectPr", inicio)
    portada = "".join(parrafo(t, e) for t, e in PORTADA)
    nuevo = doc[:inicio] + portada + md_a_xml(cuerpo_md) + doc[sect:]
    archivos["word/document.xml"] = nuevo.encode("utf-8")
    # Título del documento en las propiedades
    core = archivos.get("docProps/core.xml")
    if core:
        c = core.decode("utf-8")
        c = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>Informe PC3 Grupo 7 MYS Hermanos</dc:title>", c)
        archivos["docProps/core.xml"] = c.encode("utf-8")
    ajustes = archivos["word/settings.xml"].decode("utf-8")
    ajustes = re.sub(r"<w:zoom(?![^>]*w:percent)", '<w:zoom w:percent="100"', ajustes)
    archivos["word/settings.xml"] = ajustes.encode("utf-8")
    archivos.pop("docProps/thumbnail.jpeg", None)
    if "docProps/thumbnail.jpeg" not in archivos:
        rels = archivos["_rels/.rels"].decode("utf-8")
        rels = re.sub(r'<Relationship[^>]*thumbnail\.jpeg"[^>]*/>', "", rels)
        archivos["_rels/.rels"] = rels.encode("utf-8")
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in ["[Content_Types].xml"] + [n for n in archivos if n != "[Content_Types].xml"]:
            if not nombre.endswith("/"):
                z.writestr(nombre, archivos[nombre])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plantilla", type=Path, required=True, help="GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx")
    parser.add_argument("--salida", type=Path, default=ROOT / "output" / "pc3")
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    md = ensamblar()
    (args.salida / f"{NOMBRE}.md").write_text(md, encoding="utf-8")
    docx = args.salida / f"{NOMBRE}.docx"
    construir_docx(args.plantilla, docx, md)
    print(f"Word: {docx}")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(args.salida), str(docx)],
                       check=True, capture_output=True)
        print(f"PDF: {args.salida / (NOMBRE + '.pdf')}")
    else:
        print("LibreOffice no disponible: exporte el PDF desde Word")
    return 0


if __name__ == "__main__":
    sys.exit(main())
