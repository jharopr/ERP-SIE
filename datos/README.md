# Datos y Gobierno de la Información · Incremento PC2

**Responsable del módulo:** Ballack Zidane Quintanilla Huamanraime (PM-04: Gestión de datos, controles y privacidad; co-responsable PM-05: Pruebas del contrato).

Este directorio contiene la arquitectura de datos, el inventario de entidades y los controles comerciales definidos para la **PC2 (Escenario CRM previo al pedido)**, delimitados conceptualmente hasta la diapositiva 12 de la sesión 6.

## Contenido del directorio

- [PC2: modelo, diccionario y controles](pc2-modelo-y-controles.md): **(Vista principal vigente)** Define las entidades `CLIENTE`, `LEAD/OPORTUNIDAD`, `COTIZACION_VERSION`, `ACEPTACION`, `APROBACION_DESCUENTO` y `SOLICITUD_TRANSICION`. Incluye la matriz de controles de descuento (5% vs >5%), consulta de stock `read-only`, contexto comercial de la cuenta, consentimiento y trazabilidad de extremo a extremo.
- [Inventario de fuentes y tratamiento](inventario-fuentes.md): Campos mínimos, procedencia, datos sintéticos y políticas de privacidad aplicadas al catálogo y a los clientes.
- [Modelo de datos PC1](modelo-datos.md): Entidades y relaciones operativas de la línea base anterior (conservado como referencia de continuidad).
- [Simulación del modelo de datos](simulacion-modelo-datos.md): Validación de integridad de relaciones relacionales de apoyo.

> **Criterio de evaluación:** La gestión de datos garantiza que los precios, identidades y permisos provengan de Sistemas de Registro (SoR) oficiales (`res.partner`, `crm.lead`, catálogo C03) y no de campos libres o conversaciones informales, manteniendo siempre `order_id: null` en esta etapa.

