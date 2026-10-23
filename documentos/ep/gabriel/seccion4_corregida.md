### **4. Especificación Técnica y Gobernanza del Contrato CRM–ERP**

#### **4.1 Decisión que Defiende Gabriel y Justificación del Problema**

Como responsable de la integración técnica del tramo comercial en IMPORTACIONES MYS HERMANOS S.A.C., defiendo que la transición entre una intención comercial en el CRM y un compromiso operativo en el ERP debe estar gobernada por un **contrato técnico formal de evaluación** con frontera explícita de sistemas de registro (SoR), comprobación determinista de precondiciones y respuestas tipificadas. El contrato v1.0 delimita estrictamente el alcance evaluado para este examen parcial: culmina en la emisión de una decisión técnica tipificada donde el identificador de pedido (`order_id`) permanece nulo en todos los casos. No se realiza reserva de existencias, confirmación de venta, despacho físico, facturación electrónica ni descomposición de IGV en este corte.

La justificación de este diseño radica en la realidad operativa del mostrador de ventas de autoradios y accesorios vehiculares. En un canal presencial B2C con atención directa, el vendedor interactúa con el cliente formulando ofertas y acuerdos preliminares. Sin una compuerta defensiva intermedia, el personal comercial podría registrar compromisos con precios rebajados de manera unilateral, aceptar cotizaciones obsoletas o asegurar disponibilidad de inventario sin confirmación oficial de almacén. El contrato de transición resuelve esta vulnerabilidad al establecer que el CRM actúa como canal de engagement que propone la operación, mientras que la compuerta defensiva (C04) verifica las reglas institucionales contra los registros confiables del ERP antes de permitir cualquier compromiso empresarial.

#### **4.2 Frontera Conceptual CRM vs. ERP (Sesión 6 del Ing. Enrique Chaparro)**

Conforme a la fundamentación teórica de la Sesión 6 de cátedra, la integración de procesos no consiste en compartir tablas sin control, sino en diferenciar los sistemas de captación comercial (System of Engagement - SoE) de los sistemas centrales de registro transaccional (System of Record - SoR). Aunque Odoo organice sus aplicaciones en una plataforma común, las fronteras de responsabilidad entre la oportunidad comercial y el compromiso operativo deben mantenerse desacopladas:

| Dimensión de Análisis | CRM (C01) / Contactos (C02) | Compuerta Defensiva (C04) | Ventas (C03) / Inventario (C05) / Autorizaciones (C06) |
|---|---|---|---|
| **Sistema de Registro (SoR)** | SoR de Lead, Oportunidad e interacciones con el cliente. C02 es SoR del maestro de contactos. | Componente de control transaccional sin datos maestros propios. Gobierna la transición. | C03 es SoR exclusivo de la Cotización oficial y sus versiones. C05 es SoR de existencias. C06 es SoR de políticas. |
| **Responsabilidad Funcional** | Captación del interés comercial, registro de requerimientos y recepción de aceptación. | Evaluación determinista de 12 reglas previas al compromiso de recursos. | Mantenimiento de listas de precios oficiales, control de existencias en almacén y gobierno de excepciones. |
| **Naturaleza del Mensaje** | Solicitud de evaluación con 9 referencias canónicas inmutables (I03). | Respuesta tipificada con estado, código, responsable y acción requerida (I08). | Snapshots de cotización (I04), consulta de stock read-only (I05) y consulta de autorizaciones (I06). |
| **Límite en el Examen Parcial** | Registra oportunidad y vínculo a cotización; solicita evaluación. | Emite veredicto técnico con `order_id = null`. Persiste bitácora append-only. | Consulta de catálogos y existencias sin reservar stock ni generar orden de venta. |

*Tabla 4.1: Delimitación de fronteras SoE y SoR entre componentes. Fuente: Elaboración propia asistida por IA.*

![Figura 4.1: Arquitectura de Componentes e Interfaces del Contrato CRM–ERP (v1.0)](documentos/ep/gabriel/diagramas/figura4_1_arquitectura_contrato.png)  
*Figura 4.1: Arquitectura de Componentes e Interfaces del Contrato CRM–ERP (v1.0). Elaboración propia asistida por IA.*

#### **4.3 Especificación Formal del Mensaje de Solicitud I03 (Principio de Datos Confiables)**

El mensaje de solicitud de evaluación (interfaz I03) emitido por el CRM (C01) hacia la compuerta defensiva (C04) se rige por el principio de datos confiables en el servidor (Sesión 6, diapositiva 9). El payload del mensaje transporta estrictamente **nueve campos de referencia canónicos** y prohíbe cualquier campo adicional (`additionalProperties: false` bajo JSON Schema Draft 2020-12):

```json
{
  "contract_version": "1.0",
  "company_id": "MYS-DEMO",
  "request_id": "SOL-EP-N01",
  "correlation_id": "COR-EP-001",
  "opportunity_id": "OPP-DEMO-001",
  "customer_id": "CLI-DEMO-001",
  "quotation_id": "COT-DEMO-001",
  "quotation_version": 1,
  "acceptance_id": "ACE-EP-001"
}
```

