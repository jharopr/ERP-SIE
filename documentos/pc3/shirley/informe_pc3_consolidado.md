# Informe PC3 · Grupo 7 · Importaciones MYS Hermanos S.A.C.

> Fuente editable del informe PC3, ordenada según la plantilla oficial `GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx`. Yo, Shirley Carrión Oré, consolido el informe: escribí las secciones 1–4, 8 y 9 y el análisis 5B-II de inventarios y servicio, y comparto 5C, 6 y 7 con Benjamín y Adrián. Incorporo 5A y 5C desde los archivos de Adrián sin reescribirlos. Para generar el Word y el PDF sobre la plantilla: `python documentos/pc3/shirley/construir_informe.py --plantilla <ruta de la plantilla .docx>`.

## 1. Identificación del grupo y la empresa

| Campo | Registro |
| --- | --- |
| Evaluación: PC3 o PC4 | PC3 · Activos y mantenimiento; cadena de suministro parte I |
| Grupo | 7 |
| Empresa | Importaciones MYS Hermanos S.A.C. (RUC 20606915528) |
| Fecha | 13/11/2026 (entrega, 17:00) · exposición 14/11/2026 |
| Versión | 1.0-borrador, 12/11/2026 (consolidación de Shirley Carrión Oré) |
| Enlace al repositorio | `ERP-SIE`, rama `main` · URL pública: completar antes de exportar |
| Enlace al paquete o guía del Agente SIE | `GE703_PC3_Agente_G7_MYS_Hermanos.zip` · pendiente de entrega por Ballack Quintanilla |
| Expositor 1, si fue seleccionado | Por sorteo el 14/11/2026 |
| Expositor 2, si fue seleccionado | Por sorteo el 14/11/2026 |

## 2. Integrantes y contribuciones

| N° | Integrante | Contribución verificable |
| --- | --- | --- |
| 1 | Arancibia Ynga, Benjamín Francis | Cadena de suministro I: actores, proveedores, compras, demanda, capacidad y flujo de abastecimiento (5B-I); coautor de 4, 5C, 6 y 7; QA «5 solicitadas, 3 disponibles». **Estado al 12/11: pendiente de incorporar.** |
| 2 | Carrión Oré, Shirley | Consolidación del informe; secciones 1–4, 5B-II (inventarios, disponibilidad, servicio e indicadores), 8 y 9; coautora de 5C, 6 y 7; QA de instalación limpia, navegación, caso normal y stock/servicio con registro de defectos. Evidencia: `documentos/pc3/shirley/` y `pruebas/pc3-shirley/` |
| 3 | Chávez Mendoza, Gabriel Omar | Revisión y mejora de C01/C02; C04 transición y contrato I03; C06 autorizaciones y C07 bitácora; reglas R01–R12 y pruebas de integración. Evidencia: rama `pc3/agente-sie` / `sistema-agente` (no incluida en `main`) |
| 4 | Mansilla Soto, Adrián Antony | Activos y mantenimiento (5A); relación activos-cadena (5C); QA de descuento 10 % sin autorización, permisos y caída de Odoo (E02, A01, F01); hallazgo ADR-PC3-001. Evidencia: `documentos/pc3/adrian/` y `pruebas/pc3-adrian/` |
| 5 | Paucarcaja Ramos, Jharolym Friendly | Línea base C01/C02 (CRM y contactos); mejoras de C03 Ventas y C05 Inventario; adaptadores; guía de ejecución y ZIP con Ballack. Evidencia: ramas del agente/sistema (no incluidas en `main`) |
| 6 | Quintanilla Huamanraime, Ballack Zidane | Agente SIE: orquestador, herramientas, interfaz, explicación, escalamiento y paquete reproducible; demo en vivo. **Estado al 12/11: ZIP pendiente de entrega.** |

## 3. Resumen ejecutivo

**Problema.** MYS Hermanos importa y vende autoradios, pantallas Android, parlantes y accesorios, y los instala en dos tiendas de Naranjal «La 50» (Independencia), con almacén en Carabayllo. La promesa al cliente depende a la vez de activos disponibles (fuente de mostrador, herramientas, bahías), de componentes compatibles para cada vehículo, de información de stock confiable y de capacidad de instalación; hoy ninguno de estos datos se registra con hora y estado.

