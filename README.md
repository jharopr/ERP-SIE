# PC1 · Arquitectura ERP base · Grupo 7

Repositorio de evidencias para la Práctica Calificada 1 de GE703 (2026-2), con entrega y exposición el **26/09/2026**. El caso de estudio es **IMPORTACIONES MYS HERMANOS S.A.C.**, RUC **20606915528**. La PC1 pide justificar una arquitectura ERP base y una decisión trazable; este repositorio aún no representa un ERP implementado.

## Punto de partida

- **Hecho documentado:** la ficha RUC emitida el 05/09/2026 registra a la empresa como sociedad anónima cerrada activa, con actividad principal CIIU 4649 (venta al por mayor de otros enseres domésticos), condición de importador y emisión electrónica de facturas y boletas. Véase [registro de fuentes](fuentes/registro-fuentes.md).
- **Información del equipo por validar con la empresa:** comercialización de autoradios y accesorios para automóviles, procesos de compras, inventario, ventas, atención y posventa, y sistemas actuales de ventas, inventario, facturación y clientes. Proviene de la ficha de la semana 1; el RUC no acredita el catálogo ni los sistemas.
- **Hipótesis:** la atención al cliente no se integra bien con los canales digitales de venta. Aún faltan observaciones del flujo actual, métricas y validación de usuarios.
- **Propuesta provisional:** evaluar una arquitectura modular SaaS y probar la integración de un canal digital con ventas, inventario y facturación. La selección de proveedor sigue abierta.

## Integrantes y roles provisionales

La ficha de conformación S1 asigna facilitación a Shirley Carrión, arquitectura a Benjamin Arancibia, datos a Jharolym Paucarcaja, producto a Adrián Mansilla, procesos a Ballack Quintanilla y validación a Gabriel Chávez. Las [contribuciones verificables](documentos/contribuciones.md) se registrarán por separado.

## Ruta de lectura y estructura

| Ruta | Contenido y uso en PC1 |
| --- | --- |
| [`documentos/`](documentos/README.md) | Plan, contexto, entregables, contribuciones y versiones |
| [`arquitectura/`](arquitectura/README.md) | Vistas, interfaces, decisiones y versiones de la arquitectura |
| [`procesos/`](procesos/README.md) | Modelos, reglas, eventos y controles |
| [`datos/`](datos/README.md) | Diccionario, fuentes, datos de prueba y tratamiento de datos sensibles |
| [`producto/`](producto/README.md) | Backlog y [MVP frontend para Odoo](producto/frontend/README.md) |
| [`pruebas/`](pruebas/README.md) | Casos, resultados, incidencias y criterios de aceptación |
| [`fuentes/`](fuentes/README.md) | Bibliografía, licencias, atribución y uso de IA |

Empieza por el [plan de desarrollo](documentos/plan-desarrollo-pc1.md). El [guion de entrega](documentos/guion-entrega.md) enlaza cada requisito con su evidencia. Los insumos originales están registrados en [`documentos/insumos/`](documentos/insumos/README.md); no se copian al repositorio porque la ficha RUC incluye datos personales.

## Pasos para reproducir la revisión

1. Leer [contexto y alcance](documentos/contexto-y-alcance.md) y contrastar sus afirmaciones con el [registro de fuentes](fuentes/registro-fuentes.md).
2. Seguir el [flujo prioritario](procesos/flujos-prioritarios.md), el [comparativo](arquitectura/comparativo-erp.md) y los [criterios de selección](arquitectura/criterios-seleccion.md).
3. Abrir el [diagrama Mermaid](arquitectura/erp-base.md), revisar interfaces y límites, y contrastarlo con [backlog](producto/backlog.md) y [pruebas](pruebas/casos-pc1.md).
4. Recorrer el [guion de entrega](documentos/guion-entrega.md) para verificar la rúbrica. Los Markdown y diagramas Mermaid se pueden revisar en GitHub o en un editor compatible sin instalar dependencias.

## Estado de la entrega

La estructura, el análisis inicial, el diagrama conceptual y un [MVP frontend navegable](producto/frontend/README.md) están preparados. Faltan: contrastar con la empresa las afirmaciones de los talleres, cerrar los vacíos priorizados, revisar las fuentes oficiales de los ERP, completar las contribuciones verificables, construir la presentación con la plantilla del grupo y registrar a los dos expositores en la libreta de evaluaciones. Una propuesta no debe figurar como decisión aprobada sin evidencia de aprobación.

No subas DNI, teléfonos, correos personales, direcciones completas, datos de clientes ni reportes RUC íntegros. Quien evalúe el paquete debe recibir por un canal autorizado los insumos no públicos que sean necesarios.
