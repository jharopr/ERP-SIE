# 5C. Relación entre activos y cadena de suministro

**Empresa:** Importaciones MYS Hermanos S.A.C. **Curso:** GE703, Grupo 7, 2026-2. **Insumo de:** Adrián Mansilla. **Coautoría prevista:** Benjamín Arancibia y Shirley Carrión, pendiente de su revisión. **Corte:** 12/11/2026, Lima. **Versión:** 1.4, actualiza almacenero fijo, coordinación por cuaderno y compras a China basadas en experiencia y registros.

Esta sección aplica la integración de operaciones y mantenimiento de S10 a una comercializadora que instala equipos. La fuente de demostración, herramientas, bahías y transporte condicionan el servicio; el inventario por sí solo no determina una fecha viable. Las fuentes abreviadas remiten al registro de [5A](seccion_5a_activos_mantenimiento.md).

## 5C.1. Falla y reducción de capacidad operativa

### Atención por tienda y calendario confirmado

El propietario confirma **tres espacios utilizables en tienda 1 y uno en tienda 2**. Ambas atienden de **09:00 a 19:00**, de lunes a viernes y domingo, con cierre sabatino por motivos religiosos. La primera tienda es propia; la segunda tiene alquiler de **S/ 1,800 mensuales** [EMP-03; EMP-04].

| Sede | Espacios utilizables | Promedio aproximado de lunes a viernes | Atención dominical declarada | Alimentación de mostrador |
| --- | --- | --- | --- | --- |
| Tienda 1 | 3 | 5 vehículos por día | Hasta 12 vehículos | Fuente propia de 120 A de referencia |
| Tienda 2 | 1 | 3 vehículos por día | Hasta 5 vehículos | Fuente propia de las mismas características |

Las cifras entre semana son promedios declarados y suman **aproximadamente ocho vehículos por día**. Las dominicales conservan el alcance de «hasta» del relato; no se certifica promedio ni coincidencia de máximos en una misma fecha. Debe distinguirse la mezcla de trabajos rápidos y completos al contrastar estos datos con registros. Los **cuatro espacios simultáneos** no limitan el día a cuatro vehículos: cada espacio puede recibir varios sucesivamente.

### Modelo legible de capacidad, separado por sede

**Horas-bahía nominales = Número de espacios utilizables × Horas de atención del periodo.** Una hora-bahía representa un espacio disponible durante una hora.

El calendario tiene **10 horas de apertura por día y 60 horas semanales por sede**. El potencial espacial se calcula así:

| Recurso espacial | Cálculo diario | Horas-bahía por día de apertura | Horas-bahía por semana de seis días |
| --- | --- | --- | --- |
| Tienda 1 | 3 espacios × 10 h | **30** | 30 × 6 = **180** |
| Tienda 2 | 1 espacio × 10 h | **10** | 10 × 6 = **60** |
| Conjunto de tiendas | 4 espacios × 10 h | **40** | 40 × 6 = **240** |

Es potencial del espacio durante el horario de apertura, no horas netas de técnicos ni instalaciones garantizadas. Para disponibilidad de una fuente se usa el calendario de su propia sede —60 horas semanales— y no las 240 horas-bahía, que tienen otra unidad.

**Horas-bahía perdidas = Número de espacios afectados × Duración de la interrupción.** Esta operación supone el mismo intervalo para esos espacios y no debe duplicar pérdidas que se superponen.

**Horas-bahía efectivas = Horas-bahía nominales − Horas-bahía perdidas.**

Para convertir estas horas en trabajos terminados se necesitan duración por tipo de servicio, técnicos disponibles, pausas, materiales y secuencia. No se impone una duración uniforme de ocho horas-bahía por instalación. El mayor flujo dominical debe evaluarse con esa mezcla de trabajos y dotación; no demuestra un turno más largo. Los máximos históricos no equivalen a una promesa automática para el siguiente domingo.

| Escenario numérico de espacio | Pérdida calculada | Potencial restante del conjunto |
| --- | --- | --- |
| Sin parada espacial | 0 | **40 horas-bahía** |
| Un espacio inutilizable durante 2 h | 1 × 2 = 2 horas-bahía | 40 − 2 = **38 horas-bahía** |
| Los tres espacios de tienda 1 inutilizables durante 2 h | 3 × 2 = 6 horas-bahía | 40 − 6 = **34 horas-bahía** |
| El único espacio de tienda 2 inutilizable durante 2 h | 1 × 2 = 2 horas-bahía | 40 − 2 = **38 horas-bahía** |