| Campo Canónico | Tipo de Dato | Cardinalidad | Sistema de Origen | Propósito y Regla de Validación en Servidor |
|---|---|---|---|---|
| `contract_version` | String (const) | 1..1 | CRM (C01) | Debe ser exactamente `"1.0"`. Protege contra incompatibilidad de versiones entre módulos. |
| `company_id` | String (token) | 1..1 | CRM (C01) | Identificador de compañía. Se valida coincidencia en sesión, cliente, oportunidad y cotización. |
| `request_id` | String (token) | 1..1 | CRM (C01) | Identificador unívoco de la transacción. Clave primaria de deduplicación e idempotencia. |
| `correlation_id` | String (token) | 1..1 | CRM (C01) | Identificador transversal de la interacción comercial. Permite auditar el ciclo completo en bitácora. |
| `opportunity_id` | String (token) | 1..1 | CRM (C01) | Referencia a la oportunidad comercial activa en C01 asignada al vendedor que solicita la evaluación. |
| `customer_id` | String (token) | 1..1 | Contactos (C02) | Referencia al cliente. Se verifica que esté activo y con coincidencia de identidad revisada en C02. |
| `quotation_id` | String (token) | 1..1 | Ventas/ERP (C03) | Referencia a la cotización oficial cuyo SoR reside en Ventas/ERP (C03). No se acepta oferta externa. |
| `quotation_version` | Integer (>=1) | 1..1 | Ventas/ERP (C03) | Número entero de versión. Se comprueba que corresponda a la versión vigente en el snapshot de C03. |
| `acceptance_id` | String (token) | 1..1 | CRM (C01) | Evidencia de conformidad del cliente vinculada a la versión específica de la cotización y su total. |

*Tabla 4.2: Estructura canónica del mensaje I03. Fuente: Elaboración propia asistida por IA.*

En cumplimiento estricto del principio de desconfianza de entrada, el mensaje I03 no transporta precios unitarios, subtotales, porcentajes de descuento, saldos de stock ni indicadores de aprobación del dueño. Si el vendedor pudiera declarar los importes en el payload, el sistema quedaría expuesto a manipulación de datos en tránsito. La compuerta defensiva C04 lee las líneas, precios de catálogo y descuentos directamente desde el snapshot comercial oficial en Ventas (C03) mediante la interfaz I04, y la autorización del dueño se verifica en el componente C06 mediante I06.

#### **4.4 Matriz Integral de Interfaces del Contrato de Transición (I01–I08)**

La interacción entre los componentes del ecosistema CRM–ERP se formaliza mediante ocho interfaces estructuradas, diferenciando las consultas internas a sistemas de registro de la respuesta tipificada hacia el canal comercial:

| ID | Componente Emisor | Componente Receptor | Tipo de Operación | Descripción Técnica del Intercambio y Controles |
|---|---|---|---|---|
| **I01** | CRM (C01) | Ventas/ERP (C03) | Síncrono (RPC/REST) | Sincronización y vinculación de oportunidad comercial y cotización en preparación preliminar. |
| **I02** | Compuerta (C04) | Contactos (C02) | Solo Lectura (Query) | Validación de identidad y estado de cliente (regla R05): activo, identidad revisada y compañía coherente. |
| **I03** | CRM (C01) | Compuerta (C04) | Mensaje Canónico | Solicitud de evaluación de transición comercial. Payload restringido a 9 referencias canónicas. |
| **I04** | Compuerta (C04) | Ventas/ERP (C03) | Solo Lectura (Query) | Lectura del snapshot comercial oficial: versión vigente, estado sent, vigencia, líneas, precios y total. |
| **I05** | Compuerta (C04) | Inventario (C05) | Solo Lectura (Query) | Consulta no bloqueante de stock disponible en almacén (regla R10). No reserva existencias físicas. |
| **I06** | Compuerta (C04) | Autorizaciones (C06) | Solo Lectura (Query) | Verificación de políticas comerciales y aprobaciones vigentes emitidas por Gerencia (regla R08). |
| **I07** | Compuerta (C04) | Bitácora (C07) | Append-Only (Event) | Registro atómico de eventos de auditoría con correlation_id, actor, interfaz, código y marca temporal. |
| **I08** | Compuerta (C04) | CRM (C01) / Vendedor | Respuesta Tipificada | Retorno de la decisión evaluada: status, code, total, message, required_action y order_id = null. |

*Tabla 4.3: Matriz integral de interfaces del Contrato v1.0. Fuente: Elaboración propia asistida por IA.*

![Figura 4.2: Diagrama de Secuencia Transaccional de Evaluación](documentos/ep/gabriel/diagramas/figura4_2_diagrama_secuencia.png)  
*Figura 4.2: Diagrama de Secuencia Transaccional de Evaluación. Elaboración propia asistida por IA.*

#### **4.5 Las Doce Reglas de Evaluación en Estricto Orden Determinista (R01–R12)**

La compuerta defensiva ejecuta una tubería de evaluación de doce reglas deterministas. Cada regla evalúa una condición excluyente; ante el primer incumplimiento, el flujo interrumpe la evaluación, emite el código de rechazo correspondiente y asigna el rol responsable y la acción correctiva:

