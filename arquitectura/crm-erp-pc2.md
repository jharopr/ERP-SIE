# Arquitectura de componentes CRM–ERP · PC2

**Vista del parcial:** consultar la [arquitectura del cliente nuevo en tienda física](crm-erp-ep.md). Este archivo conserva el antecedente técnico preparado durante PC2; su diagrama histórico no sustituye la delimitación comercial de [PC2 v2.1](../documentos/pc2/entrega-pc2.md).

**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C. · **Versión:** PC2 v2.0, contrato 1.0 · **Fecha:** 15/10/2026.  
**Responsable de revisión propuesto:** Jharolym Paucarcaja, coordinado con Gabriel Chavez.  
**Estado:** diseño propuesto y simulación local. No hay una instalación de Odoo acreditada.

## 1. Decisión y frontera

Se incorpora **CRM de Odoo** al ERP seleccionado en PC1. Contactos, CRM, Ventas e Inventario comparten la plataforma y sus mecanismos de acceso. La integración es **entre módulos**, mediante llamadas al ORM dentro de Odoo; no se propone otro CRM, un microservicio comercial ni una API REST pública.

CRM es dueño de la captación y oportunidad. Ventas es dueño de la cotización y de su futura conversión en pedido. La acción «Nueva cotización» iniciada desde CRM utiliza el registro de Ventas. El contrato regula la solicitud de esa transición y la decisión de aceptarla, rechazarla o emitir una promesa condicionada. [F-PC2-04, F-PC2-05 y F-PC2-07](../fuentes/pc2.md).

**Fin evaluable:** solicitud evaluada y respuesta registrada. `ACEPTADA` significa que la solicitud superó los controles; **no significa que ya exista un pedido operativo**. En PC2 `order_id` es siempre `null`, no se ejecuta `action_confirm`, no se reserva stock y no se invoca UBLHUB. La futura confirmación deberá revalidar vigencia, disponibilidad y autorización en una transacción propia. Así, una decisión de hoy no garantiza existencias para mañana.

## 2. Diagrama que gobierna los contratos

![Componentes CRM–ERP de PC2 con sus siete interfaces](diagramas/componentes-crm-erp-pc2.svg)

[Fuente editable Mermaid](diagramas/componentes-crm-erp-pc2.mmd). Los identificadores **C01–C08** y **I01–I07** se conservan en [contratos](contratos/crm-erp-v1.md), [modelo de datos](../datos/pc2-modelo-y-controles.md) y [pruebas](../pruebas/pc2/README.md). Las flechas representan uso de interfaces, incluyendo su respuesta; no tráfico HTTP ni servidores diferentes.

## 3. Componentes y sistemas de registro

| ID | Componente | Registro oficial / responsabilidad | Tipo y límite |
| --- | --- | --- | --- |
| C01 | CRM | `crm.lead`: lead y oportunidad, responsable, campaña, fuente, medio y referencia de atención | Estándar de Odoo; etapas del caso por configurar |
| C02 | Contactos | `res.partner`: identidad única del cliente y contacto autorizado | Estándar; política de deduplicación propuesta |
| C03 | Ventas y catálogo | `sale.order`, `sale.order.line`, productos y listas de precios: cotización, líneas, moneda y vínculo a oportunidad | Estándar; versionado, aceptación y bloqueo de bypass requieren extensión |
| C04 | Control de transición | `mys.crm.transition`: solicitud, versión de contrato, huella, estado y resultado | **Extensión propuesta**, no módulo instalado; único dueño de la decisión de transición |
| C05 | Inventario | Disponibilidad por SKU, compañía y ubicación, con fecha de consulta | Estándar consultado; PC2 no reserva, entrega ni modifica existencias |
| C06 | Autorizaciones comerciales | `mys.discount.approval`: decisión humana vinculada a cotización, versión, importe y aprobador | **Extensión propuesta**; no se presume un flujo estándar ya configurado |
| C07 | Seguridad y bitácora | Identidad de sesión, grupos, reglas por registro/compañía; `mys.transition.event` para el historial específico | Accesos estándar + bitácora de transición propuesta; la bitácora nativa por sí sola no acredita inmutabilidad |
| C08 | Persistencia Odoo / PostgreSQL | Maestros, transacciones y restricciones de unicidad | C01–C07 acceden mediante ORM; ningún cliente recibe credenciales de base de datos |

Los modelos `mys.*`, `quotation_version`, el snapshot de aceptación y el control obligatorio del botón Confirmar son diseño del proyecto. Su implementación y compatibilidad con la edición/alojamiento elegidos quedan pendientes. La simulación usa JSON y SQLite para representar estos límites; no reemplaza el ORM ni demuestra sus permisos.

En Odoo `crm.lead.type` distingue lead de oportunidad. La relación de una cotización con una oportunidad se registra mediante `sale_crm`. Una cotización confirmada cambia de estado dentro de `sale.order`; **no corresponde duplicarla para crear otro pedido**. [F-PC2-07 y F-PC2-08](../fuentes/pc2.md).

## 4. Interfaces derivadas de las dependencias