**Análisis.** Levantamos activos, criticidad, disponibilidad y políticas de mantenimiento (5A); el flujo de abastecimiento y los inventarios, con indicadores de nivel de servicio (5B); y el efecto de una falla sobre la capacidad y la promesa (5C). Reprodujimos desde cero los casos del prototipo (normal, stock parcial y 10 % sin autorización).

**Hallazgos.** (1) Cada tienda depende de su fuente de 120 A para demostrar; la tienda 1 sufrió una parada de dos días y una reincidencia sin registro de horas, por lo que la disponibilidad solo puede estimarse (66.67 % en el escenario condicionado de 5A). (2) El almacén tiene un responsable fijo, pero el stock vive en cuaderno y Excel; con más de mil variantes de marcos, arneses y cables, el riesgo de servicio está en la **información por referencia compatible y ubicación**. (3) En el prototipo el caso normal se valida, el parcial se responde sin fecha y con señal de reposición, y el 10 % se rechaza; el QA detectó una lectura de stock previa al rechazo (ADR-PC3-001, abierto).

**Decisión.** Proponemos la aprobación **condicionada** de un piloto de cuatro semanas: registro único de inventario empezando por arneses y Canbus, reposición con estado y hora, mantenimiento preventivo de fuentes y trimoto, y el Agente SIE como asistente que consulta, explica y escala, sin reservar, comprar ni aprobar.

**Límites.** Los datos operativos son testimonio del propietario; los porcentajes calculados son sintéticos o condicionados; no hay un Odoo productivo en la empresa.

## 4. Problema empresarial y alcance

*Coautoría: Shirley Carrión y Benjamín Arancibia (Benjamín valida la parte de flujo y abastecimiento).*

### 4.1. Situación de la empresa

| Elemento | Situación declarada | Fuente |
| --- | --- | --- |
| Puntos de venta | Tienda 1 (propia, 3 espacios) y tienda 2 (alquilada S/ 1,800/mes, 1 espacio) en La 50; 09:00–19:00, sábado cerrado | EMP-03 |
| Atención | Aprox. 5 y 3 vehículos por día entre semana; domingos hasta 12 y 5 | EMP-03, EMP-04 |
| Almacén | Casa de dos pisos en Carabayllo: audio en el nivel 1; marcos, arneses y cables en el nivel 2; más de mil variantes | EMP-05 |
| Personal y reposición | Un hijo por tienda y un almacenero fijo (hijo de la dueña); coordinación por cuaderno; traslado mayoritariamente por inDrive | EMP-06, EMP-07 |
| Compras | Pedidos a China por experiencia y revisión de cuaderno y Excel, sin umbral ni frecuencia fija | EMP-07 |
| Activos críticos | Una fuente 7POWER de 120 A por tienda, herramientas de diagnóstico, trimoto, PC y conectividad | EMP-01, EMP-04 |
| Mantenimiento | Práctica 100 % correctiva | EMP-01 |

### 4.2. Problema e impacto

La promesa al cliente depende de cuatro condiciones simultáneas: **activo disponible**, **componente compatible**, **información confiable** (qué hay, dónde y desde cuándo) y **capacidad de instalación**. Cuando una falla, el vendedor se entera tarde y la promesa se rompe frente al cliente: se pierde la demostración, se espera una pieza sin fecha o se descarta la venta.

| Riesgo de continuidad | Qué se interrumpe | Severidad preliminar | Dónde se analiza |
| --- | --- | --- | --- |
| Falla de la fuente de mostrador | Demostración y decisión de compra en esa tienda | Alta | 5A |
| Falta de arnés, marco o Canbus compatible | Instalación del vehículo aunque haya pantalla | Alta | 5B-II, 5C |
| Registro de stock desactualizado | Respuesta confiable en mostrador; reposición oportuna | Alta | 5B-II |
| Falla de herramienta de diagnóstico o manómetro | Trabajo seguro sobre el vehículo | Alta por función | 5A |
| Falla de la trimoto | Reparto y gestiones locales de La 50 | Alta para esas tareas | 5A, 5C |
| Caída de Odoo / servidor del prototipo | Validación de solicitudes (quedan `PENDIENTE`) | Alta | 5A, 5C |
| Compra a China sin criterio documentado | Reabastecimiento a tiempo del almacén | Media, sin datos | 5B |

### 4.3. Objetivo

