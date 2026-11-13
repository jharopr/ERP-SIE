# 5B-II. Cadena de suministro I: inventarios, disponibilidad y nivel de servicio

**Curso:** GE703 Sistemas Integrados Empresariales, UNI-FIIS, 2026-2. **Grupo:** 7. **Empresa:** Importaciones MYS Hermanos S.A.C. **Autora:** Shirley Carrión Oré. **Coautoría de la cadena:** Benjamín Arancibia (flujo, proveedores, demanda y capacidad). **Corte documental:** 12/11/2026, Lima. **Versión:** 1.0 (borrador para revisión del equipo).

Benjamín explica cómo se mueve la mercadería; en esta parte yo analizo **qué disponibilidad y qué nivel de servicio produce ese movimiento** [REP, p. 2]. Uso las fuentes abreviadas (EMP-xx, S9/S10, VEN-01, COD-01) del registro común de [5A](../adrian/seccion_5a_activos_mantenimiento.md#registro-de-fuentes-y-calidad), para que las tres partes de la sección 5 usen la misma referencia.

## 5B.0. Convenciones comunes con Benjamín y Adrián

Acordé estas convenciones con Benjamín y Adrián para que el flujo (Benjamín), el servicio (mi parte) y la capacidad/activos (Adrián) se puedan sumar y comparar sin mezclar unidades.

| Magnitud | Unidad acordada | Observación |
| --- | --- | --- |
| Inventario | Unidades físicas por **referencia** (SKU o variante compatible) y por **ubicación** | Una pantalla, un marco o un arnés son referencias distintas. Las «más de mil variantes» de 5A son variedad de catálogo, no unidades [EMP-05] |
| Momento del dato | Fecha y hora de registro, zona America/Lima | Un stock sin hora de observación no sirve para prometer |
| Tiempo de reposición | Horas de apertura y días de apertura | Calendario de 5A: 09:00–19:00, seis días, sábado cerrado; 60 h semanales por sede [EMP-03] |
| Periodo de indicadores | Semana de seis días de apertura | Igual que la ventana de disponibilidad de 5A |
| Capacidad de instalación | Horas-bahía (definición de 5C) | 40 horas-bahía por día de apertura entre ambas tiendas, como potencial espacial, no como instalaciones garantizadas |
| Datos sintéticos | Prefijos `DEMO`, `EP`, `PC3` y SKU `RAD-7BT` | No se presentan como datos reales de MYS |

## 5B.1. Dónde está el stock y qué significa cada cantidad

### Ubicaciones de inventario

Reutilizo los códigos de ubicación funcional de 5A y añado dos estados que no son stock utilizable. Son **códigos que propongo para C05 Inventario**; no afirmo que estén cargados en un Odoo productivo de la empresa.

| Código propuesto | Lugar | Qué guarda | Uso en la promesa |
| --- | --- | --- | --- |
| `ALMACEN-CARABAYLLO/NIVEL-01` | Primer piso del almacén | Radios, parlantes y pantallas Android, incluida marca propia | Utilizable para reponer tiendas tras preparación y traslado |
| `ALMACEN-CARABAYLLO/NIVEL-02` | Segundo piso del almacén | Consolas plásticas o marcos, arneses, cables y Canbus | Utilizable solo si la referencia es compatible con el vehículo |
| `TIENDA-01/STOCK` | Tienda 1, La 50 | Exhibición y venta inmediata | Utilizable en el día |
| `TIENDA-02/STOCK` | Tienda 2, La 50 | Exhibición y venta inmediata | Utilizable en el día |
| `TRANSITO/REPOSICION` | Traslado Carabayllo → La 50 (mayoritariamente inDrive) | Mercadería que salió del almacén y no se ha recibido | **No utilizable** hasta la recepción |
| `IMPORTACION/EN-CAMINO` | Pedido a China no recibido | Compras firmes por llegar | **No utilizable**; solo cuenta como recepción firme con fecha confirmada |

### Cantidades que se deben distinguir

| Cantidad | Definición | Dónde vive hoy | Dónde viviría en la propuesta |
| --- | --- | --- | --- |
| Físico contado | Lo que se encuentra al contar en una ubicación | No hay conteo periódico documentado | Conteo cíclico registrado en C05 |
| Registrado | Lo que dicen los registros | Cuaderno de reposición y Excel del negocio [EMP-07] | Existencia de C05 por referencia y ubicación |
| Reservado | Unidades ya comprometidas con otro cliente o trabajo | No se registra de forma explícita | Reserva solo al confirmar un pedido operativo |
| **Disponible** | **Registrado − Reservado** | No calculable hoy | Consulta de C05 sin reservar (contrato I03/I04) |
| **Utilizable para un trabajo** | Disponible **y** compatible con el vehículo **y** en la ubicación correcta a la hora necesaria | Depende de la memoria del vendedor y del almacenero | Lista de compatibilidad + disponible + capacidad de 5C |

La diferencia entre las dos últimas filas es el núcleo del problema de servicio en MYS. Tener una pantalla en el primer piso no significa tener el marco y el arnés del segundo piso para ese vehículo (5C.2). Por eso mido el servicio por **kit de instalación**, no solo por producto.

En el prototipo, la disponibilidad se lee sin reservar: el código actúa como «cantidad menos cantidad reservada», sin modificar existencias [COD-01; parcial §4.16.3]. El agente consulta, explica y recomienda; **no reserva, no compra y no confirma pedidos** [REP, p. 3].

## 5B.2. Situación actual del inventario y su efecto en el servicio

| Aspecto | Práctica declarada | Efecto en disponibilidad y servicio |
| --- | --- | --- |
| Registro de faltantes | La tienda anota necesidades en un cuaderno [EMP-07] | La necesidad queda escrita, pero no su estado (preparada, en camino, recibida) ni la hora |
| Fuente de verdad del stock | Cuaderno y Excel; no hay conteo periódico documentado | No se puede saber si «hay» o «no hay» sin llamar o ir al almacén; la promesa depende de la memoria |
| Variedad | Más de mil variantes de marcos, arneses y cables [EMP-05] | Alta probabilidad de que falte una pieza de un kit aunque haya stock de la familia |
| Reposición interna | Almacenero fijo (hijo de la dueña) y traslado mayoritariamente por inDrive; ~40 min de viaje declarado, sentido por confirmar [EMP-06; EMP-07] | El tiempo total (anotación → atención → preparación → traslado → recepción) no está medido |
| Compra a China | Experiencia familiar, revisión de cuaderno y Excel, sin frecuencia ni umbral formal [EMP-07] | No hay forma de comprobar si se compra antes de que el quiebre afecte ventas |
| Urgencias | Antecedente: búsqueda telefónica de 1–2 h y pérdida estimada de 20–30 % de los casos afectados [EMP-06] | **Antecedente testimonial**, sin muestra ni periodo; no se usa como tasa vigente con almacenero fijo |

**Mi diagnóstico:** el riesgo principal de servicio no es la falta de mercadería en general, sino la **falta de información confiable y oportuna por referencia compatible y ubicación**. Con almacenero fijo, la función física está cubierta; lo que falta es un registro único que permita responder al cliente en mostrador sin adivinar.

## 5B.3. Indicadores de inventario y nivel de servicio

Elegí indicadores que responden a las dimensiones de la cadena de S10 (servicio, costo, inventario, capacidad y resiliencia) [S10-C]. Ninguno tiene línea base medida en la empresa: la columna «Dato hoy» dice qué falta para calcularlo. Propongo fijar las metas **después** de cuatro semanas de medición; la única meta que mantengo es la de exactitud de PC1 (98 %), por continuidad [contexto-y-alcance].

| ID | Indicador | Fórmula legible | Responsable | Dato hoy |
| --- | --- | --- | --- | --- |
| IND-01 | Cumplimiento de unidades en primera consulta | (Unidades atendibles con stock utilizable ÷ Unidades solicitadas) × 100 | Ventas | No disponible: no se registran solicitudes ni respuestas |
| IND-02 | Solicitudes completas | (Solicitudes con todas sus líneas cubiertas ÷ Solicitudes evaluadas en stock) × 100 | Ventas | No disponible |
| IND-03 | Kit de instalación completo | (Trabajos con equipo + marco + arnés/Canbus compatibles confirmados ÷ Trabajos aceptados) × 100 | Instalador / almacenero | No disponible: no hay lista de compatibilidad digital |
| IND-04 | Exactitud de inventario | (Referencias cuyo registro coincide con el conteo ÷ Referencias contadas) × 100 | Almacenero | No disponible: falta conteo; meta PC1 ≥ 98 % |
| IND-05 | Tiempo de reposición interna | Hora de recepción en tienda − Hora de anotación de la necesidad (en horas de apertura) | Almacenero + encargado de tienda | No disponible: el cuaderno no registra horas |
| IND-06 | Reposición en fecha y completa | (Reposiciones recibidas en la fecha acordada y con la cantidad pedida ÷ Reposiciones solicitadas) × 100 | Almacenero | No disponible |
| IND-07 | Ventas no concretadas por falta de componente | Número de atenciones perdidas con causa «sin componente compatible» por semana | Ventas | No disponible: hoy solo hay el antecedente testimonial |
| IND-08 | Promesas sin validación | Respuestas con fecha prometida emitida sin stock utilizable y capacidad validados | Ventas / agente | **Control: debe ser 0.** Comprobable en el prototipo |
| IND-09 | Cobertura de inventario | Disponible ÷ Demanda diaria promedio de la referencia (días) | Gestión familiar | No calculable: VEN-01 no tiene fecha transaccional |

Notas de cálculo:

- En IND-01 e IND-02 **no incluyo** las solicitudes rechazadas antes de consultar stock (por ejemplo, descuento sin autorización), porque no llegaron a evaluarse en inventario. Mezclarlas haría parecer que el problema es de stock cuando es de autorización.
- IND-03 se mide por trabajo de instalación; IND-01 por unidad. Un 100 % en IND-01 puede convivir con un IND-03 bajo si faltan piezas pequeñas de bajo costo.
- No calculo IND-09 con VEN-01: la exportación tiene 93 filas y 92 códigos pero ninguna fecha, así que no se puede convertir en demanda diaria (análisis de Adrián en 5A). Tampoco sumo ventas históricas como si fueran stock.

### Aplicación sobre los casos del prototipo (datos sintéticos)

Para comprobar las fórmulas y la lectura que debe dar el agente, ejecuté desde cero el simulador del contrato y el arnés del parcial (`pruebas/pc3-shirley/ejecutar_qa_shirley.py`, 12/11/2026). Son corridas **independientes y sintéticas**; no son tres ventas reales ni el nivel de servicio de MYS.

| Caso | Respuesta observada | Solicitadas | Disponible en el snapshot | Atendibles | Faltante | ¿Completa? |
| --- | --- | --- | --- | --- | --- | --- |
| EP-N01 normal | `ACEPTADA / VALIDADA` | 5 | 8 | 5 | 0 | Sí |
| EP-S01 stock parcial | `PROMESA_CONDICIONADA / DISPONIBILIDAD_PARCIAL` | 5 | 3 | 3 | 2 | No |
| EP-E01 descuento 10 % | `RECHAZADA / DESCUENTO_SIN_APROBACION` | 5 | — (no evaluado) | — | — | Excluido |

| Indicador sobre el prototipo | Operación | Resultado sintético |
| --- | --- | --- |
| IND-01 Cumplimiento de unidades | (5 + 3) ÷ (5 + 5) × 100 | **80 %** |
| IND-02 Solicitudes completas | 1 ÷ 2 × 100 | **50 %** |
| Señales de reposición con SKU, ubicación, faltante y responsable | 1 ÷ 1 × 100 | **100 %** |
| IND-08 Promesas sin validación | Fechas emitidas en el caso parcial | **0** (`promised_date: null`) |

El resultado me muestra algo útil aunque sea sintético: **un 80 % de unidades puede esconder que la mitad de los clientes no recibe lo que pidió**. Por eso reporto juntos IND-01 e IND-02.

### Qué debe decir el agente cuando el stock no alcanza

En el caso parcial, la respuesta correcta para el vendedor y el cliente contiene cinco elementos, que uso como criterio de QA (ficha SHI-U04):

1. Cuánto hay y dónde: «3 de 5 unidades de `RAD-7BT` disponibles en la ubicación consultada, a la hora del snapshot».
2. Que **no reservó** esas unidades.
3. Que **no hay fecha prometida** (`promised_date: null`).
4. Que el cliente debe aceptar nuevas condiciones: menos unidades, espera o alternativa, en una **nueva versión** de la cotización.
5. Que se generó una **señal de reposición** de 2 unidades para el dueño/abastecimiento, sin compra automática.

## 5B.4. Equilibrio entre servicio, costo y resiliencia

| Opción | Servicio | Costo | Resiliencia | Lectura para MYS |
| --- | --- | --- | --- | --- |
| Tener «de todo» en cada tienda | Alto en el día | Alto: duplica más de mil variantes en dos locales pequeños | Baja ante errores de registro | No viable por espacio y capital |
| Centralizar en Carabayllo y reponer por pedido (situación actual) | Depende del tiempo de reposición y de la información | Bajo en inventario; costo de traslado por viaje | Media: un almacenero fijo, pero sin registro de estado | Viable si se mide IND-05 e IND-06 |
| Centralizar + stock mínimo en tienda de los kits de mayor rotación + registro único | Alto para lo frecuente; espera validada para lo raro | Moderado | Mayor: se sabe qué hay y qué falta antes de prometer | **Propuesta**, condicionada a datos de rotación con fecha |

Todavía no fijo qué referencias forman el stock mínimo ni en qué cantidad: eso exige ventas con fecha por referencia (hoy no disponibles) y la lista de compatibilidades. Proponer números ahora sería inventarlos, y prefiero no hacerlo.

## 5B.5. Decisiones que propongo para la sección 7

| ID | Decisión | Condición de éxito verificable | Responsable propuesto |
| --- | --- | --- | --- |
| D-5B-01 | Registrar el stock por referencia y ubicación en un solo registro (C05), empezando por la familia de **arneses y Canbus** del nivel 2, que es la que más bloquea instalaciones | Conteo inicial de la familia piloto cargado con fecha; IND-04 medido en la semana 1 | Almacenero + gestión familiar |
| D-5B-02 | Reemplazar el cuaderno por una solicitud de reposición con estado (anotada, preparada, en tránsito, recibida) y hora | IND-05 e IND-06 calculables al final de la semana 2 | Encargados de tienda + almacenero |
| D-5B-03 | Mantener la regla de promesa: **sin kit completo y capacidad validada, no hay fecha**; el agente solo recomienda | IND-08 = 0 en pruebas y en operación | Ventas; Ballack/Gabriel en el agente y las reglas |
| D-5B-04 | Registrar la causa de cada atención no concretada por falta de componente | IND-07 con datos reales tras cuatro semanas; reemplaza el antecedente 20–30 % | Ventas |
| D-5B-05 | Revisión semanal de IND-01 a IND-07 y apoyo de la compra a China con esos datos, documentando qué se revisó y por qué se compra | Acta semanal y decisión de compra con cantidad, fecha y motivo | Gestión familiar (Adrián) |

## 5B.6. Límites

- Ningún indicador de esta sección tiene valor medido en la empresa; los porcentajes calculados provienen de casos sintéticos del prototipo.
- No he inspeccionado el Excel interno de decisión de compras ni he hecho un conteo físico.
- El paquete del Agente SIE y el sistema Odoo no están en la copia del repositorio revisada; la prueba de interpretación en el agente queda pendiente de ejecución en vivo (ficha [SHI-U01](../../../pruebas/pc3-shirley/ficha_qa_usabilidad_shirley.md)).
- No atribuyo a Odoo una instalación productiva en MYS.

**Uso de IA:** usé Claude (Anthropic) el 12/11/2026 como apoyo para contrastar los documentos del repositorio, redactar borradores y verificar cálculos. Revisé el contenido y las cifras; Benjamín revisa la coherencia con el flujo de 5B-I.
