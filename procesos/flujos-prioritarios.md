# Flujo prioritario de la primera liberación

## Situación actual por observar

La ficha S1, §4, plantea una desconexión entre atención al cliente y canales digitales. No documenta el canal, los sistemas ni el número de registros manuales. S2, §4, menciona desorden en clientes mayoristas, pero no aporta evidencia operativa. Por eso el flujo **actual** no se dibuja como hecho; debe levantarse con los usuarios y al menos un pedido anonimizado.

## Flujo objetivo propuesto

1. El cliente crea o solicita un pedido en un canal digital identificado.
2. La interfaz transfiere un identificador único de pedido y datos mínimos al módulo de ventas/atención.
3. Ventas consulta disponibilidad en inventario y confirma o rechaza el pedido según regla acordada.
4. La confirmación genera reserva o movimiento de stock trazable.
5. Facturación emite el comprobante que corresponda y registra aceptación o rechazo del servicio tributario configurado.
6. Atención comunica estado al cliente desde un registro único; gerencia consulta indicadores de operación.

## Reglas, eventos y controles por validar

| Elemento | Propuesta | Pregunta de validación |
| --- | --- | --- |
| Regla de unicidad | No crear dos ventas por el mismo identificador externo | ¿El canal entrega un ID estable? |
| Regla de stock | No confirmar cantidad superior a disponibilidad validada | ¿Se permite preventa o stock negativo? |
| Evento crítico | Rechazo del comprobante o pérdida de conectividad | ¿Cuál es el procedimiento actual de contingencia? |
| Control interno | Separar permisos de venta, ajuste de stock y anulación | ¿Qué roles existen y quién autoriza excepciones? |
| Control de datos | Registrar cambios y evitar datos personales en evidencias | ¿Qué datos se pueden usar en sandbox? |

La prueba reproducible se define en [pruebas/casos-pc1.md](../pruebas/casos-pc1.md).
