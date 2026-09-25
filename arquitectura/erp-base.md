# Ficha de implementación base del ERP

## 1. Propósito

Implementar una fuente única de información comercial para clientes, pedidos, inventario y ventas, con **Odoo como ERP central** y **UBLHUB como microservicio de documentos electrónicos**. La solución atiende dos canales: venta presencial registrada en el ERP y venta por WhatsApp móvil atendida manualmente.

## 2. Arquitectura seleccionada

La solución adopta una arquitectura modular e integrada:

![Arquitectura de despliegue con usuarios, Odoo, registro manual de WhatsApp, adaptador Odoo–UBLHUB, UBLHUB y SUNAT](diagramas/arquitectura-despliegue.png)

*Vista consolidada de los actores, componentes, límites y conexiones de la solución seleccionada.*

- **Odoo:** clientes, tipos de cliente, productos, cotizaciones, pedidos, inventario, ventas y reportes.
- **Adaptador Odoo–UBLHUB:** transforma solicitudes, conserva correlación, aplica idempotencia y gestiona reintentos.
- **UBLHUB:** emisión y consulta de boletas, facturas y guías de remisión.
- **WhatsApp móvil:** canal externo de conversación. En la primera etapa el vendedor registra manualmente el pedido en Odoo; la automatización queda como evolución.
- **Servicio tributario:** destino administrado por la ruta configurada en UBLHUB.

![Integración sugerida: Odoo como ERP central y UBLHUB como microservicio para boletas, facturas y guías de remisión](../imagenes/integracion-ublhub.png)

*Separación propuesta entre la lógica comercial administrada en Odoo y la emisión electrónica delegada a UBLHUB.*

## 3. Actores

| Actor | Responsabilidad |
| --- | --- |
| Cliente | Solicita, confirma y recibe información o documentos |
| Ventas/atención | Registra clientes y pedidos de ambos canales, consulta stock y responde |
| Almacén | Prepara, entrega y controla movimientos |
| Facturación/contabilidad | Supervisa documentos, rechazos, anulaciones y conciliación |
| Gerencia | Consulta indicadores por canal, cliente, producto y estado |
| Administrador | Configura usuarios, catálogos, integración y monitoreo |
| UBLHUB | Procesa documentos electrónicos y devuelve su estado |

## 4. Flujo principal

1. El cliente compra presencialmente o solicita por WhatsApp móvil.
2. Ventas busca una ficha existente y evita duplicados; si corresponde, crea el cliente y su clasificación.
3. Registra el pedido en Odoo e identifica el canal de origen.
4. Odoo valida disponibilidad y reserva o descuenta stock según la operación.
5. La venta confirmada genera una solicitud de documento al adaptador.
6. El adaptador envía a UBLHUB la boleta, factura o guía con una clave idempotente.
7. UBLHUB devuelve identificador, estado, respuesta y archivos disponibles.
8. Odoo actualiza el estado sin perder la relación con pedido, inventario y cliente.
9. El vendedor entrega el comprobante o informa la incidencia por el canal de origen.

## 5. Componentes

| Límite | Componente | Función |
| --- | --- | --- |
| Canal | Atención presencial / ERP | Captura directa de la venta |
| Canal | WhatsApp móvil | Conversación y pedido atendidos manualmente |
| ERP | Contactos y segmentación | Ficha única y tipo de cliente |
| ERP | Ventas | Cotización, pedido, confirmación, pago y estado |
| ERP | Inventario | Disponibilidad, reserva, salida, devolución y ubicación |
| ERP | Reportes | Indicadores comerciales y operativos |
| Integración | Adaptador Odoo–UBLHUB | Mapeo, seguridad, idempotencia, reintento y auditoría |
| Servicio | UBLHUB | Boletas, facturas, guías y estados asociados |
| Externo | Ruta tributaria | Recepción o validación según configuración aplicable |

## 6. Interfaces y datos mínimos

| Interfaz | Datos principales | Controles |
| --- | --- | --- |
| Usuario → Odoo | cliente, tipo, canal, productos, cantidades y entrega | permisos, campos obligatorios y duplicados |
| Odoo → UBLHUB | identificador de venta, emisor, receptor, detalle, totales y tipo de documento | autenticación, validación, cifrado e idempotencia |
| UBLHUB → Odoo | identificador externo, estado, mensaje, archivos y marcas de tiempo | firma/verificación de respuesta, auditoría y reintento controlado |
| Odoo → usuario | disponibilidad, venta y estado del documento | mensajes accionables y restricciones por rol |
| Vendedor → WhatsApp | confirmación, entrega o incidencia | verificación del destinatario y protección de datos |

## 7. Manejo de errores

- Si UBLHUB no responde, la venta permanece registrada con documento pendiente; no se duplica la emisión.
- Si el documento es rechazado, se conserva la respuesta y se habilita una corrección controlada.
- Si se repite la solicitud, la clave idempotente debe devolver o consultar el mismo resultado.
- Si no hay internet, se registra la contingencia y se procesa la cola cuando se restablece el servicio.
- Ninguna falla tributaria debe revertir silenciosamente el movimiento comercial; la conciliación queda visible.

## 8. Seguridad y operación

Los secretos de UBLHUB se almacenan en configuración segura, nunca en el repositorio. Se aplican permisos por rol, bitácora de acciones, copias de seguridad, monitoreo de integración y alertas para documentos pendientes o rechazados. Los ambientes de desarrollo y prueba usan datos ficticios.

## 9. Fases

1. **Levantamiento:** validar clientes, productos, stock, documentos, usuarios, volúmenes y reglas.
2. **Configuración:** preparar Odoo, roles, catálogos, tipos de cliente y los dos canales.
3. **Integración:** implementar y probar el adaptador con el sandbox de UBLHUB.
4. **Migración y conciliación:** depurar maestros e inventario inicial.
5. **Prueba piloto:** ejecutar ventas presenciales y de WhatsApp con usuarios seleccionados.
6. **Salida controlada:** habilitar producción, monitorear y aplicar plan de retorno.
7. **Mejora:** medir resultados y evaluar automatización de WhatsApp.

## 10. Decisiones

| ID | Decisión | Estado |
| --- | --- | --- |
| D-01 | Usar Odoo como ERP central | Adoptada; validar versión, modalidad y licencias |
| D-02 | Usar UBLHUB para boletas, facturas y guías | Adoptada; validar contrato, API y sandbox |
| D-03 | Mantener dos canales: ERP/presencial y WhatsApp móvil | Adoptada |
| D-04 | Registrar manualmente WhatsApp en la primera etapa | Adoptada; automatización posterior |
| D-05 | Configurar antes de personalizar | Adoptada |
| D-06 | Usar integración idempotente y auditable | Obligatoria para producción |

## 11. Pendientes de levantamiento

Volumen de ventas, número de usuarios, sedes, conectividad, reglas de precios, medios de pago, ubicaciones de stock, series de documentos, condiciones para guías, devoluciones, datos a migrar, SLA, costos y responsables de soporte.
