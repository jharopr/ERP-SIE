"""Precedentes en la decisión del gerente: qué se decidió antes en casos parecidos (aprendizaje del sistema)."""
import html
import urllib.parse

from odoo import fields, models
from odoo.exceptions import AccessError, UserError


class DecisionPrecedentes(models.Model):
    _inherit = 'mys.decision'

    precedentes_html = fields.Html('Casos parecidos', compute='_compute_precedentes', sanitize=True)

    def _compute_precedentes(self):
        for decision in self:
            decision.precedentes_html = False
            if decision.tipo != 'DESCUENTO' or not decision.partner_id.ref:
                continue
            consulta = urllib.parse.urlencode({'tipo': 'DESCUENTO', 'descuento': round(decision.descuento_max, 2),
                                               'cliente': decision.partner_id.ref})
            try:
                p = self.env['mys.gateway']._request('GET', '/aprendizaje/precedentes?' + consulta)
            except (UserError, AccessError):
                continue
            decision.precedentes_html = decision._render_precedentes(p)

    @staticmethod
    def _render_precedentes(p):
        e = html.escape
        if not p.get('casos_parecidos'):
            return '<p class="text-muted mb-0">Todavía no hay decisiones parecidas registradas (%s).</p>' % e(p.get('criterio', ''))
        dec = p.get('decisiones', {})
        filas = ''.join('<tr><td>%s</td><td>%s</td><td style="text-align:right">%s %%</td><td>%s</td><td><b>%s</b></td><td>%s</td></tr>' % (
            e(x['fecha']), e(x['cotizacion']), e('%g' % x['descuento'] if x['descuento'] is not None else '—'),
            e(x['nivel'] or '—'), e(x['decision']), e(x['motivo'] or '')) for x in p.get('ejemplos', []))
        promedio = p.get('descuento_promedio_aprobado')
        return ('<p class="mb-1">Casos parecidos (%s): <b>%s</b> · aprobados <b>%s</b>, rechazados <b>%s</b>%s%s.</p>'
                '<table class="table table-sm mb-1"><tr><th>Fecha</th><th>Cotización</th><th style="text-align:right">Desc.</th>'
                '<th>Nivel</th><th>Decisión</th><th>Motivo</th></tr>%s</table>'
                '<p class="text-muted small mb-0">Precedentes del propio sistema. Son contexto: la decisión es suya.</p>') % (
                    e(p['criterio']), p['casos_parecidos'], dec.get('APROBADA', 0), dec.get('RECHAZADA', 0),
                    ' · tasa de aprobación %s %%' % p['tasa_aprobacion_pct'] if p.get('tasa_aprobacion_pct') is not None else '',
                    ' · descuento promedio aprobado %s %%' % promedio if promedio is not None else '', filas)
