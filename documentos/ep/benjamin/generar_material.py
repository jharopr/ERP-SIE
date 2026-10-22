"""Construye journeys SVG, informe y panel local desde fuentes editables.

Requiere markdown para el informe HTML. No modifica insumos ni PC2.
"""

from pathlib import Path
from html import escape
import json
import hashlib
import re
import textwrap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIGURES = HERE / 'diagramas'
EVIDENCE = ROOT / 'pruebas' / 'ep-benjamin' / 'evidencias'

STAGES = ['Llegada', 'Necesidad', 'Disponibilidad', 'Oferta', 'Aceptación', 'Respuesta']
JOURNEYS = {
    'actual': {
        'title': 'Journey actual del cliente en tienda',
        'subtitle': 'Reconstrucción documental del diagnóstico. Fricciones y emociones son hipótesis por validar con clientes.',
        'rows': [
            ('Cliente', ['Pide orientación sobre autoradios', 'Explica cinco unidades y uso final', 'Pregunta si hay disponibilidad', 'Compara precio y descuento', 'Acepta o pide un ajuste', 'Pregunta qué sigue']),
            ('Interacción visible', ['Mostrador y vendedor', 'Conversación presencial', 'Consulta y respuesta manual', 'Oferta comunicada al cliente', 'Consulta al dueño si excede facultad', 'Información del vendedor']),
            ('Fricción a validar', ['Espera sin referencia de atención', 'Repetir datos o perder contexto', 'Stock sin fuente, hora o distinción de reserva', 'Versiones o condiciones poco claras', 'Aceptación ambigua y espera de autorización', 'Confundir oferta con compra confirmada']),
            ('Emoción hipotética', ['Interés y expectativa', 'Interés con posible esfuerzo', 'Incertidumbre', 'Evaluación y duda', 'Espera o duda', 'Incertidumbre sobre el siguiente paso']),
            ('Qué contrastar', ['Llegada y comienzo de atención', 'Necesidad y compatibilidad registrada', 'SKU, ubicación, fuente y hora', 'Oferta, total y vigencia', 'Versión y decisión del dueño', 'Estado comunicado y responsable']),
        ],
        'scores': [4, 3, 2, 3, 2, 2],
        'footer': 'No es un journey observado ni una medición de satisfacción. Se mantiene el corte previo al pedido para comparar.'
    },
    'propuesto': {
        'title': 'Journey propuesto del cliente en tienda',
        'subtitle': 'Público general nuevo · visita espontánea · experiencia deseada hasta la respuesta a la solicitud ERP.',
        'rows': [
            ('Cliente', ['Recibe orientación y responsable', 'Explica uso y cinco unidades', 'Conoce disponibilidad consultada', 'Recibe v1 por S/ 1,900 con vigencia', 'Acepta expresamente COT v1', 'Conoce el estado y siguiente paso']),
            ('Trabajo interno', ['Registrar consulta física 09:45', 'Buscar cliente; calificar lead y oportunidad', 'Consultar Inventario sin reservar', 'Calcular precio y controlar facultad 5 %', 'Vincular aceptación; enviar solicitud', 'Validar; comunicar motivo y responsable']),
            ('Evidencia', ['Canal FISICO y visita espontánea', 'CLI-DEMO-001 / LEAD-EP-001 / OPP-DEMO-001', 'SKU RAD-7BT, ubicación y hora', 'COT-DEMO-001 v1; total y vencimiento', 'ACE-EP-001 / SOL-EP-N01', 'COR-EP-001; estado ACEPTADA y código VALIDADA']),
            ('Emoción deseada', ['Orientación', 'Confianza en la atención', 'Claridad sobre límites', 'Comprensión de la oferta', 'Seguridad sobre lo aceptado', 'Claridad aun ante una espera']),
            ('Control y mejora', ['Responsable identificado', 'Minimizar datos y evitar duplicidad', 'Observación no equivale a reserva', 'Nueva versión si cambian condiciones', 'Aceptación exacta de la versión', 'Stock parcial: REP-EP-001; sin fecha ni compra']),
        ],
        'scores': [4, 4, 4, 4, 4, 4],
        'footer': 'Diseño por validar · emociones no medidas · sin pedido, reserva ni P2P ejecutado · datos sintéticos.'
    }
}


