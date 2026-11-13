"""Puente privado Odoo → compuerta. El navegador no recibe tokens ni roles editables."""
import json
import re
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field


class ContextoComercial(BaseModel):
    opportunity_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')
    customer_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')
    seller_uid: int = Field(gt=0)
    identidad_revisada: bool
    segmento: str = 'PUBLICO_GENERAL_NUEVO'


def registrar_integracion(app, config, repo, exigir, reloj):
    @app.get('/integracion/cotizaciones/{quotation_id}/{version}')
    def cotizacion_evaluada(quotation_id: str, version: int, quien=Depends(exigir('VENTAS', 'GERENCIA'))):
        if not quien.odoo_uid or quien.actor_type != 'HUMANO' or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', quotation_id):
            raise HTTPException(403, 'Acceso exclusivo desde Odoo.')
        with repo.conexion() as db:
            row = db.execute('SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=?',
                             (config.company_id, quotation_id, version)).fetchone()
        return {'evaluada': bool(row)}

    @app.post('/integracion/contexto')
    def contexto(datos: ContextoComercial, quien=Depends(exigir('VENTAS'))):
        if not quien.odoo_uid or quien.actor_type != 'HUMANO' or datos.seller_uid != quien.odoo_uid:
            raise HTTPException(403, 'Solo Odoo puede registrar el contexto del vendedor autenticado.')
        with repo.conexion() as db:
            actual = db.execute('SELECT opportunities_json FROM actores WHERE actor_id=?', (quien.actor_id,)).fetchone()
            opps = set(json.loads(actual[0])) if actual else set()
            opps.add(datos.opportunity_id)
            db.execute('INSERT INTO actores VALUES(?,?,?,?) ON CONFLICT(actor_id) DO UPDATE SET '
                       'rol=excluded.rol,company_id=excluded.company_id,opportunities_json=excluded.opportunities_json',
                       (quien.actor_id, quien.rol, config.company_id, json.dumps(sorted(opps))))
            db.execute("INSERT INTO mapa_ids VALUES('usuario_odoo_id',?,?) ON CONFLICT(tipo,externo) DO UPDATE SET odoo=excluded.odoo",
                       (quien.actor_id, str(quien.odoo_uid)))
            db.execute('INSERT INTO clientes_ext VALUES(?,?,?) ON CONFLICT(ref) DO UPDATE SET '
                       'identity_reviewed=excluded.identity_reviewed,segmento=excluded.segmento',
                       (datos.customer_id, int(datos.identidad_revisada), datos.segmento))
        return {'registrado': True}

    @app.get('/integracion/resumen')
    def resumen(quien=Depends(exigir('VENTAS', 'GERENCIA'))):
        if not quien.odoo_uid:
            raise HTTPException(403, 'Acceso exclusivo desde Odoo.')
        opps = repo.actores().get(quien.actor_id, {}).get('opportunities', [])
        with repo.conexion() as db:
            vencidos = db.execute("SELECT * FROM escalamientos WHERE company_id=? AND estado='ESPERANDO_DECISION' AND plazo_hasta < ?",
                                  (config.company_id, reloj().isoformat())).fetchall()
            for esc in vencidos:
                changed = db.execute("UPDATE escalamientos SET estado='SIN_DECISION' WHERE escalation_id=? AND estado='ESPERANDO_DECISION'",
                                     (esc['escalation_id'],)).rowcount
                if changed:
                    repo.registrar_evento(db, company_id=config.company_id, request_id=esc['request_id'],
                        correlation_id=esc['correlation_id'], actor_id='COMPUERTA', actor_type='SISTEMA',
                        interface_id='ESC', event_type='PLAZO_VENCIDO', code='SIN_DECISION',
                        occurred_at=reloj().isoformat(), detalle={'escalation_id': esc['escalation_id']})
            rows = db.execute('SELECT * FROM requests WHERE company_id=? ORDER BY rowid DESC LIMIT 500',
                              (config.company_id,)).fetchall()
            rows = [r for r in rows if quien.rol == 'GERENCIA' or r['opportunity_id'] in opps]
            ids = {r['request_id'] for r in rows}
            escs = db.execute('SELECT * FROM escalamientos WHERE company_id=? ORDER BY created_at DESC LIMIT 500',
                              (config.company_id,)).fetchall()
        return {'solicitudes': [json.loads(r['response_json']) for r in rows],
                'escalamientos': [dict(e) for e in escs if e['request_id'] in ids],
                'politica': repo.politica()}
