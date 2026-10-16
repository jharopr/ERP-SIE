"""Calibración documental S6, separada de los precios y políticas ficticias de MYS.

No crea pedidos ni facturas. Los hechos provienen de GE703_S6_Presentacion.pdf.
"""
import json
from pathlib import Path


def calibrate(requested=1000, available=650, replenishment=350, replenishment_date=None):
    if any(type(q) is not int or q < 0 for q in (requested, available, replenishment)):
        raise ValueError("Cantidades enteras no negativas")
    if requested == 0 or available + replenishment != requested:
        raise ValueError("La propuesta debe explicar toda la cantidad solicitada")
    return {
        "kind": "CALIBRACION_DOCUMENTAL_S6_NO_EJECUCION_ODOO",
        "source": "GE703_S6_Presentacion.pdf, pp. 25-30 (Andina)",
        "facts": {"requested_quantity": requested, "available_quantity": available,
                  "replenishment_quantity": replenishment, "partial_delivery_accepted": True,
                  "one_invoice_on_completion": True, "discount_exceeds_authority": True},
        "unknown": {"discount_percentage": None, "discount_limit": None, "authorized_approver": None,
                    "replenishment_date": replenishment_date, "price": None, "credit": None, "fiscal_identity": None},
        "scenarios": [
            {"id": "AND-A", "cause": "DESCUENTO_FUERA_DE_AUTORIDAD", "state": "PENDIENTE_APROBACION",
             "owner": "Responsable comercial identifica al aprobador autorizado",
             "next_action": "Registrar decisión de la autoridad competente antes de confirmar; porcentaje y umbral desconocidos.",
             "due_at": None, "missing": "Aprobador y plazo de atención por acordar", "order_confirmed": False},
            {"id": "AND-B", "cause": "STOCK_PARCIAL", "state": "PROMESA_POR_VALIDAR",
             "available_quantity": available, "pending_quantity": replenishment, "promised_date": replenishment_date,
             "owner": "Ventas y Almacén", "next_action": "Documentar plan parcial aceptado y validar fecha del saldo; no prometer una fecha desconocida.",
             "due_at": None, "missing": "Fecha de reposición y plazo de atención", "order_confirmed": False},
            {"id": "AND-C", "cause": "FACTURA_UNICA_AL_COMPLETAR", "state": "REGLA_DE_CONTINUIDAD",
             "owner": "Facturación", "next_action": f"Propuesta: emitir una factura al completar {requested} unidades y verificar aceptación; ejecución fuera de PC2.",
             "due_at": None, "missing": "Identidad fiscal y condiciones tributarias por validar", "invoice_issued": False},
            {"id": "AND-D", "cause": "REPOSICION_RETRASADA", "state": "ATENCION_ABIERTA_EN_CRM",
             "owner": "Ventas con Almacén", "next_action": "Registrar retraso, informar al cliente y renegociar saldo; conservar causa y aceptación de nuevas condiciones.",
             "pending_quantity": replenishment, "new_promised_date": None,
             "due_at": None, "missing": "Nueva fecha y plazo de respuesta por acordar", "opportunity_lost": False},
        ],
        "limit": "Calibración del contrato con información incompleta. No prueba precio, crédito, fiscalidad, aprobación real ni el flujo completo MYS. No se aplica el umbral MYS del 5 %.",
    }


def main():
    path = Path(__file__).with_name("evidencias") / "andina-s6.json"
    path.write_text(json.dumps(calibrate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK: calibración documental Andina, cuatro escenarios; sin ejecución operativa")


if __name__ == "__main__":
    main()