def svg_journey(key, item):
    colors = ['#e9f4f8', '#f4f7fa', '#e9f4f8', '#f4f7fa', '#e9f4f8', '#f4f7fa']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1010" viewBox="0 0 1800 1010" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(item["title"])}</title>', f'<desc id="desc">{escape(item["subtitle"])}</desc>',
             '<rect width="1800" height="1010" fill="#ffffff"/>',
             '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#173148}</style>']
    def text(x, y, value, size=20, bold=False, fill='#173148'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" style="fill:{fill}">{escape(value)}</text>')
    text(42, 57, item['title'], 34, True)
    text(42, 95, item['subtitle'], 19)
    x0, left, col, top, row_h = 42, 170, 257, 160, 145
    for i, stage in enumerate(STAGES):
        x = x0 + left + i * col
        parts.append(f'<rect x="{x}" y="125" width="{col-4}" height="47" rx="7" fill="#173148"/>')
        text(x+14, 155, f'{i+1}  {stage}', 21, True, '#ffffff')
    for r, (label, values) in enumerate(item['rows']):
        y = top + 20 + r * row_h
        for j, line in enumerate(textwrap.wrap(label, 16)):
            text(x0+5, y+35+j*25, line, 19, True)
        for c, value in enumerate(values):
            x = x0 + left + c * col
            parts.append(f'<rect x="{x}" y="{y}" width="{col-4}" height="{row_h-5}" rx="4" fill="{colors[c]}"/>')
            for n, line in enumerate(textwrap.wrap(value, width=24, break_long_words=False)):
                text(x+13, y+33+n*26, line, 20)
    text(42, 953, item['footer'], 18)
    text(42, 985, 'IMPORTACIONES MYS HERMANOS S.A.C. · Benjamin Arancibia · GE703 G7 · Examen parcial 24/10/2026', 17)
    parts.append('</svg>')
    (FIGURES / f'{"05" if key == "actual" else "06"}-journey-{key}.svg').write_text('\n'.join(parts), encoding='utf-8')
    lines = ['journey', f'    title {item["title"]} emociones hipotéticas', '    section Tramo comercial hasta solicitud y respuesta']
    for stage, score in zip(STAGES, item['scores']):
        lines.append(f'        {stage}: {score}: Cliente')
    (FIGURES / f'{"05" if key == "actual" else "06"}-journey-{key}.mmd').write_text('\n'.join(lines)+'\n', encoding='utf-8')


STYLE = '''
*{box-sizing:border-box} body{margin:0;background:#edf1f4;color:#1d2a37;font:16px/1.5 "Segoe UI",Arial,sans-serif}
a{color:#006882} main{max-width:1220px;margin:36px auto} .sheet{background:white;margin:24px 0;padding:38px 48px;box-shadow:0 3px 16px #17314812;}
.meta{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#617081;margin-bottom:14px}
h1,h2,h3{color:#000;line-height:1.2;break-after:avoid}h1{font-size:36px}h2{font-size:27px;margin:0 0 20px}h3{font-size:19px;margin:20px 0 10px}
p{margin:10px 0} table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.35;margin:18px 0}th,td{border:1px solid #d9d9d9;padding:10px 11px;vertical-align:middle;text-align:left}th{background:#173148;color:#fff}tbody tr:nth-child(even){background:#f1f6f9}
tr{break-inside:avoid}thead{display:table-header-group} img{display:block;width:100%;height:auto;margin:18px auto 12px;max-height:610px;object-fit:contain;break-inside:avoid}p:has(>img){break-inside:avoid}
pre{white-space:pre-wrap;background:#f3f5f7;padding:14px;border:1px solid #d9d9d9}code{font-family:Consolas,monospace;font-size:.91em;overflow-wrap:anywhere}li{margin:9px 0}.pagefoot{font-size:11px;color:#677786;margin-top:24px}
@page{size:A4 landscape;margin:12mm 14mm}
@media print{body{background:#fff;font-size:10.5pt;line-height:1.35}main{max-width:none;margin:0}.sheet{padding:0;margin:0;box-shadow:none;break-before:page;min-height:0}.sheet:first-child{break-before:auto}.meta{font-size:8pt;margin:0 0 3mm}h1{font-size:25pt}h2{font-size:18pt;margin-bottom:4mm}h3{font-size:12pt;margin:3mm 0 2mm}p{margin:2mm 0}table{font-size:9.1pt;line-height:1.28;margin:3mm 0}th,td{padding:2mm 2.2mm}img{max-height:137mm;margin:2mm auto;object-fit:contain}a{color:#18546b;text-decoration:none}.pagefoot{display:none}li{margin:2mm 0}pre{font-size:9pt;padding:3mm}}
'''


def build_report():
    import markdown
    source = (HERE / 'aporte-benjamin.md').read_text(encoding='utf-8')
    chunks = re.split(r'(?m)^## ', source)
    content = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            continue
        rendered = markdown.markdown('## '+chunk, extensions=['tables', 'fenced_code'])
        # Las figuras ya contienen la matriz completa. Las tablas ampliadas se
        # conservan en Markdown, sin duplicarlas tras la figura en el PDF.
        if i in (7,8,9,10):
            rendered = re.sub(r'<table>.*?</table>', '', rendered, flags=re.S)
        if i == 1:
            rendered = rendered.replace('<h2>1 Decisión que defiende Benjamin</h2>', '<h1>Recorrido O2C para el examen parcial</h1><h3>La decisión que defiende Benjamin</h3>')
        if i == 18:
            rendered = rendered.replace('<p><strong>Criterio de consistencia entre fuentes.</strong>', '</section><section class="sheet"><div class="meta">GE703 · G7 · Aporte de Benjamin · Examen parcial 24/10/2026</div><h2>Supuestos y revisión del aporte</h2><p><strong>Criterio de consistencia entre fuentes.</strong>')
        extra_class = ' graph-sheet' if i in (3,4,7,8,9,10) else ''
        content.append(f'<section class="sheet{extra_class}" id="s{i}"><div class="meta">GE703 · G7 · Importaciones MYS Hermanos S.A.C. · Aporte de Benjamin</div>{rendered}<div class="pagefoot">Material de apoyo a la intervención 04:00–06:00 · {i:02}</div></section>')
    body = '\n'.join(content)
    (HERE / 'informe-benjamin.html').write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Recorrido O2C para el examen parcial</title><style>{STYLE}</style><main>{body}</main></html>', encoding='utf-8')


def build_panel():
    results = [json.loads((EVIDENCE/f'{name}.json').read_text(encoding='utf-8')) for name in ['EP-N01','EP-S01','EP-E01']]
    manifest = json.loads((EVIDENCE/'ejecucion.json').read_text(encoding='utf-8'))
    if not all(item['passed'] and all(check['passed'] for check in item['checks']) for item in results):
        raise ValueError('La evidencia contiene comprobaciones fallidas')
    for group in ('input_sha256', 'output_sha256'):
        for name, expected in manifest[group].items():
            actual = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f'Evidencia desactualizada: {name}; regenerar la simulación')
    figures = [
        ('Mapa integrado', '02-mapa-integrado-o2c-p2p.svg'),
        ('Procesos', '01-mapa-corporativo.svg'),
        ('Journey actual', '05-journey-actual.svg'),
        ('Journey propuesto', '06-journey-propuesto.svg'),
        ('Roles', '03-flujo-roles-validacion.svg'),
        ('Línea de tiempo', '04-linea-tiempo-trazabilidad.svg'),
    ]
    all_data = json.dumps({'cases': results, 'manifest': manifest, 'figures': figures}, ensure_ascii=False).replace('</','<\\/')
    template = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Benjamin recorrido O2C</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#edf2f6;color:#172e43;font-family:Segoe UI,Arial,sans-serif}header{background:#173148;color:#fff;padding:19px 30px 16px;display:flex;justify-content:space-between;align-items:center;gap:24px}header h1{font-size:27px;line-height:1.2;margin:4px 0 7px}header p{font-size:14px;margin:0;color:#d8e6ef}.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase}.limit{font-size:13px;line-height:1.5;max-width:350px;text-align:right}.limit strong{color:white}nav{background:#fff;padding:10px 24px;display:flex;align-items:center;gap:7px;flex-wrap:wrap;border-bottom:1px solid #d4dfe8}button,a.button{font:600 13px Segoe UI,Arial,sans-serif;border:1px solid #ccd9e2;color:#173148;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;text-decoration:none}button:hover,a.button:hover{background:#edf7f9}button.active{background:#006c87;color:#fff;border-color:#006c87}main{padding:14px 24px 8px}.viewer{background:white;border:1px solid #d8e1e8;border-radius:8px;padding:8px 14px;min-height:560px;height:calc(100vh - 230px);overflow:auto}#figure{width:100%;height:100%;object-fit:contain;display:block}.foot{display:flex;gap:15px;align-items:center;justify-content:space-between;font-size:12px;padding:10px 2px;color:#506174}.casehead{display:flex;justify-content:space-between;align-items:center;margin:12px 10px 16px}.casehead h2{font-size:27px;margin:0 0 8px}.casehead p{margin:4px 0;font-size:14px}.badge{padding:10px 14px;background:#e8f5ee;color:#166246;font-weight:700;border-radius:6px}.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 10px}.fact{padding:15px;background:#f0f5f8;border-radius:6px}.fact span{font-size:12px;display:block;color:#607284}.fact strong{font-size:24px;display:block;margin-top:8px}.trace{margin:18px 10px;padding:14px;background:#e9f4f8;border-left:4px solid #006c87;font-size:16px;line-height:1.6}.casegrid{display:grid;grid-template-columns:1.2fr 1fr;gap:22px;margin:0 10px}.casegrid h3{font-size:17px;margin:10px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.35}td,th{padding:8px;border:1px solid #d9d9d9;text-align:left}th{background:#173148;color:white}tr:nth-child(even){background:#f3f7fa}.small{font-size:13px;color:#526578;line-height:1.5}.casegrid li{margin:8px 0;font-size:15px}.casegrid a{color:#006c87}.casefooter{margin:16px 10px;font-size:13px;color:#526578}.mobilemsg{display:none}@media(max-width:900px){header{display:block}.limit{text-align:left;max-width:none;margin-top:12px}.viewer{height:auto;min-height:450px}#figure{height:auto}.facts{grid-template-columns:repeat(2,1fr)}.casegrid{grid-template-columns:1fr}.foot{display:block}}@media print{header,nav,.foot{display:none}.viewer{border:0;height:auto;overflow:visible}.facts{grid-template-columns:repeat(4,1fr)}@page{size:A4 landscape;margin:10mm}}
