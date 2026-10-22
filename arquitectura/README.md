# Arquitectura Odoo + UBLHUB

Esta carpeta documenta la solución seleccionada para IMPORTACIONES MYS HERMANOS S.A.C.: **Odoo como ERP central** y **UBLHUB como microservicio de boletas, facturas y guías de remisión**.

Para el **examen parcial**, empezar por la [arquitectura integrada del caso presencial](crm-erp-ep.md), su [diagrama con iconos](diagramas/componentes-crm-erp-ep.svg) y los [casos de arquitectura](diagramas/casos-arquitectura-ep.svg). El aporte de Jharolym conserva cliente nuevo, tienda física y visita espontánea de PC2, y conecta los módulos con el recorrido de Benjamín hasta solicitud/respuesta.

La [arquitectura técnica anterior](crm-erp-pc2.md), su [diagrama histórico](diagramas/componentes-crm-erp-pc2.svg) y el [contrato con siete interfaces](contratos/crm-erp-v1.md) conservan el diseño adelantado durante PC2. El alcance comercial evaluado de PC2 v2.1 se consulta en su [entrega consolidada](../documentos/pc2/entrega-pc2.md). Los archivos de implementación base conservan el contexto operativo de PC1.

## Archivos

| Archivo | Contenido |
| --- | --- |
| [Arquitectura del parcial](crm-erp-ep.md) | Cliente nuevo presencial, C01–C08, I01–I07, sistemas de registro, controles y dependencia conceptual P2P |
| [Ficha de implementación base](erp-base.md) | Actores, flujo, componentes, interfaces, errores, fases y decisiones |
| [Actores y responsabilidades](actores-y-responsabilidades.md) | Definición detallada, permisos, límites y matriz RACI |
| [Decisión y criterios](criterios-seleccion.md) | Fundamento, caso de validación y condiciones de revisión |
| [Ficha de comparación](comparativo-erp.md) | Odoo, StarSoft, Dynamics 365 Business Central y UBLHUB |
| [Diagrama de arquitectura y despliegue](diagramas/arquitectura-despliegue.png) | Usuarios, canales, Odoo, adaptador, UBLHUB, SUNAT y límites de la solución |
| [Catálogo de diagramas](diagramas/README.md) | UML de casos de uso y secuencia, BPMN, C4 y despliegue |

La línea azul representa relaciones internas de la solución. La línea naranja discontinua identifica la integración segura Odoo–UBLHUB, ejercitada en sandbox antes de habilitar producción.
