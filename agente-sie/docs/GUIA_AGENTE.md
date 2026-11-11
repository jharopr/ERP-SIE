# Guía del Agente SIE · PC3 · G7 Importaciones MYS Hermanos

> Datos **sintéticos**. El agente **acompaña** al ERP y no lo reemplaza: Odoo es el sistema de registro, las reglas viven en código determinista (la compuerta) y el modelo de lenguaje solo interpreta, llama herramientas, explica y escala.

## Propósito
Ayudar al vendedor a llevar una cotización aceptada hasta una **respuesta trazable del ERP**. El agente explica el resultado, escala al dueño las excepciones y deja todo en la bitácora. **No confirma pedidos, no reserva stock, no aprueba descuentos y no promete fechas** (`order_id = null` y `promised_date = null` siempre).

## Entradas
| Entrada | Ejemplo | Origen |
|---|---|---|
| Mensaje del vendedor en el chat (W1) | «CLI-DEMO-001 aceptó COT-DEMO-001 v1 (ACE-PC3-001). Envía SOL-PC3-N01 con COR-PC3-001» | Chat de n8n |
| Referencias | CLI, OPP, COT y su versión, ACE, SOL y COR | Las da el vendedor; el agente no las inventa |
| Registros de Odoo | `res.partner`, `crm.lead`, `sale.order` y sus líneas, `stock.quant` | XML-RPC, solo lectura |
| Registros de la compuerta | aceptaciones, aprobaciones, señales REP, escalamientos y bitácora | SQLite de la compuerta |

## Salidas
- **Respuesta tipificada** v1.0, con `status`, `code`, `responsible_role`, `required_action`, `total` y `conditions`, explicada en español con el bloque *Resultado · Motivo · Quién actúa · Siguiente paso · IDs*.
- **Señal de reposición** `REP-PC3-00n` cuando falta stock. Se calcula como faltante = max(0, pedido − disponible), lleva `automatic_action = false` y no compra ni reserva nada.
- **Escalamiento** `ESC-PC3-00n`. W2 avisa al dueño **por correo automático** con botones de decisión; si el correo falla, el agente entrega los enlaces para reenviarlos.
- **Borrador de mensaje al cliente**, sin fechas ni compromisos que el ERP no haya dado.
- **Eventos en la bitácora**.

## Fuentes
- **Odoo 18 Community**: contactos, CRM, ventas e inventario.
- **Base de la compuerta**: aceptaciones (extensión C03), aprobaciones (C06), actores, política, mapa de IDs, señales REP, escalamientos, decisiones del dueño y bitácora.

Todos los datos son sintéticos ([DATOS_SINTETICOS.md](../datos_prueba/DATOS_SINTETICOS.md)).

## Herramientas del agente (W1)
Todas son *HTTP Request Tool* hacia `http://compuerta:8000` y usan la credencial **Compuerta VENTAS**. Ninguna escribe en Odoo.

| Herramienta | Llamada | Efecto |
|---|---|---|
| `consultar_cliente` | `GET /clientes/{ref}` | Lectura. Devuelve el estado del cliente sin datos personales |
| `consultar_cotizacion` | `GET /cotizaciones/{id}/{v}` | Lectura. Devuelve líneas, total de Odoo, vigencia, versión vigente y aceptaciones |
| `consultar_disponibilidad` | `GET /disponibilidad/{sku}` | Lectura. Devuelve físico, reservado y disponible; un 503 significa «no verificado» |
| `enviar_solicitud_i03` | `POST /solicitudes` | Evalúa con R01–R12 y la crea REP si corresponde. **No crea pedidos** |
| `consultar_solicitud` | `GET /solicitudes/{id}` | Lectura de la respuesta guardada |
| `reanudar_solicitud` | `POST /solicitudes/{id}/reanudar` | Reevalúa solo si está PENDIENTE |
| `ver_bitacora` | `GET /bitacora?correlation_id=` | Lectura |
| `consultar_escalamiento` | `GET /escalamientos/{id}` | Lectura. Es la única prueba válida de una decisión del dueño |
| `escalar_al_dueno` | *Call n8n Workflow Tool* → W2 → `POST /escalamientos` → correo al dueño | Registra que la excepción espera al dueño y le avisa por correo. **No decide** |

