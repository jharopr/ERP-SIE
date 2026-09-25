# Arquitectura Odoo + UBLHUB

Esta carpeta documenta la solución seleccionada para IMPORTACIONES MYS HERMANOS S.A.C.: **Odoo como ERP central** y **UBLHUB como microservicio de boletas, facturas y guías de remisión**.

## Archivos

| Archivo | Contenido |
| --- | --- |
| [Ficha de implementación base](erp-base.md) | Actores, flujo, componentes, interfaces, errores, fases y decisiones |
| [Decisión y criterios](criterios-seleccion.md) | Fundamento, caso de validación y condiciones de revisión |
| [Ficha de comparación](comparativo-erp.md) | Odoo, StarSoft, Dynamics 365 Business Central y UBLHUB |
| [Diagrama de arquitectura y despliegue](diagramas/arquitectura-despliegue.png) | Usuarios, canales, Odoo, adaptador, UBLHUB, SUNAT y límites de la solución |

La línea azul representa relaciones incluidas en la propuesta. La línea naranja discontinua identifica la integración Odoo–UBLHUB que debe validarse mediante API y ambiente de pruebas.