Las dos horas son un escenario didáctico, no la duración de la falla histórica de fuente. Aunque la pérdida conjunta sea igual para un espacio de cualquiera de las tiendas, la última situación elimina durante ese intervalo toda la capacidad espacial de tienda 2. No se compensan vehículos entre sedes sin validar traslado, técnico, material y aceptación.

| Escenario | Qué cambia primero | Qué falta para cuantificar los vehículos afectados |
| --- | --- | --- |
| Falla de una herramienta indispensable en tienda 1 | Disponibilidad del trabajo o de los espacios que realmente dependen de ella | Duración de la falla, sustituto, técnicos y agenda de la tienda |
| Interrupción en el único espacio de tienda 2 | Posibilidad de continuar o reasignar la atención en ese punto | Duración, trabajos en curso y alternativa realmente disponible |
| Falta de Canbus compatible | Factibilidad del trabajo del vehículo correspondiente | Modelo del vehículo, recepción confirmada del componente y trabajo alternativo |
| Falla de fuente de mostrador | Capacidad de demostración y decisión de compra en su sede | Duración, alcance y ventas/instalaciones dependientes; cada tienda tiene una fuente independiente |

La fuente alimenta el **mostrador**. La falla relatada ocurrió en la **tienda 1**; no se asigna la misma indisponibilidad a tienda 2, que tiene su propia fuente. Tampoco equivale automáticamente a detener los tres estacionamientos de tienda 1: pueden continuar trabajos previamente aceptados. El relato incluye dos días de interrupción, repuesto no oficial difícil de obtener, reincidencia al mes y otra demora de dos días; las fechas y horas faltan para cuantificar el efecto observado. Véase el cálculo condicionado de disponibilidad en 5A [EMP-03; EMP-04; S9-T, pp. 10–13; S10-G].

**Brecha de servicio = Trabajos comprometidos para el periodo − Trabajos que pueden completarse con los recursos confirmados.** Si el resultado es negativo, no hay faltante de capacidad por ese cálculo. Se compara compromiso con capacidad validada, sin usar la frecuencia aproximada como si fuera un compromiso o un máximo físico.

La falta de Canbus o arnés compatible se trata como restricción de materiales, no como avería de la bahía. Si afecta a un vehículo, debe evaluarse mover ese trabajo a espera y reasignar el espacio a otro trabajo compatible. Se confirma la capacidad efectiva considerando conjuntamente espacio, técnicos, herramientas, componentes y secuencia.

## 5C.2. Efecto en la cadena y la promesa comercial

La regla rectora es: **«El dato de capacidad cambia primero; la nueva promesa requiere validación»** [S9-T, p. 12]. La lectura de integración S10 desarrolla esta secuencia: OT → calendario del recurso → plan revisado → decisión autorizada → actualización del pedido y comunicación [S10-I, «Cadena de decisión»].

### Red operativa y tres flujos

| Enlace / nodo | Flujo de producto o servicio | Información requerida | Costo o decisión |
| --- | --- | --- | --- |
| Proveedores de China → abastecimiento internacional | Compra de mercadería para reabastecer el almacén | Experiencia de la gestión familiar, cuaderno y Excel como apoyo; detalle del pedido y condiciones por documentar | Se compra cuando se considera necesario; sin calendario fijo ni umbral calculado informado |
| Aduanas → Carabayllo | Importación trasladada por transporte pesado contratado | Recepción, cantidades, inspección y disponibilidad | Coordinar transporte y recepción; una llegada prevista no es stock utilizable |
| Carabayllo → tiendas La 50 | Reposición con transporte mayoritariamente contratado por inDrive | Necesidad registrada y coordinada mediante cuaderno; preparación por el hijo que es almacenero fijo, compatibilidad, cantidad y traslado | Confirmar preparación, salida y recepción; el transporte no sustituye el control de existencia y compatibilidad |
| Tiendas La 50 → reparto o compra local | Trimoto propia para entregas y gestiones diarias, incluida obtención de herramientas para instalaciones | Necesidad, destino, responsable, salida y retorno | Su falla afecta tareas locales; no se da por detenido automáticamente el traslado habitual por inDrive |
| Mostrador → bahías | Demostración, aceptación y servicio de instalación | Cotización/versionado, componentes compatibles, técnico y capacidad | No prometer instalación solo por existencia de pantalla |
| Carabayllo → agencias del Centro de Lima | Minivan fija de confianza subcontratada | Recojo, entrega a agencia y constancia | Capacidad/horario por confirmar antes del envío |
| Agencias → provincia | Shalom u otra agencia | Guía, recepción y seguimiento | No equiparar entrega a agencia con entrega final al cliente |
| Bahía → cliente | Instalación y prueba de funcionamiento | Conformidad técnica y comercial, trabajos pendientes | Comunicar condiciones aceptadas y registrar cierre |

