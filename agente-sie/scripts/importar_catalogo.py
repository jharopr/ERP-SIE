"""Convierte la lista de productos de la empresa (Excel) en odoo/catalogo.csv.

    py -3.11 scripts/importar_catalogo.py ../LISTA_PRODUCTOS_EMPRESA_18717.xlsx
    docker compose exec compuerta python /seed/seed_odoo.py      # carga el catálogo en Odoo

Qué toma del Excel: código interno (SKU), nombre, categoría y subcategoría, unidad,
código de barras y PRECIO DE VENTA (lista por menor).
Qué NO toma: el precio de costo (dato sensible que el agente no necesita) ni la lista
por mayor (el contrato v1.0 valida contra el precio de lista).
El Excel no trae stock: se asigna un stock SINTÉTICO, fijo y reproducible por categoría
(mismo SKU → mismo número), con ajustes para que el escenario de demostración funcione.
Se agregan los dos SKU genéricos de los casos PC3 (RAD-7BT y RAD-10X), que no se tocan.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys

for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "odoo" / "catalogo.csv"
COLUMNAS = ["sku", "nombre", "categoria", "subcategoria", "unidad", "tipo", "codigo_barras", "precio_pen", "stock_fisico"]

# Textos truncados en el Excel original.
SUBCATEGORIA_CORREGIDA = {
    "Medios Rangos (Midranges": "Medios Rangos (Midranges)",
    "Multicanal (4 y 5 Canales": "Multicanal (4 y 5 Canales)",
    "Cables de Parlante y Subwoofe": "Cables de Parlante y Subwoofer",
}
NOMBRE_CORREGIDO = {"ABLE RCA": "CABLE RCA", "UPER TWEETER": "SUPER TWEETER"}
# Productos sin categoría en el Excel: se asignan por su descripción.
SIN_CATEGORIA = {
    "EQ9": ("Ecualizadores", "Ecualizadores Digitales / Paramétricos"),
    "T1R": ("Tweeters", "Tweeters Tipo Domo / Neodimio"),
    "MS100-9": ("Radios y Pantallas", "Pantallas Android"), "MS300-9": ("Radios y Pantallas", "Pantallas Android"),
    "MS200-10": ("Radios y Pantallas", "Pantallas Android"), "MS100-10": ("Radios y Pantallas", "Pantallas Android"),
    "MS300-10": ("Radios y Pantallas", "Pantallas Android"),
    "SRV-OTROS": ("Servicios", "Instalación y Mano de Obra"),
}
# Unidad SUNAT → unidad del catálogo. MTK/MTR = metro (cables vendidos por metro).
UNIDAD = {"NIU": "unidad", "PR": "par", "KT": "kit", "ZZ": "servicio", "MTK": "metro", "MTR": "metro"}
# Rango de stock sintético por categoría (unidades; cables por metro).
RANGO_STOCK = {
    "Radios y Pantallas": (3, 12), "Medios y Parlantes": (4, 18), "Tweeters": (6, 24), "Subwoofers": (2, 8),
    "Amplificadores": (2, 7), "Cables y Conexiones": (8, 30), "Accesorios Automotrices": (5, 20),
    "Aire Acondicionado": (6, 20), "Ecualizadores": (2, 6), "Seguridad y Alarmas": (3, 10),
}
RANGO_METROS = (100, 300)
# Ajustes para que las cotizaciones de odoo/escenario_extra.json muestren cada resultado.
STOCK_ESCENARIO = {
    "MVH-S215BT": 12, "TS-G1620F-2": 14,   # COT-DEMO-101: alcanza (con reservas de otro cliente)
    "SD-YT0905PRO": 6, "STAGE2634": 10,    # COT-DEMO-102: alcanza
    "TS-A3000LS4": 3, "GM-A6704": 5,       # COT-DEMO-103: 3 físicos − 1 reservado = 2 < 3 pedidos → faltante
    "GTO609C": 6, "ION.4": 4,              # COT-DEMO-104: hay stock; el problema es el descuento
    "DEH-S4250BT": 5, "RS-NF04": 10,       # COT-DEMO-105: sin aceptación
}
CASOS_PC3 = [  # escenario.py: no cambiar precio ni stock (los casos PC3 dependen de ellos)
    {"sku": "RAD-7BT", "nombre": 'Autoradio Bluetooth 7" (genérico, casos PC3)', "categoria": "Radios y Pantallas",
     "subcategoria": "Casos PC3 (genéricos)", "unidad": "unidad", "tipo": "producto", "codigo_barras": "",
     "precio_pen": "400.00", "stock_fisico": 10},
    {"sku": "RAD-10X", "nombre": 'Autoradio pantalla 10" (genérico, casos PC3)', "categoria": "Radios y Pantallas",
     "subcategoria": "Casos PC3 (genéricos)", "unidad": "unidad", "tipo": "producto", "codigo_barras": "",
     "precio_pen": "520.00", "stock_fisico": 10},
]


def stock_sintetico(sku, categoria, unidad):
    bajo, alto = RANGO_METROS if unidad == "metro" else RANGO_STOCK.get(categoria, (3, 12))
    n = int(hashlib.sha256(sku.encode()).hexdigest(), 16)
    valor = bajo + n % (alto - bajo + 1)
    return valor - valor % 10 if unidad == "metro" else valor


def codigo_barras(valor):
    if valor in (None, ""):
        return ""
    if isinstance(valor, float) and valor < 1:  # «0.10000125»: celda con formato numérico erróneo
        valor = round(valor * 10 ** 8)
    return str(int(valor))


def leer_excel(ruta):
    import openpyxl
    hoja = openpyxl.load_workbook(ruta, data_only=True, read_only=True).active
    filas = list(hoja.iter_rows(values_only=True))
    cab = filas[1]
    idx = {nombre: i for i, nombre in enumerate(cab) if nombre}
    columnas_categoria = range(idx["CATEGORÍAS"] if "CATEGORÍAS" in idx else 10, idx["LISTA PRECIO POR MENOR"])
    avisos, productos = [], []
    for f in filas[2:]:
        if not f[idx["NOMBRE"]]:
            continue
        sku = str(f[idx["C. INTERNO"]]).strip()
        nombre = " ".join(str(f[idx["NOMBRE"]]).split())
        for malo, bueno in NOMBRE_CORREGIDO.items():
            if nombre.startswith(malo):
                nombre = bueno + nombre[len(malo):]
                avisos.append(f"{sku}: nombre truncado corregido → «{nombre[:40]}…»")
        cat = next(((cab[i], f[i]) for i in columnas_categoria if f[i]), None)
        if cat is None:
            cat = SIN_CATEGORIA.get(sku)
            avisos.append(f"{sku}: sin categoría en el Excel → {cat[0]} / {cat[1]}" if cat else f"{sku}: sin categoría")
            cat = cat or ("Otros", "Otros")
        categoria, sub = cat[0], SUBCATEGORIA_CORREGIDA.get(cat[1], cat[1])
        unidad = UNIDAD.get(str(f[idx["UND. MEDIDA"]]).strip(), "unidad")
        tipo = "servicio" if categoria == "Servicios" else "producto"
        if f[idx["ESTADO"]] != "Activo":
            avisos.append(f"{sku}: estado {f[idx['ESTADO']]}, se omite")
            continue
        barras = codigo_barras(f[idx["C. BARRAS"]])
        if isinstance(f[idx["C. BARRAS"]], float) and f[idx["C. BARRAS"]] < 1:
            avisos.append(f"{sku}: código de barras {f[idx['C. BARRAS']]} corregido → {barras}")
        productos.append({
            "sku": sku, "nombre": nombre, "categoria": categoria, "subcategoria": sub, "unidad": unidad, "tipo": tipo,
            "codigo_barras": barras, "precio_pen": f"{float(f[idx['PRECIO DE VENTA']]):.2f}",
            "stock_fisico": 0 if tipo == "servicio" else STOCK_ESCENARIO.get(sku, stock_sintetico(sku, categoria, unidad)),
        })
    return productos, avisos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("excel", help="Lista de productos de la empresa (.xlsx)")
    args = ap.parse_args()
    productos, avisos = leer_excel(args.excel)
    vistos = {p["sku"] for p in productos}
    for caso in CASOS_PC3:
        if caso["sku"] in vistos:
            raise SystemExit(f"El Excel ya tiene el SKU {caso['sku']}: cambie el SKU de los casos PC3")
    faltan = sorted(set(STOCK_ESCENARIO) - vistos)
    if faltan:
        raise SystemExit(f"El escenario de demostración usa SKU que no están en el Excel: {faltan}")
    duplicados = {p["sku"] for p in productos if sum(q["sku"] == p["sku"] for q in productos) > 1}
    if duplicados:
        raise SystemExit(f"SKU duplicados en el Excel: {sorted(duplicados)}")
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(CASOS_PC3 + productos)
    print(f"✓ {SALIDA.relative_to(RAIZ)}: {len(productos)} productos de la empresa + {len(CASOS_PC3)} genéricos PC3")
    for a in avisos:
        print(f"  · {a}")


if __name__ == "__main__":
    main()
