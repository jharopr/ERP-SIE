"""Catálogo comercial para herramientas del agente; los precios se leen de Odoo."""
import json
import os
from pathlib import Path
import unicodedata

from fastapi import Depends, HTTPException, Query, Request
from .odoo_cliente import DependenciaNoDisponible
from .snapshot import dinero


def normalizar(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')


def registrar_catalogo(app, exigir, fuente, huella_agente=None):
    @app.get('/catalogo')
    def buscar(request: Request, q: str = Query(default='', max_length=100), limite: int = Query(default=15, ge=1, le=50),
               quien=Depends(exigir('VENTAS', 'GERENCIA'))):
        path = Path(os.environ.get('CATALOGO_PATH', '/catalogo/productos.json'))
        if not path.exists():
            raise HTTPException(503, 'Catálogo no cargado.')
        data = json.loads(path.read_text(encoding='utf-8'))
        # Cada palabra debe aparecer (en cualquier orden); se aceptan plurales: «subwoofers pioneer» → subwoofer + pioneer.
        def raiz(palabra):
            for fin in ('es', 's'):
                if len(palabra) > 4 and palabra.endswith(fin):
                    return palabra[:-len(fin)]
            return palabra
        terminos = [raiz(w) for w in normalizar(q).split() if len(w) > 1]
        def texto(p):
            return normalizar(' '.join([p['nombre'], p['sku'], p['codigo_original'], p['categoria'], p.get('subcategoria', '')]))
        matches = [p for p in data['productos'] if all(t in texto(p) for t in terminos)]
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