1. Mostrar cómo una falla de activo o un faltante cambia primero el dato de capacidad o stock, y solo después la promesa.
2. Definir dónde está el stock, qué cantidad es utilizable y cómo se mide el nivel de servicio.
3. Proponer políticas de mantenimiento para los activos críticos con indicadores calculables.
4. Demostrar un Agente SIE que consulta, explica y escala, sin autoaprobar, reservar ni confirmar.

### 4.4. Continuidad con entregas previas

| Entrega | Qué se decidió o construyó | Qué hereda PC3 |
| --- | --- | --- |
| PC1 (24–25/09) | Diagnóstico de dos canales; Odoo como ERP central y UBLHUB para comprobantes; meta de exactitud de stock ≥ 98 % | Odoo como sistema de registro; indicador de exactitud (IND-04) |
| PC2 (15/10) | Escenario CRM en tienda física; componentes C01–C08, interfaces I01–I07, contrato 1.0 | Componentes e interfaces que usa el agente |
| Parcial (24/10) | Compuerta con reglas R01–R12; casos normal, stock parcial y 10 % sin autorización; 112 comprobaciones | Mismos casos como base de la demo y de los indicadores de 5B |

### 4.5. Límites del análisis

| Incluido en PC3 | Fuera de alcance |
| --- | --- |
| Activos de tiendas, almacén y transporte local; inventario por referencia y ubicación; indicadores de servicio y mantenimiento; agente que consulta y recomienda; casos normal, parcial, 10 % y reintento | Finanzas operativas y logística integrada (PC4); compras automáticas, MRP o pronóstico implementado; reserva automática de stock; emisión de comprobantes; integración real con WhatsApp; Odoo productivo en la empresa |

## 5. Procesos y análisis de la empresa

Organizamos la sección en 5A (activos y mantenimiento), 5B (cadena de suministro I: flujo de abastecimiento e inventarios/servicio) y 5C (efecto del mantenimiento sobre la continuidad de la cadena).

<!-- INCLUIR: ../adrian/seccion_5a_activos_mantenimiento.md -->
*5A. Activos y mantenimiento, de Adrián Mansilla:* [ver archivo](../adrian/seccion_5a_activos_mantenimiento.md).

<!-- INCLUIR: PENDIENTE_5B_BENJAMIN -->
*5B-I. Flujo de abastecimiento, de Benjamín Arancibia:* **pendiente de incorporar.**

<!-- INCLUIR: seccion_5b_inventarios_servicio.md -->
*5B-II. Inventarios y servicio, de Shirley Carrión:* [ver archivo](seccion_5b_inventarios_servicio.md).

<!-- INCLUIR: ../adrian/seccion_5c_relacion_activos_cadena.md -->
*5C. Relación activos-cadena, de Adrián Mansilla con Benjamín y Shirley:* [ver archivo](../adrian/seccion_5c_relacion_activos_cadena.md).

### 5C.S. Información de inventario y atención al cliente (aporte de Shirley Carrión)

5C muestra qué capacidad se pierde. Con mi aporte defino **qué debe saber el vendedor y qué debe decirle al cliente** en cada escenario, para que la promesa cambie de forma honesta y trazable.

| Escenario | Dato que cambia primero | Información de inventario necesaria | Qué se le dice al cliente | Qué no se hace |
| --- | --- | --- | --- | --- |
| Falla de la fuente de la tienda 1 | Capacidad de demostración en tienda 1 | Si el equipo está en tienda 2 o en Carabayllo, y si la fuente de tienda 2 tiene horario libre | Que hoy no se puede demostrar en esa tienda; alternativa validada (tienda 2 o nueva cita) | Prometer demostración en tienda 2 sin confirmar su agenda |
| Falta de Canbus compatible | Stock utilizable para ese vehículo = 0 | Referencia exacta, existencia en `NIVEL-02`, estado de reposición y hora | Que el equipo existe pero falta la pieza; fecha **solo** con recepción confirmada | Dar fecha por «llega mañana» sin solicitud con estado |
| Stock parcial (5 pedidos, 3 disponibles) | Disponible < solicitado | Cuánto hay, dónde, desde qué hora; señal de reposición | 3 ahora y 2 sin fecha, o esperar; requiere nueva versión aceptada | Reservar o comprar automáticamente |
| Odoo no responde | Solicitud = `PENDIENTE` | Ninguno confiable hasta recuperar | Que la consulta está pendiente y se confirmará; no es «sin stock» | Responder de memoria o con el cuaderno como si fuera el sistema |
| Trimoto fuera de servicio | Capacidad de reparto local | Pedidos con entrega local comprometida | Nuevo horario con transporte alternativo confirmado | Mantener la hora original sin transporte asegurado |

