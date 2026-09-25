# Casos y criterios de aceptación

| ID | Escenario | Criterio de aceptación | Estado |
| --- | --- | --- | --- |
| P-01 | Crear consumidor final | Se crea una sola ficha con los campos mínimos | No ejecutado |
| P-02 | Crear cliente con RUC existente | El sistema evita el duplicado y muestra la ficha encontrada | No ejecutado |
| P-03 | Registrar venta presencial | El pedido queda con canal ERP/presencial y afecta stock una vez | No ejecutado |
| P-04 | Registrar venta recibida por WhatsApp | El pedido queda con canal WhatsApp móvil y referencia de atención | No ejecutado |
| P-05 | Confirmar cantidad disponible | Se reserva o descuenta la cantidad configurada | No ejecutado |
| P-06 | Intentar vender sin stock | Se bloquea o aplica la excepción autorizada y deja auditoría | No ejecutado |
| P-07 | Emitir boleta mediante UBLHUB | Odoo conserva ID, estado y archivos devueltos | No ejecutado |
| P-08 | Emitir factura mediante UBLHUB | Los datos del receptor se validan y el resultado queda vinculado | No ejecutado |
| P-09 | Emitir guía mediante UBLHUB | La guía conserva la relación con venta y traslado | No ejecutado |
| P-10 | Repetir la misma solicitud | No se crea una segunda venta ni un segundo documento | No ejecutado |
| P-11 | Simular rechazo | El mensaje es visible, auditable y corregible | No ejecutado |
| P-12 | Simular caída de UBLHUB | La venta permanece y el documento queda pendiente para reintento | No ejecutado |
| P-13 | Consultar reporte | Se filtran resultados por canal, tipo de cliente y estado | No ejecutado |

Antes de ejecutar se necesitan Odoo configurado, sandbox de UBLHUB, datos sintéticos, roles, reglas de stock y criterios tributarios aprobados.
