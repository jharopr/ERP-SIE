# Despliegue, operación y recuperación

## Local

1. Iniciar Docker Desktop. No detener contenedores de otros proyectos.
2. Desde `app/`, ejecutar `python scripts/iniciar.py`. `docker compose ps` debe mostrar los cinco servicios saludables.
3. Abrir el portal en el puerto `APP_PORT`. Las contraseñas locales están en `.env`, excluido de Git.
4. Para actualizar código FastAPI: `docker compose up -d --build compuerta`. Para archivos del portal no hace falta compilar: están montados en Nginx.
5. Para un cambio del modelo/vistas Odoo, reiniciar Odoo y actualizar el módulo con una cuenta administrativa. El seed instala módulos faltantes; no ejecuta automáticamente una actualización de módulo existente.
6. `docker compose down` detiene este proyecto y conserva volúmenes. No usar `down -v` para una parada normal.

## Copias de seguridad

Desde `app/`, ejecutar manualmente `python scripts/backup.py`. Pausa Odoo, compuerta y n8n para evitar escrituras durante el respaldo, crea un `pg_dump` y archiva los tres volúmenes de aplicación. Siempre intenta reanudar los servicios al terminar. Guarda hashes de integridad en `backups/`, carpeta ignorada por Git. El backup contiene datos y credenciales cifradas: no se incluye en el paquete del docente.

Para restaurar, usar un proyecto/volúmenes vacíos, conservar versiones de las imágenes y la misma clave de cifrado de n8n, restaurar `odoo.dump` con `pg_restore` y los archivos de cada volumen con los servicios detenidos. Verificar propietario/permisos antes de iniciar, y repetir salud, login, catálogo y pruebas de lectura. No sobrescribir una instalación operativa sin una copia previa y un destino verificado.

## Estado persistente

| Volumen Compose | Contenido |
| --- | --- |
| `pgdata` | PostgreSQL y registros de Odoo |
| `odoo-data` | Filestore y adjuntos de Odoo |
| `compuerta-data` | SQLite, auditoría, decisiones y escenarios CAT |
| `n8n-data` | Flujos, credenciales cifradas, usuarios y ejecuciones |

Conservar `N8N_ENCRYPTION_KEY` junto con una copia protegida de `.env`: sin ella las credenciales guardadas no se recuperan. No incluirla en ZIP, capturas o evidencias compartidas.

## Servidor

La configuración entregada publica solo en `127.0.0.1` y sirve HTTP para la demostración local. Para un despliegue en servidor:

1. Aprovisionar un servidor Linux y DNS, por ejemplo `app`, `odoo` y `agente` en subdominios propios. Dimensionar con mediciones; los requisitos de demo no son garantía de capacidad productiva.
2. Crear credenciales nuevas y una base operativa diferente. **No cargar este seed ni sus saldos sintéticos en una base empresarial.**
3. Mantener PostgreSQL y compuerta en red interna. Publicar únicamente el proxy TLS y limitar el editor n8n a administradores/VPN.
4. Configurar certificados válidos y un proxy HTTPS delante de Odoo, n8n y portal. Pasar `Host`, `X-Forwarded-Proto` y los encabezados de WebSocket. En Odoo habilitar `proxy_mode`, fijar `dbfilter` y deshabilitar listado/gestión pública de bases después de aprovisionar.
5. En n8n definir `WEBHOOK_URL`, host/protocolo públicos y cookies seguras. En compuerta definir `SESSION_SECURE=true`, `PUBLIC_ODOO_URL` y `PUBLIC_N8N_URL`; confiar los encabezados de proxy solo a la red del proxy. Comprobar el origen HTTPS y las sesiones.
6. Separar el seed del servicio de ejecución: entregar la clave administrativa solo a un proceso temporal de aprovisionamiento. La compuerta regular requiere la clave del lector, no la del administrador.
7. Gestionar secretos fuera del código, programar backups y ensayar restauración de PostgreSQL, filestore, SQLite y n8n como conjunto coherente.
8. Ejecutar las pruebas con roles reales, concurrencia y las políticas validadas por el dueño. Una validación previa no reserva existencias; confirmar una venta futura exige revalidación transaccional en Odoo.

Estos pasos de servidor son una guía; no se ha publicado el sistema ni configurado un dominio o certificado real en esta entrega.

## Diagnóstico

| Síntoma | Verificación | Recuperación |
| --- | --- | --- |
| Docker no responde | `docker info` | Iniciar Docker Desktop y esperar el motor Linux |
| Odoo falla con `password authentication failed` y PostgreSQL aparece healthy | `iniciar.py` comprueba autenticación TCP; `pg_isready` por sí solo no valida la contraseña | Si se editaron claves en `.env`, ejecutar `python scripts/sincronizar_credenciales.py` y luego `python scripts/iniciar.py`; conserva los volúmenes |
| n8n rechaza una clave de cifrado distinta | Revisar log de n8n; el volumen conserva su clave original | `sincronizar_credenciales.py` respalda el volumen y recifra las credenciales existentes antes de usar la nueva clave |
| Puerto ocupado | Revisar puertos en `.env` y `docker compose ps` | Cambiar solo los puertos de este proyecto y volver a iniciar |
| No aparece el addon | Revisar montaje `odoo/addons` y logs de Odoo | Reiniciar Odoo; instalar `mys_erp` con administrador |
| Catálogo no cargado | `GET /salud`; revisar mensajes de `seed_sistema.py` | Corregir origen y repetir la carga idempotente en la base demo |
| Respuesta PENDIENTE | Revisar salud de Odoo y credencial de lectura | Restaurar servicio y reanudar la misma solicitud; no inventar stock |
| DATOS_INCONSISTENTES | Comprobar CLI/OPP/COT y mapa del vendedor | Repetir seed o corregir vínculos con un usuario autorizado |
| Cotización vencida | Revisar fecha y `COTIZACION_HORA_CIERRE` | Refrescar el seed el día de exposición; las vigencias son hora Lima |
| Ya se evaluó una versión | Revisar SOL y bitácora | Recuperar la respuesta guardada; para otra oferta, nueva versión y aceptación |
| Panel devuelve 401 | Sesión vencida o compuerta reiniciada | Volver a ingresar con el rol correcto |
| Dueño devuelve 403 | Contraseña/rol de Ventas | Usar credencial independiente de Gerencia |
| Escalamiento vencido | Revisar `plazo_hasta` | Registrar seguimiento nuevo; no falsificar la hora de decisión |
| W1 sin credencial Gemini | Revisar nodo Modelo Gemini en n8n | Registrar clave propia o usar portal/W3 sin modelo |
| W2/W3 devuelve 401 | Formulario protegido con Basic Auth | Usar usuario/clave de Ventas o Dueño según el formulario |
| Importación n8n falla | Revisar propietario, credenciales y logs | Ejecutar `python scripts/preparar_n8n.py` desde `app/` |

## Pruebas e interpretación

`scripts/probar.py` usa un Odoo simulado para probar reglas, permisos y recuperación con expectativas fijas. `scripts/verificar_sistema.py` usa Odoo/PostgreSQL reales, verifica 50 referencias, ACL, panel y tres casos CAT. El runner PC3 produce evidencia de normal, faltante, descuento, caída, reintento e intento de autoaprobación. La caída por bandera es explícitamente simulada, aun cuando los demás datos se lean del Odoo real.

No se atribuye una conversación a un modelo que no se ejecutó. Los resultados históricos del agente se conservan en su carpeta y los nuevos resultados contienen su fecha real. La configuración nueva usa cierre 23:59 para permitir ensayos nocturnos; no representa el horario comprobado de la empresa.
