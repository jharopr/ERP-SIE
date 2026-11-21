# Análisis comercial del agente · rotación, segmentación y campañas

Complementa [ARQUITECTURA_AGENTE.md](ARQUITECTURA_AGENTE.md). Son dos herramientas **de solo lectura**: Odoo calcula las cifras con reglas fijas, la compuerta filtra y ordena, y el agente solo las repite. Si una cifra no sale de una herramienta, el agente responde «no tengo ese dato en el sistema» (regla 0 del prompt `p-1.13`).

## Rotación de productos · `rotacion_productos` → `GET /analisis/rotacion`

| Dato | Cómo se calcula (Odoo, `product.product.mys_rotacion`) |
|---|---|
| Vendidas en el periodo | Unidades de líneas de venta **confirmadas** en los últimos N días (90 por defecto, entre 7 y 365). Excluye los clientes de prueba de carga `CARGA-…` |
| Última venta / días sin venta | Fecha del último pedido confirmado con ese producto (cualquier fecha). «Nunca vendido» si no hay ninguno |
| Stock disponible | Físico − reservado en la ubicación de la tienda |
| Días de cobertura | Stock disponible ÷ (vendidas ÷ días del periodo) |
| Valor en stock | Disponible × precio de lista (no es costo) |

**Clasificación:** sin stock → «Sin stock disponible»; sin ventas en el periodo → «Sin ventas en el periodo»; cobertura de 60 días o menos → alta; de 61 a 180 días → media; más de 180 días → baja.

- `orden=menor` ordena así: menos vendidas, luego más tiempo sin venderse («nunca vendido» va primero) y luego más dinero parado.
- `orden=mayor` ordena por unidades vendidas.

El usuario técnico `sie-lectura` **no puede leer pedidos de venta** que no sean cotizaciones COT-…, y esa regla se mantiene. Odoo devuelve solo totales por SKU, sin clientes ni pedidos. Es el mismo patrón que `mys_analyze_discount`.

## Segmentación de clientes · `segmentar_clientes` → `GET /analisis/clientes`

| Capacidad de compra | Monto comprado en 6 meses (perfil diario de Odoo) |
|---|---|
| ALTA | S/ 5 000 o más (igual al umbral de cliente mayorista) |
| MEDIA | De S/ 1 000 a S/ 4 999,99 |
| BAJA | Alguna compra, menos de S/ 1 000 |
| SIN_COMPRAS | Ninguna compra confirmada en 6 meses |

- **Con `categoria`**, la herramienta devuelve solo clientes afines: primero los que **ya compran** esa categoría y después aquellos a quienes se les **sugiere como complemento** de lo que compran.
- **Alcance:** un vendedor con sesión de Odoo ve **solo los clientes que tiene asignados**; el gerente ve toda la cartera.
- `dias_sin_comprar` es `null` si el cliente nunca compró. No se muestra «0 días».

## Campañas
El prompt fija esta secuencia:
1. `rotacion_productos` con `orden=menor`, para elegir el producto con datos.
2. `segmentar_clientes` con la categoría de ese producto, para definir el público.
3. Opcionalmente, `perfil_cliente` o `buscar_productos` para elegir un complemento.

La campaña se presenta como **sugerencia**. Un descuento de más de 5 % lo sigue decidiendo el gerente.

## Correcciones incluidas en esta entrega

| Problema detectado en pruebas con el chat | Corrección |
|---|---|
| El agente afirmaba «el producto que menos rota» sin ninguna herramienta que lo midiera | Herramienta de rotación y regla 0: solo afirma cifras que devuelve una herramienta |
| «Agrega 1 kit de 4 gauge más» elegía otro kit del catálogo (COBRA-4GX) | Sinónimos en la búsqueda (gauge = calibre). Los números no coinciden dentro de otros números («4» no coincide con «1400W»). Tienen prioridad las líneas que ya están en la cotización. `sumar` admite cantidades relativas |
| «Sube a 2» (desde 6) bajaba la cantidad sin avisar, y el modelo copió mal el total (S/ 2 026 en lugar de S/ 1 026) | Cada línea indica `cambio` («cantidad baja de 6 a 2»). La compuerta arma `resumen_para_el_vendedor` con las cifras exactas y `advertencias`, y el agente lo copia tal cual |
| Un vendedor podía proponer cambios en cotizaciones de otro vendedor | 403 si la versión vigente pertenece a otro vendedor |
| El agente daba por buena una aprobación de descuento ya vencida | `situacion_hoy` en cada aprobación («vigente» o «VENCIDA: hace falta una nueva decisión del gerente») |

Pruebas: `py -3.11 -m pytest agente-sie/compuerta` → 68 correctas, 12 de ellas nuevas en `tests/test_analisis.py`.
