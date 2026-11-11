# Resultados PC3 · esperado vs observado

- **Modo:** Docker: Odoo 18 + compuerta reales
- **Ejecución (UTC):** 2026-11-11T16:28:45.612391+00:00
- **Equipo:** Python 3.11.9 · Windows 10
- **Casos:** 6/6 ✓
- **Stock intacto antes/después:** ✓ (RAD-7BT: disp. 8, RAD-10X: disp. 3)
- **order_id null en todas las respuestas:** ✓
- Generado por `scripts/ejecutar_casos.py` sin modelo de lenguaje. La conversación del agente está en `agente_*.md`.

| Caso | Esperado | Observado | ✓/✗ |
|---|---|---|---|
| PC3-N01 | status="ACEPTADA"; code="VALIDADA"; responsible_role="VENTAS"; total="1900.00"; order_id=null; conditions=[]; senales=0 | status="ACEPTADA"; code="VALIDADA"; responsible_role="VENTAS"; total="1900.00"; order_id=null; conditions=[]; senales=0 | ✓ |
| PC3-E01 | status="PROMESA_CONDICIONADA"; code="DISPONIBILIDAD_PARCIAL"; responsible_role="VENTAS"; total="2470.00"; order_id=null; conditions=[{"sku": "RAD-10X", "requested_quantity": 5, "available_quantity": 3, "promised_date": null, "requires_customer_acceptance": true}]; senal.signal_id="REP-PC3-001"; senal.sku="RAD-10X"; senal.faltante=2; senal.automatic_action=0; decision_dueno="OFRECER_PARCIAL" | status="PROMESA_CONDICIONADA"; code="DISPONIBILIDAD_PARCIAL"; responsible_role="VENTAS"; total="2470.00"; order_id=null; conditions=[{"sku": "RAD-10X", "requested_quantity": 5, "available_quantity": 3, "promised_date": null, "requires_customer_acceptance": true}]; senal.signal_id="REP-PC3-001"; senal.sku="RAD-10X"; senal.faltante=2; senal.automatic_action=0; decision_dueno="OFRECER_PARCIAL" | ✓ |
| PC3-E02 | status="RECHAZADA"; code="DESCUENTO_SIN_APROBACION"; responsible_role="GERENCIA"; total=null; order_id=null; conditions=[]; sin_consulta_stock=true; aprobacion_aplicaria_a_v3=3 | status="RECHAZADA"; code="DESCUENTO_SIN_APROBACION"; responsible_role="GERENCIA"; total=null; order_id=null; conditions=[]; sin_consulta_stock=true; aprobacion_aplicaria_a_v3=3 | ✓ |
| PC3-F01 | status="PENDIENTE"; code="DEPENDENCIA_NO_DISPONIBLE"; responsible_role="ADMINISTRADOR_Y_VENTAS"; order_id=null; conditions=[]; reanudar.status="ACEPTADA"; reanudar.code="VALIDADA"; reanudar.responsible_role="VENTAS"; reanudar.total="1900.00"; reanudar.order_id=null; reanudar.conditions=[] | status="PENDIENTE"; code="DEPENDENCIA_NO_DISPONIBLE"; responsible_role="ADMINISTRADOR_Y_VENTAS"; order_id=null; conditions=[]; reanudar.status="ACEPTADA"; reanudar.code="VALIDADA"; reanudar.responsible_role="VENTAS"; reanudar.total="1900.00"; reanudar.order_id=null; reanudar.conditions=[] | ✓ |
| PC3-I01 | misma_respuesta=true; evento="REINTENTO"; una_sola_solicitud=1 | misma_respuesta=true; evento="REINTENTO"; una_sola_solicitud=1 | ✓ |
| PC3-A01 | http_403=403; evento_denegada=true; E02_sigue_rechazada="DESCUENTO_SIN_APROBACION" | http_403=403; evento_denegada=true; E02_sigue_rechazada="DESCUENTO_SIN_APROBACION" | ✓ |
