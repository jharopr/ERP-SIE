# Contrato CRM–ERP · revisión 1.1

**Base:** [cuatro módulos Odoo y sus sistemas externos](../crm-erp-pc2.md). **Fecha:** 16/10/2026. Revisión humana de Gabriel/Jharolym pendiente. Las operaciones son interfaces conceptuales internas, no endpoints publicados de Odoo.

## 1. Objeto y alcance

CRM solicita a Ventas evaluar una cotización aceptada. Ventas consulta sus datos oficiales, Contactos e Inventario, comprueba reglas y devuelve una decisión trazable a CRM. PC2 termina en solicitud/respuesta. No confirma `sale.order`, no reserva stock, no cobra ni llama a UBLHUB/SUNAT. Cotización y futuro pedido comparten el registro `sale.order`.

La revisión 1.1 sustituye a 1.0 en los mensajes y evidencias del repositorio; el validador exige `contract_version=1.1`. Los nombres de archivo `*-v1` conservan la familia de contrato. No se afirma compatibilidad de mensajes 1.0 con el validador actual.

## 2. Interfaces del diagrama

| ID / operación | Emisor → responsable | Entrada mínima / fuente confiable | Salida y excepción | Efecto autorizado |
| --- | --- | --- | --- | --- |
| I01 `resolver_cliente` | CRM → Contactos | Compañía de sesión, referencia del cliente y canal | ID único, activo, identidad revisada y evidencia de finalidad/canal/vigencia; ambigüedad → revisión | Vincular/crear ficha solo tras búsqueda y revisión; fixture en prueba |
| I02 `preparar_cotizacion` | CRM → Ventas | Oportunidad, cliente, SKU/unidad, cantidad, condiciones; precio desde catálogo | Cotización/versionado, líneas, total, vigencia, pago, lugar/modalidad/fecha solicitada; error → corregir | Preparar cotización; nueva versión invalida aceptación/aprobación previa; fixture en prueba |
| I03 `solicitar_transicion` / `consultar_transicion` | CRM → Ventas | Mensaje cerrado de referencias; actor autenticado fuera del payload | Decisión del schema; sin acceso → `NO_AUTORIZADO`; clave distinta de contenido → conflicto | Crear/consultar evaluación, nunca confirmar pedido |
| I04 `leer_snapshot` | Función interna de Ventas | Compañía, cotización/versión, oportunidad, cliente y aceptación | Datos comerciales oficiales, pago y promesa; vínculo, versión, aceptación o vigencia inválidos → rechazo | Solo lectura; no recalcular desde datos libres del solicitante |
| I05 `consultar_disponibilidad` | Ventas → Inventario | Compañía, ubicación, SKU/cantidad agregada | Cantidad observada y ubicación; parcial → promesa condicionada; proveedor caído → pendiente | Solo lectura; no reserva ni salida |
| I06 `verificar_aprobacion` | Función interna de Ventas | Descuento, cotización/versión, total y vendedor del snapshot | Decisión humana de autoridad competente y vigencia; ausente/obsoleta/autoaprobada → rechazo | Verificar autorización registrada; no autoaprobar |
| I07 `autorizar_y_auditar` | Módulos → control transversal | Actor de sesión, operación, compañía y referencias | Permiso y evento: actor, hora, interfaz, causa/código y correlación | Bloquear accesos indebidos; registrar eventos mínimos |
| **I08 `actualizar_seguimiento_crm`** | **Ventas → CRM** | **Decisión persistida, oportunidad y cotización/versionado** | **Respuesta, estado, causa, responsable, siguiente acción y plazo; fallo → rollback** | **Actualizar una proyección de seguimiento por solicitud; no cerrar oportunidad ni duplicar tareas en replay** |

WhatsApp → vendedor → CRM es registro manual. La ruta adaptador → UBLHUB → SUNAT es continuidad PC1; sus contratos tributarios no se inventan en esta revisión. I04/I06/I07 son funciones internas, no nuevos componentes desplegables.

## 3. Información contractual

[Schema I03](solicitud-pedido-v1.schema.json) y [schema de respuesta I03/I08](respuesta-pedido-v1.schema.json), Draft 2020-12; UTF-8 y campos cerrados. La solicitud incluye:

