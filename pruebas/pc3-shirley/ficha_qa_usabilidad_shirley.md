# Mi ficha QA: instalación limpia, navegación, caso normal y stock/servicio

| Campo | Registro |
| --- | --- |
| Curso / empresa | GE703, Grupo 7, UNI-FIIS, 2026-2 / Importaciones MYS Hermanos S.A.C. |
| QA asignada | Shirley Carrión Oré |
| Fecha documental | 12 de noviembre de 2026, America/Lima |
| Qué exige el reparto | Instalación limpia, navegación, caso normal e interpretación de stock/servicio en el **agente de Ballack y en el sistema**; coherencia con el informe; lista de usabilidad y defectos, reproducción y validación final [REP, p. 4] |
| Copia revisada | ZIP `ERP-SIE-main` (rama `main`), descargado el 12/11/2026 |
| Entorno ejecutado | Python 3.13, Linux, solo biblioteca estándar; directorio temporal; sin Odoo, n8n, LLM ni red |
| Autoría de ejecución | Ejecuté el script `ejecutar_qa_shirley.py`, que preparé con apoyo de IA (Claude); las pruebas en vivo del agente quedan pendientes |
| Evidencia | [resultado_qa_shirley.json](evidencias/resultado_qa_shirley.json), [indicadores_servicio.json](evidencias/indicadores_servicio.json), [resumen_shirley.json](evidencias/resumen_shirley.json) (huellas SHA-256) |
| Dictamen global | **ABIERTO.** Comprobé que el prototipo del contrato se instala y funciona limpio; no pude probar el agente ni Odoo porque su código no está en `main`; encontré dos defectos de coherencia ALTA que ya evité en el informe PC3 |

## Reproducción

Desde la raíz del repositorio, con Python 3.10 o superior:

```sh
python pruebas/pc3-shirley/ejecutar_qa_shirley.py
```

Para revalidar sin pisar la evidencia original:

```sh
python pruebas/pc3-shirley/ejecutar_qa_shirley.py --output pruebas/pc3-shirley/evidencias/revalidacion
```

Preparé el script para que copie el simulador y el arnés EP a un directorio temporal, así que **no modifica** las evidencias versionadas de PC2 ni del parcial. Devuelve 1 mientras la prueba del agente esté bloqueada o haya defectos ALTA abiertos en documentos previos; 0 cuando todo pase.

## Lista de pruebas

| ID | Prueba | Sistema | Esperado | Observado | Estado |
| --- | --- | --- | --- | --- | --- |
| SHI-U01 | Instalación limpia del Agente SIE y del sistema Odoo siguiendo solo la guía del ZIP | Agente + Odoo | Arranca desde cero con la guía, sin pasos no escritos ni credenciales en archivos | `agente-sie/` y `app/` **no existen** en `main`. Según la ficha de Adrián, están en `origin/pc3/agente-sie` (8cfbf84) y `origin/sistema-agente` (587eabb) | **BLOQUEADA** → SHI-PC3-001 |
| SHI-U02 | Instalación limpia del prototipo de contrato incluido en el repositorio | Simulador PC2 + arnés EP | Ambos generadores terminan con código 0 en una copia nueva | PC2: 0 (0.18 s). EP: 0, «3 casos, 112 comprobaciones» (0.04 s) | **CONFORME** |
| SHI-U03 | Caso normal | Simulador (hecho) / agente y Odoo (pendiente) | `ACEPTADA / VALIDADA`, total S/ 1,900.00, `order_id: null`, stock intacto | EP-N01 coincide; total 1900.00 PEN; `order_id: null` | **CONFORME en simulador**; pendiente en agente y Odoo |
| SHI-U04 | Interpretación de stock y servicio | Simulador (hecho) / agente (pendiente) | Parcial: 3 de 5, sin reserva, sin fecha, nueva aceptación, señal de 2 unidades sin compra automática | 11 de 11 controles correctos; señal REP-EP-001 con `automatic_action: false`, `purchase_order_id: null` | **CONFORME en simulador**; falta comprobar que el agente lo **explique** así |
| SHI-U05 | Navegación de la interfaz del agente | Agente | Se llega a caso normal, parcial, 10 % y reintento sin ayuda; bitácora y responsable visibles [REP, p. 3] | No ejecutable: interfaz no incluida en `main` | **BLOQUEADA** |
| SHI-U06 | Coherencia informe ↔ sistema ↔ entregas previas | Documentos | Mismos IDs, ubicaciones, estados y límites en informe, presentación y evidencia | 2 defectos ALTA y 1 MEDIA en el consolidado del parcial; el informe PC3 no los repite | **ABIERTO** para presentación; **CONFORME** en el informe PC3 |

### Lista de usabilidad para la ejecución en vivo (SHI-U01, U03, U05)

La marcaré al ejecutar el ZIP final. Cada «No» lo registraré como defecto con pasos, entrada, esperado/observado, evidencia y prioridad.

