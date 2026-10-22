"""Empaqueta el aporte, sus fuentes y la simulación para compartir localmente."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT / 'output' / 'ep' / 'GE703_EP_G7_Benjamin_O2C.zip'


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    paths = list(HERE.rglob('*')) + list((ROOT / 'pruebas/ep-benjamin').rglob('*'))
    paths += [
        ROOT / 'pruebas/pc2/simulador.py',
        ROOT / 'arquitectura/contratos/crm-erp-v1.md',
        ROOT / 'arquitectura/contratos/solicitud-pedido-v1.schema.json',
        ROOT / 'arquitectura/contratos/respuesta-pedido-v1.schema.json',
        ROOT / 'documentos/pc2/entrega-pc2.md',
        ROOT / 'documentos/contexto-y-alcance.md',
        ROOT / 'macroproesos ERP/macroprocesos-o2c.md',
        ROOT / 'output/pdf/GE703_EP_G7_Benjamin_Recorrido_O2C.pdf',
        ROOT / 'output/docx/GE703_EP_G7_BENJAMIN_PARTE_3_COMPLETA.docx',
    ]
    instructions = '''APORTE DE BENJAMIN AL EXAMEN PARCIAL GE703 G7

Descomprimir manteniendo las carpetas.
Abrir documentos/ep/benjamin/panel-benjamin.html en el navegador.
Leer output/pdf/GE703_EP_G7_Benjamin_Recorrido_O2C.pdf.
Abrir output/docx/GE703_EP_G7_BENJAMIN_PARTE_3_COMPLETA.docx para la plantilla Word con la parte 3 completa.
Editar documentos/ep/benjamin/aporte-benjamin.md.

Reproducir desde esta carpeta con Python 3:
  python pruebas/ep-benjamin/generar_evidencias.py

Las fuentes docentes adjuntas no se redistribuyen. Se incluyen los textos de
continuidad citados y las dependencias mínimas del simulador. Los documentos
históricos conservan referencias al repositorio completo que no forman parte
de este paquete. El aporte principal y el panel contienen sus gráficos y casos.

El bloque de Benjamin dura dos minutos y se integra al panel único del grupo.
Stock, precios, tiempos y descuentos son académicos. Odoo no está desplegado.
El límite es solicitud/respuesta: sin pedido confirmado, reserva ni compras.
La revisión humana y el enlace público del comité siguen pendientes.
'''
    with ZipFile(DEST, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('LEEME.txt', instructions)
        for path in sorted(set(paths)):
            if path.is_file() and '__pycache__' not in path.parts:
                zf.write(path, path.relative_to(ROOT).as_posix())
    print(f'Paquete creado: {DEST.relative_to(ROOT)} ({DEST.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
