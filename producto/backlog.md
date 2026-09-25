# Backlog de desarrollo: Odoo + UBLHUB

## 1. Objetivo y estado real

Organizar la configuración y el desarrollo de la primera versión comercial con Odoo y UBLHUB. Se conserva la arquitectura seleccionada por el equipo: Odoo centraliza clientes, pedidos e inventario; el adaptador gestiona la comunicación documental con UBLHUB; WhatsApp permanece como canal atendido manualmente.

La versión 0.4 incorpora actores y permisos, matriz RACI, diagramas de proceso, componentes, secuencia, estados y datos. Son insumos de diseño disponibles; su existencia no acredita configuración de Odoo, un adaptador operativo ni pruebas aprobadas. El frontend sigue siendo una demostración local.

La selección del proyecto no sustituye la verificación de API, cobertura, alojamiento y condiciones de servicio. Si una dependencia resulta incompatible, se registra el bloqueo y se eleva una decisión de cambio al equipo y al responsable del negocio, sin cambiar la arquitectura de manera unilateral.

## 2. Insumos incorporados

| Insumo disponible | Uso en el backlog | Trabajo restante |
| --- | --- | --- |
| [Actores, permisos y RACI](../arquitectura/actores-y-responsabilidades.md) | BL-05 y BL-14: separación de funciones y pruebas por rol | Revisar con usuarios y configurar permisos |
| [Arquitectura y reglas](../arquitectura/erp-base.md) | BL-01, BL-02, BL-07 y BL-08 | Conciliar reglas, concretar despliegue y verificar configuración |
| [ERD](../arquitectura/diagramas/modelo-datos-erd.svg) y [diccionario](../datos/inventario-fuentes.md) | BL-04 y BL-06: revisión del modelo y mapeo de datos | Revisar integridad y correspondencia con Odoo; preparar cargas |
| [Proceso comercial](../procesos/flujos-prioritarios.md) | BL-07, BL-08 y BL-14 | Verificar pedidos, reservas, entregas, devoluciones y excepciones |
| [Secuencia de emisión](../arquitectura/diagramas/secuencia-emision.svg) y [estados](../arquitectura/diagramas/estados-documento.svg) | BL-09 a BL-12 | Contrastarlos con API real y probar transiciones |
| [Casos de aceptación P-01 a P-13](../pruebas/casos-aceptacion.md) | BL-06 a BL-14 | Ejecutar y registrar resultados; completar escenarios faltantes |
| [Prototipo visual](frontend/README.md) | Referencia para revisión con usuarios | No utilizarlo como prueba de integración real |

Los actores del negocio validan resultados operativos. Los roles técnicos del backlog ejecutan configuración o desarrollo. No se asignan automáticamente esos trabajos a los integrantes de clase: la distribución debe acordarse y registrarse en [contribuciones](../documentos/contribuciones.md).

## 3. Prioridad, estado y cierre

- **P0:** insumo o decisión que bloquea el trabajo dependiente.
- **P1:** capacidad necesaria para el alcance inicial.
- **P2:** mejora posterior, fuera de la primera versión.

**Diseño disponible** significa que existe documentación. **Pendiente de ejecución** significa que no se ha acreditado implementación. **Bloqueado** indica una dependencia externa sin resolver. **Terminado** exige evidencia y revisión; no basta con especificar la tarea.

Una actividad puede comenzar cuando tenga entradas disponibles, responsable confirmado y criterio de aceptación revisado. Los estados siguientes reflejan evidencia del repositorio al momento de esta revisión; deben actualizarse si el equipo aporta trabajo adicional verificable.

## 4. Backlog priorizado

Se conservan BL-01 a BL-15 del PR original. Se añaden BL-16 y BL-17 para hacer explícitas la migración y la continuidad operativa. La numeración identifica tareas, no obliga a ejecutarlas en orden numérico.

