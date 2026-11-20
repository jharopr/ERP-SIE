# Trazabilidad de la sección 5B

Fecha de consulta: 12/11/2026, Lima. Base del repositorio: `f8613b65993ab8d489fe7f17d8c0ae7785a4daf7`. Los identificadores coinciden con la sección principal.

| ID | Fuente y localización | Tratamiento |
| --- | --- | --- |
| S1 | [Adrián 5A](../adrian/seccion_5a_activos_mantenimiento.md), §5A.1 y registro VEN-01 | Fuente empresarial vigente atribuida a EMP-01…EMP-07. Sedes, personal, cuaderno, transporte y decisión familiar; testimonio, sin auditoría operativa. VEN-01 se utiliza como evidencia secundaria. |
| S2 | [Adrián 5C](../adrian/seccion_5c_relacion_activos_cadena.md), capacidad, red de distribución y continuidad | Diferenciación entre importación y reposición; capacidad nominal frente a efectiva; proveedores locales como antecedente no identificado. |
| S3 | [PC2](../../pc2/entrega-pc2.md), §2; [arquitectura EP](../../../arquitectura/crm-erp-ep.md) | Segmento presencial y continuidad de controles; no implantación productiva. |
| S4 | Rúbrica oficial PDF pp. 1–2; plantilla general DOCX §§5–10; EP adjunto pp. 3–8, 15, 19, 30 | Requisitos académicos y continuidad. Se reemplaza la ubicación histórica del EP por la evidencia PC3 más reciente. |
| S5 | [Shirley 5B-II](../shirley/seccion_5b_inventarios_servicio.md) | Interfaz de inventarios y servicio; sus resultados sintéticos no se usan como medición. README explica unificación de unidades y cohortes. |
| S6 | Word preliminar y QA ADR-PC3-001 adjuntos | Referencia inicial de controles y fórmulas; se descartan alcance WhatsApp, roles genéricos y diagnósticos empresariales desactualizados. Incidente técnico sin trasladar a suministro. |
| P1 | `GUANGDONG XUYING TECHNOLOGY CO.docx`, carta aclaratoria | MYS identificada como comprador; Huizhou/China. Producto no identificado; fecha de emisión sin completar. Operación histórica de 2025. |
| P2 | `MEICANXIN ELECTRONICS TECHNOLOGY.docx`, carta y anexos | MYS, domicilio operativo Shenzhen/China; referencias negociadas multimedia, placa y DSP. No recepción ni vigencia 2026. |
| P3 | `SHENZHEN GEARFORCE TECHNOLOGY CO.docx`, carta y anexos | MYS, Shenzhen/China; multimedia y cámaras negociadas. No prueba de desempeño o inventario. |
| P4 | `CI OF SOTMA(1).docx`, documento comercial con destinatario SOTMA | Proveedor de Dongguan/China y mercancía descrita; referencia potencial fuera de relaciones confirmadas de MYS. |
| O1–O2 | Documentación oficial Odoo 18 enlazada en el capítulo | Capacidades de referencia para diseño futuro; la configuración concreta requiere validación en el proyecto. |
| N1 | OMG BPMN 2.0.2 y sus esquemas normativos | Modelos editables con elementos semánticos y disposición gráfica DI; no se confunde Mermaid con BPMN. |

## Evidencia y decisiones

| Diagnóstico | Evidencia | Propuesta vinculada | Indicador |
| --- | --- | --- | --- |
| Dos circuitos diferentes y trazabilidad de extremo a extremo no acreditada | S1, S2 | ID de solicitud, salida, tránsito, recepción y diferencias | K1, K2, K3 |
| Variedad de referencias y componentes compatibles; recursos limitan instalación | S1, S2 | Maestro SKU–compatibilidad, cotejo técnico y confirmación de recursos | K4, referencia a disponibilidad de 5A |
| Relaciones comerciales históricas; muestra incompleta para evaluar desempeño | P1–P4 | Catálogo proveedor–SKU, condiciones aprobadas, decisión familiar registrada | K5, K6 |
| Reporte agregado descrito sin fecha transaccional y original no disponible | S1, VEN-01 | Registro de ventas y solicitudes no atendidas por fecha, tienda, canal y segmento | K4 y análisis posterior de tendencias |

## Cobertura de requisitos de la sección

| Requisito | Evidencia entregada |
| --- | --- |
| Actores y tres flujos | 5B.1, figura 1 |
| AS-IS con responsabilidades y alternativas | 5B.2, figuras 2–3, fuentes BPMN |
| Lista de proveedores incorporada | 5B.3, figura 1; P4 separado |
| Demanda y granularidad de datos | 5B.4, VEN-01 secundario y diseño de registro |
| Inventarios por ubicación y compatibilidad | 5B.5, enlace con 5B-II |
| Capacidad nominal/efectiva y activos | 5B.6, referencia 5A/5C |
| Definición, fórmula, unidad, entradas, fuente, frecuencia, responsable y uso de KPI | 5B.7, seis fichas y reglas comunes |
| Propuesta gradual y autorización humana | 5B.8, figura 4, etapas y relación con Odoo |
| Problema, evidencia, decisión y resultados evaluables | Introducción y 5B.9 |
| Fuentes, supuestos, límites, contribución, IA y privacidad | Cierre de 5B.9 y este registro |
| Integración sin modificar aportes ajenos | README y alcance de cambios en carpeta propia |

## Calidad de los datos y publicación

No se publican los adjuntos ni sus capturas. Las ciudades y familias se extraen de cada documento, sin inferir país por el nombre empresarial. Las cartas no se tratan como registros actuales de stock o una muestra exhaustiva de compras. No se publican ponderaciones, rankings ni concentración económica calculada sobre importes privados. La condición EXW de P4 no se atribuye a MYS.

El análisis distingue hechos documentales, cálculo nominal de capacidad atribuido a 5C y diseño propuesto. No contiene indicadores empresariales inventados. Las consultas al contacto empresarial se comunican directamente al usuario y no se incluyen como lista de coordinación en el repositorio.
