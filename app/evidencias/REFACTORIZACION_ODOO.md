# Validación de la refactorización a Odoo

La entrada operativa es http://localhost:8088. El portal anterior está archivado y no se monta en Nginx. Se conservaron la base, los volúmenes, el catálogo y el motor histórico; este último es idéntico byte a byte a `pruebas/pc2/simulador.py`.

| Comprobación | Resultado |
| --- | --- |
| Python / contratos, motor, permisos, contexto firmado y regresiones | 39 pruebas correctas |
| Odoo real, mediante su sesión y RPC nativos | 32 comprobaciones correctas |
| Chat real Odoo → n8n → Gemini → herramienta de catálogo | 8 comprobaciones correctas antes del agotamiento de cuota |
| Estados del controlador sin clave, clave rechazada, cuota y modelo ausente | 4 casos simulados correctos, sin cambiar `.env` |
| Componentes Owl con la biblioteca del contenedor | Menú de 11 accesos, tablero, chat, trazabilidad y envío deshabilitado por cuota correctos en DOM simulado |
| Bundles de Odoo | JavaScript y CSS compilados y servidos sin errores |

La prueba nativa creó un contacto, una oportunidad y cotizaciones nuevas. Verificó el rechazo de un descuento del 10 %, escalamiento del vendedor, aprobación del dueño, nueva versión, nueva aceptación y evaluación aceptada. Comprobó que el vendedor no ve el botón de aprobar y tampoco puede invocarlo por RPC, falsificar resultados, cambiar líneas evaluadas o forzar un pedido confirmado. La oferta aprobada tampoco permite alterar su importe o productos. Los saldos físicos y reservas permanecieron iguales.

Resultados reproducibles en [validacion_odoo.json](validacion_odoo.json) y [validacion_chat_odoo.json](validacion_chat_odoo.json). Las familias creadas por la prueba tienen origen `VERIFICACION-ODOO-*` y permanecen como datos de demostración; no se borraron registros del usuario.

La clave Gemini configurada fue aceptada y produjo respuestas reales con productos y precios de Odoo, conservando `VEN-DEMO-01 / AGENTE` en la bitácora. Posteriormente el proveedor devolvió HTTP 429 por límite diario gratuito. W5 clasifica el error de W4 y notifica un código saneado a Odoo por un callback autenticado; Odoo muestra ese estado y deshabilita el envío temporalmente. Este límite externo no afecta al ERP ni a la evaluación determinista. La configuración del proveedor se conservó.

Las respuestas correctas previas y el estado actual se guardan en archivos separados para no presentar una prueba histórica como disponibilidad actual. `scripts/probar_n8n.py` registra el estado no disponible en `validacion_chat_estado_actual.json` cuando corresponde.

No hubo acceso a un navegador de automatización para revisión visual. La validación de componentes se hizo con Owl en DOM simulado y la de permisos, datos, vistas, bundles y flujos contra los servicios reales.
