"""Extrae 50 referencias del XLSX sin modificarlo; no requiere paquetes de Excel.

La selección representa cobertura comercial, no ventas observadas. Los saldos son
sintéticos. Los SKU originales se conservan incluso cuando se normaliza su código.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
CUOTAS = [('Q', 16), ('P', 8), ('O', 8), ('N', 8), ('M', 3), ('K', 3), ('L', 1), ('S', 2), ('R', 1)]


def leer_xlsx(path):
    with ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        rows = []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('s:sheetData/s:row', NS):
            values = {}
            for cell in row.findall('s:c', NS):
                value = cell.find('s:v', NS)
                text = value.text if value is not None else ''.join(cell.itertext())
                if cell.get('t') == 's':
                    text = strings[int(text)]
                values[re.sub(r'\d', '', cell.attrib['r'])] = text or ''
            rows.append((int(row.attrib['r']), values))
    return rows


def monto(value):
    try:
        n = Decimal(value)
        return format(n.quantize(Decimal('.01')), 'f') if n.is_finite() and n >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def sku_seguro(value):
    ascii_value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9_-]+', '-', ascii_value).strip('-')[:55].upper()


def seleccionar(path):
    rows = leer_xlsx(path)
    headers = next(v for n, v in rows if n == 2)
    candidates = []
    rejected = []
    for number, r in rows:
        if not r.get('A', '').isdigit() or not r.get('B'):
            continue
        price = monto(r.get('C', ''))
        categories = [c for c in 'KLMNOPQRSTU' if r.get(c)]
        if r.get('I') != 'Activo' or not r.get('F') or not price or Decimal(price) <= 0 or len(categories) != 1:
            rejected.append(number)
            continue
        column = categories[0]
        candidates.append({'source_row': number, 'nombre': r['B'].strip(), 'codigo_original': r['F'].strip(),
                           'sku': sku_seguro(r['F']), 'precio_venta': price, 'precio_mayorista': monto(r.get('W', '')),
                           'costo_referencia': monto(r.get('D', '')) if Decimal(monto(r.get('D', '')) or '0') > 0 else None,
                           'unidad_original': r.get('E'), 'barcode': r.get('G'), 'categoria': headers[column],
                           'subcategoria': r[column], 'columna_categoria': column})
    selected = []
    for column, count in CUOTAS:
        group = sorted((p for p in candidates if p['columna_categoria'] == column),
                       key=lambda p: (-Decimal(p['precio_venta']), p['codigo_original']))
        selected.extend(group[:count])
    if len(selected) != 50:
        raise ValueError(f'El catálogo no permite cubrir las cuotas declaradas: {len(selected)}/50')
    seen = set()
    for i, product in enumerate(selected, 1):
        code = product['sku']
        if not code or code in seen or code in {'RAD-7BT', 'RAD-10X'}:
            code = f'MYS-{product["source_row"]:04d}-{code}'[:64]
        seen.add(code)
        product.update(sku=code, prioridad_demo=i, fuente='catalogo_empresa',
                       stock_demo=3 if i == 2 else 20 + (i * 7) % 31,
                       stock_es_sintetico=True, moneda='PEN')
    return selected, candidates, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', type=Path)
    args = parser.parse_args()
    selected, candidates, rejected = seleccionar(args.archivo)
    out = ROOT / 'datos'
    out.mkdir(exist_ok=True)
    metadata = {'archivo_fuente': args.archivo.name, 'hoja': 'Worksheet',
                'sha256_fuente': hashlib.sha256(args.archivo.read_bytes()).hexdigest(),
                'productos_validos_fuente': len(candidates), 'seleccionados': 50,
                'metodo': 'Cuotas por categoría; dentro de cada cuota precio de venta descendente y código ascendente. No mide ventas ni rotación.',
                'cuotas': {next(p['categoria'] for p in candidates if p['columna_categoria'] == c): n for c, n in CUOTAS},
                'filas_excluidas_validacion': rejected,
                'moneda': 'PEN (supuesto del proyecto; el XLSX no incluye columna de moneda)',
                'stock': 'Sintético, no extraído del archivo. 3 unidades para el segundo producto; 20 + (índice × 7 mod 31) para los demás.',
                'costos_cero': 'Se representan como null: costo no informado, no margen del 100%.',
                'sku': 'Código normalizado para I03/API; codigo_original conserva el valor exacto del XLSX.',
                'productos_adicionales': 'RAD-7BT y RAD-10X permanecen como fixtures académicas PC3 fuera de estos 50.'}
    for name, data in [('productos_50.json', {'metadata': metadata, 'productos': selected}), ('procedencia.json', metadata)]:
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (out / 'productos_50.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    print(f'{len(selected)} productos seleccionados de {len(candidates)} válidos. Catálogo guardado en app/datos/.')
    print(json.dumps(dict(Counter(p['categoria'] for p in selected)), ensure_ascii=False))


if __name__ == '__main__':
    main()
