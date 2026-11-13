# Datos sintéticos · PC3

> **No son datos reales de Importaciones MYS Hermanos S.A.C.** Los nombres, productos, cantidades y montos se inventaron para la demostración académica (GE703, G7). Fecha de declaración: **10/11/2026**. La fuente única en código es [`compuerta/app/escenario.py`](../compuerta/app/escenario.py).

## Supuestos comunes
| Supuesto | Valor |
|---|---|
| Empresa / ubicación | `MYS-DEMO` / `TIENDA-DEMO` (almacén principal de Odoo renombrado) |
| Moneda | PEN (soles). Precio final académico, **sin desglose de IGV**: productos y líneas sin impuestos |
| Tope de descuento del vendedor | 5,00 % (`max_seller_discount`) |
| Disponible | **físico − reservado** (`stock.quant.quantity − reserved_quantity`), como en la Semana 11 (120 − 30 = 90) |
| Vigencia de las cotizaciones | Día de ejecución del seed, hasta las 18:00 (hora de Lima, UTC−5) |
| Aceptaciones | Registradas a la hora del seed − 5 min |
| Plazo de decisión del dueño | 10 minutos |
| Vigencia de una aprobación del dueño | 24 horas (`APROBACION_VIGENCIA_HORAS`) |

## Productos y stock (unidades)
| SKU | Producto | Precio (S/) | Físico | Reservado | Disponible |
|---|---|---|---|---|---|
| RAD-7BT | Autoradio Bluetooth 7" (genérico) | 400,00 | 10 | 2 | 8 |
| RAD-10X | Autoradio pantalla 10" (genérico) | 520,00 | 10 | 7 | 3 |

La reserva sale de **dos pedidos confirmados en Odoo de otro cliente** (CLI-DEMO-002): RES-DEMO-001 (2 × RAD-7BT) y RES-DEMO-002 (7 × RAD-10X). Por eso no basta mirar el stock físico.

## Clientes, actores y oportunidades
| ID | Tipo | Detalle |
|---|---|---|
| CLI-DEMO-001 | Cliente (`res.partner.ref`) | Consumidor final, identidad revisada |
| CLI-DEMO-002 | Cliente | Recurrente; es dueño de las reservas |
| VEN-DEMO-01 | Vendedor (VENTAS) | Usuario de Odoo `vendedor01`; oportunidades OPP-DEMO-001 y OPP-DEMO-002 |
| GER-DEMO-01 | Dueño (GERENCIA) | Aprueba descuentos mayores al 5 % y decide reposiciones |
| ADM-DEMO-01 | Administrador | Reinicio y recuperación |
| OPP-DEMO-001 / 002 | `crm.lead` (type = opportunity) | Ambas de CLI-DEMO-001 |

## Cotizaciones
Cada versión es un `sale.order` con `client_order_ref = "<id> v<n>"`. La versión vigente es la mayor que no está anulada.

| Cotización | Oportunidad | Líneas | Descuento | Total (S/) | Estado | Aceptación |
|---|---|---|---|---|---|---|
| COT-DEMO-001 v1 | OPP-DEMO-001 | 5 × RAD-7BT | 5 % | 1 900,00 | sent | ACE-PC3-001 |
| COT-DEMO-002 v1 | OPP-DEMO-002 | 5 × RAD-10X | 5 % | 2 470,00 | sent | ACE-PC3-002 |
| COT-DEMO-003 v1 | OPP-DEMO-001 | 5 × RAD-7BT | 5 % | 1 900,00 | sent | ACE-PC3-004 |
| COT-DEMO-004 v1 | OPP-DEMO-001 | 5 × RAD-7BT | 5 % | 1 900,00 | **cancel** | — |
| COT-DEMO-004 v2 | OPP-DEMO-001 | 5 × RAD-7BT | 10 % | 1 800,00 | sent | ACE-PC3-003 |
| COT-DEMO-004 v3 *(solo si el dueño aprueba; `seed --crear-v3`)* | OPP-DEMO-001 | 5 × RAD-7BT | 10 % | 1 800,00 | sent | ACE-PC3-005 |

> **Cambio respecto de las instrucciones:** el caso E02 usa **COT-DEMO-004** en lugar de COT-DEMO-001 v2. Si la v2 de COT-DEMO-001 existiera, la v1 quedaría obsoleta y el caso N01 devolvería `VERSION_OBSOLETA`, porque los casos deben convivir en la misma base. El equipo eligió esta opción el 10/11/2026. Las reglas no cambian.

## Casos
Los casos se declararon antes de ejecutar, en [`casos_pc3.json`](casos_pc3.json): N01 normal, E01 faltante, E02 descuento sin aprobación, F01 dependencia caída, I01 reintento y A01 inyección. Los resultados observados están en [`evidencias/resultados.md`](../evidencias/resultados.md).