Esta red relaciona producto, información y dinero, conforme a S10-C, pp. 5–7. No se atribuye a MYS producción industrial de COMP-A ni los valores sintéticos de Andina.

La disponibilidad de materiales debe evaluarse por SKU, modelo del vehículo, ubicación y fecha. Adaptando el MRP de S9-M, pp. 6–9, a kits de instalación:

**Necesidad neta de un componente = Demanda bruta − Stock utilizable − Recepciones firmes que llegan a tiempo.**

Si la resta da un número negativo, se registra **cero** como necesidad neta; ese componente ya tiene cobertura suficiente. Todas las cantidades deben estar expresadas en la misma unidad y corresponder al mismo componente compatible.

El cálculo requiere una lista de componentes/compatibilidades validada para cada trabajo. Un Canbus incompatible no es stock utilizable para ese vehículo. Las ventas históricas de VEN-01 son señales comerciales; no se suman como si fueran stock ni prueban la existencia actual de kits completos [S10-C, pp. 8–10].

### Almacén de dos niveles y variedad de componentes

Carabayllo es una casa de **dos pisos destinada a almacenar mercadería**. El primer piso concentra radios y parlantes de distintas marcas, incluidos parlantes y pantallas Android de marca propia; el segundo, consolas plásticas, arneses y cables. Se declaran **más de mil modelos o variantes** de estos componentes por la diversidad de vehículos [EMP-05].

Esta variedad hace necesario verificar referencia y compatibilidad antes de preparar el traslado. Tener una pantalla en el primer nivel no prueba que se tenga el marco y arnés correctos del segundo nivel. Como propuesta, la preparación debe vincular modelo/año del vehículo, referencias del equipo y adaptadores requeridos, ubicación y cantidad; no se afirma que esa lista de compatibilidad esté digitalizada actualmente. Las más de mil variantes no equivalen a mil unidades disponibles ni se dan por incorporadas al catálogo reducido del prototipo.

### Reposición actual: cuaderno y almacenero fijo

La organización vigente comprende **un hijo en tienda 1, un hijo en tienda 2 y un tercer hijo de la dueña como almacenero fijo en Carabayllo**. La responsabilidad de reposición permanece en la familia por confianza. La coordinación diaria entre tienda y almacén se realiza **mediante cuaderno**, conforme a la última aclaración del propietario; el transporte se contrata mayoritariamente por **inDrive**. Se declaran además un vendedor, un jalador y un instalador por tienda y participación de los propietarios, sin detallar una plantilla nominal completa [EMP-06; EMP-07].

| Etapa | Práctica actual declarada | Punto que debe verificarse o registrarse |
| --- | --- | --- |
| Detectar necesidad | El encargado de tienda anota faltantes en un cuaderno | Identificar producto exacto y compatibilidad; «similar» no acredita que un componente sirva para el vehículo |
| Coordinar | La comunicación operativa con almacén se maneja mediante cuaderno | Como mejora, registrar cantidad, sede, fecha y responsable; verificar que la necesidad y su estado queden identificados |
| Organizar reposición | La gestión es familiar; el relato previo situaba la reposición al día siguiente | Documentar horario de corte y fecha acordada; no se interpreta como plazo fijo garantizado |
| Preparar | Un hijo de la dueña cumple la función de almacenero fijo | Cotejar referencia, compatibilidad, cantidad y ubicación antes de dar salida; registrar horario y relevo para contingencias |
| Trasladar | Se usa mayoritariamente inDrive; la trimoto se concentra en reparto y gestiones de La 50 | Registrar salida y recepción; precisar recorrido/sentido de los aproximadamente 40 minutos mencionados y separar espera de viaje |
| Recibir en tienda | La reposición abastece el punto de venta | Se propone cotejar referencias/cantidades y registrar recepción; el mecanismo actual de conformidad no fue descrito |

