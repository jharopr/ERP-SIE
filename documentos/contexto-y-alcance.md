# Ficha de la empresa: contexto, problema y alcance

## Empresa y operación

**IMPORTACIONES MYS HERMANOS S.A.C.** comercializa autoradios y accesorios para vehículos. La ficha RUC registra a la empresa como activa, importadora y emisora electrónica de facturas y boletas. El detalle del catálogo, los volúmenes y las reglas comerciales deberá validarse durante el levantamiento.

## Situación actual

Las ventas ingresan por dos canales:

![Resumen de la situación actual: venta presencial, WhatsApp móvil manual y falta de integración entre ventas, clientes, inventario y facturación](../imagenes/situacion%20actual.png)

*Resumen visual de los canales actuales y de la necesidad de centralizar la operación en un ERP.*

1. **Presencial:** el cliente es atendido en el local. Actualmente falta un ERP que concentre el registro comercial; en la solución objetivo este canal se registrará directamente en Odoo.
2. **WhatsApp móvil:** una persona recibe consultas y pedidos manualmente. El canal no está automatizado ni integrado con inventario, clientes o facturación.

La ausencia de un sistema central dificulta conocer el historial del cliente, mantener una sola versión del stock, dar seguimiento al pedido y enlazar la venta con su comprobante. El problema principal no es WhatsApp por sí mismo, sino la fragmentación del proceso comercial.

## Tipos de cliente propuestos

El ERP debe manejar una ficha única de cliente y permitir una clasificación inicial:

| Tipo | Necesidad principal | Tratamiento propuesto |
| --- | --- | --- |
| Consumidor final | Compra ocasional y atención rápida | Datos mínimos, boleta y seguimiento del pedido |
| Cliente con factura | Compra asociada a RUC | Validación de razón social y emisión de factura |
| Cliente recurrente | Historial y atención consistente | Contactos, compras anteriores y preferencias autorizadas |
| Cliente mayorista | Volumen, condiciones y precios acordados | Lista de precios, límites comerciales y seguimiento de deuda si aplica |

Las categorías no deben duplicar personas o empresas: un cliente conserva un registro único y puede cambiar de segmento según reglas aprobadas.

## Objetivo de mejora

Centralizar en Odoo clientes, cotizaciones, pedidos, inventario y ventas; delegar a UBLHUB la emisión y consulta de boletas, facturas y guías de remisión; y dejar trazabilidad del canal de origen. Con ello se busca:

- reducir doble digitación y pedidos omitidos;
- consultar stock desde una única fuente;
- diferenciar clientes sin crear registros duplicados;
- relacionar pedido, venta, movimiento de inventario y documento electrónico;
- conocer el estado de atención y medir tiempos por canal.

## Alcance inicial

| Incluido | Posterior o sujeto a validación |
| --- | --- |
| Clientes, productos, ventas, inventario, dos canales de origen, boletas, facturas, guías y reportes básicos | Automatización de WhatsApp, compras/importaciones completas, contabilidad avanzada, campañas y comercio electrónico |
| Odoo como sistema central y UBLHUB como microservicio tributario | Integraciones adicionales y personalizaciones no justificadas por una brecha validada |

## Indicadores iniciales

- tiempo desde la solicitud hasta el registro del pedido;
- porcentaje de pedidos de WhatsApp registrados una sola vez;
- diferencia entre stock físico y stock del ERP;
- porcentaje de documentos electrónicos procesados sin reproceso;
- clientes duplicados detectados y corregidos.

Cada indicador requiere fórmula, responsable, fuente y línea base antes de fijar una meta.
