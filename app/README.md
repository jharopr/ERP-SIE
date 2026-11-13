# MYS · Sistema integrado en Odoo

**La entrada única es http://localhost:8088.** Odoo 18 Community muestra el menú lateral de MS Power Audio / Importaciones MYS Hermanos: Contactos, Leads, CRM / Oportunidades, Inventario, Cotizaciones, Ventas, Catálogo, Evaluación comercial, Decisiones del dueño, Trazabilidad y Agente SIE.

El portal anterior fue sustituido por vistas y componentes nativos del addon `mys_erp`. Se conserva como referencia en `legacy/portal/`, sin publicarse. El agente existente continúa en `agente-sie/`; conserva el motor R01–R12, el contrato I03 de nueve campos y los cuatro estados. El catálogo completo (167 productos) procede del Excel suministrado; las primeras 50 referencias son las de demostración. Clientes, stock y operaciones son de prueba. Además se conservan dos SKU académicos.

## Ingreso

Las cuentas humanas de esta demostración tienen **contraseña igual al usuario**, conforme al requisito:

| Rol | Usuario | Contraseña | Función |
| --- | --- | --- | --- |
| Vendedor | `vendedor01` | `vendedor01` | Contactos, leads, oportunidades, cotizaciones, evaluación y solicitud de excepciones |
| Dueño / Gerencia | `gerente` | `gerente` | Revisión de resultados y aprobación o rechazo de excepciones |
| Administrador | `admin` | `admin` | Configuración y administración de Odoo |

**Agente SIE no tiene usuario ni contraseña propios.** Se abre en el menú lateral de Odoo y utiliza la sesión y el rol actuales. Ventas solicita; el dueño aprueba manualmente en su módulo. El chat no puede aprobar, incluso desde una sesión del dueño.

La cuenta técnica `sie-lectura`, PostgreSQL, el puente y n8n mantienen secretos distintos, privados en `.env`. El editor n8n es una herramienta administrativa; no se necesita para operar el sistema.

## Iniciar, cerrar y volver a levantar

Requisitos: Docker Desktop iniciado, Docker Compose v2, Python 3.10+ y conexión a Internet en la primera instalación. Desde esta carpeta `app/`:

```powershell
python scripts/iniciar.py
```

El script prepara variables faltantes, comprueba PostgreSQL, actualiza el addon en una base existente, sincroniza las contraseñas humanas, inicia los servicios y publica el chat privado W4. **Un arranque normal conserva cotizaciones, versiones, evaluaciones, decisiones y stock existentes**. No refresca operaciones ni inventarios de una instalación ya cargada.

Para apagar conservando los datos:

```powershell
docker compose stop
```

Para volver a levantar sin actualizar código:

```powershell
docker compose up -d --wait
```

Después de cambiar código, `.env` o una contraseña humana, ejecutar otra vez `python scripts/iniciar.py`. Recargar el navegador con `Ctrl+F5` y volver a iniciar sesión si cambió la contraseña. No usar `down -v`: elimina los volúmenes.

## Del lead a la cotización

**Contactos** contiene diez fichas ficticias con nombres peruanos, celular, teléfono, correo, dirección en Lima, ocupación, canal preferido y notas sobre la necesidad del cliente. Las tarjetas muestran los datos de atención; la lista permite buscar por nombre, teléfono o correo y agrupar por segmento o canal. En **Datos del cliente** se identifica el documento de ejemplo, separado del documento fiscal. La pestaña **Perfil comercial** muestra el nivel del cliente (nuevo, ocasional, frecuente o mayorista) calculado por Odoo con sus compras de los últimos 6 meses; ver [docs/PERFIL_CLIENTE.md](docs/PERFIL_CLIENTE.md). No corresponden a personas reales.

La carga actualiza las referencias `CLI-DEMO-001` a `CLI-DEMO-010` sin cambiar los IDs ni sus cotizaciones. Archiva únicamente los contactos automáticos `Cliente prueba nativa <hex>`; su historial sigue disponible. Los contactos creados manualmente, incluido Benja, se conservan. El arranque normal también sincroniza estas fichas sin reiniciar operaciones.

Leads y Oportunidades muestran títulos con la necesidad o los productos y el nombre del cliente. La referencia SIE es independiente del título: renombrar una oportunidad conserva sus aceptaciones y relaciones con el agente. Los clientes automáticos del historial también reciben nombres peruanos ficticios, conservando su condición de archivados. En Cotizaciones, **Productos / motivo** resume las líneas reales; el número, la versión y la referencia interna se conservan.