| Regla | Componente / Interfaz | Comprobación Técnica Específica | Código Emitido si Falla | Estado Resultante |
|---|---|---|---|---|
| **R01** | Compuerta (I03) | Validación sintáctica contra JSON Schema Draft 2020-12 (9 campos requeridos, sin adicionales). | `CONTRATO_INVALIDO` | `RECHAZADA` |
| **R02** | Bitácora (I07) | Autenticación del actor comercial en sesión: rol Ventas, compañía autorizada y oportunidad asignada. | `NO_AUTORIZADO` | `RECHAZADA` |
| **R03** | Compuerta (I03) | Idempotencia: coincidencia de `request_id` y huella SHA-256 canónica. Devuelve respuesta histórica. | (Reintento Exitoso) | (Estado Original) |
| **R04** | Compuerta (I03) | Conflicto de huella o duplicado: si el hash difiere, o si la cotización y versión ya fue `ACEPTADA`. | `IDEMPOTENCIA_CONFLICTO` / `COTIZACION_YA_EVALUADA` | `RECHAZADA` |
| **R05** | Contactos (I02) / Ventas (I04) | Integridad de cliente y vínculos: cliente activo con identidad revisada en C02 y vínculos coherentes. | `DATOS_INCONSISTENTES` / `CLIENTE_NO_VALIDADO` | `RECHAZADA` |
| **R06** | Ventas (I04) | Vigencia comercial y versión: cotización en estado sent, versión vigente y tiempo lógico <= valid_until. | `VERSION_OBSOLETA` / `COTIZACION_NO_ENVIADA` / `COTIZACION_VENCIDA` | `RECHAZADA` |
| **R07** | Ventas (I04) | Validez de la aceptación: cliente, cotización, versión y total aceptados coinciden con snapshot oficial. | `ACEPTACION_INVALIDA` | `RECHAZADA` |
| **R08** | Autorizaciones (I06) | Política de descuento: si descuento > 5 %, requiere aprobación vigente de Gerencia en C06. | `DESCUENTO_SIN_APROBACION` | `RECHAZADA` |
| **R09** | Ventas (I04) | Consistencia de catálogo: SKUs activos, precios iguales a catálogo oficial, descuento [0..100] y cuadre. | `PRECIO_INVALIDO` | `RECHAZADA` |
| **R10** | Inventario (I05) | Disponibilidad física: si módulo no responde emite PENDIENTE; si stock < solicitado emite promesa. | `DEPENDENCIA_NO_DISPONIBLE` / `DISPONIBILIDAD_PARCIAL` | `PENDIENTE` / `PROMESA_CONDICIONADA` |
| **R11** | Compuerta (C04) | Transición de evaluación positiva: todas las reglas superadas sin condiciones de déficit de stock. | `VALIDADA` | `ACEPTADA` |
| **R12** | Bitácora (I07) | Persistencia transaccional atómica: confirmación simultánea de decisión y eventos en bitácora. | (Error de Transacción) | (Rollback) |

*Tabla 4.4: Las doce reglas de evaluación determinista. Fuente: Elaboración propia asistida por IA.*

**Justificación técnica del orden determinista:**
1. **R01 y R02 se validan antes de verificar idempotencia (R03/R04):** Un mensaje con sintaxis inválida o enviado por un actor no autorizado no debe ser procesado como transacción de negocio ni consultado en la base de datos de solicitudes.
2. **Precedencia de R08 sobre R09 y R10:** La regla de política de descuento (R08) se ejecuta intencionalmente antes de la verificación de catálogo (R09) y de la consulta de existencias en almacén (R10). El fundamento operativo es que el sistema no debe prometer disponibilidad de inventario sobre una cotización cuyo precio no cuenta con autorización comercial de Gerencia. Además, este orden garantiza que el rechazo informe la primera causa real de objeción comercial, asignando a Gerencia la responsabilidad de resolver la solicitud antes de inspeccionar inventario.

![Figura 4.3: Flujo de Decisión de las 12 Reglas Deterministas](documentos/ep/gabriel/diagramas/figura4_3_flujo_decision_12reglas.png)  
*Figura 4.3: Flujo de Decisión de las 12 Reglas Deterministas. Elaboración propia asistida por IA.*

#### **4.6 Matriz de Estados y Códigos de Respuesta Tipificados del ERP**

El contrato formaliza cuatro estados canónicos y quince códigos de respuesta tipificados retornados al CRM mediante la interfaz I08. El identificador de pedido (`order_id`) es estrictamente `null` en todos los casos:

