# Versiones y decisiones

| Versión | Fecha | Cambio | Estado |
| --- | --- | --- | --- |
| 0.1 | 24/09/2026 | Estructura inicial, comparación y arquitectura conceptual | Sustituida |
| 0.2 | 24/09/2026 | Prototipo visual estático inspirado en Odoo | Base de demostración |
| 0.3 | 25/09/2026 | Contexto real de dos canales, selección Odoo + UBLHUB y proceso comercial mejorado | Sustituida |
| 0.4 | 25/09/2026 | Actores detallados, matriz RACI, diagramas UML/BPMN/C4 y cierre de decisiones abiertas | Línea base PC1 |
| PC2 v2.0 | 15/10/2026 | CRM de Odoo, componentes C01–C08, interfaces I01–I07, contrato 1.0, datos/controles y prueba local reproducible | Incremento documentado; revisión humana pendiente |

## Registro de decisiones

| ID | Decisión | Fundamento | Estado |
| --- | --- | --- | --- |
| D-01 | Odoo será el ERP central | Cobertura modular de clientes, ventas e inventario | Adoptada |
| D-02 | UBLHUB gestionará boletas, facturas y guías | Especialización y desacoplamiento tributario | Adoptada; API y contrato son insumos obligatorios de implementación |
| D-03 | Los canales son ERP/presencial y WhatsApp móvil | Corresponden a la operación informada | Adoptada |
| D-04 | WhatsApp se registrará manualmente al inicio | Permite implantar el ERP sin depender de automatización del canal | Adoptada |
| D-05 | La automatización de WhatsApp queda fuera del alcance inicial | La operación inicial usa registro manual trazable | Adoptada |

## Decisiones del incremento PC2

El [registro D-PC2-01 a D-PC2-08](../fuentes/pc2.md#3-decisiones-de-diseño-trazables) conserva las decisiones nuevas: CRM integrado, control de transición propuesto, contrato cerrado, fuentes oficiales por objeto, idempotencia/atomicidad y separación entre promesa, pendiente y aceptación de solicitud. Una aceptación PC2 no confirma el pedido operativo. Los componentes de integración tributaria de PC1 quedan como continuidad posterior.
