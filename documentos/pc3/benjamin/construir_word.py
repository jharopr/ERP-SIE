"""Genera el Word editable desde el Markdown único; requiere python-docx y Pillow.

Ejecutar desde cualquier directorio con el Python del runtime de documentos.
Las imágenes finales se incorporan en páginas apaisadas; sus fuentes editables
se conservan en diagramas/. No lee ni publica los adjuntos privados.
"""
from pathlib import Path
import re
from urllib.parse import quote
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
SOURCE=HERE/'seccion_5b_cadena_suministro.md'
OUTPUT=HERE/'GE703_PC3_G7_Cadena_Suministro_Parte_I_Benjamin.docx'
BASE='https://github.com/jharopr/ERP-SIE/blob/f8613b65993ab8d489fe7f17d8c0ae7785a4daf7/'
BLUE='1D4867'; PALE='F0F5F9'

def inline(p,text):
    pattern=r'(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)'
    for part in re.split(pattern,text):
        if not part: continue
        link=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',part)
        if link:
            label,target=link.groups()
            if not target.startswith('http'):
                target=BASE+quote((HERE/target).resolve().relative_to(REPO).as_posix())
            rid=p.part.relate_to(target,RT.HYPERLINK,is_external=True)
            h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rid)
            r=OxmlElement('w:r'); pr=OxmlElement('w:rPr'); c=OxmlElement('w:color');c.set(qn('w:val'),BLUE);pr.append(c);r.append(pr)
            t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);p._p.append(h)
        else:
            bold=part.startswith('**'); italic=part.startswith('*') and not bold
            txt=part[2:-2] if bold else part[1:-1] if italic or part.startswith('`') else part
            run=p.add_run(txt);run.bold=bold;run.italic=italic

def geometry(sec,landscape=False):
    sec.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sec.page_width=Cm(29.7 if landscape else 21)
    sec.page_height=Cm(21 if landscape else 29.7)
    sec.top_margin=Cm(1.65);sec.bottom_margin=Cm(1.6)
    sec.left_margin=Cm(1.8);sec.right_margin=Cm(1.8)
    sec.header_distance=Cm(.7);sec.footer_distance=Cm(.7)

def cell_shade(cell,fill):
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),fill);cell._tc.get_or_add_tcPr().append(sh)

def table(doc,rows):
    n=len(rows[0]);tab=doc.add_table(rows=0,cols=n)
    tab.alignment=WD_TABLE_ALIGNMENT.CENTER;tab.autofit=False
    if n==2: widths=[4.5,12.9]
    elif 'KPI' in rows[0][0]: widths=[4.0,6.6,6.8]
    elif 'Proveedor' in rows[0][0]: widths=[4.5,5.4,7.5]
    else: widths=[3.9,6.4,7.1]
    for c,w in zip(tab.columns,widths):c.width=Cm(w)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
    tab._tbl.tblPr.append(borders)
    for i,row in enumerate(rows):
        cells=tab.add_row().cells
        trpr=tab.rows[-1]._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if i==0: trpr.append(OxmlElement('w:tblHeader'))
        for cell,txt,w in zip(cells,row,widths):
            cell.width=Cm(w);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell_shade(cell,BLUE if i==0 else PALE if i%2==0 else 'FFFFFF')
            margins=OxmlElement('w:tcMar')
            for key in ['top','left','bottom','right']:
                v=OxmlElement('w:'+key);v.set(qn('w:w'),'85');v.set(qn('w:type'),'dxa');margins.append(v)
            cell._tc.get_or_add_tcPr().append(margins)
            p=cell.paragraphs[0];inline(p,txt)
            p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
            p.paragraph_format.line_spacing=1.02
            if i==0:p.paragraph_format.keep_with_next=True
            for r in p.runs:
                r.font.size=Pt(9.0)
                if i==0:r.bold=True;r.font.color.rgb=RGBColor.from_string('FFFFFF')
    doc.add_paragraph().paragraph_format.space_after=Pt(1)