Regla común: **sin dato confiable con hora, no hay fecha**. El agente aplica la misma regla: explica el estado y escala; la decisión la toma una persona autorizada.

## 6. Datos, fuentes y supuestos

*Coautoría: Benjamín, Shirley y Adrián. El registro con la localización exacta de cada fuente (EMP-01 a EMP-07, S9, S10, VEN-01, COD-01) está en 5A, «Registro de fuentes y calidad».*

| Dato y fuente | Tipo y supuestos | Unidad, rango o fecha |
| --- | --- | --- |
| Espacios, horario y atención por tienda (EMP-03, EMP-04) | Declarado por el propietario; sin agenda ni partes diarios; los máximos dominicales no son promedio | 4 espacios; 60 h/semana por sede; 5 y 3 vehículos/día; domingos hasta 12 y 5 · recibido 12/11/2026 |
| Almacén, variantes y personal (EMP-05, EMP-07) | Declarado; «más de mil» es variedad de catálogo, no unidades; falta conteo | Dos niveles; > 1,000 variantes · 12/11/2026 |
| Reposición y transporte (EMP-06, EMP-07) | Declarado; el viaje no es el tiempo total de reposición | ~40 min de viaje, sentido por confirmar · 12/11/2026 |
| Antecedente de urgencias (EMP-06) | Declarado e histórico, sin muestra ni periodo; no se usa como tasa vigente | Búsquedas de 1–2 h; pérdida estimada 20–30 % de casos afectados |
| Fuente 7POWER y su historial (EMP-03, EMP-04) | Declarado; placa, serial y fechas por cotejar | 120 A; 12.6–14.4 V; parada de 2 días en tienda 1 |
| Disponibilidad de la fuente (5A) | Calculado bajo supuesto: una semana de 60 h y dos jornadas completas perdidas | 40 ÷ 60 h = 66.67 % (escenario, no medición) |
| Capacidad espacial (5C) | Calculado: espacios × horas de apertura; no considera técnicos ni duración de trabajos | 40 horas-bahía/día; 240/semana |
| Exportación de productos vendidos (VEN-01) | Empresarial, verificado como archivo; sin fecha transaccional | 93 filas, 92 códigos, PEN · 11/11/2026 |
| Precios, descuentos y stock de demo | **Sintético**: valores fijados para probar reglas | S/ 400 por unidad; 5 unidades; 5 % y 10 %; stock 8 y 3 unidades |
| Indicadores de servicio del prototipo (`pruebas/pc3-shirley`) | **Sintético**: corridas independientes del arnés EP | 80 % unidades; 50 % solicitudes completas · 12/11/2026 |
| Resultados E02, A01, F01 (`pruebas/pc3-adrian`) | Ejecución local sintética con Odoo simulado; sin Odoo real ni LLM | Estados, conteos y HTTP · 12/11/2026 |
| Material docente S9 y S10 (S9-T, S9-M, S10-C, S10-I, S10-G) | Fuente académica; se usan conceptos, no los datos de Andina | Sesiones 9 y 10, 2026-2 |

**Uso autorizado y privacidad.** Los datos de la empresa se usan con autorización del propietario (Adrián Mansilla) con fines académicos. No se publican datos de clientes, DNI, teléfonos, direcciones completas ni credenciales. Antes de publicar el repositorio fuera del curso, Adrián valida qué información operativa se comparte.

## 7. Evidencias y decisión sustentada

*Coautoría: Benjamín, Shirley y Adrián.*

