# PC2 · incremento acumulado del Grupo 7

**Curso:** GE703, Sistemas Integrados Empresariales, 2026-2.  
**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C.  
**Versión:** v2.0 · **Fecha del documento:** 15/10/2026 · **Exposición:** 17/10/2026.  
**Evidencias:** [índice del paquete en este repositorio](README.md). **Remoto configurado:** [jharopr/ERP-SIE](https://github.com/jharopr/ERP-SIE). Los cambios de este incremento están en el espacio de trabajo local y todavía deben publicarse para que el remoto los muestre.  
**Expositores propuestos:** Gabriel Chavez y Jharolym Paucarcaja; falta ratificación e inscripción por el grupo.  
**Estado:** propuesta técnica y pruebas locales simuladas; revisión humana pendiente, sin Odoo instalado.

## 1. Incremento desde PC1

PC1 seleccionó Odoo como núcleo de clientes, ventas e inventario, con UBLHUB como servicio de emisión electrónica y dos canales: presencial y WhatsApp móvil atendido por una persona. PC2 incorpora la etapa previa a la operación: fuente comercial, lead, oportunidad, cotización y solicitud gobernada hacia el ERP.

| Decisión PC1 | PC2 mantiene o modifica | Justificación / evidencia |
| --- | --- | --- |
| Odoo como ERP central | Mantiene y amplía con CRM de Odoo | Conserva plataforma y maestros; [arquitectura PC2](../../arquitectura/crm-erp-pc2.md) |
| WhatsApp registrado manualmente | Mantiene | El vendedor registra captación y oportunidad; no se presupone API de WhatsApp |
| Dos canales comerciales | Mantiene como contexto | La prueba PC2 usa solo el caso WhatsApp autorizado |
| Cotizaciones y pedidos en Ventas | Precisa frontera y sistemas de registro | CRM mantiene oportunidad; Ventas conserva cotización y futura conversión en el mismo `sale.order` |
| UBLHUB como servicio documental | Mantiene como continuidad posterior | Facturación y ruta tributaria quedan fuera de PC2 |
| Captación/campañas fuera de la primera liberación operativa | Añade escenario didáctico PC2 | Modela fuente y campaña sin afirmar una campaña ejecutada ni ampliar el despliegue real |
| Seguridad e idempotencia | Extiende al contrato comercial | Se proponen C04/C06 y bitácora específica; no son módulos ya instalados |

El [mapa y SIPOC O2C/P2P](../../procesos/pc2-escenario-y-flujo.md#4-macroprocesos-de-contexto) se conservan como contexto de Semana 5. El Word de macroprocesos anterior limitaba su versión a canal físico; este incremento declara expresamente el caso WhatsApp, sin reemplazar silenciosamente los límites históricos.

## 2. Escenario comercial y transición CRM–ERP

La campaña hipotética `CAM-DEMO-AUTORADIOS` origina una consulta por WhatsApp. El vendedor registra el lead, su fuente y referencia de atención; lo califica por necesidad concreta y cantidad; busca al cliente, resuelve coincidencias y convierte el lead en oportunidad. Prepara en Ventas una cotización de cinco autoradios genéricos a S/400.00 por unidad, con vigencia y versión identificadas.

En el caso normal se aplica el descuento didáctico autorizado al vendedor del 5 %: S/2,000.00 − S/100.00 = **S/1,900.00**. El cliente acepta esa versión y el vendedor solicita evaluar la transición. Con ocho unidades disponibles y todos los controles válidos, el contrato devuelve `ACEPTADA` y `VALIDADA`.

La excepción prioritaria solicita 10 % de descuento, total **S/1,800.00**, sin aprobación de Gerencia. Aunque exista aceptación del cliente, la política propuesta no está satisfecha: la solicitud se rechaza y se escala. La aceptación del cliente no sustituye la autorización de la empresa.

Si solo existen tres unidades, una cotización válida y autorizada puede recibir `PROMESA_CONDICIONADA`. Se comunica cantidad observada y necesidad de renegociar; no se inventa una fecha de reposición ni se acepta el cambio por el cliente. [Escenario, flujo por responsabilidades y casos de uso](../../procesos/pc2-escenario-y-flujo.md).

## 3. Contrato de transición CRM–ERP

![Arquitectura de componentes que gobierna el contrato](../../arquitectura/diagramas/componentes-crm-erp-pc2.svg)

La [arquitectura](../../arquitectura/crm-erp-pc2.md) separa **C01 CRM**, **C02 Contactos**, **C03 Ventas/catálogo**, **C04 control de transición**, **C05 Inventario**, **C06 autorizaciones**, **C07 seguridad/bitácora** y **C08 persistencia**. C04/C06 y el historial específico son extensiones propuestas para Odoo; los proveedores del simulador son fixtures locales.

Las interfaces quedan fijadas por ese diagrama: I01 resuelve cliente; I02 prepara cotización; I03 solicita/consulta transición; I04 lee el snapshot y la aceptación; I05 consulta disponibilidad; I06 verifica aprobación; I07 autoriza y audita. Son interfaces internas entre módulos, no endpoints REST publicados.

I03 transmite versión de contrato, compañía, solicitud, correlación, oportunidad, cliente, cotización/versionado y aceptación. Los precios y permisos no provienen del payload. El servidor obtiene identidad de sesión, comprueba acceso y consulta las fuentes oficiales. La matriz de datos y controles se desarrolla en [modelo y controles](../../datos/pc2-modelo-y-controles.md).

La [especificación completa](../../arquitectura/contratos/crm-erp-v1.md) define orden de validación, estados, acciones y recuperación. Los [schemas](../../arquitectura/contratos/solicitud-pedido-v1.schema.json) hacen explícito el formato cerrado. La clave `(company_id, request_id)` evita reejecutar una solicitud; la unicidad de cotización/versión impide duplicarla usando otra clave. Un resultado final no se sobrescribe y se audita junto con su decisión.

**Distinción de cierre:** `ACEPTADA` valida la solicitud; `RECHAZADA` expresa un incumplimiento; `PROMESA_CONDICIONADA` propone revisar condiciones; `PENDIENTE` indica falta de una lectura técnica confiable. En todos los casos `order_id` es `null`. La confirmación operativa posterior debe volver a validar los datos y usar la cotización existente, sin generar un segundo `sale.order`.

## 4. Prueba del contrato

Se ejecuta una simulación local con Python y SQLite, maestros sintéticos, un reloj comercial fijo y reglas explícitas. [Instrucciones, precondiciones, pasos y resultados obtenidos](../../pruebas/pc2/README.md). La fecha real y los hashes están en el [manifiesto de ejecución](../../pruebas/pc2/evidencias/ejecucion.json).

| Caso | Entrada / precondiciones | Estado y respuesta esperados | Evidencia obtenida | Responsable del siguiente paso |
| --- | --- | --- | --- | --- |
| PC2-N01, normal | Cotización vigente, aceptación, 5 %, ocho unidades y Ventas autorizado | ACEPTADA / VALIDADA, S/1,900.00, sin pedido operativo | [PC2-N01](../../pruebas/pc2/evidencias/PC2-N01.json) | Ventas; confirmación en otro incremento |
| PC2-E01, excepción | Cotización aceptada al 10 %, sin aprobación válida | RECHAZADA / DESCUENTO_SIN_APROBACION | [PC2-E01](../../pruebas/pc2/evidencias/PC2-E01.json) | Gerencia decide; Ventas versiona y recoge nueva aceptación |
| PC2-P01, complementario | Cotización normal pero solo tres unidades | PROMESA_CONDICIONADA / DISPONIBILIDAD_PARCIAL | [PC2-P01](../../pruebas/pc2/evidencias/PC2-P01.json) | Ventas/Cliente revisan; Almacén informa disponibilidad |
| PC2-T01, complementario | Proveedor de disponibilidad no accesible | PENDIENTE / DEPENDENCIA_NO_DISPONIBLE | [PC2-T01](../../pruebas/pc2/evidencias/PC2-T01.json) | Administrador recupera; Ventas reanuda misma solicitud |

La suite verifica además duplicidad, conflictos de clave, acceso por rol y compañía, versión/aceptación inválidas, precio alterado, aprobación independiente, recuperación, concurrencia local y rollback. Los resultados automatizados están en [unittest.txt](../../pruebas/pc2/evidencias/unittest.txt). Las simulaciones no ejecutan Odoo ni prueban sus ACL o inventario real.

## 5. Fuentes, límites y continuidad

Se distinguen **requisitos** de rúbrica/plantilla, **decisiones del equipo** autorizadas en la conversación, **supuestos didácticos** de campaña/precios/descuentos y **evidencia** generada por la simulación. Las fuentes oficiales, secciones, fecha de consulta, hashes de insumos y decisiones están en el [registro PC2](../../fuentes/pc2.md).

Se utilizó Codex para analizar los insumos, proponer la arquitectura, redactar contratos y datos, crear el SVG/Mermaid y programar/ejecutar la simulación. No se utilizó un agente comercial en la operación. La [declaración de IA](../../fuentes/uso-ia.md) identifica propósito, datos y validación humana pendiente. No se incluyeron datos personales de clientes ni credenciales.

Queda pendiente validar el negocio y configurar Odoo, elegir edición/alojamiento, implementar las extensiones, asegurar todas las rutas de confirmación y repetir pruebas sobre ORM/PostgreSQL. Posteriormente se desarrollarán el pedido operativo, reservas, pago, emisión mediante UBLHUB, entrega y posventa. Una prueba local superada no se presenta como despliegue ni aceptación empresarial.

### Participación y cierre de entrega

El [reparto actualizado](../contribuciones.md) asigna revisión y evidencia a los seis integrantes. Los archivos fueron preparados con asistencia de IA; cada persona debe registrar su revisión efectiva antes de afirmar su aporte. Gabriel y Jharolym son expositores propuestos. La publicación del incremento y la inscripción de los dos expositores requieren verificación del grupo; no se ha realizado ninguna publicación externa.