def build():
    doc=Document();geometry(doc.sections[0])
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10.5)
    normal.font.color.rgb=RGBColor(0,0,0)
    normal.paragraph_format.space_after=Pt(5)
    normal.paragraph_format.line_spacing=1.04
    normal.paragraph_format.widow_control=True
    for name,size in [('Title',21),('Heading 1',14),('Heading 2',11.5)]:
        sty=doc.styles[name];sty.font.name='Calibri';sty.font.size=Pt(size)
        sty.font.color.rgb=RGBColor(0,0,0)
        sty.paragraph_format.space_before=Pt(9);sty.paragraph_format.space_after=Pt(5)
    doc.styles['Title'].paragraph_format.space_before=Pt(0)
    # El estilo Title de la plantilla de python-docx incluye una regla azul.
    for sty in doc.styles:
        for border in list(sty.element.findall('.//'+qn('w:pBdr'))):
            border.getparent().remove(border)
    doc.styles['Caption'].font.size=Pt(9)
    doc.styles['Caption'].font.color.rgb=RGBColor.from_string('42576A')
    foot=doc.sections[0].footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    foot.add_run('GE703 PC3 · G7 · 5B  |  ').font.size=Pt(8)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
    doc.core_properties.title='Cadena de suministro Parte I de Importaciones MYS Hermanos'
    doc.core_properties.subject='GE703 PC3 Sección 5B Grupo 7'
    doc.core_properties.author='Benjamín Francis Arancibia Ynga'
    doc.core_properties.keywords='PC3, MYS, suministro, proveedores, demanda, inventarios'
    lines=SOURCE.read_text(encoding='utf8').splitlines();i=0;image_mode=False;figures=[];sources_mode=False
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('**Fuentes internas consultadas'):sources_mode=True
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',v) for v in row):rows.append(row)
                i+=1
            table(doc,rows);continue
        im=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if im:
            label,target=im.groups();p=doc.add_paragraph(label,style='Heading 1')
            # El texto remite a las figuras; se agrupan al final para evitar
            # páginas vacías y huecos al alternar orientación.
            p._p.getparent().remove(p._p)
            figures.append({'label':label,'path':target,'caption':''})
            image_mode=True;i+=1;continue
        if image_mode and line.startswith('*Figura'):
            figures[-1]['caption']=line[1:-1]
            image_mode=False;i+=1;continue
        m=re.match(r'^(#{1,3})\s+(.*)',line)
        if m:
            level=len(m.group(1));txt=m.group(2)
            doc.add_paragraph(txt,style='Title' if level==1 else f'Heading {level-1}')
        elif line.startswith('- '):
            p=doc.add_paragraph(style='Normal');p.paragraph_format.left_indent=Cm(.3)
            p.paragraph_format.first_line_indent=Cm(-.3);inline(p,'• '+line[2:])
            if '[Odoo' in line or '[BPMN' in line: p.paragraph_format.space_after=Pt(3)
        else:
            p=doc.add_paragraph();inline(p,line)
            p.paragraph_format.keep_together=True
        if sources_mode:
            p.paragraph_format.space_after=Pt(3)
            for r in p.runs:r.font.size=Pt(9)
        i+=1
    for fig in figures:
        sec=doc.add_section(WD_SECTION_START.NEW_PAGE);geometry(sec,True)
        pic=HERE/fig['path']
        with Image.open(pic) as img:ratio=img.height/img.width
        width=min(26.1,16.0/ratio)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(pic),width=Cm(width))
        p=doc.add_paragraph(style='Caption');inline(p,fig['caption'])
    doc.save(OUTPUT)
    print(OUTPUT)
    print(f'{len(doc.paragraphs)} paragraphs; {len(doc.tables)} tables; {len(doc.inline_shapes)} figures')

if __name__=='__main__':build()
