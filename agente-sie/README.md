# Agente SIE · PC3 · G7 Importaciones MYS Hermanos

Agente de IA que **acompaña** al ERP en el proceso comercial: lleva una cotización aceptada hasta una respuesta trazable de la compuerta CRM–ERP v1.0, explica el resultado, escala al dueño las excepciones y deja todo en la bitácora. **No crea pedidos, no reserva stock, no aprueba descuentos y no promete fechas.** Todos los datos son sintéticos.

```
Vendedor ─chat─► n8n W1 (AI Agent + Gemini) ─HTTP, token VENTAS─► Compuerta FastAPI ─XML-RPC (lectura)─► Odoo 18 CE ─► PostgreSQL 16
                     │ escalar_al_dueno                          (R01–R12 del motor PC2, sin cambios;
                     ▼                                             SQLite: bitácora, REP, aprobaciones)
                 n8n W2 ─ formulario del dueño ─ token GERENCIA ─►┘
                 n8n W3 = modo determinista sin IA (respaldo)
```

| Documento | Contenido |
|---|---|
| [docs/GUIA_AGENTE.md](docs/GUIA_AGENTE.md) | Propósito, entradas, salidas, fuentes, herramientas, reglas, permisos, responsable, escalamiento y bitácora |
| [docs/GUION_DEMO.md](docs/GUION_DEMO.md) | Demo en vivo de 4 min y plan B |
| [docs/DIAGNOSTICO_Y_RECUPERACION.md](docs/DIAGNOSTICO_Y_RECUPERACION.md) | Síntoma, causa, verificación y recuperación |
| [docs/LICENCIAS_Y_ACCESOS.md](docs/LICENCIAS_Y_ACCESOS.md) | Licencias, credenciales y por qué no se incluyen claves |
| [docs/USO_IA_Y_VALIDACION.md](docs/USO_IA_Y_VALIDACION.md) | Qué generó la IA, decisiones y validación |
| [docs/FUENTES.md](docs/FUENTES.md) | Fuentes con fecha de acceso y declaración de uso de IA |
| [datos_prueba/](datos_prueba/DATOS_SINTETICOS.md) | Escenario sintético y casos declarados antes de ejecutar |
| [evidencias/resultados.md](evidencias/resultados.md) | Esperado vs observado |

## 1. Requisitos (≈ 5 min)
- Docker Desktop (Windows/macOS) o Docker Engine con **Compose v2**, unos **8 GB de RAM libres** y unos 6 GB de disco para las imágenes.
- Puertos **8069**, **8000** y **5678** libres (se cambian en `.env`).
- **Python 3.10 o superior** en el equipo, para los scripts. El modo real usa solo la biblioteca estándar.
- Internet para descargar imágenes y, si se usa el agente con IA, una **clave de Google Gemini** (Google AI Studio). Sin clave, la demo funciona con **W3**.

| Imagen | Versión fijada |
|---|---|
| Odoo | `odoo:18.0` |
| PostgreSQL | `postgres:16` |
| n8n | `docker.n8n.io/n8nio/n8n:2.46.7` (stable al 10/11/2026) |
| Compuerta | `python:3.12-slim` + `compuerta/requirements.txt` |

## 2. Configurar `.env` (≈ 2 min)
```powershell
Copy-Item .env.example .env        # Linux/macOS: cp .env.example .env
python -c "import secrets; [print(secrets.token_urlsafe(32)) for _ in range(6)]"
```
Reemplace **cada** `cambiar-esto` por uno de los valores generados. Los tres `TOKEN_*` deben ser distintos. `GEMINI_API_KEY` es opcional.

## 3. Levantar los servicios (≈ 3–6 min la primera vez)
```powershell
docker compose up -d --build
docker compose ps                  # espere a que db, odoo, compuerta y n8n estén "healthy"
```

## 4. Cargar los datos sintéticos (≈ 5 min la primera vez; medido: 4 min 39 s)
```powershell
docker compose exec -T compuerta python /seed/seed_odoo.py
```
> **Git Bash en Windows:** anteponga `MSYS_NO_PATHCONV=1` a los comandos con rutas `/seed/…`; si no, Git Bash las convierte en rutas de Windows. En PowerShell no hace falta.
Crea la base `mys_demo`, instala CRM, Ventas e Inventario y carga productos, stock, reservas, oportunidades y cotizaciones. Debe terminar con:
```
[seed] ✓ RAD-7BT: físico 10, reservado 2, disponible 8 (esperado (10, 2, 8))
[seed] ✓ RAD-10X: físico 10, reservado 7, disponible 3 (esperado (10, 7, 3))
[seed] seed completo
```
Odoo queda en `http://localhost:8069`, con el usuario y la clave `ODOO_USER` / `ODOO_PASSWORD` de `.env`.

## 5. Credenciales de n8n (≈ 3 min)
1. Abra `http://localhost:5678` y cree la cuenta de propietario local (correo y clave cualquiera, solo para este equipo).
2. Opción **automática** (recomendada): `python scripts/importar_n8n.py`. Crea las credenciales desde `.env` e importa y activa W1–W3.
3. Opción **manual**: n8n → *Credentials* → *Add credential*, con los **nombres exactos**:

| Nombre exacto | Tipo | Campos |
|---|---|---|
| `Compuerta VENTAS` | Header Auth | Name: `Authorization` · Value: `Bearer <TOKEN_VENTAS>` |
| `Compuerta GERENCIA` | Header Auth | Name: `Authorization` · Value: `Bearer <TOKEN_GERENCIA>` |
| `Gemini (Agente SIE)` | Google Gemini(PaLM) API | Host: `https://generativelanguage.googleapis.com` · API Key: su clave |

