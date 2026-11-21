# Plataforma MYS Hermanos

Implementación ejecutable de Odoo 18 Community, PostgreSQL 16 y el Agente SIE existente, integrada en una sola carpeta. Incluye un portal de operación, módulo Odoo `mys_erp`, 50 referencias del catálogo suministrado y los dos SKU académicos PC3. Las reglas R01–R12, los nueve campos I03 y los cuatro estados del contrato se conservan.

## Arranque

Requisitos: Docker Desktop/Engine iniciado con Compose v2.24 o posterior, Python 3.10+, aproximadamente 8 GB de RAM disponibles y puertos 8088, 8069, 8000 y 5678 libres. El primer arranque descarga imágenes e instala los módulos de Odoo; requiere conexión a Internet.

Desde `app/`:

```powershell
python scripts/iniciar.py
```

El script completa `.env` con contraseñas locales aleatorias, inicia los cinco servicios, instala MYS, carga datos, crea el propietario de n8n solo si la instancia es nueva e importa W1/W2/W3. Conserva las claves y cuentas existentes. No requiere clave de Gemini para usar el portal o W3.

| Acceso | URL local predeterminada | Credencial en `.env` |
| --- | --- | --- |
| Portal comercial | http://localhost:8088 | Ventas: `ODOO_SELLER_PASSWORD`; Dueño: `ODOO_OWNER_PASSWORD` |
| Odoo | http://localhost:8069 | `ven-demo-01` / `ODOO_SELLER_PASSWORD`; `ger-demo-01` / `ODOO_OWNER_PASSWORD` |
| Administración Odoo | http://localhost:8069 | `ODOO_USER` / `ODOO_PASSWORD` |
| Editor n8n | http://localhost:5678 | `N8N_OWNER_EMAIL` / `N8N_OWNER_PASSWORD`, si fue creado por el script |
| API de compuerta | http://localhost:8000/docs | Bearer por rol; tokens `TOKEN_*` |
| Chat SIE | http://localhost:5678/webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat | Basic Auth `ven-demo-01` + contraseña de Ventas; modelo configurado en n8n |
| Respaldo sin modelo W3 | http://localhost:5678/form/modo-determinista | Basic Auth `ven-demo-01` + contraseña de Ventas |
| Decisión del dueño W2 | http://localhost:5678/form/decision-dueno | Basic Auth `ger-demo-01` + contraseña del dueño |

Los puertos se cambian en `.env`. El panel no entrega los tokens de servicio al navegador. Sus sesiones son locales, expiran en ocho horas y se cierran al reiniciar la compuerta. El usuario técnico `sie-lectura` consulta Odoo sin permisos de crear, editar o borrar registros.

### Cambiar claves en una instalación existente

Las contraseñas de PostgreSQL y del administrador Odoo, y la clave de cifrado de n8n, también están guardadas en sus volúmenes. Editar `.env` no actualiza esos registros. Si se cambiaron esas claves:

```powershell
python scripts/sincronizar_credenciales.py
python scripts/iniciar.py
```

La sincronización detiene los servicios de aplicación, crea un respaldo privado en `backups/`, aplica las claves de `.env` a PostgreSQL y al administrador Odoo y recifra las credenciales existentes de n8n con la clave nueva. Conserva las bases, flujos y credenciales; no elimina volúmenes. Requiere acceso administrativo local a Docker. El arranque normal ahora comprueba autenticación TCP de PostgreSQL y da este diagnóstico antes de intentar levantar Odoo.

## Uso

1. Ingresar al portal como Ventas. El catálogo lee precios y existencias de Odoo en ese momento.
2. Abrir **Evaluación comercial**. Ejecutar PC3-N01: `ACEPTADA / VALIDADA`, S/ 1,900.00.
3. Ejecutar PC3-E01: `PROMESA_CONDICIONADA`, 3 disponibles de 5, faltante 2. Solicitar revisión humana.
4. Cerrar sesión e ingresar como Dueño. En **Decisiones del dueño**, elegir y justificar una decisión. No crea compra ni reserva.
5. Consultar **Trazabilidad** por `COR-PC3-002`.
6. Probar PC3-E02: descuento 10 % no aprobado; `RECHAZADA / DESCUENTO_SIN_APROBACION`, sin consulta de inventario.
7. Probar CAT-001/002/003: los mismos controles con productos del Excel, no solo con los SKU académicos.

En Odoo, abrir la aplicación **MYS Hermanos** para ver catálogo, clientes, oportunidades y cotizaciones con sus referencias. CRM, Ventas, Inventario y Compras son módulos nativos. El addon conserva la procedencia del producto y añade la cuenta de integración de lectura. La compuerta y las aprobaciones siguen en el servicio FastAPI existente: no se presentan como modelos Odoo ya implementados.

## Catálogo y datos de prueba

