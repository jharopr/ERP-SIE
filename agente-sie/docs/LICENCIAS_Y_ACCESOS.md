# Licencias y accesos

## Componentes
| Componente | Versión fijada | Licencia | Notas |
|---|---|---|---|
| Odoo Community | imagen `odoo:18.0` | LGPL-3.0 | Solo módulos estándar (crm, sale_management, stock); no se usan módulos Enterprise |
| PostgreSQL | imagen `postgres:16` | PostgreSQL License | Solo en la red interna de Docker |
| n8n | `docker.n8n.io/n8nio/n8n:2.46.7` | Sustainable Use License (*fair-code*) | Permite el uso interno y no comercial; no permite revenderlo como servicio |
| Python | 3.12 (imagen `python:3.12-slim`) | PSF License | |
| FastAPI 0.115.6 · Uvicorn 0.32.1 · Pydantic 2.10.3 | `compuerta/requirements.txt` | MIT / BSD-3 / MIT | |
| pytest · httpx · jsonschema | `compuerta/requirements-dev.txt` | MIT / BSD-3 / MIT | Solo para pruebas |
| Modelo de lenguaje | Google Gemini (`models/gemini-3.5-flash`), configurable | Términos del proveedor | **Es responsabilidad de quien ejecuta**: cuenta, cuota y datos enviados |
| Código del grupo (compuerta, scripts, flujos) | — | Uso académico GE703 | |

## Accesos y secretos
- **No se incluye ninguna clave, token ni contraseña.** `.env.example` solo trae valores `cambiar-esto`, y `.env` está en `.gitignore`.
- `scripts/empaquetar.py` revisa que ningún archivo del ZIP contenga valores de `.env`.
- Los flujos de n8n se exportan **sin credenciales**: los nodos las referencian por nombre.
- El docente usa **su propia clave del modelo**, o el modo **W3**, que no necesita modelo.

| Credencial | Dónde vive | Quién la usa |
|---|---|---|
| `ODOO_MASTER_PASSWORD`, `ODOO_PASSWORD`, `POSTGRES_PASSWORD` | `.env` | Odoo, el seed y la compuerta (solo lectura por XML-RPC) |
| `TOKEN_VENTAS` | `.env` y credencial n8n **Compuerta VENTAS** | W1 (agente), W2 (al registrar el escalamiento) y W3 |
| `TOKEN_GERENCIA` | `.env` y credencial n8n **Compuerta GERENCIA** | **Solo W2**, cuando el dueño envía el formulario |
| `TOKEN_ADMIN` | `.env` | Administrador: `/admin/reiniciar` y `/admin/simulacion` |
| Clave de Gemini | Credencial n8n **Gemini (Agente SIE)** | Nodo «Modelo Gemini» de W1 |
| `N8N_ENCRYPTION_KEY` | `.env` | Cifrado de las credenciales dentro de n8n |

## Exposición de puertos
Los puertos 8069, 8000 y 5678 se publican en `localhost` del equipo anfitrión para la demo. No exponga estos servicios a internet: los tokens son estáticos y las cookies de n8n van sin HTTPS (`N8N_SECURE_COOKIE=false`).