Si `GEMINI_API_KEY` estaba vacía, cree a mano la credencial de Gemini aunque haya usado la opción automática.

## 6. Importar los flujos (si usó la opción manual)
- Por interfaz: *Workflows* → *Import from file* → `n8n/workflows/W2_escalamiento_dueno.json`, luego `W3_…` y luego `W1_…`. Abra cada nodo con un aviso de credencial y elija la credencial del mismo nombre. Después active cada flujo (interruptor *Active/Publish*).
- Por CLI: `docker compose exec n8n n8n import:workflow --separate --input=/workflows`

| Flujo | URL |
|---|---|
| W1 · chat del vendedor | `http://localhost:5678/webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat` |
| W2 · formulario del dueño | `http://localhost:5678/form/decision-dueno` |
| W3 · modo determinista (sin IA) | `http://localhost:5678/form/modo-determinista` |

## 7. Demo
Abra el chat de W1 y pegue los mensajes de [docs/GUION_DEMO.md](docs/GUION_DEMO.md). Por ejemplo:
> CLI-DEMO-001 aceptó COT-DEMO-001 v1 (ACE-PC3-001), oportunidad OPP-DEMO-001. Envía la solicitud SOL-PC3-N01 con COR-PC3-001.

Antes de cada ensayo o de la exposición, ejecute `scripts/demo_reset.ps1` (o `.sh`) **el mismo día y antes de las 18:00**, y abra un chat nuevo.

## 8. Evidencias reproducibles (≈ 2 min)
```powershell
python scripts/ejecutar_casos.py                 # F01 detiene y arranca el contenedor odoo
python scripts/ejecutar_casos.py --caida bandera # F01 con la bandera ADMIN (no detiene Odoo)
```
Escribe `evidencias/<caso>.json` (entrada, respuesta, bitácora y stock antes y después) y `evidencias/resultados.md`. Criterio: **6/6 ✓**, stock intacto y `order_id` null.

Pruebas automáticas de la compuerta: `cd compuerta; pip install -r requirements-dev.txt; python -m pytest -q`.

## 9. Apagar
```powershell
docker compose down        # conserva los datos
docker compose down -v     # borra Odoo, la compuerta y n8n
```

## Atajos
Con `make` (Linux, macOS o Git Bash): `make up | seed | n8n | demo-reset | evidencias | verificar | test | zip | down`. Para armar el ZIP de entrega: `python scripts/empaquetar.py`, que excluye `.env` y verifica que no haya secretos.

## API de la compuerta
Documentación interactiva en `http://localhost:8000/docs`. Todas las rutas, salvo `/salud`, requieren `Authorization: Bearer <token>`, y el rol sale del token.

| Ruta | Rol |
|---|---|
| `GET /salud` | — |
| `GET /clientes/{ref}`, `GET /cotizaciones/{id}/{v}`, `GET /disponibilidad/{sku}` | VENTAS |
| `POST /solicitudes`, `POST /solicitudes/{id}/reanudar`, `GET /solicitudes/{id}` | VENTAS |
| `POST /aceptaciones` · `POST /eventos-agente` · `POST /escalamientos` · `GET /escalamientos/{id}` | VENTAS |
| `POST /aprobaciones` · `POST /decisiones-reposicion` · `POST /escalamientos/{id}/decision` | **GERENCIA** |
| `GET /bitacora?correlation_id=` | VENTAS / ADMIN |
| `POST /admin/simulacion` · `POST /admin/reiniciar` | ADMIN |

## Cambios respecto de las instrucciones
1. **E02 usa COT-DEMO-004** (v1 anulada, v2 al 10 %), para que N01 no quede obsoleto. Ver [DATOS_SINTETICOS.md](datos_prueba/DATOS_SINTETICOS.md).
2. **W2 no bloquea al agente con un *Wait*.** El agente registra el escalamiento y entrega el enlace; el dueño decide en un formulario y la compuerta controla el plazo de 10 min (`SIN_DECISION`).
3. La herramienta opcional `buscar_contacto_odoo`, que habría sido el nodo Odoo, no se incluyó. El agente lee contactos por `consultar_cliente`, sin datos personales.

## Estado de verificación (10/11/2026, Windows 11 + Docker Desktop 29.2.1, 3,7 GB de RAM para Docker)
| Pieza | Estado |
|---|---|
| `docker compose up` (4 servicios *healthy*) | ✓ verificado |
| Seed en Odoo 18.0-20261102 (base, módulos, PEN, reservas 2/7, disponible 8/3, 5 cotizaciones) | ✓ verificado (4 min 39 s) |
| 6 casos PC3 contra Odoo real (`ejecutar_casos.py`, F01 deteniendo el contenedor) | ✓ 6/6, stock intacto, `order_id` null |
| Pruebas pytest de la compuerta | ✓ 22/22 |
| Importación y publicación de W1–W3 por CLI en n8n 2.46.7 | ✓ verificado |
| W3, modo determinista (formulario → compuerta → Odoo) | ✓ verificado |
| W2, formulario del dueño (token GERENCIA, cierra el escalamiento) | ✓ verificado |
| W1, conversación con Gemini y herramienta `escalar_al_dueno` → W2 | ⏳ pendiente de la clave de Gemini |
| Prueba en limpio en otra PC siguiendo solo este README | ⏳ pendiente (equipo) |
