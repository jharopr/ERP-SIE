# Criterios de selección y decisión provisional

## Decisión provisional

**Propuesta:** evaluar una arquitectura ERP modular SaaS con una capa de integración para WhatsApp, manteniendo abierta la selección del producto hasta realizar demostraciones, pruebas equivalentes, validación de facturación electrónica y comparación de costos. Odoo y Microsoft Dynamics 365 Business Central son los candidatos principales de S2; StarSoft se conserva como referencia local. No hay marca elegida ni puntajes asignados.

## Criterios para las demostraciones

| Criterio | Pregunta verificable | Evidencia exigida |
| --- | --- | --- |
| Integración con WhatsApp | ¿Cómo llega y vuelve un mensaje o pedido? | Mecanismo autorizado, versión, partner y demostración; API actual de la empresa **ND** |
| Flujo integrado de venta | ¿Se registra una sola venta por pedido de prueba? | Rastro del identificador externo y venta creada |
| Consistencia entre venta e inventario | ¿Se consulta y reserva o descuenta la cantidad correcta? | Estado antes y después del caso común |
| Facturación electrónica peruana | ¿Se genera factura o boleta de prueba y se registra aceptación, observación o rechazo? | Demo con localización y ruta OSE, PSE o SUNAT identificadas |
| Despliegue SaaS | ¿Se accede por navegador sin infraestructura local de la empresa? | Modalidad contractual y arquitectura del proveedor |
| Continuidad operativa | ¿Qué ocurre ante caída de conexión o servicio? | SLA, respaldo, monitoreo y procedimiento de contingencia |
| Costo total | ¿Cuánto cuestan licencias, implementación, integración y operación? | Cotizaciones bajo el mismo alcance, plazo y número de usuarios por confirmar |
| Soporte | ¿Quién resuelve incidentes y en qué plazo? | Alcance y horarios del proveedor o partner por escrito |
| Extensibilidad | ¿Se adapta la interfaz sin modificar el núcleo? | Documentación técnica y prueba en sandbox |
| Capacidad de demostrar el flujo | ¿Puede completarse el caso de principio a fin? | Registro de pasos, versión, configuración, fallos y condiciones |

**Interpretación:** el taller S2 documenta despliegue y extensibilidad generales, pero no demuestra este flujo de WhatsApp ni cobertura tributaria concreta. Una función **ND** no equivale a ausencia de capacidad; exige verificación. No se inventan pesos, puntajes ni precios.

## Caso común para Odoo y Business Central

Ejecutar con datos ficticios y el mismo escenario en ambos productos:

1. Recibir un pedido de prueba desde WhatsApp o, si el acceso aún no está disponible, registrar la imposibilidad técnica como **pendiente**.
2. Crear **una sola venta** vinculada al identificador externo de la conversación.
3. Consultar disponibilidad en inventario.
4. Reservar o descontar stock según el flujo configurado.
5. Confirmar la venta.
6. Generar factura o boleta de prueba, sin emitir documentos productivos.
7. Registrar aceptación, observación o rechazo devueltos por la ruta tributaria demostrada.
8. Devolver el estado a ventas y atención para comunicarlo por WhatsApp.

Registrar por cada producto: versión, modalidad SaaS, configuración, proveedor/partner, capturas anonimizadas, resultado por paso, error, tiempo y costo ofertado. Si una etapa no puede ejecutarse, marcar **ND** o **pendiente de demostración**; no simular un resultado como prueba.

## Condiciones de cambio

**Pendiente:** validar canal real, conectividad, número de usuarios, presupuesto, SLA, restricciones de alojamiento y comprobantes exigidos. Si SaaS no cumple una restricción confirmada, se revisa D-01. Si la integración nativa cubre el caso sin servicio separado, se revisa D-03. La decisión final requiere evidencia comparable y aprobación de la empresa. Véase [arquitectura base](erp-base.md) y [comparativo S2 acotado](comparativo-erp.md).
