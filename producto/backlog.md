# Backlog de desarrollo: Odoo + UBLHUB

## 1. Alcance y estado actual

Implementar clientes, pedidos, inventario y documentos electrónicos con Odoo + UBLHUB. Los pedidos recibidos por WhatsApp se registrarán manualmente; su automatización queda fuera del alcance inicial.

El repositorio contiene actores, permisos propuestos, modelo de datos, diagramas y casos de aceptación. Estos documentos orientan la implementación, pero no acreditan una instalación de Odoo ni una integración operativa con UBLHUB.

## 2. Backlog priorizado

- **P0:** definición o insumo necesario para habilitar el trabajo dependiente.
- **P1:** funcionalidad o control necesario para la primera versión.
- **P2:** mejora posterior, fuera del alcance inicial.

| ID | Prioridad | Tarea | Dependencias | Criterio de aceptación |
|---|---|---|---|---|
| BL-01 | P0 | Confirmar alcance, herramientas actuales y tratamiento del requisito PLE de S3. | Información del negocio | Alcance revisado con inclusiones, exclusiones, reglas y datos pendientes identificados. |
| BL-02 | P0 | Definir versión, edición y alojamiento de Odoo, ubicación del adaptador y soporte. | BL-01; información técnica y comercial | Configuración objetivo documentada, con compatibilidad de integración, costos y responsable de operación. |
| BL-03 | P0 | Verificar cobertura, API y acceso de pruebas de UBLHUB. | BL-01; documentación y acceso del proveedor | Documentación identificable de boletas, facturas, guías, autenticación y consulta de estados; acceso al ambiente de pruebas comprobado. |
| BL-04 | P0 | Revisar el ERD y diccionario existentes y relacionarlos con los objetos de Odoo. | BL-01; modelo existente | Entidades, claves y relaciones coherentes; objetos estándar, campos adicionales y extensiones necesarios identificados. |
| BL-05 | P1 | Preparar Odoo de pruebas y configurar los roles definidos. | BL-02; matriz de permisos revisada | El ambiente puede iniciarse siguiendo instrucciones. Cada rol ejecuta una acción permitida y tiene bloqueada una prohibida. |
| BL-06 | P1 | Configurar clientes, productos y precios con datos sintéticos. | BL-04 y BL-05 | Se aplican los precios definidos y una carga repetida no duplica clientes ni productos. Las coincidencias ambiguas se revisan antes de seleccionar una ficha; se exigen los datos mínimos aprobados. |
| BL-07 | P1 | Configurar pedidos presenciales y de WhatsApp, seguimiento, pagos y descuentos. | BL-06; reglas comerciales revisadas | Cada pedido conserva identificador único, canal, vendedor, cliente, detalle e historial de estados; los de WhatsApp incluyen referencia de atención. Reprocesar el mismo pedido no genera otra venta ni movimiento de stock. Se verifica el pago antes de entregar y los descuentos excepcionales requieren autorización. |
| BL-08 | P1 | Configurar reservas, entregas, preventas y devoluciones. | BL-07; reglas de inventario revisadas | Con 10 unidades en existencia, confirmar 2 deja 2 reservadas y 8 disponibles; al entregar, quedan 8 en existencia y se libera esa reserva. Se bloquea el stock negativo; la preventa requiere autorización sin simular una salida inexistente. Las devoluciones quedan vinculadas a la venta y generan el movimiento correspondiente. |
| BL-09 | P1 | Definir mensajes, eventos de emisión, estados y controles del adaptador. | BL-02, BL-03 y BL-04; reglas de BL-01 | Cada documento tiene campos obligatorios, identificador de operación y reglas de respuesta, error y reintento. Se distinguen reenvíos de una solicitud y nuevas operaciones legítimas, incluidos traslados diferentes. |
| BL-10 | P1 | Integrar emisión y consulta de boletas y facturas. | BL-05, BL-07 y BL-09; sandbox disponible | Cada documento de prueba conserva identificador, estado, archivos disponibles y vínculo con la venta. Los datos inválidos producen un error visible y no se registran como emisión exitosa. |
| BL-11 | P1 | Integrar guías de remisión. | BL-08 y BL-09; sandbox disponible | La guía de prueba conserva datos del traslado, identificador, estado y vínculo con la entrega. Solo se solicita cuando corresponde según las reglas aprobadas. |
| BL-12 | P1 | Implementar y probar controles de duplicación, rechazo, anulación y recuperación. | BL-10 y BL-11; controles diseñados en BL-09 | Repetir una solicitud no duplica el documento. Ante una respuesta perdida, se consulta o concilia el resultado antes de reenviar. Los errores conservan historial, los reintentos tienen límite y las anulaciones requieren autorización. |
| BL-13 | P1 | Configurar consultas por canal, tipo de cliente y estado documental. | BL-07, BL-08 y BL-12 | Los filtros devuelven los registros correspondientes y los totales coinciden con las ventas consultadas. El usuario autorizado puede localizar documentos pendientes o rechazados y acceder a su operación de origen. |
| BL-14 | P1 | Ejecutar pruebas integrales, capacitación por rol y piloto. | BL-05 a BL-13, BL-16 y BL-17 | Cada prueba tiene resultado y evidencia. Los usuarios completan los escenarios de su rol. El piloto requiere autorización y ausencia de fallos críticos de stock, duplicación, permisos o trazabilidad. |
| BL-15 | P2 | Evaluar la automatización de WhatsApp. | Resultados del proceso inicial | Decisión sustentada en volumen de pedidos, reproceso, costos y requisitos del canal. Esta tarea no incluye desarrollar el conector. |
| BL-16 | P1 | Ensayar la migración de clientes, productos y stock inicial. | BL-04, BL-06 y BL-08 | Registros y cantidades de origen y destino conciliados, errores identificados y carga repetida sin duplicados. |
| BL-17 | P1 | Probar respaldo, restauración y contingencia por desconexión. | BL-02 y BL-05; BL-12 para fallos de integración | Se restaura un respaldo en pruebas y se verifica el procedimiento de interrupción, recuperación y conciliación, incluida la pérdida de acceso al ERP desde el local. |

