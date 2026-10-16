# Arquitectura e implementación ERP · Importaciones MYS Hermanos

Este repositorio reúne el análisis del negocio, la comparación de soluciones y la arquitectura base para implementar un sistema de gestión en **IMPORTACIONES MYS HERMANOS S.A.C.** (RUC 20606915528).

## Incremento vigente · PC2

La [entrega PC2](documentos/pc2/README.md) incorpora **CRM de Odoo** y documenta el recorrido fuente/lead → oportunidad → cotización → solicitud de transición al ERP. El tramo termina en aceptación, rechazo o promesa condicionada; una falla técnica queda pendiente. Pedido operativo, facturación, entrega y posventa continúan fuera de esta evaluación.

![Arquitectura de componentes CRM–ERP de PC2](arquitectura/diagramas/componentes-crm-erp-pc2.svg)

- [Entrega integrada en cinco secciones](documentos/pc2/entrega-pc2.md).
- [Componentes y sistemas de registro](arquitectura/crm-erp-pc2.md) → [contrato e interfaces I01–I08](arquitectura/contratos/crm-erp-v1.md).
- [Escenario y flujos](procesos/pc2-escenario-y-flujo.md), [datos y controles](datos/pc2-modelo-y-controles.md), [fuentes y supuestos](fuentes/pc2.md).
- [Dos métricas S6](documentos/pc2/metricas-s6.md) y [calibración Andina](documentos/pc2/calibracion-andina-s6.md).
- [Prueba local reproducible y evidencias](pruebas/pc2/README.md): `python pruebas/pc2/generar_evidencias.py`.

**Estado:** arquitectura propuesta y contrato simulado con datos sintéticos. No hay una instalación Odoo acreditada. Los precios/reglas son supuestos y las revisiones humanas del equipo están pendientes. La documentación operativa que sigue corresponde a la línea base de PC1 y su implementación futura.

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
