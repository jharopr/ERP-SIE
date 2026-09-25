# Inventario de fuentes y tratamiento de datos

## Fuentes del análisis

| Fuente | Datos útiles para PC1 | Estado y límite |
| --- | --- | --- |
| Ficha RUC SUNAT, 05/09/2026, pp. 1-2 | Razón social, RUC, tipo, actividad CIIU, condición de importador, emisión electrónica | Evidencia tributaria a esa fecha; no acredita catálogo ni procesos internos |
| Ficha S1, §§3-4 | Productos, clientes y sistemas descritos por el equipo; hipótesis de integración | Declaración académica por confirmar con empresa |
| Comparativo S2, §§2-5 | Alternativas, despliegue, integración y vacíos | Análisis del equipo; no prueba funcionamiento ni precios |
| Estrategia S3, §§2-6 | Alcance, fases, indicadores y riesgos propuestos | Plan de implementación, pendiente de aprobación |

## Diccionario mínimo para la prueba de flujo

| Entidad | Campos mínimos propuestos | Restricción |
| --- | --- | --- |
| Producto | SKU sintético, descripción genérica, unidad, estado | No asumir catálogo real |
| Pedido | ID externo, fecha, canal, SKU, cantidad, estado | ID único e idempotencia |
| Inventario | SKU, ubicación sintética, disponible, reservado, movimiento | Conciliar antes/después |
| Venta | ID ERP, referencia de pedido, total, estado | Trazable al pedido |
| Comprobante | Tipo, serie/número de prueba, ID de venta, estado de aceptación | No emitir comprobantes reales durante la demo |
| Interacción de atención | ID de pedido, fecha de respuesta, estado | Usar cliente ficticio |

## Datos de prueba y datos sensibles

Usar un SKU ficticio como `DEMO-001`, un cliente ficticio y cantidades de ejemplo. No incluir DNI, teléfonos, direcciones, correos, datos de clientes ni capturas del RUC completo. La ficha RUC original contiene datos personales de representantes y socios, por lo que permanece fuera del repositorio. Si se comparte una evidencia, ocultar esos campos y revisar también metadatos y capturas.

Los datos empresariales reales, la calidad de maestros y el motor de base de datos siguen pendientes de autorización y levantamiento. La prueba de concepto debe funcionar con datos sintéticos hasta contar con permiso y controles apropiados.
