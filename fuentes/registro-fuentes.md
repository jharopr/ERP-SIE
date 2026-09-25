# Fuentes de la comparación de soluciones

Esta carpeta registra únicamente fuentes técnicas y comerciales relevantes para evaluar la solución.

| ID | Solución | Fuente | Uso en la comparación | Control documental |
| --- | --- | --- | --- | --- |
| F-01 | Odoo | [Documentación de arquitectura](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/01_architecture.html) | Arquitectura, módulos y extensibilidad | Odoo 19 es la referencia documental base |
| F-02 | Odoo | [Modalidades de alojamiento](https://www.odoo.com/documentation/19.0/administration/hosting.html) | Opciones de despliegue | La orden de implementación registra alojamiento y SLA |
| F-03 | Odoo | [Localización de Perú](https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/peru.html) | Referencia para configuración peruana | Odoo gestiona la operación y UBLHUB los documentos definidos |
| F-04 | StarSoft | [Gold Edition](https://www.starsoft.com.pe/producto-gold-edition.php) | Alternativa ERP local | Antecedente de comparación; no seleccionado |
| F-05 | StarSoft | [Información corporativa](https://www.starsoft.com.pe/nosotros.php) | Contexto del proveedor | Fuente comercial del antecedente |
| F-06 | Dynamics 365 Business Central | [Integración con Azure](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/integration-azure-overview) | Alternativas de integración | Antecedente de comparación; no seleccionado |
| F-07 | Dynamics 365 Business Central | [Desarrollo de extensiones AL](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-dev-overview) | Extensibilidad | Fuente técnica del antecedente |
| F-08 | UBLHUB | Documentación técnica y contrato de API del microservicio | Boletas, facturas, guías, estados, autenticación y errores | El anexo de implementación registra versión, URL, sandbox, SLA y mensajes |

## Criterios de uso

- Priorizar documentación oficial y vigente del producto o proveedor.
- Registrar versión, fecha de consulta y alcance exacto de cada afirmación.
- Toda capacidad crítica se acepta mediante evidencia de demostración o sandbox.
- Mantener cotizaciones, credenciales y contratos fuera del repositorio público.
- No publicar datos reales de clientes ni secretos de integración.

## Decisión relacionada

Las fuentes respaldan la comparación, pero la decisión del proyecto ya está establecida: **Odoo como ERP central y UBLHUB como microservicio de documentos electrónicos**. StarSoft y Dynamics 365 Business Central se mantienen como antecedentes de comparación.
