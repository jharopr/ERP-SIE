# Fuentes, fecha de acceso y uso de IA

Fecha de acceso de todas las fuentes en línea: **10/11/2026**.

## Fuentes técnicas consultadas
| Fuente | Para qué se usó | URL |
|---|---|---|
| Documentación de n8n: instalación con Docker | Versión estable fijada (2.46.7), volumen `/home/node/.n8n` y variables de entorno | https://docs.n8n.io/hosting/installation/docker/ |
| Imagen oficial de Odoo en Docker Hub | Imagen `odoo:18.0`, variables `HOST`, `USER` y `PASSWORD`, y `ODOO_RC` | https://hub.docker.com/_/odoo |
| Documentación de la API externa de Odoo 18 (XML-RPC) | `/xmlrpc/2/common`, `/xmlrpc/2/object`, `search_read` y `execute_kw` | https://www.odoo.com/documentation/18.0/developer/reference/external_api.html |
| API de Google Gemini (AI Studio) | Validación de la clave y modelos disponibles; se eligió `gemini-3.5-flash` porque `gemini-2.5-flash` ya no se ofrece a cuentas nuevas | https://ai.google.dev/gemini-api/docs |
| FastAPI | Framework de la compuerta | https://fastapi.tiangolo.com/ |
| Licencias de n8n (Sustainable Use License) y de Odoo Community (LGPL-3) | [LICENCIAS_Y_ACCESOS.md](LICENCIAS_Y_ACCESOS.md) | https://docs.n8n.io/sustainable-use-license/ · https://www.odoo.com/documentation/18.0/legal/licenses.html |

## Fuentes internas del grupo
| Fuente | Uso |
|---|---|
| `arquitectura/contratos/crm-erp-v1.md` y los schemas v1.0 | Contrato de la compuerta (I03, R01–R12, estados y códigos) |
| `pruebas/pc2/simulador.py` y sus fixtures | Motor de reglas, reutilizado **sin cambios** |
| `INSTRUCCIONES_IA_AGENTE_SIE_PC3.md` | Especificación del paquete PC3 |
| Consigna oficial PC3 (rúbrica del curso GE703) | Requisitos del Agente SIE |

## Datos
Todos los datos del paquete son **sintéticos** y no representan a Importaciones MYS Hermanos S.A.C. Supuestos, unidades y rangos: [DATOS_SINTETICOS.md](../datos_prueba/DATOS_SINTETICOS.md).

## Uso de IA y validación humana
- IA de código: Claude Code (Claude Opus 5.5). Detalle de qué generó, qué decidió el equipo y cómo se validó: [USO_IA_Y_VALIDACION.md](USO_IA_Y_VALIDACION.md).
- IA dentro del producto: el agente W1 usa Google Gemini (`gemini-3.5-flash`) solo para interpretar, llamar herramientas y explicar. Las decisiones las toma la compuerta, con reglas deterministas.
- La validación humana de cada integrante se registra en la tabla de [USO_IA_Y_VALIDACION.md](USO_IA_Y_VALIDACION.md).