| ID | Trabajo concreto | Prioridad | Dependencias | Responsable ejecutor propuesto | Estado |
| --- | --- | --- | --- | --- | --- |
| BL-01 | Consolidar línea base y alcance: herramientas actuales, usuarios, sedes, datos, reglas comerciales y tratamiento de PLE respecto de S3. Conciliar discrepancias entre documentos. | P0 | Información del negocio y documentos del proyecto | Análisis funcional; validan gerencia y áreas operativas | Diseño disponible; validación del negocio por acreditar |
| BL-02 | Registrar edición, versión y alojamiento de Odoo, ubicación del adaptador, costos y responsabilidades de operación. | P0 | BL-01; información contractual y técnica | Arquitectura y administrador ERP | Pendiente de concreción documental |
| BL-03 | Obtener y revisar documentación, cobertura, autenticación, consulta de estados, sandbox y condiciones de servicio de UBLHUB. | P0 | Alcance documental de BL-01; acceso al proveedor | Integración; consulta a facturación | Bloqueado por documentación y acceso verificables |
| BL-04 | Revisar el ERD y diccionario existentes, alinear entidades y claves y mapearlas a objetos de Odoo sin duplicar innecesariamente modelos nativos. | P0 | BL-01; ERD y diccionario v0.4 | Datos y configuración ERP | Diseño disponible; revisión y mapeo pendientes |
| BL-05 | Preparar Odoo de pruebas y configurar permisos de Ventas, Almacén, Facturación, Gerencia y Administrador según la matriz de actores. | P1 | BL-02; permisos revisados | Administrador ERP | Diseño disponible; ejecución no acreditada |
| BL-06 | Configurar clientes, productos y listas de precios; cargar datos sintéticos y probar unicidad e importaciones. | P1 | BL-04 y BL-05 | Datos y configuración ERP | Pendiente de ejecución |
| BL-07 | Configurar cotización, pedido, canal presencial/WhatsApp, condiciones comerciales, registro de pago y descuentos autorizados. | P1 | BL-01 y BL-06 | Configuración ERP; valida Ventas | Diseño disponible; ejecución no acreditada |
| BL-08 | Configurar ubicaciones, reserva al confirmar, salida al entregar, bloqueo de stock negativo, preventa autorizada y devolución vinculada. | P1 | BL-06 y BL-07 | Configuración ERP; valida Almacén | Diseño disponible; ejecución no acreditada |
| BL-09 | Especificar el contrato del adaptador: mapeos por documento, evento de emisión, correlación, estados, autenticación, deduplicación y recuperación. | P1 | BL-02, BL-03 y BL-04; reglas de BL-01 | Integración y arquitectura | Diagramas disponibles; contrato bloqueado por API |
| BL-10 | Implementar emisión y consulta de boletas y facturas, conservando respuesta, archivos y referencia de origen. | P1 | BL-05, BL-07 y BL-09; sandbox | Integración; valida Facturación | Bloqueado |
| BL-11 | Implementar guías con datos de traslado y relación con la entrega correspondiente. | P1 | BL-08 y BL-09; cobertura y sandbox | Integración; validan Almacén y Facturación | Bloqueado |
| BL-12 | Implementar y probar control de duplicación, respuestas perdidas, rechazos, correcciones, anulaciones y reintentos limitados. | P1 | BL-10 y BL-11; diseño de controles en BL-09 | Integración; valida Facturación | Diseño disponible; ejecución bloqueada |
| BL-13 | Configurar consultas por canal y estado, documentos en cola o rechazados y trazabilidad a pedido, movimiento y operación documental. | P1 | BL-07, BL-08 y BL-12 | Configuración ERP; validan Gerencia y Facturación | Pendiente de ejecución |
| BL-14 | Ejecutar aceptación integral, capacitación por rol y un piloto autorizado; registrar resultados, defectos y decisión de avance. | P1 | BL-05 a BL-13, BL-16 y BL-17 | Validación y usuarios clave; gerencia autoriza piloto | Casos definidos; ejecución no acreditada |
| BL-15 | Evaluar automatización de WhatsApp con volumen, reproceso, costos y requisitos del canal. | P2 | Evidencia del proceso inicial y decisión de alcance | Análisis funcional e integración | Fuera del alcance inicial |
| BL-16 | Ensayar carga de clientes, productos y stock inicial; depurar duplicados y conciliar con un conjunto de origen autorizado. | P1 | BL-04, BL-06 y BL-08; datos autorizados | Datos; valida Almacén | Planificado; no ejecutado |
| BL-17 | Definir y probar respaldo, restauración, monitoreo, contingencia por desconexión y retorno del piloto. | P1 | BL-02 y BL-05; BL-12 para fallos de integración | Administrador ERP; validan áreas operativas | Planificado; no ejecutado |

## 5. Criterios de aceptación y evidencia de cierre

Son condiciones para aceptar trabajo futuro. Los casos P corresponden al archivo de pruebas existente; los casos adicionales deben documentarse antes de su ejecución.