**Diagnóstico actual:** la función de almacén cuenta con un responsable fijo, mientras la información de reposición se gestiona manualmente. El control debe permitir relacionar la necesidad anotada con el componente existente, su preparación y la recepción en tienda. No se ha aportado evidencia de actualización simultánea de registros ni de una integración digital entre almacén y puntos de venta [EMP-07].

**Tiempo total hasta reposición = Tiempo desde la anotación hasta su atención + Búsqueda y preparación + Traslado + Verificación de recepción.**

Los aproximadamente cuarenta minutos informados no cubren por sí solos toda esa secuencia. Falta confirmar el trayecto y si es de ida; no se duplican para afirmar ochenta minutos ni se usan como promesa automática. El horario específico de almacén debe documentarse antes de igualarlo al de las tiendas; disponer de almacenero fijo no acredita por sí solo una cobertura horaria determinada.

La disponibilidad para una atención requiere verificar **producto existente, componente compatible, acceso a despacho, traslado y capacidad de instalación**. El primer dato no sustituye los demás [S10-C, pp. 7, 9–10 y 13; S10-I].

### Abastecimiento desde China: criterio empírico apoyado en registros

La compra internacional se decide mediante **experiencia de la gestión familiar, revisión del cuaderno y consulta del Excel que utiliza el negocio**, cuando se considera que es momento de realizar un pedido. No se ha informado una revisión con frecuencia fija, un umbral de inventario formal ni un cálculo automático de compra. La práctica combina conocimiento comercial y registros manuales/digitales, sin constituir por ello un pronóstico cuantitativo o MRP implementado [EMP-07; S10-C, pp. 8–12].

| Decisión | Base actual declarada | Registro necesario para sustentarla |
| --- | --- | --- |
| Qué referencias pedir | Experiencia y revisión del cuaderno y Excel | Identificar referencias y compatibilidad, y vincular la necesidad con ventas, solicitudes o faltantes registrados |
| Cuándo pedir | Juicio de la gestión familiar sobre el momento de reabastecer | Fecha de revisión y motivo de la decisión; documentar plazos del proveedor y de llegada antes de fijar un criterio |
| Cuánto pedir | No se ha detallado un método de cálculo | Cantidad por referencia, existencia contada, pedidos firmes pendientes de recepción y restricciones del proveedor |
| Desde dónde atender al cliente | Mercadería en Carabayllo y reposición hacia las tiendas | Disponibilidad por ubicación, despacho y recepción confirmados; un pedido a China aún no recibido no es stock utilizable |

**Reposición interna y compra internacional tienen alcances distintos.** La primera mueve mercadería ya disponible en Carabayllo hacia La 50; la segunda busca reabastecer ese almacén y requiere validar condiciones y fechas de suministro. Los plazos, lotes mínimos, costos y periodicidad de compra a China no fueron aportados, por lo que se dejan como datos por levantar.

La mejora propuesta es **hacer explícito y trazable el criterio de compra que hoy se aplica por experiencia**: registrar qué se revisó en cuaderno y Excel, contrastarlo con el conteo por referencia, identificar pedidos aún no recibidos y dejar cantidad, fecha, motivo y responsable de cada decisión. Con una base consistente se podrán evaluar criterios de reposición por familia. No se inventa un umbral, una demanda promedio por SKU ni una cantidad de seguridad.

### Antecedente de urgencias: búsqueda local de arnés o Canbus

En la descripción previa se relataban dificultades de contacto con almacén, búsqueda telefónica en proveedores locales durante **una a dos horas** y descarte de la venta si no se obtenía el componente. La pérdida estimada de **20–30 %** correspondía a esos casos afectados, sin muestra ni periodo registrado [EMP-06]. Se conserva como antecedente de servicio; **no se atribuye a una ausencia actual del almacenero ni se presenta como tasa vigente con el puesto fijo** [EMP-07]. Para el funcionamiento actual, la excepción relevante es no contar con suministro compatible confirmado.