**Evaluación de esta versión** verifica las reglas de la oferta concreta (datos, vigencia, aceptación, descuento y stock). **Autorización del descuento** indica si el gerente permitió superar el 5 % para una versión e importe concretos. Una oferta rechazada puede mostrar **Aprobada para nueva versión** y el enlace **Versión autorizada**: su resultado histórico no cambia. La oferta nueva muestra **Aprobada para esta versión** y todavía requiere aceptación y evaluación. Si la oferta cambia y deja de coincidir con su autorización, muestra **Revisar aprobación**.

La lista de **Cotizaciones** resume esos controles en una sola columna **Estado comercial**. Muestra el siguiente paso: por evaluar, solicitar aprobación, pendiente del gerente, revisar autorización o disponibilidad, verificación pendiente, pendiente del cliente, requiere corrección, cotización vencida o lista para confirmar. Las ofertas sustituidas muestran **Reemplazada por S…**. **Estado del documento** permanece separado (borrador, enviada o cancelada). Al abrir la cotización, **Reglas comerciales SIE** conserva el detalle de evaluación, autorización, versión autorizada y la explicación del estado resumido.

El estado comercial se calcula al consultar: una oferta vencida deja de aparecer lista aunque nadie la haya editado. **Lista para confirmar** requiere la oferta vigente de la oportunidad, aceptación válida, evaluación ACEPTADA / VALIDADA y autorización del descuento cuando corresponde. La confirmación sigue comprobando las reglas y el stock en el servidor. Este resumen no cambia los estados del contrato, las decisiones ni las operaciones existentes. Los filtros de la lista permiten encontrar ofertas por su estado comercial.

En **Leads**, complete el cliente y agregue líneas en **Productos solicitados**. Seleccione producto y cantidad: el precio unitario, descuento de tarifa y subtotal se calculan con las reglas nativas de Ventas y la tarifa del cliente. El importe estimado se muestra sin impuestos; permite varios productos y no reserva stock.

Al **Convertir a oportunidad**, si existen cliente y productos, se crea una sola cotización en borrador vinculada a la oportunidad, con sus líneas y referencia `COT-MYS-L… v1`. También funciona al agregar productos a una oportunidad existente que todavía no tiene cotización. Las cotizaciones existentes se conservan y no se duplican.

El **ingreso esperado** utiliza el importe sin impuestos de la cotización vigente, convertido a la moneda de la compañía. Se actualiza al cambiar cantidades, precios, descuentos o versión. Antes de tener cotización utiliza el importe estimado del lead. Una vez generada la oferta, sus cambios se realizan desde Ventas; el detalle solicitado queda protegido en el lead.

La cotización se abre desde el botón nativo **Cotizaciones** de la oportunidad o desde **Seguimiento comercial → Cotización vigente**. Después se prepara/presenta, se registra la aceptación real del cliente y se evalúan las reglas.

## Demostrar un descuento y sus roles

1. Ingresar como vendedor y abrir **Cotizaciones**. Crear una cotización desde una oportunidad del CRM, o duplicar una de prueba. En la pestaña **Reglas comerciales SIE** se puede seleccionar la oportunidad. El cliente debe tener referencia y la casilla **Identidad revisada** en su ficha MYS.
2. Completar productos, cantidades, precios, descuento y vencimiento. Pulsar **1. Preparar / enviar**; esto marca la oferta como enviada y asigna una referencia de familia y versión. No envía un correo automáticamente.
3. Tras obtener la aceptación real del cliente, pulsar **2. Registrar aceptación**. Esto registra la evidencia indicada por el vendedor; no simula una firma del cliente.
4. Pulsar **3. Evaluar reglas**. Hasta 5 % no requiere excepción; más de 5 % produce `RECHAZADA / DESCUENTO_SIN_APROBACION` si no existe autorización válida. El resultado muestra motivo, siguiente paso, condiciones y correlación.
5. El vendedor pulsa **Solicitar decisión del dueño**. Puede seguir el estado, pero no ve botones de aprobar ni tiene permiso para invocarlos por RPC.
6. **El dueño recibe un aviso automático**: una tarea pendiente en Odoo (icono del reloj) y un correo con el resumen, el total verificado, el plazo y el botón **Abrir la decisión en Odoo**. Llega igual si la excepción se escaló con el botón o desde el chat del agente. El dueño ingresa con su cuenta, abre la decisión (o **Decisiones del dueño**), escribe el motivo y pulsa **Aprobar descuento** o **Rechazar descuento**. La solicitud tiene un plazo de diez minutos. Una solicitud vencida puede volver a escalarse desde la evaluación.
7. Si se aprueba, Odoo crea **una cotización nueva en borrador con versión siguiente**, mismo importe y vendedor. No crea un pedido confirmado. El vendedor abre esa versión, la prepara/envía, registra una **nueva aceptación** del cliente y evalúa de nuevo. La autorización vale solo para la versión y total exactos.

