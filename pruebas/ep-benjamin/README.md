# EP · Evidencia sintética de Benjamin: frontera CRM–ERP

Estas pruebas complementan el caso de IMPORTACIONES MYS HERMANOS S.A.C., cliente **nuevo del público general y canal físico**. Reutilizan sin modificar `pruebas/pc2/simulador.py` mediante `importlib`, con fixtures nuevas: visita espontánea, cinco autoradios a S/ 400.00, descuento ordinario 5%, total S/ 1,900.00 y disponibilidad inicial de ocho unidades. No hay campaña ni canal remoto en estas fixtures.

Es una **recreación nueva del EP**, no una reproducción literal de PC2: el Word consolidado previo indica cinco unidades de stock y el Markdown v2.1 indica ocho. Aquí se fija explícitamente el supuesto académico de ocho para EP-N01 y EP-E01 y tres para EP-S01. Tampoco se atribuye el umbral 5% a una entrevista verificada: se conserva como política didáctica pendiente de validar con la empresa, al no disponer de un registro primario de entrevista.

Desde la raíz del repositorio, con Python 3.10 o posterior y solo biblioteca estándar:

```sh
python pruebas/ep-benjamin/generar_evidencias.py
```

La ejecución comprueba las expectativas estáticas de `fixtures/casos.json` y falla con código distinto de cero si alguna no coincide. Genera entradas completas, resultados esperado frente a observado, respuesta del reintento, auditoría nativa y comprobaciones por caso en `evidencias/`. [resultados.md](evidencias/resultados.md) es el resumen generado automáticamente de los tres casos y sus 112 comprobaciones; no requiere edición manual. `ejecucion.json` registra hashes SHA-256 de insumos y resultados, entorno y UTC real. Los JSON de cada caso y el resumen son reproducibles; la hora de ejecución del manifiesto cambia.

| Caso | Condición sintética | Estado / código esperado | Límite y siguiente decisión |
| --- | --- | --- | --- |
| EP-N01 | 5 unidades, 5% descuento; stock 8 | `ACEPTADA` / `VALIDADA` | Solicitud evaluada. Sin pedido operativo ni reserva. |
| EP-S01 | 5 unidades solicitadas; stock 3 | `PROMESA_CONDICIONADA` / `DISPONIBILIDAD_PARCIAL` | Déficit 2. Revisar cantidad/plazo y nueva versión/aceptación; sin prometer fecha. |
| EP-E01 | Versión 2, descuento 10%, S/ 1,800; sin aprobación del dueño | `RECHAZADA` / `DESCUENTO_SIN_APROBACION` | Articulación con el análisis de excepción de Adrián: Gerencia decide; no se aprueba anticipadamente. |

`ACEPTADA` es el **estado** de la solicitud y `VALIDADA` su **código** en el contrato 1.0: no son dos etapas, ni significan pedido confirmado o venta cobrada. En los tres casos `order_id` es `null`. La respuesta rechazada por descuento conserva `total: null` según el simulador reutilizado; el importe propuesto S/ 1,800 permanece en la cotización v2 de entrada, sin autorizarse comercialmente.

La cadena documental es `CLI-DEMO-001 → LEAD-EP-001 → OPP-DEMO-001 → COT-DEMO-001 v1 → ACE-EP-001 → SOL-EP-N01` para EP-N01, con correlación `COR-EP-001`. EP-S01 usa `SOL-EP-S01`; EP-E01 usa cotización **v2**, `ACE-EP-002` y `SOL-EP-E01`. SKU `RAD-7BT`, ubicación `TIENDA-DEMO`. Son variantes aisladas del mismo escenario académico, cada una con su base SQLite en memoria; no representan tres operaciones simultáneas. El reintento idéntico devuelve el resultado persistido y deja una sola solicitud y una sola decisión. La auditoría conserva adicionalmente el evento del reintento.

La fecha de negocio **2026-10-24, zona -05:00**, y vigencia hasta las **18:00 de ese día** son simuladas. Las líneas de tiempo muestran actor, hora lógica, objeto y control desde la atención hasta solicitud/respuesta, pero los pasos anteriores al envío son **narrativa didáctica**, no logs de una instalación CRM. La auditoría `audit` sí procede de la ejecución real del simulador, usando esa hora lógica. El instante real de generación se registra por separado en UTC en el manifiesto.

La línea de tiempo común registra consulta del cliente 09:45, lead 09:46, oportunidad 09:48, stock 09:50, cotización v1 09:52, aceptación 09:54, solicitud 09:55 y respuesta 09:55:01. EP-E01 incorpora actualización v2 a las 09:53 y aceptación sintética a las 09:54:30. `business_time` es `2026-10-24T09:55:01-05:00`: recepción, consultas y decisión de la primera evaluación se auditan juntas en esa transacción lógica; el reintento se ejecuta a las 09:56:01. No se presentan esos intervalos como desempeño medido.

La consulta lógica de las 09:50 observa ocho unidades en EP-N01/EP-E01 y tres en la corrida independiente EP-S01. No se representa un cambio de ocho a tres en una operación real ni se inventa su causa. En la variante parcial la disponibilidad de la oferta es condicionada y requiere revisar condiciones con el cliente.

En EP-E01 la aceptación sintética corresponde a la misma v2 y al mismo total de S/ 1,800. Esto permite aislar el control de autorización de descuento; **la aceptación del cliente no sustituye la aprobación del dueño**, ni demuestra que una oferta excepcional haya sido emitida válidamente por la empresa. El caso se rechaza antes de consultar inventario y se entrega como evidencia de apoyo para el análisis de Adrián.

`REP-EP-001`, dentro del resultado EP-S01, es una **señal conceptual** de evaluación P2P por un déficit de dos unidades. La genera el arnés de evidencia después de leer la respuesta parcial; no forma parte del contrato ni de un módulo implantado. Conserva SKU, ubicación, cantidad solicitada/disponible, déficit, hora de observación, referencia al snapshot de entrada, oportunidad, cotización/versión, solicitud, correlación y responsable funcional `DUENO_ABASTECIMIENTO`. No crea compra, pedido, reserva ni fecha de reposición. Tampoco supone que dos sea la cantidad de una futura orden: Abastecimiento deberá evaluar inventario global y reglas aprobadas en otro alcance.

Se comprueban realmente correlación y versión de los objetos de la fixture, aritmética, código/estado, conservación de maestros y stock, idempotencia y persistencia local. La validación de entrada utiliza el control del simulador; la salida comprueba campos del contrato y expectativas del caso, sin pretender ejecutar un motor completo de JSON Schema. Las referencias al lead, segmento y origen verifican consistencia **documental de los fixtures**, no reglas operativas de CRM ni identidad de una persona.

Los precios, stock, aceptación, identidad revisada y umbral del vendedor son sintéticos. Estas pruebas no validan journeys observados ni métricas de servicio, no acreditan Odoo en producción, permisos de Odoo, PostgreSQL, concurrencia de inventario o integración UBLHUB. El límite del EP permanece en **solicitud/respuesta**: no ejecuta pedido operativo, factura, boleta, cobro, entrega, posventa ni P2P. No modifican evidencias anteriores de PC2.
