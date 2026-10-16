# Catálogo de diagramas

Los diagramas se complementan entre sí; cada notación responde una pregunta distinta y evita sobrecargar una sola imagen.

## Incremento PC2

El [diagrama de componentes CRM–ERP](componentes-crm-erp-pc2.svg), con [fuente Mermaid editable](componentes-crm-erp-pc2.mmd), define C01–C08 e I01–I07. Distingue componentes estándar y extensiones propuestas y conserva UBLHUB solo como continuidad. Es la vista que gobierna los [contratos PC2](../contratos/crm-erp-v1.md). La fuente Mermaid conserva la estructura semántica; el SVG es una composición manual de la misma vista, no una exportación automática del archivo Mermaid.

El [flujo comercial y estados](../../procesos/pc2-escenario-y-flujo.md) y el [ERD de PC2](../../datos/pc2-modelo-y-controles.md) complementan esa vista. Las vistas siguientes corresponden a la línea base PC1, que incluye ejecución y facturación posteriores al incremento evaluable.

| Diagrama | Notación | Pregunta que responde |
| --- | --- | --- |
| [Actores y casos de uso](actores-casos-uso.svg) | UML — casos de uso | ¿Quién usa cada capacidad? |
| [Proceso comercial](proceso-comercial-bpmn.svg) | BPMN simplificado — carriles | ¿Quién ejecuta cada paso y dónde cambia la responsabilidad? |
| [Componentes](componentes-c4.svg) | C4 — componentes | ¿Qué piezas forman la solución y qué intercambian? |
| [Secuencia de emisión](secuencia-emision.svg) | UML — secuencia | ¿En qué orden colaboran los participantes durante la emisión? |
| [Modelo de datos](modelo-datos-erd.svg) | ERD — entidad–relación | ¿Qué información se conserva y cómo se relaciona? |
| [Estados del documento](estados-documento.svg) | UML — máquina de estados | ¿Cómo cambia el documento ante aceptación, rechazo o falta de respuesta? |
| [Despliegue](arquitectura-despliegue.png) | UML — despliegue | ¿En qué entorno se ejecuta cada pieza? |

Los archivos SVG conservan texto nítido y pueden abrirse en un navegador. El PNG de despliegue se mantiene como evidencia visual de la topología seleccionada.
