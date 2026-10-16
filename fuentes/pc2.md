# Fuentes, decisiones y supuestos de PC2

**Fecha de consulta y registro:** 15/10/2026, America/Lima. Revisión humana pendiente. No se copian los documentos originales al repositorio ni se publican datos personales de clientes.

## 1. Insumos y fuentes primarias

| ID | Fuente / sección consultada | Qué respalda y límite |
| --- | --- | --- |
| F-PC2-01 | `GE703_PC2_Instrucciones_y_Rubrica (1) (1).docx`: Propósito, Alcance evaluable, Producto mínimo, Criterios de calidad y lista de verificación | Seis productos mínimos, contrato probado, dos expositores, declaración de IA y fin en solicitud/respuesta; exige evidencia verificable y declaración de límites |
| F-PC2-02 | `GE703_PC2_G7_IMPORTACIONES_MYS_HERMANOS_S_A_C_.docx`: Identificación, Integrantes y guion 1–5 | Estructura del documento integrado; no se creó ni modificó Word por instrucción del usuario |
| F-PC2-03 | `Distribucion_Actividades_PC2_Grupo7_Con_Plantilla (2).pdf`, pp. 2–5 | Escenario de cinco autoradios por WhatsApp; Jharolym arquitectura/interfaces/IA, reparto de secciones y revisiones |
| F-PC2-04 | Odoo 19, [Create quotations](https://www.odoo.com/documentation/19.0/applications/sales/sales/sales_quotations/create_quotations.html), apartados Tracking y Sending and confirming quotations | Cotización en Ventas, vínculo con oportunidad y conversión al confirmar; consulta mediante extractos indexados de la página oficial |
| F-PC2-05 | Odoo 18, [Create and send quotations](https://www.odoo.com/documentation/18.0/applications/sales/crm/acquire_leads/send_quotes.html), introducción | Preparar cotización desde oportunidad; referencia funcional de versión 18, no prueba de instalación/compatibilidad en 19 |
| F-PC2-06 | Odoo 19, [Security in Odoo](https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html), Access Rights y Record Rules | Capas de autorización mediante ORM; la política del caso y protección del contrato requieren diseño y pruebas propias; consulta de extractos oficiales indexados |
| F-PC2-07 | Odoo 19, [modelo CRM](https://github.com/odoo/odoo/blob/19.0/addons/crm/models/crm_lead.py), `CrmLead`, `_name`, `type` y `partner_id` | Lead y oportunidad comparten `crm.lead` y se vinculan al contacto; código oficial consultado vía raw, sin incorporar código de terceros al repositorio |
| F-PC2-08 | Odoo 19, [integración sale_crm](https://github.com/odoo/odoo/blob/19.0/addons/sale_crm/models/sale_order.py), extensión de `sale.order`; y [prueba oficial de Ventas](https://github.com/odoo/odoo/blob/19.0/addons/sale/tests/test_sale_to_invoice.py), confirmación de cotización | Referencia a integración CRM/Ventas y cambio de estado; no se copia implementación ni se ejecuta el método en este proyecto |
| F-PC2-09 | Usuario, conversación del 15/10/2026 | Confirma falta de avances/instalación, integración de CRM de Odoo, caso WhatsApp y autorización para supuestos; solicita modificar solo repositorio con diagrama de componentes y contratos derivados |
| F-PC2-10 | [Línea base PC1](../arquitectura/erp-base.md), [versiones](../documentos/versiones.md), [README del prototipo](../producto/frontend/README.md) | Odoo + UBLHUB, registro manual de WhatsApp y límites del frontend estático; no demuestra operación real |
| F-PC2-11 | `SIE - GRUPOI7 - AVANCE MACROPROCESOS (1).docx`, Propósito, corrección de alcance y secciones 1–5 | Antecedente de Semana 5 con canal físico y P2P excluido; PC2 declara cambio de escenario a WhatsApp y P2P solo de contexto |

Las fuentes técnicas describen capacidades/modelos del producto. No sustentan precios, existencia real de campañas, políticas de MYS ni que estén desarrollados los componentes `mys.*`. No se copiaron fragmentos de código oficial ni imágenes de terceros; los SVG/Mermaid y scripts son elaborados para esta propuesta. No se atribuye una licencia al repositorio completo ni se cambian las de sus dependencias.

### Integridad de insumos locales

El SHA-256 identifica el archivo leído. Los originales permanecen en Downloads del usuario; los revisores deben obtenerlos por el canal autorizado del grupo, no mediante enlaces absolutos a otra computadora.

| Insumo | SHA-256 |
| --- | --- |
| F-PC2-01, rúbrica | `1AC503DC4F14408DC35E05207359B96035E5B0A8E81B40A1C593A64BDDB2508B` |
| F-PC2-02, plantilla | `BE9E30DA88AA69BE7BBB4DC898BA7223851CCA8C1A7F1CA895043DC592F88A3F` |
| F-PC2-03, distribución | `AC52F1C27CE0E7D8126578042F4AC8BFEDC8CD203704CC5A50B8135C0B358073` |
| F-PC2-11, macroprocesos | `14DA62EC6B7D2E84B9B74145FCB3B4B9C95AA914F5BFED67CCD55B1AFD0117D1` |

## 2. Supuestos didácticos, no hechos empresariales

| ID | Supuesto | Uso / validación requerida |
| --- | --- | --- |
| S-01 | Publicación promocional `PUBLICACION-DEMO` origina consulta WhatsApp; campaña `CAM-DEMO-AUTORADIOS` | Caso comercial; falta evidencia de campaña real |
| S-02 | Cinco autoradios genéricos, precio final S/400.00 por unidad, moneda PEN | Total S/2,000.00 antes de descuento; sin cálculo ni asesoría tributaria |
| S-03 | Vendedor puede aplicar hasta 5 %; más requiere gerencia | Regla para reproducir normal 5 % y excepción 10 %; pendiente de aprobación empresarial |
| S-04 | Cotización enviada/aceptada el 15/10, vigencia al 16/10 23:59:59 -05:00 | Fechas sintéticas; no promesa comercial real |
| S-05 | Disponible normal 8; variante parcial 3; no hay fecha acreditada de reposición | Ejercita aceptación/promesa; lectura sin reserva |
| S-06 | Roles de prueba Ventas, Gerencia y Almacén; una compañía/ubicación de demostración | No son usuarios ni sedes realmente configurados |
| S-07 | Precio final se redondea por línea a dos decimales y se suma con Decimal | Convención del ejemplo; configuración real de precios/tributos pendiente |
| S-08 | Una aceptación efectiva por cotización/versionado | Política propuesta de aceptación y su histórico; pendiente de implementación |
| S-09 | Mapa P2P propuesto de necesidad → aprobación → compra → recepción → conciliación → pago | Solo contexto académico; no acredita cómo compra/importa la empresa |

## 3. Decisiones de diseño trazables

| ID | Decisión | Motivo / evidencia |
| --- | --- | --- |
| D-PC2-01 | Terminar en decisión de solicitud, `order_id: null` | F-PC2-01 y F-PC2-02; impide atribuir ejecución de pedido |
| D-PC2-02 | CRM integrado en Odoo; C04/C06 y auditoría específica como extensiones propuestas | F-PC2-09; preservar PC1 y distinguir estándar de diseño |
| D-PC2-03 | Schema cerrado, importes confiables desde Ventas y cálculo Decimal | Evitar inyección de precios y ambigüedad del contrato; tests |
| D-PC2-04 | Identidad desde sesión, permisos por compañía/oportunidad y cliente revisado | Principio de acceso mínimo; pruebas locales, no ACL reales |
| D-PC2-05 | Clave idempotente + unicidad de versión + resultado/auditoría atómicos | Evitar duplicados y decisiones sin evidencia; SQLite simula restricciones |
| D-PC2-06 | Snapshot versionado, aceptación exacta y revalidación antes del pedido futuro | Prevenir aceptación obsoleta y confusión con disponibilidad garantizada |
| D-PC2-07 | Gerencia independiente, aprobación vinculada a versión/total y vigencia | Prevenir autoaprobación y reutilización de autorizaciones |
| D-PC2-08 | Distinguir promesa condicionada de falla técnica pendiente | No inventar stock/fecha ni convertir una caída en rechazo comercial |

## 4. Vacíos y validación humana

Faltan: entrevista empresarial de reglas, campañas y catálogo; versión/edición/alojamiento y extensiones Odoo; configuración de acceso y multiempresa; aceptación comercial verificable; política de retención; pruebas de ORM/stock concurrente e integración real. El [manifiesto de pruebas](../pruebas/pc2/evidencias/ejecucion.json) acredita solo ejecución local. Nadie ha validado en nombre de la empresa ni de los integrantes por el hecho de que los archivos existan.