Una versión ya evaluada queda protegida contra cambios y borrado por las cuentas comerciales. Se corrige con **Nueva versión**. Una evaluación `PENDIENTE` se puede reanudar con el mismo botón de evaluar. Evaluar y aprobar descuentos siguen sin crear pedidos ni reservas. La venta requiere la acción humana separada **4. Confirmar venta**.

Para faltantes, el resultado es `PROMESA_CONDICIONADA`; el dueño puede indicar ofrecer parcial, evaluar reposición o descartar. Estas decisiones no ejecutan compras ni reservas.

## Cotizaciones, ventas y filtros

**Cotizaciones** muestra el estado del documento, la evaluación comercial (incluido Sin evaluar), la aprobación de descuento y la referencia con su versión. Una evaluación rechazada por descuento puede tener una solicitud pendiente del dueño; son estados separados. Los filtros permiten consultar borradores, enviadas, canceladas, resultados de evaluación y descuentos sin solicitud, pendientes, aprobados o rechazados.

**4. Confirmar venta** está disponible para el vendedor asignado cuando la oferta fue aceptada por las reglas. El servidor exige la oferta vigente de una oportunidad activa, la aceptación del cliente para sus condiciones exactas, la evaluación ACEPTADA / VALIDADA y, si supera el 5 %, la autorización de esa versión. La compuerta vuelve a comprobar las reglas con datos actuales, sin sustituir la evaluación original. Si caducaron las condiciones, la autorización o el stock, la venta no se confirma. Odoo verifica que todos los productos almacenables queden reservados en la misma transacción; si falla, revierte la confirmación completa.

**Ventas** muestra pedidos confirmados y conserva los que luego se cancelen, con facturación y entrega separadas. Confirmar no factura, cobra ni valida entregas. Las vistas comerciales comparten criterios de cliente, vendedor y fecha, y permiten agrupar por sus estados específicos; los filtros elegidos no se trasladan automáticamente entre pantallas.

## Trazabilidad por operación

Desde una cotización, venta, evaluación o decisión, pulse **Ver trazabilidad**. Se reúnen las versiones y registros vinculados a la oportunidad; también puede buscar por número S…, familia COT…, cliente, oportunidad o identificador de seguimiento. Se muestran creación, presentación, aceptación, reglas, escalamientos, motivos de las decisiones, revalidación y confirmación/cancelación, cuando esos eventos estén registrados.

Los filtros incluyen cliente, vendedor, fechas, versión, tipo de evento y responsable. Las horas se presentan en Lima. Los eventos de aceptación anteriores que no tenían correlación se consultan por familia de cotización. Para registros históricos sin fecha específica de decisión se identifica la fecha de última actualización disponible, sin inventar eventos. Si la compuerta no responde, se conserva el historial de Odoo y se avisa que faltan los eventos remotos. El vendedor consulta sus operaciones; gerencia consulta las de su compañía. La consulta se limita a 200 registros relacionados y avisa cuando se requiere precisar la búsqueda.

## Aviso al dueño por correo

Por defecto los correos llegan al buzón local **Mailpit**: http://localhost:8025, sin cuenta ni configuración. Para que lleguen a un correo real, complete en `app/.env`:

```dotenv
CORREO_DUENO=<correo del dueño>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SEGURO=true
SMTP_USUARIO=<cuenta>@gmail.com
SMTP_CLAVE=<contraseña de aplicación de 16 letras, no la clave normal>
```

y ejecute `python scripts/iniciar.py`. Los avisos automáticos de Odoo que genera la carga de datos («Te asignaron…», «Cambio de contraseña») se cancelan para no llenar el buzón; solo salen los avisos `[MYS]`. La tarea del dueño se cierra sola cuando decide o vence el plazo.

## Cómo se le habla al agente

Con palabras normales, **sin códigos**: el nombre del cliente o el número de cotización que muestra Odoo (S000…). El agente busca la cotización, su versión vigente y su aceptación, y arma la solicitud con los mismos identificadores que el botón «3. Evaluar reglas» (validar por chat o por botón da el mismo resultado). Si hay varias cotizaciones, pregunta cuál con productos y precios. Ejemplos:

- «Busca subwoofers Pioneer» · «¿Cuánto stock disponible hay de RAD-7BT?»
- «Carlos Alberto Condori Mamani aceptó su cotización, ¿me la validas?» · «Valida la S00007, el cliente la aceptó»
- «¿Quién es Carlos Alberto Condori Mamani y qué le puedo ofrecer?» (usa el perfil comercial y sugiere complementos)
- «¿Qué decidió el gerente sobre la S00007? Redáctame un mensaje para el cliente»
- Como gerente: «Resume las cotizaciones de José Luis Quispe Huamán con su % de descuento y el descuento en soles»

El agente no aprueba (ni siquiera en la sesión del gerente), no crea pedidos, no reserva stock ni promete fechas. `admin` es la cuenta técnica y tampoco puede aprobar.

## Agente integrado y estado de Gemini

