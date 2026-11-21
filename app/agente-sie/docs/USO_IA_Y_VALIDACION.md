# Uso de IA y validación

## Qué generó la IA de código
La IA de código (Claude Code, modelo Claude Opus 5.5) construyó el paquete `agente-sie/` siguiendo `INSTRUCCIONES_IA_AGENTE_SIE_PC3.md` (10/11/2026):

| Pieza | Generado por IA | Base humana reutilizada |
|---|---|---|
| Compuerta FastAPI (`compuerta/app/*.py`) | Sí | Motor `TransitionSimulator` y schemas v1.0 del equipo (PC2), **copiados sin cambios** |
| Seed de Odoo (`odoo/seed_odoo.py`) | Sí | Escenario de la sección 3 de las instrucciones |
| Flujos n8n W1–W3 y prompt | Sí (con `scripts/generar_workflows.py`) | Reglas del prompt de la sección 6 |
| Pruebas pytest y `ejecutar_casos.py` | Sí | Casos PC2 del equipo, usados para la equivalencia |
| Documentación (`docs/`, README) | Sí | — |

## Correcciones encontradas al ejecutar con Docker
- Odoo cortaba la creación de la base a los 120 s (`limit_time_real`); se subió a 1800 s.
- Los `curl` del healthcheck quedaban como zombies (Odoo es PID 1); se agregó `init: true`.
- El healthcheck de la compuerta consultaba Odoo; ahora usa `/vivo`, que no lo toca.
- En el Form Trigger v2.2 de n8n la ruta va en `options.path`.

## Decisiones tomadas con el equipo (10/11/2026)
1. **E02 en COT-DEMO-004.** Con COT-DEMO-001 v2 en la misma base, el caso N01 devolvería `VERSION_OBSOLETA`.
2. **Gemini como proveedor inicial.** Se podrá cambiar a Claude reemplazando solo el nodo del modelo.
3. **W2 en dos entradas** (registro del escalamiento y formulario del dueño), en lugar de un nodo *Wait* que bloquee la herramienta del agente. Un bloqueo de 10 min cortaría el chat. El plazo de 10 min lo controla la compuerta (`SIN_DECISION`).

## Desviaciones y hallazgos reportados (sin tocar el contrato ni el motor)
- `pruebas/ep-benjamin/` y `pruebas/ep-jharolym/` **no existen en el repositorio**, en ninguna rama. La equivalencia se probó con los 4 casos PC2 existentes (N01, E01, P01 y T01).
- Las instrucciones citan «8 escenarios y 133 comprobaciones» para el simulador. En el repositorio hay 24 pruebas unitarias (`pruebas/pc2/test_contrato.py`), todas en verde.
- **Extensiones de la compuerta** que no estaban en la especificación: `POST /aceptaciones` (C03, para la v3 de E02), `POST/GET /escalamientos`, `POST /escalamientos/{id}/decision`, `POST /admin/simulacion` (bandera documentada para F01) y `POST /admin/reiniciar`.
- Si Odoo cae **antes** de leer los datos comerciales, la envoltura devuelve PENDIENTE / DEPENDENCIA_NO_DISPONIBLE y lo persiste, para que `reanudar` y la idempotencia funcionen. Sin esto, el motor habría respondido `DATOS_INCONSISTENTES`, que es una decisión definitiva y errónea.

## Cómo se validó
| Validación | Resultado | Evidencia |
|---|---|---|
| El motor de la compuerta es copia exacta del de PC2 (SHA-256) | ✓ | `compuerta/tests/test_motor_equivalente.py` |
| Mismas respuestas y bitácora que el original en los 4 casos PC2 | ✓ | ídem |
| 6 casos PC3, permisos, escalamiento y plazo con Odoo simulado (pytest) | 22/22 ✓ | `cd compuerta && python -m pytest -q` |
| 6 casos PC3 en modo simulado (`ejecutar_casos.py --simulado`) | 6/6 ✓ | `evidencias/` (etiquetado «SIMULADO») |
| Ejecución real con Docker (Odoo 18 + compuerta), 10/11/2026 | 6/6 ✓, stock intacto | `evidencias/resultados.md` (modo «Docker: Odoo 18 + compuerta reales») |
| n8n 2.46.7: importación y publicación, W3 y formulario del dueño (W2) | ✓ | README → «Estado de verificación» |
| Conversación del agente con Gemini (N01, E01, A01) | ⏳ pendiente de la clave de Gemini | `evidencias/agente_*.md` |

## Revisión humana (completar por el equipo)
| Integrante | Qué revisó | Fecha | Firma / ✓ |
|---|---|---|---|
| <nombre> | Reglas y casos esperados (`casos_pc3.json`) frente a la PC2 | | |
| <nombre> | Ejecución en limpio en otra PC siguiendo solo el README | | |
| <nombre> | Prompt del agente y prueba adversarial A01 | | |
| <nombre> | Licencias, ausencia de secretos y contenido del ZIP | | |

La IA no valida en nombre de ningún integrante. Las filas se llenan después de que cada persona revise.
