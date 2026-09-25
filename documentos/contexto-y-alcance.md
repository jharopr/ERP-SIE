# Contexto, problema y alcance

## Evidencia de la empresa

La ficha RUC emitida el 05/09/2026 identifica a **IMPORTACIONES MYS HERMANOS S.A.C.** (RUC 20606915528) como sociedad anónima cerrada activa, con domicilio fiscal habido, fecha de inscripción 18/11/2020 y comienzo de actividades 23/11/2020. Declara CIIU 4649, venta al por mayor de otros enseres domésticos; figura como importador y emisor electrónico de factura desde el 26/11/2021 y boleta desde el 05/06/2023 (SUNAT, pp. 1-2). El registro tributario no describe todos los productos, canales, almacenes ni aplicaciones internas.

## Información reportada por el equipo

La ficha S1, §3, describe autoradios y accesorios para automóviles, clientes conductores y propietarios de vehículos, y procesos de compras, inventario, ventas, atención y posventa. Enumera sistemas de ventas, inventario, facturación y clientes, pero no identifica proveedores, interfaces ni evidencia de uso. S2, §4, agrega observaciones sobre ventas mayoristas/minoristas, tienda y almacén separados y ausencia de equipo de TI; requieren confirmación directa antes de tratarlas como restricciones reales.

## Problema de integración

**Hipótesis de S1, §4:** la atención al cliente no se integra adecuadamente con canales digitales de venta, lo que podría causar demoras y pérdida de oportunidades. No hay línea base ni prueba documentada. La PC1 debe mostrar los eventos a contrastar: recepción del pedido, identificación del cliente, disponibilidad de stock, registro de venta, emisión del comprobante y respuesta al cliente.

## Alcance propuesto

| Primera liberación propuesta | Fuera o pendiente de decisión |
| --- | --- |
| Ventas, inventario, facturación electrónica y conexión de **un** canal digital con atención comercial | Manufactura, planillas, todos los canales digitales, automatización de importaciones, migración completa y despliegue productivo |
| Arquitectura base, interfaces conceptuales, criterios de elección y prueba de flujo | Selección contractual del ERP y partner, presupuesto aprobado y fecha de arranque |

La visión posterior puede incluir compras e importaciones, según S3, §2. El alcance se validará con la empresa; no se presume que los sistemas actuales admitan API ni que un ERP cubra SUNAT/PLE sin configuración o partner.

## Usuarios y resultados por validar

Usuarios candidatos: ventas/atención, almacén, facturación/contabilidad y gerencia. Indicadores candidatos de S3, §2: tiempo de respuesta, pedidos digitales sin doble digitación, diferencia entre stock físico y sistema y comprobantes emitidos sin reproceso. Definir fórmula, fuente y línea base antes de prometer mejoras.