</style></head><body>
<header><div><div class="eyebrow">GE703 · Grupo 7 · IMPORTACIONES MYS HERMANOS S.A.C.</div><h1>Recorrido O2C de público general en tienda</h1><p>Benjamin Arancibia · Sección 3 · 04:00–06:00 · Examen parcial 24/10/2026</p></div><div class="limit"><strong>Decisión</strong> Trazar hasta solicitud y respuesta.<br>Un faltante activa evaluación P2P.<br>Consulta y aceptación no reservan stock.</div></header>
<nav id="nav" aria-label="Evidencias de Benjamin"></nav>
<main><div class="viewer" id="viewer" aria-live="polite"></div><div class="foot"><span>Diseño y simulación local · Odoo no desplegado · Datos sintéticos · Sin pedido, reserva ni compra</span><span><a class="button" href="informe-benjamin.html">Informe</a> <a class="button" href="aporte-benjamin.md">Fuente editable</a></span></div></main>
<script id="data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent);const nav=document.getElementById('nav'),viewer=document.getElementById('viewer');
const esc=x=>String(x).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const buttons=[];function active(i){buttons.forEach((b,j)=>{b.classList.toggle('active',i===j);b.setAttribute('aria-pressed',String(i===j))})}
function add(label,fn){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{active(buttons.indexOf(b));fn()};buttons.push(b);nav.appendChild(b)}
data.figures.forEach(([label,path])=>add(label,()=>{viewer.innerHTML='<img id="figure" alt="'+esc(label)+'" src="diagramas/'+esc(path)+'">'}));
const labels=['Caso normal','Faltante y P2P','Descuento'];data.cases.forEach((c,i)=>add(labels[i],()=>showCase(c)));
function showCase(c){const r=c.observed;const signal=c.conceptual_p2p_signal;const cond=r.conditions[0];const rows=[['Estado',c.expected.status,r.status],['Código',c.expected.code,r.code],['Total',c.expected.total,r.total],['Pedido',String(c.expected.order_id),String(r.order_id)]];viewer.innerHTML=`<div class="casehead"><div><h2>${esc(c.case_id)} · ${esc(labels[data.cases.indexOf(c)])}</h2><p>Esperado y observado de una corrida local independiente · ${esc(c.business_time)}</p></div><div class="badge">${c.checks.length} comprobaciones correctas</div></div><div class="facts"><div class="fact"><span>CANTIDAD</span><strong>5 autoradios</strong></div><div class="fact"><span>BASE</span><strong>S/ 2,000</strong></div><div class="fact"><span>DESCUENTO</span><strong>${c.case_id==='EP-E01'?'10 % · sin dueño':'5 % · supuesto'}</strong></div><div class="fact"><span>TOTAL ${c.case_id==='EP-E01'?'PROPUESTO':'COTIZADO'}</span><strong>S/ ${c.case_id==='EP-E01'?'1,800':'1,900'}</strong></div></div><div class="trace">${c.chain.map(esc).join(' → ')}<br><b>${esc(c.request.correlation_id)}</b> · ${esc(r.status)} / ${esc(r.code)}</div><div class="casegrid"><div><h3>Resultado verificable</h3><table><thead><tr><th>Dato</th><th>Esperado</th><th>Observado</th></tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')}</tbody></table><p class="small">Un solo registro tras repetir el mensaje. Los maestros y el stock permanecen intactos. La aceptación del cliente no sustituye la autorización del dueño.</p></div><div><h3>Decisión y siguiente paso</h3><p>${esc(r.message)}</p><p>${esc(r.required_action)}</p>${signal?'<ul><li>Disponible: <b>3</b> · solicitado: <b>5</b> · déficit: <b>2</b></li><li><b>REP-EP-001</b> · evaluación de reposición por dueño y abastecimiento</li><li>Fecha prometida: <b>null</b> · compra automática: <b>no</b></li></ul>':'<p class="small">'+(c.case_id==='EP-E01'?'La prueba bloquea la solicitud antes de consultar disponibilidad. La oportunidad puede continuar en seguimiento.':'Estado ACEPTADA y código VALIDADA significan evaluación favorable; la confirmación operativa sigue pendiente.')+'</p>'}<p><a href="../../../pruebas/ep-benjamin/evidencias/${c.case_id}.json">Abrir JSON con trazas</a> · <a href="../../../pruebas/ep-benjamin/evidencias/${c.case_id}-entrada.json">Snapshot de entrada</a></p></div></div><div class="casefooter">Ejecutado realmente ${esc(data.manifest.executed_at_utc)} · ${data.manifest.checks_passed} comprobaciones en tres casos · Revisión humana pendiente</div>`}
buttons[0].click();
</script></body></html>'''
    (HERE/'panel-benjamin.html').write_text(template.replace('__DATA__', all_data), encoding='utf-8')


def main():
    FIGURES.mkdir(exist_ok=True)
    for key, value in JOURNEYS.items():
        svg_journey(key, value)
    build_report()
    build_panel()
    print('Generados 2 journeys SVG/Mermaid, informe HTML y panel HTML local')


if __name__ == '__main__':
    main()
