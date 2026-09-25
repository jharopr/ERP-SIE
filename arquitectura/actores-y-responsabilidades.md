# Actores, responsabilidades y permisos

## 1. Criterio de modelado

La solución distingue tres clases de participantes:

- **Actores de negocio:** personas que toman decisiones o ejecutan tareas operativas.
- **Actores de sistema:** componentes que aplican reglas, conservan trazabilidad o intercambian información.
- **Sistemas externos:** servicios fuera del control operativo de la empresa.

`ERP/presencial` y `WhatsApp móvil` son **canales de origen**, no actores. Ambos desembocan en el mismo registro comercial de Odoo.

![Diagrama UML de actores y casos de uso](diagramas/actores-casos-uso.svg)

*Notación UML de casos de uso: los actores aparecen fuera del límite de Odoo; las elipses representan capacidades del sistema y las líneas muestran quién participa en cada una.*

## 2. Mapa general

| Actor | Tipo | Objetivo | Responsabilidad principal | Resultado que entrega |
| --- | --- | --- | --- | --- |
| Cliente | Negocio externo | Comprar y recibir atención trazable | Solicitar productos, proporcionar datos, confirmar condiciones y recibir producto y documento | Pedido confirmado y recepción conforme |
| Ventas y atención | Negocio interno | Convertir solicitudes en pedidos correctos | Identificar al cliente, registrar el canal, preparar la cotización, confirmar el pedido y comunicar estados | Pedido completo y trazable |
| Almacén | Negocio interno | Mantener exactitud física y lógica del inventario | Reservar, preparar, entregar, recibir devoluciones y registrar movimientos | Movimiento de inventario conciliado |
| Facturación y contabilidad | Negocio interno | Asegurar consistencia comercial y tributaria | Revisar datos fiscales, supervisar emisión, resolver rechazos, anular con autorización y conciliar | Documento electrónico vinculado y conciliado |
| Gerencia | Negocio interno | Controlar desempeño y autorizar excepciones | Consultar indicadores, aprobar preventas, descuentos excepcionales, anulaciones y cambios de política | Decisión registrada y seguimiento de indicadores |
| Administrador ERP e integración | Negocio técnico | Mantener la plataforma disponible y segura | Gestionar usuarios, roles, catálogos técnicos, secretos, respaldos, monitoreo e incidentes | Servicio operable, seguro y auditable |
| Odoo | Sistema interno | Ser la fuente única de la operación comercial | Aplicar reglas de cliente, pedido, stock, venta, permisos y trazabilidad | Estado comercial consolidado |
| Adaptador Odoo–UBLHUB | Sistema interno | Desacoplar la operación comercial de la emisión electrónica | Transformar mensajes, autenticar, asignar claves idempotentes, registrar intercambios y reintentar | Solicitud y respuesta correlacionadas |
| UBLHUB | Sistema externo | Procesar documentos electrónicos | Recibir solicitudes, procesar boletas, facturas y guías, y devolver estado y archivos | Resultado electrónico identificable |
| SUNAT | Sistema externo regulador | Recibir y responder por la ruta tributaria | Procesar la comunicación tributaria canalizada por UBLHUB | Constancia, aceptación u observación tributaria |

## 3. Responsabilidad detallada por actor

### 3.1 Cliente

El cliente inicia el proceso presencialmente o por WhatsApp. Indica el producto, cantidad, datos de contacto, modalidad de entrega y tipo de documento. Confirma la cotización y el pago, recibe el producto y el comprobante, y comunica observaciones sobre la atención.

No accede a Odoo ni modifica pedidos, stock o documentos. Sus datos se registran una sola vez y se usan únicamente para atender la operación y cumplir las obligaciones aplicables.

### 3.2 Ventas y atención

Ventas atiende ambos canales y es dueño del pedido hasta su confirmación. Busca primero al cliente por documento, RUC o teléfono normalizado; crea la ficha únicamente cuando no existe coincidencia; registra el canal de origen; selecciona productos y cantidades; consulta disponibilidad; prepara la cotización; registra la confirmación y mantiene informado al cliente.

Puede crear y actualizar cotizaciones y pedidos abiertos. No realiza ajustes directos de inventario, no modifica una venta contabilizada, no cambia permisos y no elimina respuestas de UBLHUB.

### 3.3 Almacén

