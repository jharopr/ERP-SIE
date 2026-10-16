# PC2 · incremento comercial CRM–ERP

**Grupo 7 · IMPORTACIONES MYS HERMANOS S.A.C. · Exposición: 17/10/2026 · Versión: v2.1.**

Estado: propuesta documentada y contrato simulado localmente. La empresa no ha validado aún precios, campaña ni política de descuentos; no existe una instalación Odoo acreditada. El contenido fue desarrollado con asistencia de IA; las revisiones individuales del equipo están pendientes.

## Ruta de revisión

1. [Entrega integrada en las cinco secciones oficiales](entrega-pc2.md).
2. [Arquitectura de Jharolym: componentes, sistemas de registro y responsabilidades](../../arquitectura/crm-erp-pc2.md).
3. [Diagrama de componentes SVG](../../arquitectura/diagramas/componentes-crm-erp-pc2.svg) y [fuente Mermaid](../../arquitectura/diagramas/componentes-crm-erp-pc2.mmd).
4. [Contrato 1.1 e interfaces I01–I08](../../arquitectura/contratos/crm-erp-v1.md), [schema de solicitud](../../arquitectura/contratos/solicitud-pedido-v1.schema.json) y [respuesta](../../arquitectura/contratos/respuesta-pedido-v1.schema.json).
5. [Escenario, flujo, casos de uso y SIPOC de contexto](../../procesos/pc2-escenario-y-flujo.md).
6. [Modelo de datos, diccionario y matriz de controles](../../datos/pc2-modelo-y-controles.md).
7. [Pruebas, comandos y resultados obtenidos](../../pruebas/pc2/README.md).
8. [Fuentes, supuestos, decisiones y vacíos](../../fuentes/pc2.md); [declaración de IA](../../fuentes/uso-ia.md).

9. [Calibración Andina S6](calibracion-andina-s6.md) y [dos métricas del contrato](metricas-s6.md).
10. [Word: aporte personal de Jharolym](../../output/docx/GE703_PC2_G7_Aporte_Jharolym_S6.docx), secciones 3 y 5; las secciones 1, 2 y 4 quedan para sus responsables.

## Qué revisar por integrante

| Integrante | Evidencia preparada para su revisión | Revisión pendiente |
| --- | --- | --- |
| Benjamin | Sección 1, mapa y SIPOC de contexto | Continuidad de PC1 y registro de enlaces |
| Shirley | Escenario, cotización y registro de fuentes | Campaña, supuestos y fuentes empresariales |
| Gabriel | Contrato, eventos, reglas y respuestas | Consistencia con interfaces y prueba |
| Adrian | Flujo, casos de uso y casos N01/E01 | Modelado y reproducción del contrato |
| Jharolym | Cuatro módulos Odoo, componentes externos, interfaces I01–I08 y límites/IA | Frontera CRM–Ventas y especificación técnica |
| Ballack | Diccionario, controles y evidencia generada | Calidad, privacidad y resultados de pruebas |

La preparación de estos archivos no se atribuye como trabajo o validación individual ya realizado. Cada integrante debe revisar su parte y registrar fecha, cambio o comentario y evidencia antes de declarar su contribución.

## Alcance de evaluación

PC2 termina en la solicitud de transición y su respuesta. `ACEPTADA` no confirma un pedido operativo ni reserva stock. UBLHUB permanece como continuidad de PC1. Los documentos anteriores de ERP/facturación y el prototipo estático conservan su valor como línea base; los artefactos de esta ruta son los vigentes para el incremento PC2.
