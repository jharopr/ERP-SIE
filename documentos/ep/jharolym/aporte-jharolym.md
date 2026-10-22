# Arquitectura integrada del caso presencial

IMPORTACIONES MYS HERMANOS S.A.C. · GE703 · Grupo 7 · 2026-2  
Jharolym Friendly Paucarcaja Ramos · Sección 2 · Comité del 24/10/2026 · 01:00–04:00

## Decisión que defiendo

Propongo mantener Odoo como núcleo integrado para identificar al cliente, registrar su necesidad y conservar una cotización vinculada a la oportunidad. Contactos mantiene identidad; CRM, lead y oportunidad; Ventas, oferta y condiciones; Inventario, disponibilidad fechada. El control de transición verifica esos registros y la autorización comercial antes de conservar una respuesta.

Mantengo el caso delimitado en PC2: persona natural nueva del público general, atención presencial en tienda y visita espontánea. La necesidad de cinco autoradios para vehículos familiares es el supuesto del ejemplo; la cantidad no determina que el cliente sea mayorista. El vendedor busca coincidencias antes de crear la ficha y recoge únicamente datos necesarios y autorizados.

En el parcial, la arquitectura sostiene el hilo que demuestra Benjamín hasta solicitud y respuesta. La aceptación de la cotización por el cliente y la respuesta `ACEPTADA` del evaluador son hechos diferentes. La respuesta validada conserva `order_id = null`; pedido, reserva y ejecución posterior quedan pendientes.

## Texto integrado para la sección 2

**Responsable:** Jharolym Friendly Paucarcaja Ramos. **Evidencia:** diagrama C01–C08 con iconos, interfaces I01–I07, matriz de registros y casos EP-N01/EP-S01/EP-E01 compartidos con Benjamín.

Odoo se conserva como plataforma propuesta desde PC1, con UBLHUB reservado para emisión futura. PC2 delimita la gestión comercial a un cliente nuevo del público general que llega al local por visita espontánea. Para el parcial, identificamos las responsabilidades que sostienen ese mismo caso: Contactos registra `CLI-DEMO-001`; CRM conserva el lead y `OPP-DEMO-001`; Ventas mantiene `COT-DEMO-001`, su versión y evidencia de aceptación. La cotización usa cinco autoradios a S/ 400, base S/ 2,000 y descuento didáctico del 5 %, con total S/ 1,900.

El control de transición propuesto consulta la versión vigente y aceptada en Ventas, la disponibilidad en Inventario y la autorización comercial cuando corresponde. La bitácora conserva actor, evento, fecha, solicitud y correlación. En el caso normal se obtiene estado `ACEPTADA` y código `VALIDADA`, sin pedido operativo. En la variante con tres unidades disponibles, el faltante de dos origina una señal conceptual para evaluar abastecimiento. En el caso de descuento del 10 % sin aprobación válida, la solicitud se rechaza y se escala al dueño. Las tres variantes son independientes y utilizan datos sintéticos.

El diagrama representa una arquitectura lógica por implementar. Los modelos de transición, aprobaciones, versionado y bitácora específica son extensiones propuestas; la evidencia local en JSON/SQLite no acredita Odoo desplegado. La especificación de datos y estados continúa con Gabriel y el recorrido funcional se presenta en el bloque de Benjamín.

## Material de apoyo

![Arquitectura del caso presencial](../../../arquitectura/diagramas/componentes-crm-erp-ep.svg)

La [especificación de arquitectura](../../../arquitectura/crm-erp-ep.md) contiene la matriz completa de componentes, sistemas de registro e interfaces. El [segundo gráfico](../../../arquitectura/diagramas/casos-arquitectura-ep.svg) relaciona los controles con las tres variantes del ejemplo.

La lectura del diagrama comienza en la tienda, continúa por identidad y oportunidad, identifica la cotización y llega a C04. Desde ese control se leen oferta, inventario y autorización; la respuesta se conserva junto a seguridad y persistencia. El trazo discontinuo hacia P2P marca evaluación de una necesidad, no una compra.

## Cómo explicar los eventos en la arquitectura

“Además de los módulos y las interfaces, identifico los hechos que activan su colaboración. La aceptación de la cotización permite que Ventas solicite la evaluación; la recepción activa el control de transición. Este conserva una decisión validada, condicionada por disponibilidad o rechazada por falta de aprobación. Cada decisión queda correlacionada en la bitácora. Si se identifican dos unidades faltantes, REP-EP-001 documenta una necesidad para evaluar abastecimiento y conecta O2C con P2P. Esa señal es conceptual y no crea una compra. Repetir la misma solicitud recupera la respuesta original.”