El agente **no tiene** ninguna herramienta para aprobar ni para decidir reposiciones.

## Reglas
Las reglas R01–R12 del contrato CRM–ERP v1.0 se aplican **en la compuerta**, que reutiliza `TransitionSimulator` sin cambios; el modelo de lenguaje no las aplica. El orden es: contrato → autorización → idempotencia → vínculos → cliente → versión → estado → vigencia → aceptación → precios → descuento (tope del 5 %) → disponibilidad.

## Permisos
| Rol (token) | Quién lo usa | Puede | No puede |
|---|---|---|---|
| **VENTAS** | Agente (W1), W2 al registrar el escalamiento, W3 | Consultar, enviar I03, reanudar, escalar, ver la bitácora | Aprobar (403 + evento DENEGADA), decidir reposiciones, administrar |
| **GERENCIA** | Solo W2, cuando el **dueño** envía el formulario | Aprobar o rechazar descuentos, decidir reposiciones | Enviar I03 |
| **ADMIN** | Administrador de la demo | Reiniciar, simular la caída de Odoo, ver la bitácora | Aprobar |

El rol sale del token y **nunca del cuerpo** de la petición. `approver_id` también sale del token y debe ser distinto del vendedor.

## Responsable humano
- **Vendedor VEN-DEMO-01**: comunica el resultado al cliente.
- **Dueño GER-DEMO-01**: decide los descuentos mayores al 5 % y las reposiciones.
- **Administrador ADM-DEMO-01**: recupera las dependencias caídas.

## Escalamiento
| Código | Destinatario | Mecanismo | Decisiones |
|---|---|---|---|
| `DESCUENTO_SIN_APROBACION` | Dueño | W2: correo con botones → formulario `/form/decision-dueno` (1 clic) | APROBADA / RECHAZADA. La aprobación vale **solo para la versión siguiente** (v3), con una nueva aceptación y una nueva solicitud |
| `DISPONIBILIDAD_PARCIAL` | Dueño y abastecimiento | W2: el mismo correo y formulario | OFRECER_PARCIAL / EVALUAR_REPOSICION / DESCARTAR |
| `DEPENDENCIA_NO_DISPONIBLE` | Administrador | El agente informa; el administrador recupera Odoo y luego se reanuda | — |
| `IDEMPOTENCIA_CONFLICTO` | Administrador y ventas | Se consulta la solicitud original | — |

Si el dueño no responde en **10 minutos**, `consultar_escalamiento` devuelve `SIN_DECISION`: «sin decisión, la oportunidad queda en seguimiento».

## Bitácora
Cada evento guarda `event_id`, `correlation_id`, `request_id`, interfaz (I03–I07, REP, ESC, C03, C06, AGENTE, API), tipo, código, actor, **`actor_type`** (HUMANO, AGENTE o SISTEMA) y hora de Lima.
- Las llamadas del agente registran una **huella**: herramienta, versión del flujo, versión del prompt y SHA-256 de la entrada. Nunca guardan el texto.
- La bitácora **nunca guarda nombres, DNI ni teléfonos**.

Ejemplo de secuencia para COR-PC3-002: `RECIBIDA → CONSULTA (I04) → CONSULTA (I06) → CONSULTA (I05) → SENAL_REP → DECISION → ESCALADO → DECISION_DUENO`.

## Límites
- Las cifras las da Odoo o la compuerta; el modelo no calcula montos ni stock.
- El modelo puede equivocarse al redactar. La decisión válida es siempre la respuesta tipificada de la compuerta.
- No hay confirmación operativa del pedido, facturación (UBLHUB) ni integración con WhatsApp: corresponden a incrementos posteriores.
- Las vigencias cierran a las 18:00 del día del seed. Fuera de ese horario hay que ejecutar `demo_reset` o ajustar `COTIZACION_HORA_CIERRE`.

## Próximos pasos
1. Confirmación operativa del pedido en Odoo, con nueva revalidación de stock y aprobación.
2. Canal del dueño por Telegram o correo (*Send and Wait*), con credencial propia del equipo.
3. Señal REP conectada a compras o P2P.
4. Persistencia de la compuerta en PostgreSQL y tokens con vencimiento (OIDC).
