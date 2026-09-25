# Plan de implementación base del ERP

## Objetivo

Poner en funcionamiento Odoo como sistema central de ventas e inventario, integrado con UBLHUB para boletas, facturas y guías de remisión, manteniendo los dos canales reales: ERP/presencial y WhatsApp móvil.

## Fases y resultados

| Fase | Trabajo principal | Resultado de salida |
| --- | --- | --- |
| 1. Levantamiento | Confirmar usuarios, clientes, productos, stock, precios, pagos, documentos, volúmenes y excepciones | Alcance y reglas aprobados |
| 2. Diseño | Definir módulos Odoo, roles, tipos de cliente, estados, datos e interfaz con UBLHUB | Diseño funcional y técnico revisado |
| 3. Configuración | Preparar Odoo, catálogos, permisos, canales y flujos | Ambiente de prueba utilizable |
| 4. Integración | Implementar autenticación, mapeos, idempotencia, estados y reintentos con UBLHUB | Boleta, factura y guía probadas en sandbox |
| 5. Migración | Limpiar clientes, productos y stock inicial; cargar y conciliar | Maestros sin duplicados críticos y stock conciliado |
| 6. Piloto | Ejecutar ventas presenciales y de WhatsApp con usuarios seleccionados | Aceptación del flujo y defectos prioritarios cerrados |
| 7. Producción | Capacitar, respaldar, habilitar usuarios y monitorear | Salida controlada con plan de retorno |
| 8. Mejora | Medir indicadores y evaluar automatización de WhatsApp | Backlog priorizado con evidencia |

## Dependencias

- versión y modalidad de Odoo;
- contrato, documentación, credenciales y sandbox de UBLHUB;
- reglas para boleta, factura, guía, anulación y contingencia;
- inventario de datos actuales y calidad de maestros;
- conectividad, usuarios, sedes, equipos y soporte;
- responsables de ventas, almacén, facturación y administración.

## Criterios de paso a producción

1. Los dos canales registran pedidos en Odoo con trazabilidad.
2. Los clientes no se duplican por documento o RUC.
3. El stock se concilia y no se altera dos veces por reintentos.
4. UBLHUB procesa en pruebas los tres tipos de documento definidos.
5. Los errores y estados son visibles y recuperables.
6. Los permisos críticos están separados.
7. Existe respaldo, monitoreo, soporte y procedimiento de contingencia.
8. Los usuarios completan los escenarios de aceptación.

## Riesgos principales

| Riesgo | Control |
| --- | --- |
| Doble digitación desde WhatsApp | Registro único en Odoo y referencia del pedido |
| Clientes duplicados | Reglas de búsqueda, documento/RUC único y revisión de coincidencias |
| Stock inicial incorrecto | Conteo, carga controlada y conciliación firmada |
| Doble emisión | Clave idempotente y consulta del estado antes de reintentar |
| Rechazo tributario | Mensaje accionable, corrección controlada y auditoría |
| Caída de servicio | Cola, reintento con límite, alerta y procedimiento manual |
| Personalización excesiva | Configurar primero y aprobar cada brecha antes de desarrollar |
