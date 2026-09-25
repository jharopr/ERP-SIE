# Flujo comercial prioritario

## Proceso actual

### Venta presencial

1. El cliente consulta un producto en el local.
2. El vendedor verifica disponibilidad por los medios actuales.
3. Registra o coordina la venta sin un ERP central que relacione cliente, pedido, stock y comprobante.
4. Se entrega el producto y se emite el documento correspondiente mediante el mecanismo disponible.

### Venta por WhatsApp móvil

1. El cliente escribe al número atendido manualmente.
2. El vendedor identifica el producto y consulta disponibilidad.
3. Los datos se trasladan manualmente para preparar la venta.
4. El vendedor confirma pago, entrega o recojo y comunica el estado por WhatsApp.
5. La conversación y el registro comercial quedan separados, lo que genera riesgo de omisión, duplicidad y falta de seguimiento.

## Proceso objetivo con Odoo + UBLHUB

![Resumen del proceso objetivo desde el cliente presencial o por WhatsApp, pasando por Odoo y UBLHUB hasta SUNAT](../imagenes/proceso%20objetivo.png)

*Vista resumida del flujo objetivo. Los pasos siguientes detallan controles, estados y responsabilidades.*

![Proceso comercial objetivo con responsables por carril](../arquitectura/diagramas/proceso-comercial-bpmn.svg)

*Vista BPMN simplificada: cada carril identifica al responsable y cada flecha muestra el traspaso de trabajo.*

1. El vendedor identifica el canal de origen: `ERP/presencial` o `WhatsApp móvil`.
2. Busca al cliente por documento, teléfono normalizado o RUC; si no existe, crea una ficha única y asigna el tipo de cliente.
3. Registra cotización o pedido en Odoo con productos, cantidades y referencia de la conversación cuando corresponda.
4. Odoo consulta la disponibilidad. Al confirmar el pedido reserva las unidades; si no existe stock suficiente, bloquea la confirmación y Ventas ofrece una alternativa o solicita una preventa autorizada por Gerencia.
5. Al confirmar la venta, Odoo genera el movimiento de inventario y solicita a UBLHUB la boleta, factura o guía de remisión.
6. UBLHUB procesa el documento por la ruta tributaria configurada y devuelve estado, identificadores y archivos asociados.
7. Odoo conserva el estado integral. El vendedor entrega o envía el comprobante y responde al cliente por el canal de origen.
8. Gerencia consulta ventas, stock, documentos y tiempos de atención por canal y tipo de cliente.

## Responsables por etapa

| Etapa | Responsable | Participantes | Evidencia en Odoo |
| --- | --- | --- | --- |
| Solicitud | Cliente | Ventas | Canal, fecha y referencia de atención |
| Identificación | Ventas | Cliente | Ficha única o coincidencia reutilizada |
| Cotización | Ventas | Cliente, Odoo | Productos, cantidades, precio y vigencia |
| Reserva | Almacén | Ventas, Odoo | Cantidad, ubicación y responsable |
| Confirmación | Ventas | Cliente, Facturación | Pedido, pago y estado de venta |
| Preparación y entrega | Almacén | Cliente, Ventas | Salida, entrega o devolución |
| Emisión | Facturación | Odoo, adaptador, UBLHUB | Clave idempotente, estado y archivos |
| Excepción | Gerencia | Área originadora | Autorización, motivo, fecha y responsable |
| Seguimiento | Gerencia | Todas las áreas | Indicadores y acciones registradas |

La definición completa de responsabilidades, permisos y límites está en [Actores y responsabilidades](../arquitectura/actores-y-responsabilidades.md).

## Reglas y controles

| Elemento | Regla operativa |
| --- | --- |
| Cliente único | Evitar duplicados por documento/RUC y aplicar coincidencias controladas para teléfono |
| Canal | Toda venta debe registrar `ERP/presencial` o `WhatsApp móvil` |
| Stock | Bloquear stock negativo; una preventa exige autorización de Gerencia y fecha comprometida |
| Idempotencia | Una solicitud repetida no debe crear dos ventas ni dos documentos electrónicos |
| Facturación | El tipo de documento depende del tipo de cliente y de los datos tributarios completos |
| Guía de remisión | Emitirla mediante UBLHUB cuando el traslado y la normativa aplicable lo requieran |
| Excepciones | Registrar rechazo, reintento, anulación y responsable sin perder la referencia original |
| Privacidad | Usar datos reales solo con autorización y restringir su exposición en evidencias |

Los escenarios verificables están en [casos funcionales](../pruebas/casos-aceptacion.md).