| Estado Canónico | Código Tipificado | Significado Técnico Operativo | Rol Asignado | Acción Requerida |
|---|---|---|---|---|
| `ACEPTADA` | `VALIDADA` | Evaluación comercial completada; precondiciones satisfechas; confirmación de pedido pendiente. | VENTAS | Informar conformidad al cliente; proceder con confirmación operativa en siguiente incremento. |
| `RECHAZADA` | `CONTRATO_INVALIDO` | Payload I03 no cumple con el JSON Schema Draft 2020-12 (campos faltantes o adicionales). | VENTAS | Corregir estructura del mensaje en CRM según la especificación del Contrato v1.0. |
| `RECHAZADA` | `NO_AUTORIZADO` | Actor comercial sin permisos sobre la compañía o no asignado a la oportunidad comercial. | VENTAS | Solicitar asignación de permisos; no intentar alterar identificadores en el payload. |
| `RECHAZADA` | `IDEMPOTENCIA_CONFLICTO` | El `request_id` ya fue registrado previamente pero la huella SHA-256 del contenido actual difiere. | VENTAS | Generar un nuevo request_id para solicitudes con datos modificados; no reutilizar identificadores. |
| `RECHAZADA` | `COTIZACION_YA_EVALUADA` | La versión de cotización ya cuenta con una decisión ACEPTADA previa en la base de datos. | VENTAS | Consultar la solicitud aceptada preexistente; para cambios comerciales generar nueva versión. |
| `RECHAZADA` | `DATOS_INCONSISTENTES` | Discrepancia referencial entre identificadores de compañía, cliente, oportunidad o vendedor. | VENTAS | Corregir los vínculos entre entidades en el CRM y volver a vincular la oportunidad. |
| `RECHAZADA` | `CLIENTE_NO_VALIDADO` | El cliente se encuentra inactivo en C02 o mantiene observaciones de identidad no resueltas. | VENTAS | Resolver coincidencia de identidad en el maestro de Contactos (C02) antes de cotizar. |
| `RECHAZADA` | `VERSION_OBSOLETA` | La versión enviada no corresponde a la versión vigente oficial registrada en Ventas (C03). | VENTAS | Sincronizar la cotización en CRM para obtener la última versión aprobada en Ventas. |
| `RECHAZADA` | `COTIZACION_NO_ENVIADA` | La cotización en Ventas (C03) no ha alcanzado el estado formal de enviada (`state != 'sent'`). | VENTAS | Emitir formalmente la cotización al cliente antes de solicitar la evaluación de transición. |
| `RECHAZADA` | `COTIZACION_VENCIDA` | La fecha y hora lógica de la solicitud superó el límite de vigencia comercial (`valid_until`). | VENTAS | Generar una nueva versión de cotización con vigencia comercial actualizada y aceptada. |
| `RECHAZADA` | `ACEPTACION_INVALIDA` | La aceptación del cliente no coincide en versión, total o fecha respecto al snapshot oficial. | VENTAS | Registrar formalmente la aceptación del cliente para la versión e importe vigentes. |
| `RECHAZADA` | `PRECIO_INVALIDO` | Precios unitarios alterados respecto al catálogo oficial, descuento fuera de rango o error de cálculo. | VENTAS | Recalcular cotización con base en la lista oficial de precios del catálogo de Ventas. |
| `RECHAZADA` | `DESCUENTO_SIN_APROBACION` | Descuento superior al 5 % sin aprobación vigente registrada en Autorizaciones (C06). | GERENCIA | Gerencia debe registrar aprobación en C06; luego preparar nueva versión y aceptación. |
| `PENDIENTE` | `DEPENDENCIA_NO_DISPONIBLE` | El módulo de Inventario (C05) no respondió o devolvió datos de stock no confiables. | ADMINISTRADOR_Y_VENTAS | Restablecer conectividad del módulo de Inventario y reanudar la solicitud (`resume=true`). |
| `PROMESA_CONDICIONADA` | `DISPONIBILIDAD_PARCIAL` | Stock disponible en C05 menor a la cantidad solicitada; requiere conformidad del cliente. | VENTAS | Acordar con el cliente entrega diferida o despacho parcial; emitir nueva cotización. |

*Tabla 4.5: Matriz completa de 4 estados y 15 códigos de respuesta tipificados. Fuente: Elaboración propia asistida por IA.*

#### **4.7 Idempotencia Estricta, Huella SHA-256 y Persistencia Atómica**

El Contrato v1.0 garantiza la coherencia del estado mediante un mecanismo de idempotencia basado en el resumen criptográfico SHA-256 del contenido canónico de la solicitud:

1. **Huella canónica de integridad técnica:** Antes de almacenar la solicitud, se normaliza el payload I03 bajo serialización canónica RFC 8785 (claves ordenadas lexicográficamente, separadores compactos `','` y `':'`, codificación UTF-8). Se calcula el resumen SHA-256 que actúa como huella de integridad técnica e idempotencia para detectar reintentos idénticos o manipulaciones accidentales. Se aclara que esta huella no constituye una firma digital ni proporciona no repudio legal (lo cual exigiría certificados digitales PKI bajo la Ley 27269), sino que funciona como control transaccional de concurrencia y deduplicación.
2. **Bitácora append-only:** La bitácora de auditoría (`audit`) es un registro de solo inserción (append-only por diseño; la inmutabilidad real requiere permisos de base de datos a nivel de motor, por validar en PC3). Cada evento persiste el `event_id`, identificadores de compañía, solicitud y correlación, el actor responsable, la interfaz consultada, el tipo de evento y la marca temporal lógica.
3. **Persistencia atómica y frontera transaccional:** Toda la evaluación se ejecuta dentro de una transacción atómica exclusiva (`BEGIN IMMEDIATE` en SQLite local). La verificación de la huella ocurre dentro de la transacción, respaldada por una restricción UNIQUE.
4. **Regla de reintentos y unicidad condicionada:**
   - Si se recibe el mismo `request_id` con la misma huella SHA-256, se retorna la respuesta previa almacenada y se anota un evento `REINTENTO`.
   - Si se reutiliza el `request_id` pero el payload fue alterado, se rechaza inmediatamente con `IDEMPOTENCIA_CONFLICTO`.
   - Si se evalúa una cotización y versión con un nuevo `request_id`, la restricción UNIQUE sobre `(quotation_id, quotation_version)` aplica **exclusivamente si ya existe una decisión previa en estado `ACEPTADA`**, retornando `COTIZACION_YA_EVALUADA`. Por el contrario, si la evaluación previa culminó en `RECHAZADA`, `PENDIENTE` o `PROMESA_CONDICIONADA`, la versión no se considera consumida y se permite reevaluar con un `request_id` nuevo tras subsanar la causa.
   - *Reporte del simulador local:* En el prototipo actual en SQLite (`pruebas/pc2/simulador.py`), la tabla `requests` implementa una restricción incondicional `UNIQUE (company_id, quotation_id, quotation_version)`. Para alinear el simulador con el diseño arquitectónico propuesto para PostgreSQL, se reporta que el índice debe ser parcial: `CREATE UNIQUE INDEX idx_requests_accepted ON requests (company_id, quotation_id, quotation_version) WHERE json_extract(response_json, '$.status') = 'ACEPTADA';`.

