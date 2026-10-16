# Declaración de uso de IA

En la versión 0.1 del repositorio se utilizó **Codex, asistente de IA de OpenAI**, el 24/09/2026 para leer y resumir los insumos proporcionados, proponer la estructura y redactar documentos Markdown. En la versión 0.2 se usó para programar el prototipo frontend y la herramienta integrada de imágenes de OpenAI para crear un render PNG de autoradio genérico, citado en el [README del frontend](../producto/frontend/README.md). En la versión 0.3 se reorganizó la documentación alrededor de los dos canales reales y de la decisión Odoo + UBLHUB. La IA no entrevistó a la empresa ni ejecutó pruebas reales de ERP o facturación.

El equipo controla las afirmaciones contra los documentos del proyecto, revisa los diagramas y ejecuta la integración en sandbox antes de producción. Todo uso adicional de IA se registra aquí con herramienta, fecha, propósito, artefactos afectados y responsable de revisión.

En la versión 0.4 se utilizó Codex el 25/09/2026 para consolidar actores, responsabilidades y separación de funciones; redactar las vistas UML, BPMN y C4; y eliminar expresiones de decisión abierta. La arquitectura adoptada no fue sustituida: se hizo explícita y verificable.

## PC2 v2.0 · 15/10/2026

Se utilizó **Codex de OpenAI** para leer los insumos académicos proporcionados por el usuario, contrastar referencias oficiales de Odoo, desarrollar el escenario aproximado autorizado, redactar la arquitectura de componentes y los contratos/interfaces, elaborar SVG/Mermaid y programar y ejecutar una simulación local con pruebas automáticas. No se empleó generación de imágenes para el diagrama técnico: es SVG editable elaborado para el proyecto.

| Elemento | Declaración |
| --- | --- |
| Propósito | Preparar el incremento comercial y evidencia revisable del contrato hasta solicitud/respuesta |
| Datos autorizados | Documentos del curso, documentación existente, referencias públicas de Odoo y fixtures sintéticas; sin clientes reales ni credenciales |
| Artefactos | `documentos/pc2`, `arquitectura/crm-erp-pc2.md`, `arquitectura/contratos`, diagrama PC2, proceso, datos/controles y `pruebas/pc2` |
| Ejecución | Los [resultados locales](../pruebas/pc2/evidencias/ejecucion.json) identifican herramienta, entorno, hora y hashes; no fueron ejecutados en Odoo |
| Validación humana | Pendiente por los seis integrantes según [responsabilidades](../documentos/contribuciones.md); la existencia de archivos no implica su aprobación |
| Límites | No entrevistó a la empresa, no ejecutó campañas, no configuró Odoo, no envió WhatsApp, no creó pedidos ni emitió documentos; no hay agente comercial operativo |

Los precios, descuento, existencias, fechas comerciales y campaña son [supuestos declarados](pc2.md). La revisión debe comprobar fuentes, coherencia de diagramas y mensajes, reproducción de pruebas y ausencia de afirmaciones empresariales no verificadas. Los aportes individuales solo se registrarán como realizados después de una revisión o cambio efectivo del integrante.

## PC2 v2.1 · 16/10/2026 · revisión S6 y Word personal

Codex analizó el PDF de Semana 6, simplificó la vista a cuatro módulos Odoo, distinguió canal manual y sistemas externos, revisó contratos 1.1 e I08, condiciones/plazos, calibración Andina y dos métricas. Actualizó la simulación/evidencias y las secciones 3 y 5 del Word de Jharolym con el mismo diagrama. Se conserva la plantilla y las secciones ajenas sin completar. La revisión humana sigue pendiente. No se instaló Odoo ni se ejecutaron servicios externos; los nuevos campos de pago, canal y plazo son supuestos declarados.
