# Casos y criterios de aceptación

| ID | Escenario | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| P-01 | Crear consumidor final | Se crea una sola ficha con los campos mínimos | Caso definido |
| P-02 | Crear cliente con RUC existente | El sistema evita el duplicado y muestra la ficha encontrada | Caso definido |
| P-03 | Registrar venta presencial | El pedido queda con canal ERP/presencial y afecta stock una vez | Caso definido |
| P-04 | Registrar venta recibida por WhatsApp | El pedido queda con canal WhatsApp móvil y referencia de atención | Caso definido |
| P-05 | Confirmar cantidad disponible | Se reserva al confirmar y se descuenta al entregar | Caso definido |
| P-06 | Intentar vender sin stock | Se bloquea o aplica la preventa autorizada y deja auditoría | Caso definido |
| P-07 | Emitir boleta mediante UBLHUB | Odoo conserva ID, estado y archivos devueltos | Caso definido |
| P-08 | Emitir factura mediante UBLHUB | Los datos del receptor se validan y el resultado queda vinculado | Caso definido |
| P-09 | Emitir guía mediante UBLHUB | La guía conserva la relación con venta y traslado | Caso definido |
| P-10 | Repetir la misma solicitud | No se crea una segunda venta ni un segundo documento | Caso definido |
| P-11 | Simular rechazo | El mensaje es visible, auditable y corregible | Caso definido |
| P-12 | Simular caída de UBLHUB | La venta permanece y el documento queda en cola para reintento | Caso definido |
| P-13 | Consultar reporte | Se filtran resultados por canal, tipo de cliente y estado | Caso definido |

La ejecución usa Odoo configurado, sandbox de UBLHUB, datos sintéticos, roles, reglas de stock y criterios tributarios aprobados. Cada resultado cambia a `Aprobado` o `Observado` y enlaza su evidencia; `Caso definido` significa que el criterio está completo, no que la prueba ya pasó.
