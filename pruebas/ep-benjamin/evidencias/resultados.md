# EP Benjamin · Resultados de simulación local

Archivo generado automáticamente por `generar_evidencias.py`; no editar manualmente.

**3 casos aprobados y 112 comprobaciones satisfactorias.** Expectativas fijas independientes de las respuestas observadas.

| Caso | Estado / código esperado | Estado / código observado | Comprobaciones | Resultado |
| --- | --- | --- | ---: | --- |
| [EP-N01](EP-N01.json) | `ACEPTADA` / `VALIDADA` | `ACEPTADA` / `VALIDADA` | 37 | Aprobado |
| [EP-S01](EP-S01.json) | `PROMESA_CONDICIONADA` / `DISPONIBILIDAD_PARCIAL` | `PROMESA_CONDICIONADA` / `DISPONIBILIDAD_PARCIAL` | 37 | Aprobado |
| [EP-E01](EP-E01.json) | `RECHAZADA` / `DESCUENTO_SIN_APROBACION` | `RECHAZADA` / `DESCUENTO_SIN_APROBACION` | 38 | Aprobado |

En todos los casos `order_id: null`; stock y maestros intactos. La repetición idéntica mantiene una sola solicitud y una sola decisión, con reintento adicional auditado.

EP-S01: déficit sintético 2 para `RAD-7BT` en `TIENDA-DEMO`; señal `REP-EP-001` exclusivamente conceptual, sin compra, reserva ni fecha prometida.

EP-E01: cotización v2 y aceptación sintética de la misma versión; el rechazo por falta de aprobación del dueño precede a la consulta de inventario. Evidencia de apoyo al análisis de excepción de Adrián.

Fecha lógica simulada: 24/10/2026, zona -05:00. Solicitud 09:55, respuesta y auditoría inicial en la misma transacción 09:55:01; reintento 09:56:01. Vigencia de la oferta hasta las 18:00. No son tiempos de servicio medidos.

La línea de tiempo anterior al envío es didáctica. No se valida un journey observado, identidad real ni una instalación de Odoo. Límite: solicitud/respuesta; no se ejecuta pedido, factura, entrega, posventa o P2P.

[Manifiesto de ejecución UTC y hashes](ejecucion.json) · [Método y límites](../README.md)
