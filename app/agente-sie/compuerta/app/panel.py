"""Panel local: sesiones humanas y acceso a las mismas reglas que usa n8n.

No envía tokens de servicio al navegador. La contraseña distingue VENTAS de
GERENCIA; el agente conserva exclusivamente su credencial VENTAS independiente.
"""
from __future__ import annotations

from datetime import timedelta
import json
import os
from pathlib import Path
import secrets
import threading
import time
from typing import Literal

from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import escenario as E
from .odoo_cliente import DependenciaNoDisponible
from .seguridad import Identidad


class Login(BaseModel):
    rol: Literal['VENTAS', 'GERENCIA']
    password: str = Field(min_length=1, max_length=256)


def registrar_panel(app, config, repo, fuente, ejecutar, escalar, decidir, reloj):
    sessions, attempts = {}, {}
    lock = threading.RLock()
    catalog_path = Path(os.environ.get('CATALOGO_PATH', '/catalogo/productos_50.json'))
    cases_path = Path(config.database).parent / 'casos_catalogo.json'
    pc3_path = Path(__file__).resolve().parents[2] / 'datos_prueba' / 'casos_pc3.json'
    # El Dockerfile copia los casos de demostración a esta ubicación.
    if not pc3_path.exists():
        pc3_path = Path('/casos/casos_pc3.json')

    def check_origin(request):
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            raise HTTPException(403, 'Origen de la solicitud no permitido.')

    def who(request: Request):
        cookie = request.cookies.get('mys_session', '')
        with lock:
            session = sessions.get(cookie)
            if not session or session['until'] < time.monotonic():
                sessions.pop(cookie, None)
                raise HTTPException(401, 'Inicie sesión para continuar.')
        if request.method != 'GET':
            check_origin(request)
        return Identidad(session['rol'], 'VEN-DEMO-01' if session['rol'] == 'VENTAS' else 'GER-DEMO-01', 'HUMANO')

    def owner(user):
        if user.rol != 'GERENCIA':
            raise HTTPException(403, 'Solo el dueño registra decisiones.')

    def cases():
        out = []
        if pc3_path.exists():
            out.extend(c for c in json.loads(pc3_path.read_text(encoding='utf-8'))['casos']
                       if c.get('solicitud') and c['id'] in ('PC3-N01', 'PC3-E01', 'PC3-E02'))
        if cases_path.exists():
            out.extend(json.loads(cases_path.read_text(encoding='utf-8')))
        return out

    @app.post('/panel/sesion')
    def login(data: Login, request: Request, response: Response):
        check_origin(request)
        host = request.client.host if request.client else 'local'
        now = time.monotonic()
        with lock:
            fails = [t for t in attempts.get(host, []) if now-t < 60]
            attempts[host] = fails
            if len(fails) >= 10:
                raise HTTPException(429, 'Demasiados intentos. Espere un minuto.')
        expected = os.environ.get('ODOO_SELLER_PASSWORD' if data.rol == 'VENTAS' else 'ODOO_OWNER_PASSWORD', '')
        if not expected or not secrets.compare_digest(expected, data.password):
            with lock:
                attempts.setdefault(host, []).append(now)
            raise HTTPException(401, 'Acceso inválido.')
        cookie = secrets.token_urlsafe(40)
        with lock:
            expired = [k for k,v in sessions.items() if v['until'] < now]
            for k in expired:
                sessions.pop(k, None)
            sessions[cookie] = {'rol': data.rol, 'until': now+8*3600}
            attempts.pop(host, None)
        response.set_cookie('mys_session', cookie, httponly=True, samesite='strict', max_age=8*3600,
                            secure=os.environ.get('SESSION_SECURE', 'false').lower() == 'true')
        return {'rol': data.rol}

    @app.delete('/panel/sesion')
    def logout(request: Request, response: Response, user=Depends(who)):
        with lock:
            sessions.pop(request.cookies.get('mys_session'), None)
        response.delete_cookie('mys_session')
        return {'sesion_cerrada': True}

    @app.get('/panel/resumen')
    def summary(user=Depends(who)):
        with repo.conexion() as db:
            requests = [json.loads(r[0]) for r in db.execute('SELECT response_json FROM requests ORDER BY request_id')]
            signals = [dict(r) for r in db.execute('SELECT * FROM senales_rep ORDER BY created_at DESC')]
            escalations = [dict(r) for r in db.execute('SELECT * FROM escalamientos ORDER BY created_at DESC')]
        try:
            health = {'disponible': True, **fuente.ping()}
        except DependenciaNoDisponible:
            health = {'disponible': False}
        return {'rol': user.rol, 'odoo': health, 'solicitudes': requests, 'senales': signals,
                'escalamientos': escalations, 'hora': reloj().isoformat(),
                'enlaces': {'odoo': os.environ.get('PUBLIC_ODOO_URL', 'http://localhost:8069'),
                            'n8n': os.environ.get('PUBLIC_N8N_URL', 'http://localhost:5678')},
                'limite': 'Evaluación comercial. Sin pedido, reserva, compra ni fecha prometida.'}

    @app.get('/panel/catalogo')
    def catalog(user=Depends(who)):
        if not catalog_path.exists():
            raise HTTPException(503, 'El catálogo todavía no está cargado.')
        data = json.loads(catalog_path.read_text(encoding='utf-8'))
        refs = [p['sku'] for p in data['productos']]
        location = repo.mapa('ubicacion', config.ubicacion_id)
        try:
            live_products = fuente.productos(refs)
            stock = fuente.stock(refs, int(location)) if location else {}
        except DependenciaNoDisponible:
            raise HTTPException(503, 'Odoo no responde. No es posible afirmar precio o stock actuales.')
        from .snapshot import dinero
        products = []
        for p in data['productos']:
            current, s = live_products.get(p['sku']), stock.get(p['sku'])
            products.append({'sku': p['sku'], 'codigo_original': p['codigo_original'], 'nombre': current.get('name',p['nombre']) if current else p['nombre'],
                             'categoria': p['categoria'], 'subcategoria': p['subcategoria'],
                             'precio': dinero(current['list_price']) if current else None,
                             'fisico': s['fisico'] if s else None, 'reservado': s['reservado'] if s else None,
                             'disponible': s['fisico']-s['reservado'] if s else None,
                             'stock_es_sintetico': True})
        return {'productos': products, 'observado_en': reloj().isoformat(), 'fuente': 'Odoo',
                'metodo': data['metadata']['metodo']}

    @app.get('/panel/casos')
    def list_cases(user=Depends(who)):
        return {'casos': cases()}

    @app.post('/panel/casos/{case_id}/evaluar')
    def evaluate(case_id: str, user=Depends(who)):
        if user.rol != 'VENTAS':
            raise HTTPException(403, 'La solicitud la envía Ventas.')
        case = next((c for c in cases() if c['id'] == case_id), None)
        if not case:
            raise HTTPException(404, 'Caso de demostración no encontrado.')
        result = ejecutar(case['solicitud'], user)
        return {'respuesta': result, 'senales_reposicion': repo.senales_de(result['request_id'])}

    @app.post('/panel/solicitudes/{request_id}/escalar')
    def escalate(request_id: str, request: Request, user=Depends(who)):
        from .main import Escalamiento
        if user.rol != 'VENTAS':
            raise HTTPException(403, 'El vendedor solicita la intervención del dueño.')
        stored = repo.respuesta(config.company_id, request_id)
        if not stored:
            raise HTTPException(404, 'Solicitud no encontrada.')
        code = stored['respuesta']['code']
        kind = {'DESCUENTO_SIN_APROBACION': 'DESCUENTO', 'DISPONIBILIDAD_PARCIAL': 'REPOSICION',
                'DEPENDENCIA_NO_DISPONIBLE': 'DEPENDENCIA', 'IDEMPOTENCIA_CONFLICTO': 'IDEMPOTENCIA'}.get(code)
        if not kind:
            raise HTTPException(409, 'Este resultado no requiere escalamiento.')
        return escalar(Escalamiento(tipo=kind, request_id=request_id, resumen='Revisión humana solicitada desde el panel MYS.'), request, user)

    @app.post('/panel/escalamientos/{escalation_id}/decision')
    def decision(escalation_id: str, data: dict, user=Depends(who)):
        from .main import DecisionDueno
        owner(user)
        return decidir(escalation_id, DecisionDueno.model_validate(data), user)

    @app.get('/panel/bitacora/{correlation_id}')
    def audit(correlation_id: str, user=Depends(who)):
        return {'eventos': repo.bitacora(correlation_id=correlation_id)}