- Fuente: `LISTA_PRODUCTOS_EMPRESA_18717.xlsx`, hoja `Worksheet`, proporcionada por el usuario. El original no se modifica ni se copia al paquete.
- 167 productos activos identificados; 159 pasan las validaciones de precio/código/categoría del importador.
- Se seleccionan **50 referencias**: 16 radios/pantallas, 8 amplificadores, 8 subwoofers, 8 medios/parlantes, 3 tweeters, 3 cables/conexiones, 1 alarma, 2 accesorios y 1 ecualizador. Dentro de cada categoría se ordena por precio descendente y código ascendente.
- Es una selección para cobertura comercial, **no un ranking de los más vendidos**: el archivo no incluye ventas ni rotación.
- Se conservan nombre, código original, precio, categoría, fila y SHA-256 de origen. Algunos SKU se normalizan para la API; el código original queda disponible.
- Moneda PEN como supuesto del proyecto. Un costo 0 se registra como desconocido (`null`), sin inventar margen. Las cotizaciones usan precios finales de prueba sin desglose de impuestos.
- Inventario, clientes, proveedor, leads, oportunidades, aceptaciones y reservas son sintéticos. Los productos PC3 `RAD-7BT` y `RAD-10X` son dos referencias adicionales: **52 SKU en total**, de los cuales 50 provienen del Excel.

La metodología y las filas fuente están en [datos/procedencia.json](datos/procedencia.json). Para regenerar la selección:

```powershell
python scripts/importar_catalogo.py "C:\ruta\LISTA_PRODUCTOS_EMPRESA_18717.xlsx"
docker compose exec -T compuerta python /plataforma/seed_sistema.py
```

## Pruebas y evidencias

```powershell
# Primera vez: entorno aislado de pruebas
python -m venv .venv
.venv\Scripts\python -m pip install -r agente-sie/compuerta/requirements-dev.txt
.venv\Scripts\python scripts/probar.py

# Seis casos PC3 contra Odoo real (refresca la demo)
python -X utf8 agente-sie/scripts/ejecutar_casos.py --caida bandera

# Catálogo real, ACL de Odoo, panel y tres casos de catálogo
python scripts/verificar_sistema.py

# Formularios W3 y W2 contra n8n real, sin modelo
python scripts/probar_n8n.py
```

`--caida bandera` simula indisponibilidad en la compuerta y lo declara en las evidencias. Sin esa opción, el runner detiene y vuelve a iniciar únicamente Odoo de este proyecto. Los resultados PC3 se guardan en `agente-sie/evidencias/`; las comprobaciones de plataforma en `evidencias/`. El motor histórico se conserva byte a byte; sus pruebas de equivalencia lo contrastan cuando el repo original está presente.

Ejecutar estas verificaciones en ese orden, sin correr un reset o una caída simulada en paralelo: la prueba F01 deja temporalmente indisponible la fuente usada por el catálogo. `probar_n8n.py` verifica una decisión humana de reposición sobre CAT-002 y la registra en la bitácora.

Para refrescar las vigencias antes de exponer:

```powershell
python scripts/iniciar.py --reiniciar --sin-n8n
```

`--reiniciar` limpia solicitudes, bitácora y decisiones de **la demo del agente**. El seed escribe saldos sintéticos: no usar contra una base operativa. No elimina las bases o volúmenes y no desconfirma pedidos manuales. Las vigencias se fijan al día de ejecución, hasta `COTIZACION_HORA_CIERRE` (23:59 en la configuración nueva). Usar un chat nuevo al reiniciar.

## Organización

```text
app/
  compose.yaml             cinco servicios y volúmenes persistentes
  agente-sie/              agente existente, compuerta, flujos, pruebas y evidencias
  odoo/addons/mys_erp/     módulo Odoo, vistas y ACL
  odoo/seed_sistema.py      carga integrada e idempotente
  datos/                   50 productos, CSV, JSON y procedencia
  portal/                  interfaz comercial, sin claves en JavaScript
  nginx/                   entrada HTTP local y proxy hacia la compuerta
  scripts/                 configuración, arranque, pruebas y verificaciones
  docs/                    arquitectura, despliegue y recuperación
  evidencias/              resultados verificables de plataforma
```

El nombre Compose `agente-sie` se conserva para reutilizar los volúmenes del desarrollo anterior. No ejecutar simultáneamente otro Compose con ese nombre. El archivo `agente-sie/docker-compose.yml` solo incluye el Compose raíz por compatibilidad; no define una segunda plataforma.

## Límites

El agente acompaña al ERP y no confirma pedidos, reserva stock, aprueba descuentos, compra ni promete fechas. Las dos reservas previas de otro cliente las crea el **seed administrador** para demostrar físico − reservado, no el agente. UBLHUB, emisión SUNAT, cobro y despacho quedan fuera de este incremento.

W1 conserva el modelo Gemini del agente original; necesita una clave válida registrada en n8n. No se incluye ninguna. W3 y el portal siguen funcionando sin modelo. La asignación de usuarios es una demo de una compañía y un vendedor; múltiples vendedores requieren identidades y asignaciones individuales, no compartir `TOKEN_VENTAS`.

Para el servidor y recuperación consultar [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) y [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

Para generar el paquete autocontenido sin claves, bases, backups ni el entorno Python: `python scripts/empaquetar.py`. El ZIP queda en `app/dist/`.
