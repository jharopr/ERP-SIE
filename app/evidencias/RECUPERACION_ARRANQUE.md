# Recuperación del arranque tras cambiar las claves

Verificado el 11/11/2026 sobre la instalación local existente.

El volumen PostgreSQL conservaba la contraseña inicial aunque `POSTGRES_PASSWORD` ya había cambiado en `.env`. `pg_isready` informaba disponibilidad, pero Odoo no podía autenticarse. La clave configurada de n8n tampoco coincidía con la guardada en su volumen.

Se respaldaron PostgreSQL y n8n, se sincronizó el rol PostgreSQL y el administrador Odoo, y se migraron el llavero y las credenciales de n8n con los cifradores de la versión instalada. No se eliminaron volúmenes, bases ni flujos.

Resultado comprobado:

- `python scripts/iniciar.py` terminó con código 0.
- Los cinco servicios aparecen saludables en Docker Compose.
- Portal y sesión de Ventas: HTTP 200.
- Catálogo: 50 productos leídos de Odoo real.
- Compuerta: Odoo disponible.
- W3 ejecutó el caso normal y W2 registró la decisión autenticada del dueño.
- Las cinco credenciales de n8n se pudieron descifrar; la credencial Gemini coincide con `.env`. No se ejecutó una consulta al proveedor del modelo.

El arranque ahora comprueba autenticación TCP antes de iniciar Odoo y muestra un diagnóstico con el comando de sincronización, sin volcar claves ni un traceback genérico.