La numeración identifica tareas; sus dependencias determinan el orden de ejecución. Las pruebas utilizarán datos sintéticos. Las evidencias no expondrán conversaciones, datos personales ni credenciales reales.

## 3. Estado y seguimiento

- **BL-01 y BL-04:** documentación disponible; falta validar el alcance y revisar la correspondencia del modelo con Odoo.
- **BL-02 y BL-03:** definiciones de despliegue, documentación técnica y acceso de pruebas pendientes de acreditar.
- **BL-05 a BL-13:** existen reglas y diagramas que orientan estas tareas; configuración, desarrollo y pruebas pendientes de acreditar.
- **BL-14:** 17 casos de aceptación definidos, registrados como “No ejecutado” en la versión revisada; ejecución y piloto pendientes.
- **BL-16 y BL-17:** migración, restauración y contingencia pendientes de ejecución.
- **BL-15:** fuera del alcance inicial.

Antes de iniciar cada tarea se confirmarán el responsable, sus dependencias y el esfuerzo estimado. Una tarea pasará a **Terminada** cuando cumpla su criterio de aceptación y registre **fecha, ejecutor, resultado y enlace a evidencia revisada por otro integrante**.

La documentación de una tarea no equivale a su implementación. Los estados se actualizarán cuando exista evidencia nueva.

## 4. Relación con casos de aceptación

Se utilizarán los [casos de aceptación del repositorio](../pruebas/casos-aceptacion.md):

| Tarea | Casos relacionados |
|---|---|
| BL-05: permisos | SEG-01 |
| BL-06: clientes | WA-02 y WA-03 |
| BL-07: pedidos y seguimiento | WA-01, WA-07, WA-08 y ERP-01 |
| BL-08: inventario | WA-04 a WA-06 |
| BL-10: boletas y facturas | UBL-01 y UBL-02 |
| BL-11: guías | UBL-03 |
| BL-12: errores y duplicación | UBL-04 a UBL-06 |
| BL-13: reportes | REP-01 |
| BL-14: aceptación integral | Todos los anteriores |

Se completarán escenarios de precios, cargas repetidas, pagos, descuentos, devoluciones, anulaciones, migración y restauración. SEG-01 deberá identificar acciones permitidas y prohibidas por rol.

Antes de ejecutar las pruebas se ajustarán estas precisiones:

- **WA-04 y WA-06:** distinguir reserva al confirmar y salida al entregar.
- **WA-07:** distinguir la referencia de atención del identificador del pedido; una conversación puede originar varios pedidos legítimos.
- **UBL-04:** identificar la operación documental para diferenciar un reintento de una nueva emisión legítima.