| Hallazgo y decisión | Evidencia o enlace | Responsable |
| --- | --- | --- |
| Las fuentes de mostrador son activos de criticidad alta sin historial registrado → inspección de ambas unidades, plan preventivo y OT con prueba de retorno | 5A.2–5A.5; matriz de criticidad y escenario de disponibilidad | Adrián |
| El stock vive en cuaderno y Excel; riesgo de servicio por referencia compatible → registro único por referencia y ubicación, empezando por arneses y Canbus (D-5B-01) | 5B-II.1–5B-II.3; IND-01 a IND-09 | Shirley; almacenero y gestión familiar |
| Reposición sin estado ni hora → solicitud de reposición con estado (D-5B-02) | 5B-II.2; 5C.2 | Benjamín y Shirley; tiendas y almacenero |
| El prototipo responde el parcial sin fecha, sin reserva y con señal de reposición; 80 % de unidades vs. 50 % de solicitudes completas → medir siempre ambos indicadores | `pruebas/pc3-shirley/evidencias/indicadores_servicio.json` | Shirley |
| Instalación limpia del prototipo de contrato conforme; agente y Odoo no incluidos en `main` (SHI-PC3-001) → entregar el agente ejecutable desde el ZIP | `pruebas/pc3-shirley/ficha_qa_usabilidad_shirley.md` | Ballack, Jharolym, Gabriel |
| R08 rechaza el 10 %, pero lee stock antes (ADR-PC3-001) → diferir la lectura de disponibilidad hasta superar la autorización | `pruebas/pc3-adrian/ficha_qa_descuento_adrian.md` | Gabriel y Jharolym; revalida Adrián |
| Decir «el dueño ya aprobó por WhatsApp» no otorga permisos (A01 backend: HTTP 403) → la aprobación solo la registra el dueño en su flujo | `pruebas/pc3-adrian/evidencias/PC3-A01-local.json` | Adrián, Ballack |
| Flujo y mapa de abastecimiento; prueba de stock parcial en agente y sistema | 5B-I y ficha QA de Benjamín (pendientes) | Benjamín |

**Proponemos una aprobación condicionada** de un piloto de cuatro semanas.

| Componente del piloto | Acción | Cómo se verifica |
| --- | --- | --- |
| Inventario | Registro único por referencia y ubicación, empezando por arneses y Canbus | Conteo inicial con fecha; IND-04 en la semana 1 |
| Reposición | Solicitud con estado y hora en lugar del cuaderno | IND-05 e IND-06 calculables en la semana 2 |
| Mantenimiento | Inspección de ambas fuentes y de la trimoto; plan preventivo y OT de 5A | OT cerradas con prueba de retorno |
| Promesa | Sin kit completo y capacidad validada, no hay fecha | IND-08 = 0 |
| Agente SIE | Asistente que consulta, explica y escala | Demo reproducible desde el ZIP |

**Efecto sobre el problema.** Con esta decisión atacamos la causa común de las promesas rotas: la falta de un dato confiable, con hora, sobre el activo, el componente y la capacidad. **Condiciones para pasar a la implantación:** ADR-PC3-001 corregido y revalidado; SHI-PC3-001 cerrado; cuatro semanas de datos para fijar metas de IND-01 a IND-07; decisiones de descuento registradas por una persona autorizada. **Alternativa que descartamos:** contratar otro almacenero, porque la función ya está cubierta (EMP-07); el problema es de información y control.

## 8. Resultados, conclusiones y límites

| Resultado | ¿Observado o estimado? | Base |
| --- | --- | --- |
| El prototipo valida el caso normal, responde el parcial sin fecha y rechaza el 10 % sin autorización | **Observado** en ejecución local sintética | `pruebas/pc3-shirley`, `pruebas/ep-benjamin` |
| El agente no puede autoaprobar el descuento por permisos | **Observado** en backend; chat con LLM no ejecutado | Ficha de Adrián, A01 |
| El rechazo por descuento ocurre antes de leer stock | **No se cumple**: lectura anticipada | ADR-PC3-001 |
| Disponibilidad de la fuente 66.67 % | **Estimado** bajo supuesto de dos jornadas perdidas | 5A.3 |
| El riesgo de servicio está en la información por referencia compatible | **Inferencia** de la operación declarada | 5B-II.2 |
| Indicadores de servicio de MYS | **No medidos**; solo fórmulas y valores sintéticos | 5B-II.3 |

