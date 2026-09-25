# Versiones y decisiones

| Versión | Fecha | Cambio | Estado |
| --- | --- | --- | --- |
| 0.1 | 24/09/2026 | Estructura inicial, comparación y arquitectura conceptual | Sustituida |
| 0.2 | 24/09/2026 | Prototipo visual estático inspirado en Odoo | Base de demostración |
| 0.3 | 25/09/2026 | Contexto real de dos canales, selección Odoo + UBLHUB y proceso comercial mejorado | Sustituida |
| 0.4 | 25/09/2026 | Actores detallados, matriz RACI, diagramas UML/BPMN/C4 y cierre de decisiones abiertas | Vigente |

## Registro de decisiones

| ID | Decisión | Fundamento | Estado |
| --- | --- | --- | --- |
| D-01 | Odoo será el ERP central | Cobertura modular de clientes, ventas e inventario | Adoptada |
| D-02 | UBLHUB gestionará boletas, facturas y guías | Especialización y desacoplamiento tributario | Adoptada; API y contrato son insumos obligatorios de implementación |
| D-03 | Los canales son ERP/presencial y WhatsApp móvil | Corresponden a la operación informada | Adoptada |
| D-04 | WhatsApp se registrará manualmente al inicio | Permite implantar el ERP sin depender de automatización del canal | Adoptada |
| D-05 | La automatización de WhatsApp queda fuera del alcance inicial | La operación inicial usa registro manual trazable | Adoptada |