![Figura 4.4: Flujo de Idempotencia por Huella SHA-256 y Persistencia Atómica](documentos/ep/gabriel/diagramas/figura4_4_idempotencia_sha256.png)  
*Figura 4.4: Flujo de Idempotencia por Huella SHA-256 y Persistencia Atómica. Elaboración propia asistida por IA.*

#### **4.8 Calibración con el Caso Andina Manufactura (Sesión 7 del Ing. Chaparro)**

El alcance del presente examen parcial cubre las operaciones comerciales de mostrador hasta la Sesión 6, caracterizadas por transacciones minoristas al contado con retiro inmediato en tienda. En contraste, el caso Andina Manufactura (Sesión 7) modela un entorno industrial B2B con líneas de crédito empresarial, despachos parciales escalonados y facturación única subordinada al cumplimiento total de la orden. El Contrato v1.0 no modela líneas de crédito ni cronogramas de entrega diferida (backorders); por tanto, no es neutral al segmento ni comparte reglas idénticas con dicho modelo. Para adaptar este contrato a un escenario tipo Andina se requeriría incorporar reglas deterministas adicionales para el límite de crédito disponible (`R_CREDITO`), la validación de condiciones de pago a 30/60 días (`R_CONDICION_PAGO`) y la programación de órdenes de entrega parcial (`R_DESPACHO_PARCIAL`), manteniendo como principio común la compuerta defensiva previa al compromiso operativo.

![Figura 4.5: Calibración Conceptual: Contrato v1.0 MYS (Sesión 6) vs. Andina Manufactura (Sesión 7)](documentos/ep/gabriel/diagramas/figura4_5_calibracion_andina_mys.png)  
*Figura 4.5: Calibración Conceptual: Contrato v1.0 MYS (Sesión 6) vs. Andina Manufactura (Sesión 7). Elaboración propia asistida por IA.*

#### **4.9 Comportamiento y Evidencia Observada en los Tres Casos del Parcial**

La implementación técnica del contrato fue verificada mediante la ejecución del generador compartido de pruebas (`pruebas/ep-benjamin/generar_evidencias.py`), alcanzando un total de **112 comprobaciones automatizadas aprobadas (100 % de éxito)** distribuidas en los tres escenarios evaluados:

| Parámetro / Resultado | Caso Normal: EP-N01 | Disponibilidad Parcial: EP-S01 | Excepción de Descuento: EP-E01 |
|---|---|---|---|
| **Identificador de Solicitud** | `SOL-EP-N01` | `SOL-EP-S01` | `SOL-EP-E01` |
| **Cotización y Versión** | `COT-DEMO-001` (Versión 1) | `COT-DEMO-001` (Versión 1) | `COT-DEMO-001` (Versión 2) |
| **Detalle de Mercancía** | 5 autoradios RAD-7BT @ S/ 400.00 | 5 autoradios RAD-7BT @ S/ 400.00 | 5 autoradios RAD-7BT @ S/ 400.00 |
| **Subtotal Bruto** | S/ 2,000.00 | S/ 2,000.00 | S/ 2,000.00 |
| **Descuento Aplicado** | 5.0 % (S/ 100.00) - Autónomo | 5.0 % (S/ 100.00) - Autónomo | 10.0 % (S/ 200.00) - No autorizado |
| **Total Liquidado** | S/ 1,900.00 PEN | S/ 1,900.00 PEN | null (No liquidado) |
| **Stock en Almacén** | 8 unidades disponibles | 3 unidades disponibles (Déficit: 2) | 8 unidades (No consultado por R08) |
| **Estado Resultante** | `ACEPTADA` | `PROMESA_CONDICIONADA` | `RECHAZADA` |
| **Código Tipificado** | `VALIDADA` | `DISPONIBILIDAD_PARCIAL` | `DESCUENTO_SIN_APROBACION` |
| **Identificador de Pedido** | `order_id = null` | `order_id = null` | `order_id = null` |
| **Condiciones / Señal P2P** | Lista vacía `[]` | `{requested: 5, available: 3, promised_date: null}` | Lista vacía `[]` |
| **Comprobaciones Aprobadas** | **37 comprobaciones** (100 %) | **37 comprobaciones** (100 %) | **38 comprobaciones** (100 %) |

