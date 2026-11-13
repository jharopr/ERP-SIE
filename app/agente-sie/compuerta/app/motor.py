"""Envoltura del motor probado en PC2.

`motor_base/simulador.py` es una copia byte a byte de `pruebas/pc2/simulador.py`
(la prueba `test_motor_es_copia_exacta` lo verifica). Aquí NO se cambia el orden
ni la lógica de R01-R12: solo se extiende por subclase para

1. etiquetar cada evento con `actor_type` (HUMANO, AGENTE o SISTEMA);
2. guardar el payload original (para `reanudar`);
3. crear la señal REP-… en la MISMA transacción cuando hay PROMESA_CONDICIONADA;
4. devolver PENDIENTE si Odoo cayó antes de poder leer los datos comerciales (R08/R09).
"""

from __future__ import annotations

from pathlib import Path

from .motor_base import simulador as base
from .repositorio import DDL, Repositorio

# El motor resuelve el schema relativo a su ubicación original; aquí se apunta a la copia.
base.SCHEMA_PATH = Path(__file__).resolve().parent / "contrato" / "solicitud-pedido-v1.schema.json"

valid_request = base.valid_request
canonical = base.canonical

# Eventos que ejecuta la propia compuerta, no la persona ni el agente.
EVENTOS_SISTEMA = {"CONSULTA", "DECISION", "SENAL_REP"}


class Compuerta(base.TransitionSimulator):
    def __init__(self, masters, database, actor_type="HUMANO", prefijo_rep="REP-PC3", comercial_disponible=True):
        super().__init__(masters, database)
        self.db.executescript(DDL)
        self.actor_type = actor_type
        self.prefijo_rep = prefijo_rep
        self.comercial_disponible = comercial_disponible
        self.senales_creadas: list[str] = []

    def _event(self, request, actor, interface, event, code, detalle=None):
        super()._event(request, actor, interface, event, code)
        event_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        tipo = "SISTEMA" if event in EVENTOS_SISTEMA else self.actor_type
        self.db.execute("INSERT INTO audit_ext(event_id,actor_type,detalle) VALUES(?,?,?)",
                        (event_id, tipo, canonical(detalle) if detalle else None))

    def _submit_authorized(self, request, actor, resume):
        normalized = {**request, "quotation_version": int(request["quotation_version"])}
        self.db.execute("INSERT OR IGNORE INTO solicitudes_payload(company_id,request_id,payload_json) VALUES(?,?,?)",
                        (request["company_id"], request["request_id"], canonical(normalized)))
        return super()._submit_authorized(request, actor, resume)

    def _evaluate(self, request, actor):
        if not self.comercial_disponible:
            self._event(request, actor, "I04", "CONSULTA", "DEPENDENCIA_NO_DISPONIBLE")
            return self._response(request, "DEPENDENCIA_NO_DISPONIBLE",
                                  "No hay lectura confiable de los datos comerciales en Odoo.",
                                  "Recuperar dependencia y reanudar la misma solicitud.",
                                  "ADMINISTRADOR_Y_VENTAS", "PENDIENTE", None)
        result = super()._evaluate(request, actor)
        policy = self.masters.get('quotations', {}).get(request.get('quotation_id'), {}).get('commercial_policy')
        if policy and (result['status'] in ('ACEPTADA', 'PROMESA_CONDICIONADA') or result['code'] == 'DESCUENTO_SIN_APROBACION'):
            self._event(request, actor, 'I06', 'CONSULTA', 'POLITICA_COMERCIAL_MYS', policy)
            if policy.get('blocking_code'):
                result = self._response(request, 'DEPENDENCIA_NO_DISPONIBLE' if policy.get('pending') else 'DATOS_INCONSISTENTES', policy['message'],
                    'Complete los datos verificados o prepare una nueva oferta; el agente no autoriza descuentos.',
                    'ADMINISTRADOR_Y_VENTAS' if policy.get('pending') else 'VENTAS',
                    'PENDIENTE' if policy.get('pending') else 'RECHAZADA')
        if result["status"] == "PROMESA_CONDICIONADA":
            self._crear_senales(request, actor, result)
        return result

    def _crear_senales(self, request, actor, result):
        """Señal de reposición sugerida; automatic_action=0: no compra ni reserva nada."""
        prefijo = f"{self.prefijo_rep}-"
        for condicion in result["conditions"]:
            ultimo = self.db.execute("SELECT COUNT(*) FROM senales_rep WHERE signal_id LIKE ?", (prefijo + "%",)).fetchone()[0]
            signal_id = f"{prefijo}{ultimo + 1:03d}"
            faltante = max(0, condicion["requested_quantity"] - condicion["available_quantity"])
            self.db.execute(
                "INSERT INTO senales_rep(signal_id,company_id,request_id,correlation_id,sku,requested,available,"
                "faltante,automatic_action,estado,created_at) VALUES(?,?,?,?,?,?,?,?,0,'ABIERTA',?)",
                (signal_id, request["company_id"], request["request_id"], request["correlation_id"], condicion["sku"],
                 condicion["requested_quantity"], condicion["available_quantity"], faltante, self.now.isoformat()))
            self._event(request, actor, "REP", "SENAL_REP", "REPOSICION_SUGERIDA",
                        {"signal_id": signal_id, "sku": condicion["sku"], "faltante": faltante})
            self.senales_creadas.append(signal_id)


def evaluar(masters, database, request, actor, *, actor_type, prefijo_rep, comercial_disponible, resume=False):
    motor = Compuerta(masters, database, actor_type, prefijo_rep, comercial_disponible)
    try:
        return motor.submit(request, actor, resume)
    finally:
        motor.close()


__all__ = ["Compuerta", "evaluar", "valid_request", "Repositorio"]
