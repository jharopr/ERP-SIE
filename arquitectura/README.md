# Arquitectura ERP base de PC1

Esta carpeta documenta una **propuesta conceptual y neutral respecto del producto ERP** para IMPORTACIONES MYS HERMANOS S.A.C. La primera liberación propuesta se limita a **WhatsApp como único canal digital**, ventas y atención comercial, inventario y facturación electrónica. Los sistemas actuales y las interfaces disponibles siguen pendientes de confirmación con la empresa.

## Archivos

| Archivo | Contenido |
| --- | --- |
| [Arquitectura ERP base](erp-base.md) | Actores, contexto, flujo, componentes, interfaces, despliegue, decisiones y límites |
| [Criterios de selección](criterios-seleccion.md) | Criterios y caso común para evaluar Odoo y Business Central |
| [Comparativo ERP](comparativo-erp.md) | Evidencia de S2, vacíos y demostraciones pendientes; StarSoft como referencia local |
| [Diagrama de contexto e integración](diagramas/arquitectura-contexto-integracion.png) | Flujo de WhatsApp a ERP y retorno al cliente |
| [Diagrama de despliegue](diagramas/arquitectura-despliegue.png) | Usuarios, plataforma SaaS y servicios externos |

Las fuentes editables de los dos PNG son [contexto e integración SVG](diagramas/arquitectura-contexto-integracion.svg) y [despliegue SVG](diagramas/arquitectura-despliegue.svg). Cada gráfico usa fondo blanco y relación 16:9. El azul oscuro delimita el ERP, el verde identifica roles internos, el gris los servicios externos y el naranja señala integraciones pendientes. Las líneas continuas representan relaciones incluidas en la propuesta; las discontinuas, integraciones que requieren demostración. **ND** significa no documentado.

Las afirmaciones se marcan como **Evidencia**, **Interpretación**, **Propuesta**, **Supuesto**, **Pendiente** o **ND**. Las decisiones del documento no equivalen a una aprobación de la empresa. Los insumos son la [ficha S1](../documentos/contexto-y-alcance.md), el [taller S2](../fuentes/registro-fuentes.md), la [estrategia S3](../documentos/plan-desarrollo-pc1.md) y el [backlog](../producto/backlog.md).
