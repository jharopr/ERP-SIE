"""Catálogo comercial para herramientas del agente; los precios se leen de Odoo."""
import json
import os
from pathlib import Path
import re
import unicodedata

from fastapi import Depends, HTTPException, Query, Request
from .odoo_cliente import DependenciaNoDisponible
from .snapshot import dinero


def normalizar(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')


_CACHE = {}

# Cómo lo dice el vendedor → cómo aparece en el catálogo. Cada término acepta cualquiera de sus formas.
SINONIMOS = {
    'gauge': ('gauge', 'calibre', 'ga'), 'awg': ('awg', 'calibre', 'ga'), 'calibre': ('calibre', 'gauge', 'ga'),
    'amplificador': ('amplificador', 'amp', 'monoblock'), 'parlante': ('parlante', 'medio', 'altavoz', 'speaker'),
    'radio': ('radio', 'autorradio', 'autoradio'), 'autoradio': ('autoradio', 'autorradio', 'radio'),
    'autorradio': ('autorradio', 'autoradio', 'radio'), 'pantalla': ('pantalla', 'multimedia', 'android'),
    'bajo': ('bajo', 'subwoofer'), 'subwoofer': ('subwoofer', 'bajo', 'sub'),
}


def _raiz(palabra):
    for fin in ('es', 's'):
        if len(palabra) > 4 and palabra.endswith(fin):
            return palabra[:-len(fin)]
    return palabra


def terminos(texto):
    """Palabras buscadas (sin tildes, en singular), cada una con sus sinónimos."""
    salida = []
    for w in normalizar(texto or '').replace(',', ' ').split():
        if (len(w) > 1 or w.isdigit()) and w not in ('de', 'del', 'la', 'el', 'los', 'las', 'para', 'con', 'y'):
            r = _raiz(w)
            salida.append(SINONIMOS.get(r, SINONIMOS.get(w, (r,))))
    return salida


def coincide(buscados, texto):
    """Todas las palabras buscadas aparecen (alguna de sus formas) en el texto."""
    t = normalizar(texto or '')

    def esta(f):  # un número no debe coincidir dentro de otro («4» no está en «1400w», sí en «4ga»)
        return re.search(rf'(?<![0-9]){f}(?![0-9])', t) if f.isdigit() else f in t
    return all(any(esta(f) for f in formas) for formas in buscados)


def cargar_catalogo(path=None):
    """Catálogo JSON leído una vez y releído solo si el archivo cambia (mtime). Precios: siempre de Odoo."""
    path = Path(path or os.environ.get('CATALOGO_PATH', '/catalogo/productos.json'))
    if not path.exists():
        return None
    marca = path.stat().st_mtime_ns
    guardado = _CACHE.get(str(path))
    if not guardado or guardado[0] != marca:
        data = json.loads(path.read_text(encoding='utf-8'))
        for p in data.get('productos', []):
            p['_texto'] = normalizar(' '.join([p['nombre'], p['sku'], p['codigo_original'], p['categoria'], p.get('subcategoria', '')]))
        guardado = _CACHE[str(path)] = (marca, data)
    return guardado[1]


def registrar_catalogo(app, exigir, fuente, huella_agente=None):
    @app.get('/catalogo')
    def buscar(request: Request, q: str = Query(default='', max_length=100), limite: int = Query(default=15, ge=1, le=50),
               quien=Depends(exigir('VENTAS', 'GERENCIA'))):
        data = cargar_catalogo()
        if data is None:
            raise HTTPException(503, 'Catálogo no cargado.')
        # Cada palabra debe aparecer (en cualquier orden); se aceptan plurales y sinónimos:
        # «subwoofers pioneer» → subwoofer + pioneer; «kit 4 gauge» → kit + 4 + (gauge|calibre|ga).
        buscados = terminos(q)
        matches = [p for p in data['productos'] if coincide(buscados, p['_texto'])]
        try:
            current = fuente.productos([p['sku'] for p in matches[:limite]])
        except DependenciaNoDisponible:
            raise HTTPException(503, 'Odoo no responde; no se pueden verificar precios.')
        if huella_agente:
            huella_agente(request, quien, q.encode(), None)
        return {'coincidencias':len(matches), 'productos':[{'sku':p['sku'], 'nombre': current[p['sku']].get('name', p['nombre']),
                'categoria':p['categoria'], 'precio':dinero(current[p['sku']]['list_price']), 'moneda':current[p['sku']]['currency']}
                for p in matches[:limite] if p['sku'] in current and current[p['sku']]['active']],
                'nota':'Precios leídos de Odoo. Para disponibilidad use la herramienta específica. No se reserva stock.'}
