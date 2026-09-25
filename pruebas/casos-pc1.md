# Casos y criterios de aceptación de PC1

## Revisión de la propuesta

| ID | Caso | Criterio de aceptación | Resultado | Incidencia |
| --- | --- | --- | --- | --- |
| T-01 | Revisar contexto contra SUNAT y S1 | Hechos tributarios separados de productos/sistemas declarados por el equipo | Pendiente de revisión cruzada | — |
| T-02 | Revisar diagrama de arquitectura | Incluye actores, sistemas, interfaces, flujo principal, despliegue y límite | Pendiente de revisión cruzada | — |
| T-03 | Revisar comparativo | Cada criterio tiene fuente, fecha, interpretación y vacío | Pendiente de revisión cruzada | — |
| T-04 | Revisar paquete | README, fuentes, backlog, versiones, aportes e IA enlazados; sin datos sensibles | Pendiente de revisión cruzada | — |

## Prueba de concepto posterior, con datos sintéticos

| ID | Escenario | Criterio de aceptación propuesto | Resultado | Incidencia |
| --- | --- | --- | --- | --- |
| P-01 | Enviar pedido `DEMO-001` desde un canal | Aparece una sola venta vinculada al ID externo | No ejecutado | — |
| P-02 | Reenviar el mismo pedido | No se duplica venta ni movimiento de stock | No ejecutado | — |
| P-03 | Confirmar pedido con stock disponible | Reserva/descuento y estado visibles para atención | No ejecutado | — |
| P-04 | Intentar pedido sin stock suficiente | Se aplica regla acordada y se informa al canal | No ejecutado | — |
| P-05 | Simular comprobante aceptado/rechazado | Se conserva estado y se permite corregir sin perder trazabilidad | No ejecutado | — |
| P-06 | Cortar conexión durante transferencia | Reintento controlado sin duplicados y registro de error | No ejecutado | — |

Antes de ejecutar P-01 a P-06 se necesita sandbox, versión del ERP, configuración peruana, canal definido, reglas aprobadas y datos de prueba. Registrar fecha, ejecutor, capturas anonimizadas y defectos reales en esta tabla, sin anticipar resultados.