*Tabla 4.6: Matriz comparativa de resultados observados en la simulación. Fuente: Ejecución de generar_evidencias.py.*

![Figura 4.6: Evidencias de Ejecución de los Tres Casos Evaluados en el Simulador](documentos/ep/gabriel/diagramas/figura4_6_evidencias_tres_casos.png)  
*Figura 4.6: Evidencias de Ejecución de los Tres Casos Evaluados en el Simulador. Elaboración propia asistida por IA.*

#### **4.10 Dimensiones ERP e Indicadores de Rendimiento del Contrato**

Para evaluar objetivamente el desempeño del contrato técnico de integración, se establecen tres indicadores cuantificables sobre la ejecución observada:

| Indicador Técnico | Fórmula de Cálculo y Fuente de Datos | Valor Esperado | Valor Observado en Simulación | Interpretación Técnica |
|---|---|---|---|---|
| **Rechazos R01–R08 que no llegaron a consultar inventario** | (Rechazos en R01–R08 sin consulta a I05 / Total de solicitudes rechazadas en R01–R08) * 100 | 100.0 % | 100.0 % (1/1 en EP-E01) | Confirma que la compuerta defensiva bloquea solicitudes con precios no autorizados sin consultar existencias. |
| **Tasa de Idempotencia y Trazabilidad Canónica** | (Solicitudes con request_id, huella SHA-256 y correlation_id verificados / Total de solicitudes) * 100 | 100.0 % | 100.0 % (3/3 casos) | Asegura que todas las transacciones quedan selladas con resumen criptográfico en bitácora append-only. |
| **Tiempo de Respuesta de la Compuerta Local** | Tiempo transcurrido entre I03 y emisión de I08 registrado en milisegundos en entorno local | < 50 ms | < 15 ms por solicitud | Demuestra que la validación secuencial de 12 reglas en memoria y SQLite local opera sin latencia apreciable. |

*Tabla 4.7: Indicadores técnicos de rendimiento del Contrato v1.0. Fuente: Elaboración propia asistida por IA.*

#### **4.11 Guía de Reproducción Local y Ejecución de Evidencias**

Para garantizar la auditabilidad y reproducibilidad de los resultados reportados, los miembros del comité pueden ejecutar la simulación local mediante comandos estándar de Python (versión 3.10 o superior) en el repositorio:

1. **Ejecución del arnés compartido de pruebas (112 comprobaciones):**
   ```powershell
   python pruebas/ep-benjamin/generar_evidencias.py
   ```
   *Salida esperada:* Mensaje de conformidad `OK: 3 casos, 112 comprobaciones; evidencia en pruebas/ep-benjamin/evidencias` con conteos exactos de 37 para EP-N01, 37 para EP-S01 y 38 para EP-E01.
2. **Evaluación unitaria directa del caso normal EP-N01:**
   ```powershell
   python pruebas/pc2/simulador.py pruebas/ep-benjamin/evidencias/EP-N01-entrada.json
   ```
   *Resultado:* Retorno de estructura JSON con estado `ACEPTADA`, código `VALIDADA`, total `"1900.00"` y `order_id = null`.
3. **Evaluación unitaria del caso de quiebre de descuento EP-E01:**
   ```powershell
   python pruebas/pc2/simulador.py pruebas/ep-benjamin/evidencias/EP-E01-entrada.json
   ```
   *Resultado:* Retorno de estructura JSON con estado `RECHAZADA`, código `DESCUENTO_SIN_APROBACION`, responsable `GERENCIA` y `order_id = null`.

*Nota de entorno:* Se reitera que las pruebas se ejecutan sobre un motor de simulación local en SQLite con fixtures preconfiguradas. El diseño relacional para PostgreSQL y las interfaces REST corresponden a la arquitectura técnica propuesta, sin que exista un entorno de Odoo desplegado en producción.

#### **4.12 Protocolo de Demostración y Validación Transaccional**

La defensa técnica del contrato de integración se articula en cuatro pilares de ingeniería verificables:
1. **Principio de desconfianza de entrada y datos confiables:** El mensaje I03 transporta exclusivamente 9 referencias canónicas. Los precios, descuentos y líneas se obtienen del snapshot en C03 vía I04; el cliente se valida en C02 vía I02; la aprobación del dueño se consulta en C06 vía I06; y el inventario se inspecciona en C05 vía I05.
2. **Tubería determinista de precedencia estricta:** La regla R08 de política de precios se evalúa antes de verificar inventario en R10. Esto garantiza que no se prometa stock sobre precios no autorizados, señalando de forma unívoca la causa raíz del rechazo a Gerencia.
3. **Comprobación multicaso en entorno controlado:** Los tres escenarios evaluados cubren la totalidad de los flujos de transición: validación completa (EP-N01), promesa condicionada ante déficit físico (EP-S01) y contención de descuento no autorizado (EP-E01), sumando 112 comprobaciones verificables.
4. **Idempotencia técnica por huella SHA-256:** Las solicitudes son procesadas dentro de transacciones atómicas `BEGIN IMMEDIATE`. Reintentos con idéntico payload retornan la respuesta previa sin duplicar registros, y la bitácora registra cada evento de forma append-only.

