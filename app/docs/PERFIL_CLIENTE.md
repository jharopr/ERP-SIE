# Perfil comercial del cliente

## Propósito
Conocer a cada cliente con datos de sus compras para **recomendarle productos** y ayudar al **gerente** a decidir excepciones (por ejemplo, un descuento mayor al 5 %). El perfil **no cambia los topes de descuento**: eso exigiría modificar las reglas del contrato y lo decide el negocio (ver «Fase 3»).

## Quién lo calcula
**Odoo, con reglas fijas** (`mys_erp/models/contacto.py`), no el modelo de lenguaje: las mismas cifras dan siempre el mismo nivel y cualquiera puede revisarlo. Se recalcula:
- cada día, con la tarea programada «MYS: perfil comercial de clientes» (`mys_erp/data/cron.xml`);
- con el botón **Recalcular perfil** de la ficha del cliente;
- al ejecutar el seed (`python scripts/iniciar.py`).

## Fuente
Ventas **confirmadas** del cliente en los **últimos 180 días** (`sale.order` en estado «Orden de venta»).

## Indicadores
| Indicador | Cálculo |
|---|---|
| Compras (6 meses) | Número de ventas confirmadas |
| Monto (6 meses) | Suma de sus totales |
| Unidades (6 meses) | Cantidades de productos físicos; sin servicios ni productos vendidos por metro (cables) |
| Ticket promedio | Monto ÷ compras |
| Última compra / días sin comprar | Fecha de la última venta confirmada (sin límite de tiempo) |
| Inactivo | Más de 90 días sin comprar |
| Descuento promedio obtenido | Descuento en soles ÷ importe de lista de lo comprado |
| Cotizaciones que terminan en compra | Ventas ÷ cotizaciones resueltas (compradas, anuladas o vencidas sin compra); las vigentes no cuentan |
| Qué compra más | 3 categorías por importe y 3 productos por cantidad |
| Complementos sugeridos | Categorías complementarias de las que más compra y que todavía no compra |

## Nivel
Se evalúa en este orden y se guarda el **motivo**:

| Nivel | Regla |
|---|---|
| Nuevo | Sin compras confirmadas en 6 meses |
| Mayorista | Monto ≥ S/ 5 000 **o** unidades ≥ 30 en 6 meses |
| Frecuente | 3 o más compras en 6 meses |
| Ocasional | 1 o 2 compras en 6 meses |

Si además lleva más de 90 días sin comprar, el motivo agrega «Atención: N días sin comprar».

## Dónde se ve
- Ficha del cliente → pestaña **Perfil comercial**; lista de contactos (columna Nivel).
- **Decisión del dueño/gerente** (bloque «Perfil del cliente») y el **correo** de aviso.
- **Agente SIE**: herramienta `perfil_cliente` (solo lectura, `GET /clientes-perfil`). El agente repite el nivel y su motivo, recomienda complementos con `buscar_productos` y nunca autoriza descuentos.

## Datos de prueba
`app/datos/historial_compras.json`: pedidos SINTÉTICOS con productos reales del catálogo. Se confirman y su entrega se cancela, para no reservar ni descontar stock de los casos PC3. Resultado esperado: CLI-DEMO-003 y CLI-DEMO-002 mayoristas, CLI-DEMO-006 frecuente, CLI-DEMO-001 ocasional e inactivo, CLI-DEMO-005 nuevo con alerta de inactividad.

## Siguientes fases (no implementadas)
1. **Calificación de leads** nuevos (origen, interés, urgencia, tipo de cliente), que aún no tienen historial.
2. **Topes de descuento por nivel** (p. ej. 5 % general y 8 % mayorista): cambia las reglas del contrato CRM–ERP; requiere acuerdo del negocio.
3. Datos de pago y crédito cuando se integre la facturación.
