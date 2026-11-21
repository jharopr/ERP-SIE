# Diagnóstico y recuperación

Primer paso siempre: `python scripts/verificar_entorno.py` (o `make verificar`) y `docker compose ps`.

| Síntoma | Causa probable | Cómo verificar | Recuperación |
|---|---|---|---|
| Odoo no levanta o queda en *unhealthy* | Postgres todavía no está listo, falta RAM o `.env` está incompleto | `docker compose logs odoo --tail 50` y `docker compose logs db --tail 20` | Revise `POSTGRES_*` en `.env`, deje unos 8 GB libres, ejecute `docker compose up -d` otra vez y espere 1–2 min |
| `docker compose up` falla con «port is already allocated» | El puerto 8069, 8000 o 5678 está ocupado | Windows: `netstat -ano \| findstr :8069`; Linux: `ss -ltnp \| grep 8069` | Cierre el proceso o cambie `ODOO_PORT`, `COMPUERTA_PORT` o `N8N_PORT` en `.env` |
| El seed dice «No se pudo crear la base» | `ODOO_MASTER_PASSWORD` cambió después de crear el volumen | Mensaje del seed | Use la clave original, o `docker compose down -v` (borra todo) y repita |
| El seed dice «Autenticación rechazada» | `ODOO_PASSWORD` no coincide con la base ya creada | Mensaje del seed | Use la clave con la que se creó, o `docker compose down -v` |
| El seed falla con `ConnectionRefusedError` al crear la base, y en los logs de Odoo aparece «virtual real time limit (…/120s) reached» | Odoo cortó la petición por su límite de tiempo (120 s por defecto) | `docker compose logs odoo \| grep "time limit"` | El compose ya fija `limit_time_real = 1800`. Si ocurrió con otra configuración: `docker compose exec db psql -U odoo -d postgres -c "DROP DATABASE mys_demo"` y repita el seed |
| Con Git Bash, `python: can't open file '/srv/C:/Program Files/Git/seed/…'` | Git Bash convierte las rutas que empiezan con `/` | El mensaje de error | Anteponga `MSYS_NO_PATHCONV=1`, o use PowerShell |
| El seed tarda mucho en «instalando módulos» | Es la primera instalación de crm, ventas e inventario | `docker compose logs -f odoo` | Espere de 2 a 5 min. Si se corta, vuelva a ejecutar el seed (es idempotente) |
| El seed marca ✗ en el stock (disponible ≠ 8 o 3) | La reserva no se generó, o alguien editó stock en Odoo | Odoo → Inventario → RAD-10X → «A mano» y «Reservado» | `scripts/demo_reset.*`. Si persiste, `docker compose down -v` y repita |
| La compuerta devuelve **PENDIENTE / DEPENDENCIA_NO_DISPONIBLE** | Odoo está caído o en mantenimiento, tardó más de 5 s, o quedó activa la bandera de caída simulada | `curl http://localhost:8000/salud` → `odoo.disponible` | `docker compose start odoo`; si fue la bandera, `POST /admin/simulacion {"odoo_caido": false}` con el token ADMIN. Luego `POST /solicitudes/<SOL>/reanudar`. **PENDIENTE no significa «sin stock»** |
| **401** en la compuerta | Falta el token o es incorrecto | Cabecera `Authorization: Bearer …` | Revise que la credencial de n8n tenga `Bearer <TOKEN>` con el valor de `.env`; si cambió, ejecute `python scripts/importar_n8n.py` |
| **403** en la compuerta | El rol no tiene permiso; por ejemplo, VENTAS intentó aprobar (esperado en A01) | `GET /bitacora?correlation_id=…` → evento `DENEGADA` | Comportamiento correcto. Solo W2, con la credencial **Compuerta GERENCIA**, aprueba |
| El agente no responde o da error del modelo (clave inválida, cuota, sin internet) | Falta la credencial **Gemini (Agente SIE)**, la clave es inválida o se agotó la cuota gratuita | n8n → Executions → W1 → nodo «Modelo Gemini» | **Use W3** (`http://localhost:5678/form/modo-determinista`): mismos casos, sin IA. Después corrija la credencial |
| El agente inventa un ID o una fecha | Error del modelo | Compare con `GET /solicitudes/<SOL>` | Vale la respuesta de la compuerta. Abra un chat nuevo y dé todas las referencias. Plan B: W3 |
| **COTIZACION_VENCIDA** | La demo es después de las 18:00 del día del seed, o el seed es de otro día | `GET /cotizaciones/COT-DEMO-001/1` → `vigente_hasta` | `scripts/demo_reset.*` el mismo día. Para ensayar de noche, suba `COTIZACION_HORA_CIERRE` en `.env` y ejecute `docker compose up -d compuerta` y el reset |
| **COTIZACION_YA_EVALUADA** o se repite la respuesta anterior al rehacer la demo | Esa versión ya se evaluó (idempotencia del contrato) | `GET /solicitudes/<SOL>` | `scripts/demo_reset.*` (borra solicitudes y bitácora, y refresca Odoo) |
| **ACEPTACION_INVALIDA** justo después del seed | Se ejecutó el seed después de las 18:00: la aceptación queda fuera de vigencia | Hora del seed | Igual que en COTIZACION_VENCIDA |
| E02 devuelve **VERSION_OBSOLETA** | Quedó una COT-DEMO-004 v3 de un ensayo anterior | Odoo → Ventas → buscar «COT-DEMO-004» | `scripts/demo_reset.*` (anula las versiones extra) |
| El formulario del dueño responde «ya está en estado …» | Ese escalamiento ya se decidió o venció (10 min) | `GET /escalamientos/<ESC>` | Pida al agente escalar de nuevo o haga un reset |
| El chat o los formularios de n8n dan 404 | Los flujos no están activos o publicados | n8n → Workflows → interruptor *Active/Published* | Actívelos en la interfaz o ejecute `python scripts/importar_n8n.py` |
| La importación de n8n falla con «credential … not found» | La credencial no existe todavía | n8n → Credentials | Cree las credenciales con los **nombres exactos** del README e importe otra vez |

## Recuperación total (último recurso)
```sh
docker compose down -v      # borra Odoo, la compuerta y n8n
docker compose up -d --build
docker compose exec -T compuerta python /seed/seed_odoo.py
python scripts/importar_n8n.py
```
Tarda unos 8–10 min. Si falla todo durante la exposición, use como respaldo `evidencias/resultados.md` y la grabación. La rúbrica aclara que la grabación no reemplaza la ejecución en vivo.