#### **4.13 Banco de Preguntas y Respuestas para el Comité Evaluador**

1. **¿Por qué el campo `order_id` es estrictamente nulo en todas las respuestas del contrato?**  
   *Respuesta:* Porque el alcance del parcial culmina en la compuerta defensiva de evaluación comercial. La confirmación del pedido de venta, la reserva física de stock y la emisión del comprobante corresponden a incrementos operativos posteriores una vez confirmado el cobro. Mantener `order_id = null` previene que procesos aguas abajo confundan una evaluación positiva con una orden formal de despacho.
2. **¿Por qué la regla R08 de descuento se evalúa antes de la consulta de inventario (R10)?**  
   *Respuesta:* Por coherencia operativa: el sistema no debe consultar ni comprometer stock sobre una cotización cuyo precio carece de aprobación de Gerencia. Además, este orden garantiza que el rechazo informe la causa comercial primaria y asigne a Gerencia la acción correctiva correspondiente, evitando cargas innecesarias sobre el módulo de inventario.
3. **¿Qué ocurre si un vendedor presiona repetidamente el botón de envío en el CRM?**  
   *Respuesta:* Opera la regla de idempotencia R03: el contrato identifica el mismo `request_id` y verifica que la huella SHA-256 coincida exactamente. En lugar de reevaluar las reglas o duplicar registros, retorna de inmediato la respuesta original persistida y anota un evento de `REINTENTO` en la bitácora.
4. **¿Por qué se requiere este contrato si Odoo unifica CRM y Ventas en una misma plataforma?**  
   *Respuesta:* Porque compartir base de datos no garantiza gobernanza transaccional. Sin una compuerta defensiva con reglas explícitas, la interfaz de CRM podría forzar la creación de cotizaciones o pedidos sin verificar la vigencia de la oferta, la autorización de descuentos o la identidad del cliente. El contrato formaliza las precondiciones técnicas que cualquier aplicación cliente debe respetar.

#### **4.14 Matriz de Defensa, Evidencias Verificables y Límites del Alcance**

Sustituyendo autocalificaciones subjetivas, se presenta la matriz técnica de compromisos defendidos, evidencias reproducibles y límites formales del alcance:

| Qué Defiendo en este Examen Parcial | Con qué Evidencia Técnica se Demuestra | Qué Límite Reconozco Objetivamente |
|---|---|---|
| **Frontera SoE/SoR desacoplada** | Matriz de interfaces I01–I08 y Tabla 4.1 con C03 como SoR de cotización. | No se implementaron servicios web REST productivos; opera mediante funciones en simulador local. |
| **Payload I03 basado en datos confiables** | JSON Schema Draft 2020-12 cerrado con exactamente 9 referencias canónicas. | Los maestros de datos provienen de fixtures JSON estáticas y no de bases de datos operativas en línea. |
| **Precedencia determinista (R08 antes de R10)** | Flujo de reglas, traza de eventos en caso EP-E01 y bloqueo previo a consulta de stock. | No se simularon múltiples solicitudes concurrentes compitiendo por existencias en tiempo real. |
| **Idempotencia estricta por huella SHA-256** | Prueba de reintento en simulador con `BEGIN IMMEDIATE` y hash SHA-256 canónico. | La huella SHA-256 no es una firma digital con PKI; no acredita no repudio legal bajo Ley 27269. |
| **Comportamiento observable multicaso** | 112 comprobaciones automatizadas aprobadas en `generar_evidencias.py` (37/37/38). | Las pruebas acreditan la lógica determinista del contrato, no la disponibilidad de red o infraestructura. |
| **Delimitación estricta de alcance (order_id null)** | Respuestas tipificadas I08 de los 3 casos con `order_id: null` y sin reserva. | No se modela la confirmación de pedido, el cobro en caja, la facturación ni la entrega de bienes. |
| **Calibración conceptual con Sesión 7** | Tabla comparativa de dimensiones operativas frente al caso industrial Andina. | Contrato v1.0 no modela líneas de crédito B2B ni entregas escalonadas; requiere reglas adicionales. |

*Tabla 4.8: Matriz de compromisos técnicos defendidos, evidencias y límites del alcance. Fuente: Elaboración propia asistida por IA.*

#### **4.15 Registro de Fuentes Académicas, Supuestos Didácticos y Uso Responsable de IA**

- **Fuentes Académicas Primarias:**
  1. Chaparro, E. (2026). *Sesión 6: CRM, marketing y ventas: De la oportunidad comercial al pedido gobernado por el ERP*. Curso GE703 Sistemas Integrados Empresariales, UNI FIIS.
  2. Chaparro, E. (2026). *Sesión 7: Del interés comercial a la factura trazable: Caso Andina*. Curso GE703 Sistemas Integrados Empresariales, UNI FIIS.
  3. Internet Engineering Task Force (IETF). (2020). *RFC 8785: JSON Canonicalization Scheme (JCS)*.