| Paso | Situación y control aplicable | Decisión y dato por conservar |
| --- | --- | --- |
| 1. Necesidad específica | El vehículo requiere un arnés o Canbus compatible | Modelo/año y referencia exacta; no sustituir por una pieza solo parecida |
| 2. Verificación en Carabayllo | El almacenero fijo debe comprobar la existencia y preparación de la referencia solicitada | Necesidad anotada, existencia comprobada y estado del despacho; distinguir falta de información, falta de stock y demora de preparación |
| 3. Búsqueda alternativa | Se llama a proveedores locales; se han presentado esperas de una a dos horas | Proveedor, disponibilidad compatible, costo y tiempo confirmado; no asumir que la consulta garantiza suministro |
| 4. Resolución | Si no se consigue el componente, se descarta la venta | Registrar resultado y causa. Si se encuentra, validar condiciones y aceptación antes de confirmar la atención |

Este caso conecta el almacén, el proveedor local y la promesa al cliente. La mejora debe permitir conocer el estado del componente solicitado y registrar la respuesta del proveedor alternativo, sin presentar la búsqueda urgente como garantía de suministro.

### Mejoras propuestas sobre la organización ya existente

El puesto de almacenero fijo está cubierto por un hijo de la dueña. El plan se orienta a **fortalecer su función y los controles de información**, conservando la experiencia del negocio como aporte a decisiones documentadas. Las medidas siguientes son propuestas; no se presentan como implementadas ni como sustitución de personal [EMP-07].

| Mejora para evaluar | Qué pretende resolver | Condición de aprobación y evidencia |
| --- | --- | --- |
| Control de la función de almacén | Necesidad de conocer quién prepara y valida cada salida | Documentar funciones, horario, autorización y relevo para contingencias del responsable fijo |
| Cuaderno con referencia de solicitud, salida y recepción | Dificultad de relacionar lo pedido con lo efectivamente recibido | Acordar campos mínimos: fecha, tienda, referencia, cantidad, responsable y estado, conservando el soporte actual |
| Conciliación de cuaderno, Excel y conteo físico | Información dispersa para decidir reposición y compra internacional | Verificar referencias y cantidades, registrar diferencias y conservar fecha de actualización; no se afirma que los soportes ya estén sincronizados |
| Registro de decisión de compra a China | Criterio de compra que depende de apreciación y experiencia sin método detallado | Documentar revisión realizada, referencias, cantidades, motivo y condiciones confirmadas; definir una frecuencia o umbral solo cuando existan datos suficientes |
| Directorio de proveedores de componentes compatibles | Llamadas sin respuesta y búsquedas prolongadas de arnés/Canbus | Validar contactos, referencias atendidas y confirmación de disponibilidad/precio/plazo; no atribuir existencias al proveedor por una conversación anterior |
| Revisión de componentes antes del domingo | Riesgo de faltar un adaptador en el día de mayor atención declarada | Revisar agenda y compatibilidad en una jornada de apertura previa; cantidades según necesidades, sin inventar stock de seguridad |

No se atribuyen ahorros ni reducción de ventas perdidas sin medir el funcionamiento vigente. El control propuesto asigna a la dirección del negocio la autorización de compra, al almacenero fijo la comprobación/preparación de salida y a la tienda la conformidad de recepción. El detalle de responsabilidades y respaldo debe quedar acordado; no se presupone un control digital ya implantado.

### Indicadores de servicio propuestos para secciones 6 y 7

| Indicador | Operación legible | Registro necesario / estado actual |
| --- | --- | --- |
| Solicitudes con información incompleta | (Solicitudes que requieren aclaración de referencia o cantidad ÷ Total de solicitudes registradas en el periodo) × 100 | Cuaderno con datos y motivo de aclaración; **sin línea base medida** |
| Tiempo de reposición | Hora de recepción conforme − Hora de solicitud | Mismo ID y fechas completas en ambos extremos; separar espera, preparación y viaje |
| Cumplimiento de ventana acordada | (Solicitudes recibidas en la ventana acordada ÷ Solicitudes con ventana acordada que vencen en el periodo) × 100 | Acordar la ventana antes de medir; no fijar «día siguiente» como compromiso no confirmado |
| Atención completa de reposición | (Solicitudes recibidas completas y compatibles ÷ Solicitudes recibidas en el periodo) × 100 | Cantidad y referencias solicitadas/recibidas; definir tratamiento de parciales |
| Resultado de atención urgente | Conteo de ventas completadas, esperadas/reprogramadas, sustituidas y perdidas por causa | Registrar el desenlace real; no tratar toda espera como pérdida de venta |
| Pérdida en solicitudes con faltante o demora de reposición | (Solicitudes afectadas que terminan en venta perdida ÷ Total de solicitudes afectadas registradas en el periodo) × 100 | Definir unidad de caso, causa y periodo para medir la situación actual. El 20–30 % anterior no se usa como tasa vigente ni como comparación directa con otra base |
| Tiempo de respuesta de alternativa local | Hora de respuesta útil y confirmada del proveedor − Hora de inicio de búsqueda | Registrar llamadas sin respuesta y causa; una a dos horas es antecedente declarado, no promedio medido |
| Compras a China con sustento registrado | (Pedidos a China con revisión y motivo documentados ÷ Total de pedidos a China del periodo) × 100 | Registrar decisión apoyada en cuaderno, Excel y existencia verificada; **sin línea base medida** |

