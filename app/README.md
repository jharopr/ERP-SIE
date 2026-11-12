# MYS · Sistema integrado en Odoo

**La entrada única es http://localhost:8088.** Odoo 18 Community muestra el menú lateral de MS Power Audio / Importaciones MYS Hermanos: Contactos, Leads, CRM / Oportunidades, Inventario, Ventas / Cotizaciones, Catálogo, Evaluación comercial, Decisiones del dueño, Trazabilidad y Agente SIE.

El portal anterior fue sustituido por vistas y componentes nativos del addon `mys_erp`. Se conserva como referencia en `legacy/portal/`, sin publicarse. El agente existente continúa en `agente-sie/`; conserva el motor R01–R12, el contrato I03 de nueve campos y los cuatro estados. Los 50 productos proceden del Excel suministrado; clientes, stock y operaciones son de prueba. Además se conservan dos SKU académicos.

## Ingreso

Las cuentas humanas de esta demostración tienen **contraseña igual al usuario**, conforme al requisito:

| Rol | Usuario | Contraseña | Función |
| --- | --- | --- | --- |
| Vendedor | `ven-demo-01` | `ven-demo-01` | Contactos, leads, oportunidades, cotizaciones, evaluación y solicitud de excepciones |
| Dueño / Gerencia | `ger-demo-01` | `ger-demo-01` | Revisión de resultados y aprobación o rechazo de excepciones |
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

## Demostrar un descuento y sus roles

1. Ingresar como vendedor y abrir **Ventas / Cotizaciones**. Crear una cotización desde una oportunidad del CRM, o duplicar una de prueba. En la pestaña **Reglas comerciales SIE** se puede seleccionar la oportunidad. El cliente debe tener referencia y la casilla **Identidad revisada** en su ficha MYS.
2. Completar productos, cantidades, precios, descuento y vencimiento. Pulsar **1. Preparar / enviar**; esto marca la oferta como enviada y asigna una referencia de familia y versión. No envía un correo automáticamente.
3. Tras obtener la aceptación real del cliente, pulsar **2. Registrar aceptación**. Esto registra la evidencia indicada por el vendedor; no simula una firma del cliente.
4. Pulsar **3. Evaluar reglas**. Hasta 5 % no requiere excepción; más de 5 % produce `RECHAZADA / DESCUENTO_SIN_APROBACION` si no existe autorización válida. El resultado muestra motivo, siguiente paso, condiciones y correlación.
5. El vendedor pulsa **Solicitar decisión del dueño**. Puede seguir el estado, pero no ve botones de aprobar ni tiene permiso para invocarlos por RPC.
6. El dueño ingresa con su cuenta, abre **Decisiones del dueño**, escribe el motivo y pulsa **Aprobar descuento** o **Rechazar descuento**. La solicitud tiene un plazo de diez minutos. Una solicitud vencida puede volver a escalarse desde la evaluación.
7. Si se aprueba, Odoo crea **una cotización nueva en borrador con versión siguiente**, mismo importe y vendedor. No crea un pedido confirmado. El vendedor abre esa versión, la prepara/envía, registra una **nueva aceptación** del cliente y evalúa de nuevo. La autorización vale solo para la versión y total exactos.

Una versión ya evaluada queda protegida contra cambios y borrado por las cuentas comerciales. Se corrige con **Nueva versión**. Una evaluación `PENDIENTE` se puede reanudar con el mismo botón de evaluar. Ningún resultado crea pedidos, reserva stock, compra ni promete fechas. El botón nativo de confirmar está bloqueado en el servidor para este alcance de demostración.

Para faltantes, el resultado es `PROMESA_CONDICIONADA`; el dueño puede indicar ofrecer parcial, evaluar reposición o descartar. Estas decisiones no ejecutan compras ni reservas.

## Agente integrado y estado de Gemini

Abrir **Agente SIE** desde Odoo. Ejemplos: «Busca radios con pantalla» o «Consulta la disponibilidad de RAD-7BT». El chat usa el catálogo y las herramientas existentes; los resultados se leen de Odoo y la compuerta.

En `app/.env`:

```dotenv
GEMINI_API_KEY=<clave de la cuenta de prueba>
GEMINI_MODEL=models/gemini-3.5-flash
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
.venv/Scripts/python scripts/probar_n8n.py
python scripts/verificar_estado_agente.py
```

`verificar_odoo.py` crea una familia de cotizaciones de prueba y comprueba el flujo vendedor → dueño → nueva aceptación, permisos por RPC y ausencia de movimientos de stock. No reinicia la base. `probar_n8n.py` comprueba la entrada privada y realiza una consulta de catálogo con el modelo cuando está habilitado. Usa la API configurada. Los resultados están en `evidencias/`.

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
  datos/                        catálogo de 50 productos y procedencia
  nginx/                        entrada única hacia Odoo
  scripts/                      arranque, actualización, sincronización, pruebas y respaldo
  docs/                         arquitectura efectiva y despliegue
  evidencias/                   resultados de validación
  legacy/                       portal retirado y guías históricas; no desplegados
```

Los servicios auxiliares conservan puertos locales de diagnóstico: Odoo 8069, compuerta 8000 y editor n8n 5678. El uso comercial se realiza por 8088, con una sola sesión. No hay dos bases de clientes o productos: Odoo es la fuente; SQLite conserva solicitudes, autorizaciones, idempotencia y auditoría del contrato. Las vistas nativas reflejan esos resultados y los escalamientos del chat.

UBLHUB, emisión SUNAT, cobro, WhatsApp automático y despacho quedan fuera de este incremento. La identidad firmada admite distintos usuarios Odoo; la instalación y los casos de prueba aquí se limitan a una compañía. Para detalles consultar [arquitectura](docs/ARQUITECTURA.md) y [despliegue](docs/DESPLIEGUE.md).