```json
{
  "contract_version": "1.1",
  "company_id": "MYS-DEMO",
  "request_id": "SOL-DEMO-001",
  "correlation_id": "COR-DEMO-001",
  "opportunity_id": "CRM-DEMO-001",
  "customer_id": "CLI-DEMO-001",
  "quotation_id": "COT-DEMO-001",
  "quotation_version": 1,
  "acceptance_id": "ACE-DEMO-001"
}
```

IDs: 1–64 caracteres ASCII, letras, números, guion o guion bajo; versión de cotización entera positiva. `request_id` es clave idempotente por compañía; `correlation_id` une el recorrido. Compañía, oportunidad, cliente, cotización y aceptación deben coincidir entre sí y con la sesión. El mensaje no contiene precios, stock, rol ni booleanos de aprobación.

| Dimensión de S6, pp. 14–15 | Datos resueltos desde el sistema dueño | Regla del caso MYS |
| --- | --- | --- |
| Identidad | Cliente único, compañía, activo, identidad revisada; evidencia del canal con finalidad y vigencia | Consentimiento sintético solo para atender cotización por WhatsApp manual, no campañas masivas ni validación fiscal |
| Oferta | SKU/unidad, cantidad, precio, descuento, moneda, vigencia y versión | PEN; precio final sintético; cálculo `Decimal`, redondeo por línea a 2 decimales; aceptación exacta |
| Promesa | Pago, modalidad, lugar, fecha solicitada, aceptación de entrega parcial | Contado y recojo `ALM-DEMO`; fecha solicitada no equivale a fecha prometida. Crédito u otras condiciones requieren validación |
| Trazabilidad | Oportunidad → cotización/versionado → aceptación → solicitud → respuesta → seguimiento/pedido futuro | No duplicar la cotización al convertirla; `response_id` identifica la revisión de decisión |
| Gobernanza | Actor, autorización de excepción, estado/causa, responsable, acción, plazo y eventos | Descuento >5 % requiere Gerencia independiente; atención de excepción en 24 h es supuesto, no SLA real |

Cambiar oferta o promesa relevante exige nueva versión, aceptación y autorización aplicable. Las referencias del mensaje resuelven ese snapshot; no se omiten condiciones por no transportarlas duplicadas en JSON.

## 4. Orden de validación y estados

1. Validar schema y sesión autorizada para compañía/oportunidad antes de consultar caché.
2. Comprobar clave y huella del JSON normalizado: misma solicitud/contenido devuelve resultado; contenido distinto genera `IDEMPOTENCIA_CONFLICTO`; otra clave para la misma cotización/versión genera `COTIZACION_YA_EVALUADA`.
3. Verificar vínculos, cliente, finalidad/canal/vigencia, pago y entrega; luego versión actual, estado `sent`, vigencia y aceptación exacta.
4. Recalcular catálogo, precio y total. Verificar aprobación de Gerencia cuando supera 5 %, con versión/total/vigencia exactos y persona distinta del vendedor. Este control precede al stock.
5. Consultar disponibilidad agregada por SKU: lectura fallida → `PENDIENTE`; cantidad insuficiente → `PROMESA_CONDICIONADA`; controles superados → `ACEPTADA`.
6. Persistir decisión, proyección CRM y eventos juntos. Error al actualizar seguimiento revierte la transacción completa.