Los porcentajes requieren denominador mayor que cero; un periodo sin solicitudes se marca «no aplica». Son indicadores de operación de almacén, separados de disponibilidad técnica, MTBF y MTTR de las fuentes o trimoto.

### Protocolo ante una interrupción y clientes en espera

1. El instalador o encargado identifica activo/componente, ubicación, causa e intervalo; contiene la tarea y genera solicitud de OT o faltante según corresponda.
2. El encargado actualiza la disponibilidad del recurso. Benjamín y Shirley contrastan materiales, confirmación del almacenero fijo sobre preparación y despacho, trabajos aceptados, técnicos y transporte para obtener un plan por vehículo.
3. Ventas conserva la cotización y aceptación originales, registra la incidencia y comunica que la fecha se está validando. No transforma una hipótesis en compromiso.
4. Se comparan **reprogramar** con **recuperar capacidad autorizada**. Reprogramar exige una ventana y aceptación del cliente; recuperar exige repuesto/equipo/técnico o transporte realmente disponibles y costo aprobado por Adrián.
5. Solo tras retorno a servicio probado y validación del plan se ofrece una alternativa. Si cambian términos de la oferta, se prepara nueva versión y nueva aceptación.
6. Se registra decisión, responsable, costo, versión del plan y aviso al cliente. El seguimiento permanece abierto mientras falte información o aceptación.

Mensaje propuesto: «La instalación requiere una verificación técnica y de disponibilidad. Estamos revisando una alternativa; te confirmaremos la nueva atención cuando estén validados el equipo, los componentes y el horario». No contiene una fecha inventada.

| Alternativa ante la trimoto detenida en sus tareas locales | Beneficio | Condición antes de confirmar |
| --- | --- | --- |
| Reprogramar entrega o gestión local | Evita gasto urgente | Verificar efecto en la instalación, herramienta solicitada y nueva disponibilidad; obtener aceptación si afecta al cliente |
| Contratar transporte alternativo para la tarea local | Puede recuperar reparto u obtención de herramienta | Cotización, capacidad, horario y autorización del dueño; no asumir que el proveedor de transporte está disponible |

El flete contratado es un costo distinto de la pérdida de instalaciones. El incremento de más de 40 % mencionado en el prompt inicial carece de comprobantes comparables y no se usa para calcular la tarifa de inDrive, que ya es el medio mayoritario de reposición. No se calcula un total de pérdidas sin registros de servicios, margen y transporte.

El alquiler de tienda 2 continúa como costo fijo aunque una falla afecte la atención, pero los S/ 1,800 mensuales no prueban una pérdida por día ni por vehículo. Para el domingo se propone prever componentes compatibles y comprobar herramientas y fuentes antes de la atención. El sábado cerrado no se convierte en jornada de mantenimiento del personal: cualquier intervención requiere una ventana acordada que respete el motivo religioso del cierre.

## 5C.3. Agente SIE y compuerta ante indisponibilidad TI: PC3-F01

En la rama de trabajo existe `agente-sie/`; la plataforma nativa `app/` está en `origin/sistema-agente`, revisada por referencia en el commit `587eabb`. No se ha fusionado para este aporte documental. Las dos PC empresariales actualmente usadas con Excel no se presentan como servidores Odoo de producción.

Si la compuerta permanece operativa y no puede consultar Odoo, `snapshot.construir` y el motor producen:

```json
{
  "status": "PENDIENTE",
  "code": "DEPENDENCIA_NO_DISPONIBLE",
  "responsible_role": "ADMINISTRADOR_Y_VENTAS",
  "order_id": null,
  "conditions": []
}
```