Abrir **Agente SIE** desde Odoo. Ejemplos: «Busca radios con pantalla» o «Consulta la disponibilidad de RAD-7BT». El chat usa el catálogo y las herramientas existentes; los resultados se leen de Odoo y la compuerta.

En `app/.env`:

```dotenv
GEMINI_API_KEY=<clave de la cuenta de prueba>
GEMINI_MODEL=models/gemini-3.5-flash-lite
```

La clave suministrada está en el `.env` local y en la credencial cifrada de n8n. No se incluye en Git, documentación ni en el navegador. Para aplicar un cambio ejecutar `python scripts/iniciar.py`.

Odoo consulta la API de Gemini y muestra **habilitado**, **sin clave**, **clave rechazada**, **modelo no disponible**, **sin conexión** o **sin cuota**. La validación se conserva durante un minuto. Una cuota de generación agotada puede aparecer al enviar el mensaje aunque listar modelos haya funcionado; ese estado deshabilita el envío y se conserva una hora para evitar repetir llamadas. Las funciones deterministas de Odoo siguen operativas sin Gemini.

Los antiguos accesos directos W1/W2/W3 están despublicados. W4 recibe llamadas internas firmadas y autenticadas desde Odoo. W5 notifica a Odoo los errores del proveedor mediante una cabecera privada. Las conversaciones se separan por usuario y conversación. El navegador nunca recibe tokens de compuerta ni del webhook.

## Verificación y respaldo

Para ejecutar las pruebas de Python:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r agente-sie/compuerta/requirements-dev.txt
.venv/Scripts/python scripts/probar.py
.venv/Scripts/python scripts/verificar_odoo.py
.venv/Scripts/python scripts/verificar_ventas.py
.venv/Scripts/python scripts/probar_n8n.py
python scripts/verificar_estado_agente.py
```

`verificar_odoo.py` crea una familia de cotizaciones de prueba y comprueba el flujo vendedor → dueño → nueva aceptación, permisos por RPC y ausencia de movimientos de stock durante la evaluación. `verificar_ventas.py` confirma únicamente la oferta sintética recién generada, comprueba filtros y trazabilidad, y la cancela para liberar sus reservas; conserva el pedido cancelado como evidencia. No reinician la base. `probar_n8n.py` comprueba la entrada privada y realiza una consulta de catálogo con el modelo cuando está habilitado. Usa la API configurada. Los resultados están en `evidencias/`.

La prueba de los componentes Owl usa la biblioteca exacta del contenedor en un DOM simulado:

```powershell
npm install --prefix .test-runs/owl jsdom@26.1.0 --ignore-scripts --no-audit --no-fund
node scripts/verificar_plantillas.cjs
```

Respaldo de los volúmenes y paquete sin secretos:

```powershell
python scripts/backup.py
python scripts/empaquetar.py
```

`--reiniciar` en el arranque **es una acción explícita para reiniciar el escenario comercial sintético**, no para apagar/encender: borra sus transacciones y vuelve a cargar saldos de prueba. No usar en una base operativa. Las cotizaciones creadas manualmente se conservan.

Si cambian la contraseña de PostgreSQL o la clave maestra de cifrado de n8n en una instalación existente, primero ejecutar `python scripts/sincronizar_credenciales.py`. El script crea respaldo y sincroniza el estado persistido; editar esas variables por sí solo no actualiza los volúmenes.

## Arquitectura y límites

```text
app/
  compose.yaml                  PostgreSQL, Odoo, compuerta, n8n y Nginx
  odoo/addons/mys_erp/           menú, vistas, roles, reglas de edición, chat y controladores
  agente-sie/                   motor, contrato, herramientas, workflows y pruebas existentes
  datos/                        catálogo completo (167 productos) y procedencia
  nginx/                        entrada única hacia Odoo
  scripts/                      arranque, actualización, sincronización, pruebas y respaldo
  docs/                         arquitectura efectiva y despliegue
  evidencias/                   resultados de validación
  legacy/                       portal retirado y guías históricas; no desplegados
```

Los servicios auxiliares conservan puertos locales de diagnóstico: Odoo 8069, compuerta 8000 y editor n8n 5678. El uso comercial se realiza por 8088, con una sola sesión. No hay dos bases de clientes o productos: Odoo es la fuente; SQLite conserva solicitudes, autorizaciones, idempotencia y auditoría del contrato. Las vistas nativas reflejan esos resultados y los escalamientos del chat.

UBLHUB, emisión SUNAT, cobro, WhatsApp automático y despacho quedan fuera de este incremento. La identidad firmada admite distintos usuarios Odoo; la instalación y los casos de prueba aquí se limitan a una compañía. Para detalles consultar [arquitectura](docs/ARQUITECTURA.md) y [despliegue](docs/DESPLIEGUE.md).