| Estado de solicitud | Código principal / significado | Seguimiento y responsable | Recuperación |
| --- | --- | --- | --- |
| ACEPTADA | VALIDADA: controles superados | SIN_TAREA; Ventas informa resultado | Confirmación operativa futura con nueva validación, fuera de PC2 |
| RECHAZADA | DESCUENTO_SIN_APROBACION | PENDIENTE_APROBACION; Gerencia decide en plazo supuesto | Mantener oportunidad; nueva versión/aceptación/solicitud después de resolver |
| RECHAZADA | CLIENTE_NO_VALIDADO, DATOS_INCONSISTENTES, CONTACTO_NO_AUTORIZADO, CONDICIONES_POR_VALIDAR | CORREGIR_DATOS; Ventas | Corregir fuente oficial; nueva evaluación/versionado aplicable |
| RECHAZADA | VERSION_OBSOLETA, COTIZACION_NO_ENVIADA, COTIZACION_VENCIDA, ACEPTACION_INVALIDA, PRECIO_INVALIDO | CORREGIR_DATOS; Ventas | Preparar versión válida y nueva aceptación |
| RECHAZADA | CONTRATO_INVALIDO / NO_AUTORIZADO | CORREGIR_DATOS / REVISAR_ACCESO | No crea solicitud comercial ni proyección CRM; solo denegación mínima |
| RECHAZADA | IDEMPOTENCIA_CONFLICTO / COTIZACION_YA_EVALUADA | CONSULTAR_ORIGINAL | No sobrescribe decisión ni seguimiento original |
| PROMESA_CONDICIONADA | DISPONIBILIDAD_PARCIAL | NEGOCIAR_PROMESA; Ventas con Almacén | Revisar cantidad/plazo con cliente; nueva versión y aceptación; fecha desconocida permanece nula |
| PENDIENTE | DEPENDENCIA_NO_DISPONIBLE | RECUPERAR_SERVICIO; Administración y Ventas | Recuperar servicio y reanudar explícitamente misma solicitud; revalidar versión vigente |

`RECIBIDA` es un evento transaccional, no un estado final del schema. Solo `PENDIENTE` admite reanudación; los demás resultados se conservan como evidencia histórica. Añadir una aprobación después del rechazo no sobrescribe ese resultado.

## 5. Respuesta y retorno a CRM

Todas las respuestas incluyen versión, `response_id`, solicitud/correlación, cotización/versión, estado/código/mensaje, responsable, acción, plazo, seguimiento, total/moneda, condiciones y referencia/estado de pedido. Referencias nulas solo cuando el mensaje no es estructuralmente válido. Los errores de acceso y conflictos devuelven respuesta al llamante sin publicar datos en CRM.

En stock parcial, `conditions` precisa SKU, solicitado, disponible, pendiente, modalidad/lugar, fecha solicitada, `promised_date:null` y necesidad de aceptación de nuevas condiciones. Una lectura fallida no ofrece cantidades como si fueran confiables.

**Dos estados distintos:** `status=ACEPTADA` valida la solicitud; `order_state=CONFIRMADO` requiere pedido operativo real. El perfil simulado siempre devuelve `order_state=NO_CONFIRMADO` y `order_id=null`. El schema admite `order_id` no nulo únicamente con `CONFIRMADO` y solicitud `ACEPTADA`, para la continuidad posterior; validar esa forma no demuestra una confirmación implementada.

I08 mantiene en SQLite `crm_feedback`, una proyección por compañía/solicitud con `opportunity_lost:false`. El rechazo genera seguimiento de aprobación, no marca la oportunidad como perdida. La consulta de seguimiento aplica el mismo control de acceso que la consulta de solicitud. Un replay devuelve la decisión previa y no publica otra tarea; una reanudación pendiente actualiza la misma proyección y conserva eventos anteriores. Es una representación local, no un módulo ni una notificación de Odoo ejecutada.

## 6. Seguridad, persistencia y evidencia

La huella SHA-256 usa JSON canónico y normaliza versión numérica a entero. SQLite aplica `BEGIN IMMEDIATE`, clave primaria y unicidad de cotización/versión. Cada decisión nueva se guarda con I07 y actualización I08; el replay agrega solo evento de reintento. Producción requerirá equivalente ORM/PostgreSQL, permisos, versionado y protección de confirmaciones por interfaz, importación y automatización; ocultar botones no basta.

No hay datos reales de clientes ni credenciales. El plazo de 24 h, el consentimiento sintético, contado/recojo y la política 5 % son supuestos por validar, no reglas verificadas de MYS. [Fuentes y decisiones](../../fuentes/pc2.md), [pruebas reproducibles](../../pruebas/pc2/README.md), [calibración Andina](../../documentos/pc2/calibracion-andina-s6.md) y [dos métricas S6](../../documentos/pc2/metricas-s6.md).