Es un extracto de campos, no la respuesta completa del contrato. Significa **no se pudo verificar**, sin concluir que el stock sea cero. El agente explica la dependencia y deriva a Administración. Si se cae también el anfitrión de la compuerta, no puede esperarse ese JSON: el canal llamante debe gestionar el error de transporte y mantener el caso sin confirmar. La caída de la base local de la compuerta tampoco está demostrada por el ensayo F01 de Odoo.

El abastecimiento de Carabayllo requiere datos operativos distintos de la disponibilidad técnica de Odoo: existencia compatible, preparación por el almacenero fijo y traslado confirmado. **El prototipo no acredita lectura automática del cuaderno ni del Excel interno de compras, ni decisiones automáticas de pedido a China.** Una consulta de stock tampoco confirma por sí sola el despacho. La futura integración requeriría registros fiables de movimientos y autorizaciones; no se añaden campos, estados ni funciones al contrato I03 como si estuvieran implementados.

La recuperación conserva `company_id`, `request_id`, versión, aceptación, correlación y huella del contenido. Mientras está caída la dependencia, reenviar el mismo contenido conserva el resultado pendiente. Tras restaurar Odoo, se usa `POST /solicitudes/SOL-PC3-F01/reanudar`. No se modifica la solicitud para eludir un error. Una segunda reanudación de una solicitud resuelta devuelve HTTP 409; una misma clave con otro contenido es conflicto de idempotencia.

La [evidencia local F01](../../../pruebas/pc3-adrian/evidencias/PC3-F01-local.json) documenta, con **Odoo simulado**, `PENDIENTE` durante la caída, misma respuesta al reintentar, `ACEPTADA / VALIDADA` al reanudar y una sola solicitud almacenada. `ACEPTADA` no crea un pedido, no reserva y no compromete fecha. La caída física/recuperación del Odoo real queda por ensayar con el equipo.

### Trazabilidad y límites de la bitácora

Los eventos guardan fecha/hora, actor, interfaz, solicitud, correlación y causa. La bitácora conserva eventos durante el flujo ordinario; sin embargo, el DDL revisado de `repositorio.py` no impone inmutabilidad mediante triggers o almacenamiento externo y `/admin/reiniciar` permite borrar transacciones de demo. Por ello se declara **trazable dentro del prototipo, sin inmutabilidad fuerte acreditada**. Una huella SHA-256 del archivo exportado permite comprobar su integridad respecto de la copia conservada, pero no vuelve inmutable la base.

Para fortalecer la evidencia se propone exportar eventos antes de cualquier reinicio, limitar permisos administrativos y conservar un respaldo con control de cambios. Son mejoras propuestas, no capacidades desplegadas. Tampoco se conecta automáticamente una OT física a la capacidad del agente: esa interfaz de mantenimiento queda fuera de lo demostrado.

## Acuerdo de integración para Shirley y Benjamín

Mantener las mismas unidades: cuatro espacios simultáneos, vehículos atendidos/día, instalaciones completas cuando estén identificadas, horas-bahía, unidades de SKU y soles de transporte. Incorporar en sección 6 el horario confirmado, promedios diarios de lunes a viernes, alcance de los picos dominicales, familias del almacén, almacenero fijo, coordinación mediante cuaderno y transporte mayoritario por inDrive. Describir la compra a China como decisión por experiencia apoyada en cuaderno y Excel, sin umbral o frecuencia formal informados. En sección 7 proponer conciliación de registros, trazabilidad de compra y directorio de proveedores. Los indicadores carecen de línea base medida; el 20–30 % queda como antecedente testimonial de otra situación operativa. Conservar el hallazgo `ADR-PC3-001` de la [ficha QA](../../../pruebas/pc3-adrian/ficha_qa_descuento_adrian.md): la ausencia de `I05` en la bitácora todavía no garantiza ausencia de una lectura real de stock en E02.

**Uso de IA y validación:** preparación y pruebas locales asistidas por Codex; coautores deben validar capacidad, red, decisiones y límites. Bases: S9-T pp. 10–13; S9-M pp. 6–9; S10-I «Cadena de decisión»; S10-G, rúbrica; S10-C pp. 5–13; REP pp. 2 y 4. Registro completo en 5A.
