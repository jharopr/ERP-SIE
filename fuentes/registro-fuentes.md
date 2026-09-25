# Fuentes de la comparación de soluciones

Esta carpeta registra únicamente fuentes técnicas y comerciales relevantes para evaluar la solución.

| ID | Solución | Fuente | Uso en la comparación | Verificación pendiente |
| --- | --- | --- | --- | --- |
| F-01 | Odoo | [Documentación de arquitectura](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/01_architecture.html) | Arquitectura, módulos y extensibilidad | Confirmar versión elegida |
| F-02 | Odoo | [Modalidades de alojamiento](https://www.odoo.com/documentation/19.0/administration/hosting.html) | Opciones de despliegue | Seleccionar modalidad y SLA |
| F-03 | Odoo | [Localización de Perú](https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/peru.html) | Referencia para configuración peruana | Delimitar qué cubrirá Odoo y qué delegará a UBLHUB |
| F-04 | StarSoft | [Gold Edition](https://www.starsoft.com.pe/producto-gold-edition.php) | Alternativa ERP local | Obtener ficha técnica, API, SLA y cotización comparables |
| F-05 | StarSoft | [Información corporativa](https://www.starsoft.com.pe/nosotros.php) | Contexto del proveedor | Contrastar capacidades con demostración |
| F-06 | Dynamics 365 Business Central | [Integración con Azure](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/integration-azure-overview) | Alternativas de integración | Confirmar arquitectura ofertada por partner |
| F-07 | Dynamics 365 Business Central | [Desarrollo de extensiones AL](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-dev-overview) | Extensibilidad | Confirmar límites, localización y costos |
| F-08 | UBLHUB | Documentación técnica y contrato de API del microservicio | Boletas, facturas, guías, estados, autenticación y errores | Incorporar versión, URL oficial, sandbox, SLA y esquema de mensajes |

## Criterios de uso

- Priorizar documentación oficial y vigente del producto o proveedor.
- Registrar versión, fecha de consulta y alcance exacto de cada afirmación.
- No considerar una capacidad como validada hasta ejecutarla en demostración o sandbox.
- Mantener cotizaciones, credenciales y contratos fuera del repositorio público.
- No publicar datos reales de clientes ni secretos de integración.

## Decisión relacionada

Las fuentes respaldan la comparación, pero la decisión del proyecto ya está establecida: **Odoo como ERP central y UBLHUB como microservicio de documentos electrónicos**. StarSoft y Dynamics 365 Business Central se mantienen como antecedentes de comparación.