| ID | Criterio observable | Evidencia y relación con pruebas |
| --- | --- | --- |
| BL-01 | La línea base distingue hechos, reglas de diseño y datos no confirmados. Define el alcance de PLE y resuelve la secuencia pedido–reserva–entrega y sus discrepancias documentales. | Ficha revisada, observaciones y decisión sobre cada discrepancia; revisión funcional |
| BL-02 | Se identifican modalidad de Odoo y entorno del adaptador, acceso de integración compatible, responsable, costos conocidos y condiciones pendientes. | Registro técnico/contractual o referencia autorizada; no basta mencionar una orden sin identificarla |
| BL-03 | Cada capacidad requerida tiene fuente o respuesta identificable. Se comprueba acceso de pruebas o se registra la imposibilidad y se mantiene el bloqueo. | Matriz de cobertura, versión de API y evidencia de acceso sin secretos |
| BL-04 | ERD y diccionario concuerdan en entidades, claves, cardinalidades y relaciones. El mapeo distingue objetos estándar, campos adicionales y extensiones necesarias. | Revisión del modelo y tabla de mapeo; una imagen por sí sola no cierra el trabajo |
| BL-05 | Cada rol ejecuta una acción permitida y recibe rechazo ante una prohibida. Ventas no ajusta stock; Almacén no altera precios; permisos críticos requieren aprobación. | Configuración e instrucciones reproducibles; pruebas adicionales de permisos con fecha y ejecutor |
| BL-06 | Se crea un cliente válido y se detecta documento/RUC existente. Una carga repetida no duplica clientes ni SKU; las listas de precios se aplican según la regla aprobada. | P-01, P-02 y pruebas adicionales de carga y precios |
| BL-07 | Se registra un pedido de cada canal con cliente, líneas, cantidades y referencia. Un descuento excepcional deja autorización y se verifica la regla de pago antes de entrega. | P-03 y P-04; casos adicionales de pago y descuento |
| BL-08 | Con 10 unidades, confirmar 2 reserva 2 sin reducir las existencias físicas; entregar deja 8 y libera la reserva. No se registra stock negativo; la preventa autorizada no simula una salida inexistente. Una devolución deja movimiento inverso y referencia original. | P-05 y P-06; pruebas adicionales de devolución y preventa. P-03 debe aclarar que la salida se registra al entregar |
| BL-09 | Se documentan mensajes sintéticos, campos obligatorios, eventos de emisión y estados según la API. La identidad estable distingue reintentos de nuevas operaciones legítimas; se contempla una venta con varios documentos o traslados. | Contrato revisado, mapeo de estados y secuencia; no implementar solo una clave genérica venta/tipo sin evaluar esos casos |
| BL-10 | Una boleta y una factura de prueba conservan identificador, estado y archivos disponibles; una solicitud inválida deja error trazable. | P-07 y P-08, mensajes anonimizados y correlación con la operación |
| BL-11 | La guía de prueba conserva datos de traslado, identificador, estado y vínculo con la entrega. Traslados diferentes se identifican sin confundirse con reintentos. | P-09 y caso adicional de entregas parciales si el alcance las admite |
| BL-12 | Solicitudes repetidas o concurrentes no duplican emisión. Ante pérdida de respuesta se consulta/concilia antes de reenviar. Un rechazo conserva historial; una anulación requiere autorización y no borra evidencia. Los reintentos tienen límite y escalamiento. | P-10, P-11 y P-12; casos adicionales de concurrencia, pérdida de respuesta y anulación |
| BL-13 | Usuarios autorizados consultan canal y estado, encuentran pendientes/rechazos y navegan hasta el pedido y documento relacionado. | P-13 y contraste de consultas con datos de prueba |
| BL-14 | Cada caso tiene precondiciones, ejecutor, fecha, ambiente, resultado y evidencia. No se autoriza piloto con duplicación, pérdida de trazabilidad, permisos indebidos o stock incorrecto. | Informe de aceptación, capacitación y decisión de gerencia; simulaciones identificadas como tales |
| BL-15 | Se justifica automatizar o mantener el registro manual mediante datos del proceso y requisitos técnicos y económicos. | Caso de mejora; no exige construir el conector |
| BL-16 | Una carga de ensayo concilia cantidades de origen/destino, detecta rechazos y demuestra que repetirla no duplica registros. El saldo inicial se aprueba antes del piloto. | Reporte de migración y conciliación; datos sintéticos o autorizados. La carga productiva exige autorización separada |
| BL-17 | Se restaura un respaldo en pruebas y se ejecuta el procedimiento ante caída del servicio o pérdida de acceso desde el local. Se identifican responsable, registro de contingencia y reconciliación posterior. | Evidencia de restauración y simulación de contingencia; plan de retorno revisado |

## 6. Secuencia y dependencias externas

1. **Preparación:** BL-01 a BL-04. Se reutilizan los diseños v0.4, se revisan y se concretan las dependencias. La falta de API bloquea la integración, pero no toda la configuración comercial.
2. **Configuración comercial:** BL-05 a BL-08. BL-09 puede diseñarse en paralelo cuando tenga sus entradas; los controles de duplicación se diseñan aquí, no después de emitir documentos.
3. **Integración:** BL-10 y BL-11, seguidos por la comprobación transversal de BL-12. BL-13 incorpora los estados ya normalizados.
4. **Preparación de piloto:** BL-16 y BL-17 avanzan cuando sus dependencias lo permitan. BL-14 requiere sus resultados además del flujo integrado.
5. **Evolución:** BL-15 permanece fuera de la primera versión.

## 7. Correspondencia con el backlog anterior de main

| ID anterior | Trabajo conservado en esta versión |
| --- | --- |
| B-01: línea base | BL-01 |
| B-02: cliente único | BL-04 y BL-06 |
| B-03: dos canales | BL-07 |
| B-04: inventario | BL-08 |
| B-05: integración | BL-03, BL-09, BL-10 y BL-11 |
| B-06: documentos en sandbox | BL-10, BL-11 y BL-14 |
| B-07: errores y contingencia | BL-12 y BL-17 |
| B-08: migración | BL-16 |
| B-09: capacitación y piloto | BL-14 |
| B-10: WhatsApp automático | BL-15, evaluación fuera del alcance inicial |