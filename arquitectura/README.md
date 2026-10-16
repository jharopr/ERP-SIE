# Arquitectura Odoo + UBLHUB

Esta carpeta documenta la solución seleccionada para IMPORTACIONES MYS HERMANOS S.A.C.: **Odoo como ERP central** y **UBLHUB como microservicio de boletas, facturas y guías de remisión**.

Para PC2, empezar por [Arquitectura CRM–ERP](crm-erp-pc2.md), su [diagrama de componentes](diagramas/componentes-crm-erp-pc2.svg) y el [contrato con siete interfaces](contratos/crm-erp-v1.md). Incorporan CRM integrado en Odoo y extensiones propuestas; el alcance termina en la respuesta a la solicitud. Los archivos de implementación base conservan el contexto operativo de PC1.

## Archivos

| Archivo | Contenido |
| --- | --- |
| [Ficha de implementación base](erp-base.md) | Actores, flujo, componentes, interfaces, errores, fases y decisiones |
| [Actores y responsabilidades](actores-y-responsabilidades.md) | Definición detallada, permisos, límites y matriz RACI |
| [Decisión y criterios](criterios-seleccion.md) | Fundamento, caso de validación y condiciones de revisión |
| [Ficha de comparación](comparativo-erp.md) | Odoo, StarSoft, Dynamics 365 Business Central y UBLHUB |
| [Diagrama de arquitectura y despliegue](diagramas/arquitectura-despliegue.png) | Usuarios, canales, Odoo, adaptador, UBLHUB, SUNAT y límites de la solución |
| [Catálogo de diagramas](diagramas/README.md) | UML de casos de uso y secuencia, BPMN, C4 y despliegue |

La línea azul representa relaciones internas de la solución. La línea naranja discontinua identifica la integración segura Odoo–UBLHUB, ejercitada en sandbox antes de habilitar producción.