- **Supuestos Didácticos:** Los precios (S/ 400.00 por autoradio RAD-7BT), cantidades (5 unidades), políticas de descuento (5 % vendedor, 10 % dueño) y niveles de existencias (8 y 3 unidades) son parámetros de calibración didáctica para la simulación local y no reflejan inventarios privados de IMPORTACIONES MYS HERMANOS S.A.C.
- **Declaración de Uso de IA:** Se empleó asistencia de modelos de lenguaje (OpenAI Codex / Claude) el 22/10/2026 para la estructuración de tablas comparativas y refinamiento de sintaxis en scripts. La autoría técnica, diseño del contrato y defensa oral corresponden a Gabriel Chavez Mendoza. Estado de control grupal: revisión humana de Gabriel Chavez: por completar.

#### **4.15.1 Guion de Intervención Oral y Preguntas Probables de Vocal (Minutos 06:00–09:00)**

**Guion de Intervención Oral (Tiempo asignado: 3 minutos exactos | 405 palabras):**

Buenos días profesor y miembros del comité. En estos tres minutos defenderé la especificación técnica de la compuerta defensiva que gobierna la transición entre el CRM y el ERP de Importaciones MYS Hermanos.

Mi primera idea central es el principio de datos confiables en la solicitud I03. El vendedor en mostrador registra la oportunidad y el cliente acepta una cotización, pero al solicitar la evaluación comercial, el CRM no envía precios, montos, descuentos ni saldos de almacén. El mensaje I03 transporta estrictamente nueve referencias canónicas: identificadores de compañía, solicitud, correlación, oportunidad, cliente, cotización, versión y aceptación. Los importes, líneas y vigencia se leen directamente desde el registro oficial en Ventas mediante I04, y los datos del cliente se verifican en Contactos con I02. Esto elimina cualquier posibilidad de que un usuario altere importes o saldos en tránsito.

La segunda decisión de diseño es la precedencia de la regla R08 sobre las reglas R09 y R10. En nuestro diseño determinista, la política de descuento de Gerencia se evalúa antes de verificar el catálogo o consultar las existencias de almacén. La razón es operativa: el ERP no debe consultar ni prometer disponibilidad de inventario sobre una oferta cuyo precio no tiene autorización comercial vigente. Si un vendedor otorga un diez por ciento de descuento cuando el límite autónomo es cinco por ciento, la compuerta rechaza de inmediato con el código DESCUENTO_SIN_APROBACION, asigna la responsabilidad a Gerencia e instruye registrar la autorización en el componente C06. Esto informa la primera causa real del rechazo y evita procesar inventario innecesariamente.

La tercera idea es la evidencia verificable y el límite formal de nuestra entrega. Hemos validado las doce reglas con el generador del equipo, superando ciento doce comprobaciones en tres escenarios: en el caso normal EP-N01 se aceptan las cinco unidades a precio de catálogo con treinta y siete comprobaciones; en EP-S01 se detecta disponibilidad parcial de tres unidades y se emite promesa condicionada con treinta y siete comprobaciones; y en EP-E01 se rechaza el descuento no autorizado con treinta y ocho comprobaciones. El límite que reconocemos con total transparencia es que el alcance del examen parcial termina en la respuesta tipificada I08: el campo order_id es estrictamente nulo en todos los casos, no se reservó stock ni se generó pedido de venta en este incremento, y la validación se ejecutó en un simulador local en SQLite, dejando el esquema en PostgreSQL propuesto para la siguiente fase. Muchas gracias.

**Banco de Preguntas Probables del Vocal Invitado:**

1. **¿Cómo se reintenta una solicitud rechazada después de que el dueño aprueba la excepción comercial?**  
   *Respuesta:* Dado que la evaluación previa concluyó en estado `RECHAZADA`, la versión de la cotización no fue consumida en el contrato de transición. Tras registrarse la aprobación del dueño en el componente de Autorizaciones (C06), el CRM emite una nueva solicitud I03 con un `request_id` nuevo para esa misma cotización y versión. La compuerta defensiva comprueba en R08 la existencia de dicha autorización vigente en C06 y avanza normalmente hacia la inspección de existencias en almacén.
2. **¿Por qué se emplea una huella SHA-256 en lugar de una firma digital completa?**  
   *Respuesta:* El resumen SHA-256 se utiliza como una huella canónica de integridad técnica y control de idempotencia para detectar reintentos idénticos dentro de la transacción local. No constituye una firma digital en los términos de la Ley 27269, ya que no implementa infraestructura de clave pública (PKI) ni certificados digitales acreditados para garantizar no repudio legal. Para este corte académico de simulación local, el hash resuelve el control de duplicados de forma eficiente sin sobrecarga criptográfica innecesaria.
3. **¿Por qué el campo `order_id` es estrictamente nulo en todas las respuestas del contrato?**  
   *Respuesta:* Porque el alcance del parcial culmina en la compuerta defensiva de evaluación comercial y no realiza reservas físicas ni confirmaciones operativas. La generación del pedido de venta formal y la asignación del `order_id` corresponden a los incrementos posteriores tras la confirmación del cobro en caja. El valor nulo garantiza que ningún proceso posterior confunda una respuesta de validación con una orden de despacho en almacén.
