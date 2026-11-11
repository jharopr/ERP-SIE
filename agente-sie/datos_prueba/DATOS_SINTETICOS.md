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
| VEN-DEMO-01 | Vendedor (VENTAS) | Usuario de Odoo `ven-demo-01`; oportunidades OPP-DEMO-001 y OPP-DEMO-002 |
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

## Catálogo real y escenario extra (para ver el flujo con más datos)
> **Catálogo:** 167 productos **reales** de la empresa (lista `LISTA_PRODUCTOS_EMPRESA_18717.xlsx`, entregada el 11/11/2026): nombre, SKU (código interno), categoría, unidad, código de barras y **precio de venta**. No se carga el precio de costo. **Stock, clientes, oportunidades, cotizaciones y reservas siguen siendo sintéticos.** Conversión: `scripts/importar_catalogo.py` → [`odoo/catalogo.csv`](../odoo/catalogo.csv); detalle en [`odoo/README.md`](../odoo/README.md).

- 169 productos en Odoo: 167 de la empresa + RAD-7BT y RAD-10X (genéricos, de los casos PC3), en 11 categorías y 25 subcategorías. Seis son servicios (sin stock) y los cables se venden por metro.
- El stock sintético es fijo por SKU, dentro de un rango por categoría (por ejemplo, subwoofers de 2 a 8 y tweeters de 6 a 24).
- Tres ventas confirmadas de otros clientes generan reservas: MVH-S215BT 4, TS-G1620F-2 4, TS-A3000LS4 1, STAGE2634 2 y SD-YT0905PRO 1.
- Dos **leads sin convertir** (LEAD-DEMO-201 y 202) muestran el paso «lead → oportunidad» en el CRM.

[`odoo/escenario_extra.json`](../odoo/escenario_extra.json) agrega 4 clientes sintéticos (taller mayorista, consumidor final, empresa con RUC y recurrente) y 5 cotizaciones con productos reales:

| Cotización | Oportunidad / Cliente | Aceptación | Contenido | Total (S/) | Resultado (verificado 11/11/2026) |
|---|---|---|---|---|---|
| COT-DEMO-101 v1 | OPP-DEMO-101 / CLI-DEMO-003 | ACE-DEMO-101 | 6 autorradios Pioneer MVH-S215BT + 6 pares de parlantes Pioneer TS-G1620F-2, 3 % | 2 677,20 | ACEPTADA / VALIDADA |
| COT-DEMO-102 v1 | OPP-DEMO-102 / CLI-DEMO-004 | ACE-DEMO-102 | Pantalla Android 9" SD-YT0905PRO + parlantes JBL STAGE2634 | 690,00 | ACEPTADA / VALIDADA |
| COT-DEMO-103 v1 | OPP-DEMO-103 / CLI-DEMO-005 | ACE-DEMO-103 | 3 subwoofers Pioneer TS-A3000LS4 + 3 amplificadores GM-A6704, 5 % | 3 106,50 | PROMESA_CONDICIONADA (TS-A3000LS4: 2 de 3) + REP; aviso al dueño |
| COT-DEMO-104 v1 | OPP-DEMO-104 / CLI-DEMO-006 | ACE-DEMO-104 | 2 componentes JBL GTO609C + amplificador ION.4, 8 % | 1 352,40 | RECHAZADA / DESCUENTO_SIN_APROBACION; aviso al dueño |
| COT-DEMO-105 v1 | OPP-DEMO-105 / CLI-DEMO-004 | — (no aceptada) | Autorradio Pioneer DEH-S4250BT + filtro RS-NF04 | 490,00 | RECHAZADA / ACEPTACION_INVALIDA |
