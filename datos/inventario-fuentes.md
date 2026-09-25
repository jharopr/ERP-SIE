# Inventario de datos y fuentes operativas

## Fuentes para el levantamiento

| Fuente | Datos útiles | Estado y límite |
| --- | --- | --- |
| Ficha de la empresa | productos, clientes, canales, proceso actual y necesidades | Validar con responsables del negocio |
| Ficha de comparación de ERPs | capacidades, brechas y razones de selección | No sustituye demostración ni cotización |
| Ficha de implementación base del ERP | alcance, fases, integración, controles y riesgos | Base sujeta a validación técnica |
| Odoo | clientes, productos, pedidos, ventas, inventario y estados | Sistema central propuesto |
| UBLHUB | solicitudes, identificadores, documentos, respuestas y errores | Servicio tributario propuesto |
| WhatsApp móvil | conversación y referencia del pedido | Canal manual; evitar copiar conversaciones completas sin autorización |

## Diccionario mínimo

| Entidad | Campos mínimos | Regla |
| --- | --- | --- |
| Cliente | ID, tipo, documento/RUC, nombre o razón social, contacto autorizado, estado | Un registro por persona o empresa; controlar duplicados |
| Producto | SKU, descripción, unidad, precio, impuestos, estado | SKU único |
| Pedido | ID, fecha, canal, cliente, líneas, total y estado | Canal obligatorio: ERP/presencial o WhatsApp móvil |
| Inventario | SKU, ubicación, disponible, reservado y movimiento | Conciliar antes y después |
| Venta | ID Odoo, pedido, cliente, total, pago y estado | Trazable al pedido |
| Documento electrónico | tipo, serie/número, ID de venta, ID UBLHUB, estado, archivos y error | Idempotencia y trazabilidad |
| Interacción | referencia de pedido, canal, fechas y estado | No almacenar más datos de conversación de los necesarios |

## Datos de prueba y privacidad

Usar SKU, clientes, documentos, teléfonos y cantidades ficticios. No incluir DNI, teléfonos, direcciones, correos, credenciales ni conversaciones reales en capturas o archivos de prueba. Los datos productivos solo se migran con autorización, respaldo, reglas de limpieza y conciliación.