| # | Pregunta | Sí / No | Evidencia |
| --- | --- | --- | --- |
| 1 | ¿La guía indica versión de Python/Docker y la lista de dependencias fijadas? | | |
| 2 | ¿Se instala en una carpeta nueva sin pasos que no estén escritos en la guía? | | Tiempo total: ___ min |
| 3 | ¿La guía dice cómo comprobar que arrancó (URL, puerto, mensaje de salud)? | | |
| 4 | ¿Hay datos de demo cargados sin escribir credenciales reales en archivos? | | |
| 5 | ¿Desde la pantalla inicial se encuentra el caso normal en ≤ 3 clics o pasos? | | |
| 6 | ¿Se ven el estado, el código, el responsable y el ID de correlación de cada respuesta? | | |
| 7 | ¿El caso parcial muestra cuánto hay, que no reservó, que no hay fecha y la señal de reposición? | | |
| 8 | ¿El 10 % sin autorización se rechaza antes de stock y muestra a quién se escala? | | Ver ficha de Adrián |
| 9 | ¿El reintento muestra que no se duplicó la solicitud? | | |
| 10 | ¿Los mensajes de error dicen qué hacer, sin trazas técnicas para el vendedor? | | |
| 11 | ¿La guía explica cómo recuperarse si Odoo no responde (`PENDIENTE`)? | | |
| 12 | ¿Las cifras y nombres que aparecen coinciden con el informe (S/ 400, 5 unidades, 5 %/10 %, S/ 1,900/1,800)? | | |

## Registro de defectos

Circuito: registrar → asignar a Jharolym, Gabriel o Ballack → corregir → repetir la prueba [REP, p. 4].

| ID | Prioridad | Estado | Pasos y entrada | Esperado / observado | Asignación | Validación de cierre |
| --- | --- | --- | --- | --- | --- | --- |
| SHI-PC3-001 | ALTA | ABIERTO | Descomprimir `main` y buscar la guía del agente | Esperado: agente y Odoo ejecutables desde el entregable. Observado: carpetas ausentes; solo existen en ramas | Ballack (ZIP), con Jharolym y Gabriel | Repetir SHI-U01/U03/U04/U05 sobre `GE703_PC3_Agente_G7_MYS_Hermanos.zip` y completar la lista de usabilidad |
| SHI-PC3-002 | ALTA | ABIERTO en parcial; evitado en PC3 | `GE703_EP_G7_CONSOLIDADO_COMPLETO.md`, líneas 45 y 870 | Esperado: tiendas en Naranjal «La 50», Independencia, y almacén en Carabayllo (5A). Observado: «San Juan de Lurigancho» y una dirección completa | Shirley (informe y presentación); Adrián confirma | El script no encuentra la ubicación en el informe PC3; la presentación usa La 50 / Carabayllo y no publica direcciones |
| SHI-PC3-003 | MEDIA | ABIERTO en parcial | Mismo archivo, línea 714 | Esperado: la ubicación que muestra la evidencia (`TIENDA-DEMO`) o las ubicaciones de 5B. Observado: `ALM-SJL-01` | Shirley / Benjamín | Informe y diapositivas citan el código de la evidencia |
| SHI-PC3-004 | ALTA | ABIERTO en parcial; evitado en PC3 | Mismo archivo, 15 líneas con «inmutable» o «no repudio» | Esperado: la bitácora con huella SHA-256 permite **detectar** cambios; no es inmutable (ficha de Adrián). Observado: se afirma inmutabilidad | Gabriel (redacción técnica) | Informe PC3 sin «inmutable»; en la defensa se explica el límite |
| SHI-PC3-005 | MEDIA | INFORMATIVO | Ficha de Adrián | El escenario PC3 usa `COT-DEMO-004 v2` para el 10 %; el parcial usaba `COT-DEMO-001 v2` | Shirley (yo) | Informe y presentación citan `COT-DEMO-004 v2 / SOL-PC3-E02` para PC3 |
| ADR-PC3-001 | ALTA | ABIERTO (de Adrián) | Ver ficha de Adrián | Lectura de stock antes del rechazo por descuento | Gabriel + Jharolym | Se reporta en el informe como hallazgo abierto hasta su revalidación |

## Observación que dejo (no defecto)

El prototipo visual de `producto/frontend` es de PC1, guarda datos en el navegador y **no** ejecuta las reglas del contrato. No debe mostrarse en la demo como «el sistema» de PC3.

## Cierre

- [x] Instalé limpio el prototipo de contrato y casos normal/parcial/descuento comprobados con evidencia y huellas.
- [x] Calculé los indicadores de servicio sobre los casos y los llevé a 5B, marcados como sintéticos.
- [x] Registré los defectos de coherencia con archivo, línea, prioridad y responsable.
- [ ] Cuando Ballack entregue el ZIP, ejecuto SHI-U01, U03, U04 y U05 y completo la lista de usabilidad.
- [ ] Vuelvo a probar ADR-PC3-001 tras la corrección de Gabriel/Jharolym.
- [ ] Incorporo las capturas de la demo en vivo al anexo del informe.
- [ ] Mi firma y fecha: **pendientes**.