| Interfaz | Consumidor → proveedor | Operación conceptual | Resultado y control clave |
| --- | --- | --- | --- |
| I01 | C01 → C02 | Buscar/vincular cliente | Ficha existente o alta revisada; coincidencia ambigua bloquea transición |
| I02 | C01 → C03 | Preparar/vincular cotización | Referencia y versión de cotización, con líneas y precios oficiales |
| I03 | C01 → C04 | Solicitar transición / consultar resultado | Contrato JSON 1.0; autorización, idempotencia y correlación |
| I04 | C04 → C03 | Leer snapshot comercial y aceptación | Precio, total, vigencia, cliente, oportunidad y versión confiables; no se aceptan importes del solicitante |
| I05 | C04 → C05 | Consultar disponibilidad | Cantidad observada y ubicación; una consulta no es reserva ni compromiso de fecha |
| I06 | C04 → C06 | Verificar aprobación | Aprobación vigente, de gerencia y de la misma versión; sin autoaprobación |
| I07 | C01–C06 → C07 | Autorizar acción y registrar evento | Actor de sesión, permisos, compañía, código, correlación y fecha; la identidad no se toma del JSON |

El detalle de entradas, salidas, errores, mutaciones y responsabilidades está en la [especificación de interfaces y contrato](contratos/crm-erp-v1.md). C08 es persistencia interna, no una octava interfaz comercial. La relación posterior Ventas → adaptador → UBLHUB se conserva como contexto de PC1, con trazo discontinuo en el diagrama.

## 5. Reglas arquitectónicas

1. **Maestros únicos:** C02 conserva clientes; C03 conserva productos, precios y cotizaciones. CRM mantiene referencias, no copias editables de estos maestros.
2. **Precios del servidor:** I03 contiene identificadores; C04 obtiene por I04 las líneas y aceptación de la versión exacta. No acepta un descuento, rol o aprobación declarados por el cliente.
3. **Control central:** una futura implementación debe bloquear confirmaciones manuales, importaciones, RPC y automatizaciones que omitan C04; ocultar un botón no basta.
4. **Operación única:** `(company_id, request_id)` identifica el reintento y `(company_id, quotation_id, quotation_version)` impide evaluar dos solicitudes distintas de la misma versión. La correlación sirve para rastrear; no reemplaza la clave idempotente.
5. **Actualización explícita:** una cotización corregida genera nueva versión, aceptación y solicitud. Una promesa no acepta automáticamente cantidades o plazos nuevos.
6. **Atomicidad:** solicitud, decisión y eventos se guardan en una misma transacción. En producción se requieren restricciones únicas y bloqueo de la versión/snapshot; el stock se vuelve a comprobar al confirmar operativamente.
7. **Permisos por compañía y oportunidad:** se verifica acceso antes de consultar incluso un resultado idempotente. No se autoriza con un `actor_role` enviado por el usuario ni con elevación indiscriminada de permisos. [F-PC2-06](../fuentes/pc2.md).
8. **Falla técnica visible:** inventario no disponible produce `PENDIENTE`, no `ACEPTADA` ni rechazo comercial. Se consulta y reanuda la misma solicitud; no se crea otra operación para reintentar.

## 6. Responsabilidades y revisión

| Actividad | Ejecuta | Aprueba / responde | Evidencia |
| --- | --- | --- | --- |
| Registrar captación y calificar | Ventas | Responsable comercial | Campaña, referencia de atención y oportunidad |
| Identificar cliente | Ventas | Responsable comercial | Ficha vinculada; revisión de coincidencias |
| Cotizar y registrar aceptación | Ventas | Cliente acepta la versión; gerencia aprueba la excepción | Snapshot, vigencia, referencia de aceptación |
| Evaluar solicitud | C04 bajo identidad autorizada | Responsable comercial | Solicitud, reglas y respuesta |
| Resolver descuento excepcional | Gerencia | Gerencia, sin autoaprobación | Decisión vinculada a versión y vendedor |
| Informar stock insuficiente | Ventas con información de almacén | Cliente decide si acepta nuevas condiciones | Promesa condicionada y posterior cotización revisada |
| Recuperar indisponibilidad | Administrador técnico | Responsable comercial valida el resultado | Solicitud original y evento de reanudación |

Benjamin revisa continuidad PC1–PC2; Shirley el escenario y sus fuentes; Gabriel el contrato; Jharolym componentes e interfaces; Adrian el flujo y prueba normal/excepción; Ballack el diccionario y evidencia. Son responsabilidades de revisión asignadas, **no validaciones ya realizadas**.

## 7. Decisiones pendientes de implementación

- Elegir versión, edición, alojamiento y compatibilidad de módulos; Odoo 19 es referencia documental, no instalación existente.
- Implementar `mys.*`, snapshot/versionado, restricciones y protección de todas las rutas de confirmación.
- Configurar roles, reglas multiempresa y pruebas reales de acceso, bloqueo y concurrencia en Odoo/PostgreSQL.
- Validar campaña, precio, descuento, disponibilidad y reglas con la empresa.
- Definir retención y protección de evidencias; medir tiempos de respuesta antes de prometer un SLA.
- Ejecutar la confirmación operativa, reservas, pago, facturación, entrega y posventa en incrementos posteriores.
