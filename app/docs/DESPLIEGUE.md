# Despliegue y recuperación

## Equipo local

Desde `app/`, ejecutar `python scripts/iniciar.py`. Entrar en http://localhost:8088 con las cuentas del [README](../README.md). El chat está en el mismo menú y no pide otra clave.

El script completa variables internas faltantes; comprueba autenticación TCP de PostgreSQL; actualiza `mys_erp` sin recrear datos; sincroniza el administrador y las cuentas de demostración; levanta servicios; y configura n8n con el chat W4. Una instalación ya cargada conserva stock y operaciones. Un cambio de Python/XML del addon requiere actualizar con este script; un reinicio simple no actualiza vistas almacenadas en PostgreSQL.

Apagar: `docker compose stop`. Volver a levantar: `docker compose up -d --wait`. Ver servicios: `docker compose ps`. Diagnóstico: `docker compose logs --tail 80 odoo compuerta n8n web`. No usar `down -v` para reiniciar.

## Contraseñas y configuración

`ODOO_PASSWORD`, `ODOO_SELLER_PASSWORD` y `ODOO_OWNER_PASSWORD` se aplican a usuarios Odoo durante el arranque. La clave maestra de bases no es la clave de acceso de `admin`. El agente no tiene clave humana; `GEMINI_API_KEY` configura el proveedor.

Las contraseñas de PostgreSQL y el cifrado de n8n persisten en volúmenes. Si estas se modifican en `.env`, ejecutar `python scripts/sincronizar_credenciales.py` y luego iniciar. La sincronización respalda PostgreSQL/n8n antes de aplicar claves y recifra también el llavero de despliegue de n8n. No se limita a importar credenciales. Conservar los respaldos en privado.

## Respaldo y restauración

`python scripts/backup.py` genera un respaldo de PostgreSQL y los volúmenes del proyecto en `backups/`. Guardar también una copia privada de `.env`: el cifrado de n8n requiere su clave. Los respaldos se excluyen del paquete de entrega.

Para recuperar, detener el mismo proyecto, restaurar PostgreSQL con `pg_restore` y los archivos de los volúmenes correspondientes, recuperar el `.env` asociado y ejecutar el arranque. No mezclar una base de credenciales con otra clave de cifrado. El detalle del respaldo creado está en su manifest.

`--reiniciar` restablece exclusivamente el escenario sintético y elimina sus transacciones de evaluación y auditoría. Cambia saldos de prueba; no es el procedimiento para apagar/encender. Debe usarse en una base destinada a demostración y con respaldo.

## Servidor

La configuración suministrada es para demostración local. Para publicar una instalación:

1. Respaldar la instalación y configurar un dominio con HTTPS hacia **una sola entrada Odoo**. El usuario continúa con una sesión nativa.
2. Mantener PostgreSQL, compuerta, webhook y editor n8n en red interna. El editor puede administrarse mediante túnel o acceso restringido. No publicar el webhook como una página de chat.
3. Configurar contraseñas propias y cuentas individuales; las cuentas `usuario=contraseña` del README son de demostración. Fijar `dbfilter`, deshabilitar el listado/gestor público después de aprovisionar y mantener `proxy_mode` detrás del proxy de confianza.
4. Para Odoo con varios workers, separar el servicio gevent/WebSocket y enrutarlo al puerto configurado. Este Compose usa el servidor sin workers y WebSocket en 8069.
5. Configurar copias periódicas, logs y almacenamiento persistente; probar restauración. Comprobar tiempo de espera del proxy para respuestas de modelo de hasta cien segundos.
6. Aplicar actualizaciones de addon con Odoo detenido, como hace `actualizar_odoo.py`, y recrear servicios si cambian variables de entorno. Reimportar W4 mediante `iniciar.py` después de cambiar la clave/modelo.

Los límites de este incremento son evaluación comercial y decisión humana; facturación electrónica, cobranza, compra y despacho requieren implementación adicional.