| Limitación o pendiente | Impacto | Responsable y siguiente acción |
| --- | --- | --- |
| Agente y sistema Odoo no incluidos en `main` (SHI-PC3-001) | No se puede certificar la demo ni la instalación limpia del agente | Ballack entrega el ZIP; Shirley, Adrián y Benjamín ejecutan sus pruebas |
| Lectura de stock antes del rechazo por descuento (ADR-PC3-001) | Incumple el control «rechazo previo a stock» | Gabriel y Jharolym corrigen; Adrián revalida en agente y sistema |
| 5B-I y ficha QA de stock parcial sin incorporar | Falta el mapa de abastecimiento y la prueba de Benjamín | Benjamín incorpora con las unidades de 5B.0 |
| Datos operativos solo declarados; sin conteos ni registros diarios | Ningún indicador tiene valor medido en la empresa | Gestión familiar: conteo de la familia piloto y cuatro semanas de registro |
| Fechas de falla, placas y seriales de las fuentes sin cotejar | La disponibilidad es un escenario, no una medición | Adrián coteja y registra fechas e intervalos |
| Frecuencias de mantenimiento no provienen del fabricante | Pueden no ser adecuadas | Adrián y técnico ajustan con manual |

**Conclusiones.** (1) Concluimos que en MYS la continuidad de la cadena depende tanto de los activos como de la información: una fuente caída detiene la demostración y un componente sin registro detiene la instalación, aunque haya mercadería. (2) El mantenimiento correctivo y el cuaderno producen el mismo efecto: el problema se descubre cuando el cliente ya está en mostrador. (3) El prototipo muestra que se puede responder con honestidad (sin fecha cuando no hay validación y con escalamiento cuando hace falta autorización), pero queda un defecto abierto y la demo del agente debe certificarse desde el ZIP. (4) La decisión recomendada es un piloto acotado y medible, no una implantación completa.

## 9. Fuentes y uso de IA

| Elemento | Registro |
| --- | --- |
| Fuentes y fecha de acceso | Información del propietario EMP-01 a EMP-07 (recibida el 12/11/2026); reparto PC3 del grupo (10–12/11/2026); material docente S9 y S10 de GE703 (2026-2); VEN-01 (exportación del 11/11/2026); repositorio `ERP-SIE` rama `main` y evidencias de PC1 (25/09), PC2 (15/10), parcial (24/10) y PC3 (12/11/2026). Localización detallada en 5A, «Registro de fuentes y calidad» |
| Herramientas de IA usadas y propósito | Adrián declara el uso de Codex (OpenAI) en sus aportes y pruebas. Yo (Shirley) usé Claude (Anthropic) el 12/11/2026 para la consolidación, 5B-II y mi QA: contraste de documentos, borradores de redacción, verificación de indicadores, script de QA y detección de incoherencias |
| Validación humana realizada | Revisé la consolidación, 5B-II y mi QA; cada integrante valida lo que se le atribuye y Adrián valida los datos de la empresa. La IA no entrevistó a la empresa ni aprobó decisiones comerciales |
| Datos sensibles excluidos o anonimizados | Sin datos de clientes, DNI, teléfonos, correos, direcciones completas ni credenciales; clientes, cotizaciones y SKU de demo son sintéticos (`CLI-DEMO-001`, `RAD-7BT`) |
| Límites, supuestos y pendientes | Datos operativos declarados sin conteos; indicadores sintéticos o condicionados; sin Odoo productivo en la empresa; demo del agente pendiente de certificar; ADR-PC3-001 y SHI-PC3-001 abiertos |

## 10. Anexos

| Anexo | Contenido | Archivo en el repositorio |
| --- | --- | --- |
| A | Matriz de activos, criticidad, indicadores de mantenimiento y flujo de OT | `documentos/pc3/adrian/seccion_5a_activos_mantenimiento.md` |
| B | Cadena de suministro: flujo y mapa de abastecimiento | 5B-I de Benjamín (pendiente) |
| C | Indicadores de inventario y servicio | `documentos/pc3/shirley/seccion_5b_inventarios_servicio.md` y `pruebas/pc3-shirley/evidencias/indicadores_servicio.json` |
| D | Ficha QA de Shirley Carrión, lista de usabilidad y registro de defectos | `pruebas/pc3-shirley/ficha_qa_usabilidad_shirley.md` |
| E | Ficha QA de Adrián (E02, A01, F01) | `pruebas/pc3-adrian/ficha_qa_descuento_adrian.md` |
| F | Ficha QA de Benjamín (stock parcial) | Pendiente |
| G | Capturas de la demo del agente | Pendiente de la ejecución en vivo |
