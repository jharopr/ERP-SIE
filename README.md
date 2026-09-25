# Arquitectura e implementación ERP · Importaciones MYS Hermanos

Este repositorio reúne el análisis del negocio, la comparación de soluciones y la arquitectura base para implementar un sistema de gestión en **IMPORTACIONES MYS HERMANOS S.A.C.** (RUC 20606915528).

## Situación y decisión

- La empresa vende por dos canales: **atención presencial registrada directamente en el ERP** y **WhatsApp móvil**, hoy atendido manualmente.
- La operación necesita centralizar clientes, pedidos, inventario, ventas y seguimiento para evitar registros dispersos, consultas manuales de stock y pérdida de trazabilidad.
- La solución seleccionada es **Odoo como ERP central** y **UBLHUB como microservicio de facturación electrónica** para boletas, facturas y guías de remisión.
- StarSoft y Microsoft Dynamics 365 Business Central permanecen solo como alternativas evaluadas en la comparación; ya no son candidatos activos.

## Documentos base

Los documentos base se identifican por nombres funcionales:

1. **Ficha de la empresa**: contexto, operación actual, clientes, canales y problema.
2. **Ficha de comparación de ERPs**: comparación de Odoo, StarSoft, Microsoft Dynamics 365 Business Central y UBLHUB.
3. **Ficha de implementación base del ERP**: alcance, arquitectura, fases, riesgos y criterios de aceptación.

## Alcance inicial

La primera liberación contempla gestión de clientes, ventas por ambos canales, inventario, emisión electrónica mediante UBLHUB y reportes operativos básicos. WhatsApp continúa siendo atendido por una persona y cada pedido se registra manualmente en Odoo. La automatización del canal está fuera del alcance inicial.

## Estructura

| Ruta | Contenido |
| --- | --- |
| [`documentos/`](documentos/README.md) | Fichas, alcance, plan de implementación, decisiones y versiones |
| [`arquitectura/`](arquitectura/README.md) | Arquitectura Odoo + UBLHUB, interfaces y comparación de alternativas |
| [`procesos/`](procesos/README.md) | Proceso actual y proceso objetivo para los dos canales |
| [`datos/`](datos/README.md) | Entidades, fuentes operativas y tratamiento de datos |
| [`producto/`](producto/README.md) | Backlog y prototipo visual del ERP |
| [`pruebas/`](pruebas/README.md) | Casos funcionales y criterios de aceptación |
| [`fuentes/`](fuentes/README.md) | Fuentes técnicas y comerciales usadas para comparar soluciones |

## Ruta de lectura

1. Revisar el [contexto y alcance](documentos/contexto-y-alcance.md).
2. Leer el [flujo comercial](procesos/flujos-prioritarios.md).
3. Consultar la [comparación de soluciones](arquitectura/comparativo-erp.md) y la [decisión](arquitectura/criterios-seleccion.md).
4. Revisar los [actores y responsabilidades](arquitectura/actores-y-responsabilidades.md) y el [catálogo de diagramas](arquitectura/diagramas/README.md).
5. Revisar la [arquitectura base](arquitectura/erp-base.md), el [plan de implementación](documentos/plan-implementacion-erp.md) y el [backlog](producto/backlog.md).

No se deben publicar DNI, teléfonos, correos personales, direcciones completas, datos reales de clientes ni reportes RUC íntegros. Las pruebas deben utilizar información sintética o anonimizada.