La [tabla y el flujo de eventos E01–E07](../../../arquitectura/crm-erp-ep.md#eventos-que-articulan-la-arquitectura) detallan origen, destinatario, acción y evidencia. Estos hechos pueden explicarse dentro de los bloques de controles y abastecimiento del guion, manteniendo los tres minutos. Los nombres de exposición no reemplazan los tipos técnicos `RECIBIDA`, `DECISION` y `REINTENTO` ni convierten `ACEPTADA` en un pedido confirmado.

![Eventos de la arquitectura integrada](../../../arquitectura/diagramas/eventos-crm-erp-ep.svg)

## Fila para integrantes y contribuciones

| Integrante | Contribución verificable | Decisión que defenderá |
| --- | --- | --- |
| Paucarcaja Ramos, Jharolym Friendly | Arquitectura C01–C08 e I01–I07 con iconos, sistemas de registro, continuidad de PC2, controles y correspondencia con las evidencias de Benjamín | Mantener Odoo integrado con responsabilidades explícitas antes de comprometer operación |

## Guion de tres minutos

**01:00–01:30 · Decisión y continuidad.** “Defiendo mantener Odoo como núcleo integrado. En PC1 se seleccionó el ERP y se dejó UBLHUB para emisión futura. PC2 delimitó un cliente nuevo del público general que llega a la tienda física. Conservo ese caso y explico cómo se distribuyen sus registros y controles.”

**01:30–02:15 · Lectura del diagrama.** “Contactos conserva la identidad; CRM, el lead y la oportunidad; Ventas, la cotización con sus condiciones. Inventario informa disponibilidad fechada. El control de transición reúne verificaciones y conserva una respuesta. El escudo identifica permisos y bitácora; el cilindro representa persistencia. Estas cajas son responsabilidades de una plataforma propuesta.”

**02:15–03:00 · Controles del caso normal.** “Usamos OPP-DEMO-001 y COT-DEMO-001 v1. Cinco autoradios a 400 soles suman 2,000; con el 5 % del ejemplo, el total es 1,900. La evaluación lee la versión aceptada, revisa vigencia y autorización y consulta stock. ACEPTADA con código VALIDADA conserva el pedido nulo: aún no lo confirma.”

**03:00–03:35 · Dependencia con abastecimiento.** “Con tres unidades disponibles para cinco solicitadas, aparece una brecha de dos. La respuesta parcial permite documentar REP-EP-001. El dueño y abastecimiento evalúan esa necesidad. La señal conecta O2C con P2P sin ejecutar compras ni prometer una fecha.”

**03:35–04:00 · Evidencia y transición.** “El diagrama y los casos se contrastan con evidencias locales; Odoo aún no está desplegado. Mi aporte identifica dónde vive cada dato y dónde actúa cada control. Benjamín mostrará ahora el recorrido del mismo cliente hasta la respuesta.”

El tiempo es una pauta de ensayo; debe comprobarse con la navegación real. Mi bloque prepara la arquitectura, Benjamín demuestra el recorrido y Gabriel detalla el contrato; se conservan los mismos módulos e identificadores entre intervenciones.

## Preguntas para la defensa

**¿CRM y ERP son aplicaciones distintas aquí?** Son responsabilidades gobernadas dentro del Odoo propuesto. La integración lógica entre módulos requiere definir datos, permisos, eventos y resultados aunque comparta plataforma.

**¿Quién conserva la cotización?** Ventas. CRM relaciona la oportunidad con esa oferta. La futura confirmación cambia el estado de su registro; no exige duplicarlo como otro pedido.

**¿Por qué una consulta de stock no permite confirmar la entrega?** Es una observación con producto, ubicación y hora. No reserva unidades; la disponibilidad debe revalidarse antes de una futura confirmación.

**¿REP-EP-001 forma parte del contrato?** No. El arnés de evidencia de Benjamín la documenta después de leer la respuesta parcial como enlace conceptual a P2P. El contrato 1.0 y la simulación no crean una compra.

**¿Qué demuestra realmente la prueba?** Comportamiento local de los controles y consistencia de los datos sintéticos. No demuestra permisos reales de Odoo, PostgreSQL, concurrencia ni una política empresarial aprobada.

**¿Qué sucede si el dueño no aprueba el 10 %?** El vendedor no se autoriza. La transición sin aprobación válida es rechazada y la oportunidad puede continuar en seguimiento comercial.

## Cobertura de la rúbrica individual

| Criterio | Evidencia que puedo mostrar | Límite que reconozco |
| --- | --- | --- |
| Dominio funcional y contexto | Cliente presencial, continuidad PC1/PC2 y dependencia O2C–P2P | Cantidades y uso familiar son académicos |
| Integración y arquitectura | Diagrama, sistemas de registro, interfaces y eventos E01–E07 con origen, destinatario y acción | Diseño por implementar; redacción literal de la rúbrica por contrastar |
| Datos y trazabilidad | Cliente, oportunidad, cotización/versión, aceptación, solicitud y COR | Identidad y permisos de la prueba son sintéticos |
| Reproducibilidad | Generador SVG y resultados compartidos | La verificación gráfica no reemplaza la prueba del contrato |
| Argumentación | Decisión, evidencia, límite y guion de tres minutos | Ensayo y revisión humana pendientes |
| Contribución y coordinación | Archivos propios y paso al recorrido de Benjamín | Panel único del grupo por consolidar |
| Ética y propiedad intelectual | [Fuentes, supuestos e IA](../../../fuentes/ep-jharolym.md) | Sin entrevistas nuevas ni datos personales reales |

Esta matriz organiza la preparación; no atribuye una nota ni una validación ya realizada. Los parámetros y diferencias entre documentos se conservan en el registro de fuentes para no mezclar stock 5/8/3 ni la vigencia histórica de PC2 con el reloj lógico EP.
