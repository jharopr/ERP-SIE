# Decisión de solución y criterios de validación

## Decisión adoptada

La solución base es **Odoo como ERP central + UBLHUB como microservicio para boletas, facturas y guías de remisión**. La combinación separa la gestión comercial de la responsabilidad tributaria especializada y permite iniciar con los dos canales reales: registro presencial en el ERP y venta atendida manualmente por WhatsApp móvil.

## Razones principales

| Criterio | Aplicación en la decisión |
| --- | --- |
| Cobertura funcional | Odoo concentra clientes, ventas, productos, inventario y reportes |
| Adecuación al tamaño y evolución | Permite comenzar con módulos prioritarios y ampliar por etapas |
| Integración | UBLHUB se desacopla como microservicio y evita cargar al núcleo del ERP con toda la lógica tributaria |
| Trazabilidad | Pedido, venta, movimiento y documento conservan identificadores relacionados |
| Canales | Ambos canales usan el mismo proceso en Odoo; WhatsApp se registra manualmente al inicio |
| Mantenibilidad | Se configura primero y se personaliza solo ante una brecha demostrada |
| Riesgo | La emisión se prueba en sandbox antes de habilitar documentos productivos |

## Caso de validación de extremo a extremo

1. Crear o identificar un cliente sin duplicar documento o RUC.
2. Registrar un pedido con canal ERP/presencial o WhatsApp móvil.
3. Consultar y reservar inventario en Odoo.
4. Confirmar la venta.
5. Solicitar a UBLHUB una boleta, factura o guía según el caso.
6. Recibir identificador, estado, respuesta tributaria y archivos.
7. Guardar el resultado en Odoo sin emitir dos veces ante un reintento.
8. Comunicar el resultado al cliente por su canal de origen.
9. Verificar la trazabilidad completa en el reporte operativo.

## Criterios de aceptación técnica

- autenticación y secretos fuera del código fuente;
- idempotencia por venta y tipo de documento;
- registro de solicitud, respuesta, error y reintento;
- estados comprensibles para el usuario del ERP;
- conciliación entre venta, stock y documento;
- operación controlada cuando UBLHUB o internet no estén disponibles;
- permisos separados para vender, ajustar stock, emitir y anular;
- datos de prueba anonimizados en todos los ambientes no productivos.

## Condiciones para revisar la decisión

La combinación deberá reevaluarse si UBLHUB no cubre un documento obligatorio, no ofrece una API o soporte compatible, o si el costo y SLA no cumplen las restricciones aprobadas. También se revisará el despliegue de Odoo si conectividad, presupuesto, volumen o requisitos de alojamiento cambian materialmente.
