"""Ajustes de concurrencia encontrados con la prueba de carga (scripts/prueba_carga.py).

Puntaje predictivo de leads (CRM nativo): al ganar o perder una oportunidad, Odoo suma +1 en
`crm_lead_scoring_frequency` dentro de la MISMA transacción de la venta. Esa tabla es global (una
fila por variable y equipo), así que con varios vendedores cerrando a la vez PostgreSQL rechaza
las transacciones ("could not serialize access due to concurrent update"); Odoo reintenta hasta 5
veces y, con 4 vendedores en paralelo, una venta agotó los reintentos.

Odoo ya trae el cron «Predictive Lead Scoring: Recompute Automated Probabilities», que RECONSTRUYE
la tabla completa desde los leads cerrados. Por eso el incremento en vivo sobra: se omite y se
activa el cron diario (data/cron.xml). Resultado: el puntaje se sigue aprendiendo cada noche y
la venta deja de competir por las mismas filas.
"""
from odoo import models


class CrmLeadRendimiento(models.Model):
    _inherit = 'crm.lead'

    def _pls_increment_frequencies(self, from_state=None, to_state=None):
        if self.env.context.get('mys_pls_en_vivo'):   # comportamiento nativo, si alguna vez se necesita
            return super()._pls_increment_frequencies(from_state=from_state, to_state=to_state)
        return None