Almacén controla la correspondencia entre existencias físicas y Odoo. Revisa la reserva, prepara el pedido, registra salida o devolución, entrega al cliente o transportista y reporta diferencias. Cada movimiento conserva usuario, fecha, ubicación, documento de origen y motivo.

Puede operar reservas, transferencias, entregas, recepciones y conteos. No cambia precios, datos fiscales ni estados tributarios.

### 3.4 Facturación y contabilidad

Facturación y contabilidad revisa los datos tributarios del receptor, supervisa boletas, facturas y guías, consulta estados, analiza rechazos, corrige datos permitidos, ejecuta reintentos controlados y solicita anulaciones conforme al procedimiento. Concilia venta, pago, movimiento y documento electrónico.

Puede gestionar el ciclo documental y la conciliación. No altera stock físico ni borra la evidencia de solicitudes, respuestas o errores.

### 3.5 Gerencia

Gerencia consulta ventas, márgenes, stock, documentos, excepciones y tiempos por canal. Autoriza operaciones fuera de política —preventa, descuento excepcional, anulación o ajuste relevante— y registra la justificación. También revisa indicadores y asigna responsables cuando una alerta supera el tiempo de atención definido.

Su rol es de control y aprobación; no sustituye la ejecución diaria de ventas, almacén o administración técnica.

### 3.6 Administrador ERP e integración

El administrador crea usuarios, asigna roles bajo autorización, mantiene catálogos técnicos, configura series y parámetros, custodia secretos fuera del repositorio, ejecuta respaldos, monitorea colas e integraciones y atiende incidentes. Toda intervención crítica queda en bitácora.

No aprueba sus propios cambios de permisos ni usa credenciales compartidas. El acceso a producción se limita a tareas administradas y auditables.

### 3.7 Odoo

Odoo conserva la ficha única del cliente, productos, precios, cotizaciones, pedidos, reservas, movimientos, ventas, pagos y referencias documentarias. Aplica campos obligatorios, permisos, unicidad, disponibilidad, estados y reglas de transición. Es la fuente oficial del estado comercial.

### 3.8 Adaptador Odoo–UBLHUB

El adaptador recibe una venta confirmada, construye el mensaje requerido por UBLHUB, aplica autenticación y cifrado, genera una clave idempotente por venta y tipo de documento, registra solicitud y respuesta, controla reintentos y devuelve a Odoo un estado normalizado. No contiene lógica de precios, clientes ni inventario.

### 3.9 UBLHUB

UBLHUB recibe la solicitud del adaptador, procesa el documento electrónico, canaliza la comunicación tributaria y devuelve identificadores, estado, mensaje y archivos. No administra pedidos, pagos, stock ni conversaciones de WhatsApp.

### 3.10 SUNAT

SUNAT es el sistema regulador externo al que llega la documentación por la ruta gestionada por UBLHUB. Su respuesta se conserva asociada a la venta, pero la empresa no controla sus tiempos ni disponibilidad.

## 4. Matriz RACI

**R** ejecuta, **A** responde por el resultado, **C** aporta criterio y **I** recibe información.

| Actividad | Cliente | Ventas | Almacén | Facturación | Gerencia | Administrador |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Identificar o crear cliente | C | R/A | I | C | I | I |
| Registrar cotización y pedido | C | R/A | I | I | I | I |
| Confirmar condición comercial | R | A | I | C | C | I |
| Reservar y preparar productos | I | C | R/A | I | I | I |
| Entregar y registrar movimiento | C | I | R/A | I | I | I |
| Emitir documento electrónico | I | C | I | R/A | I | C |
| Resolver rechazo o reintento | I | C | I | R/A | I | C |
| Autorizar excepción o anulación | I | C | C | R | A | I |
| Administrar usuarios y permisos | I | I | I | C | A | R |
| Monitorear integración y respaldos | I | I | I | C | I | R/A |
| Revisar indicadores | I | C | C | C | R/A | I |

## 5. Reglas de separación de funciones

1. Quien vende no ajusta existencias ni administra permisos.
2. Quien entrega productos no modifica precios ni documentos tributarios.
3. Quien administra la plataforma no aprueba sus propios accesos.
4. Toda anulación, preventa, descuento excepcional o ajuste relevante requiere autorización de gerencia y motivo registrado.
5. Ningún actor elimina la trazabilidad de una venta, movimiento, solicitud, respuesta o error.
