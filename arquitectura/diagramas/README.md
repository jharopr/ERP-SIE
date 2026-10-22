# Catálogo de diagramas

Los diagramas se complementan entre sí; cada notación responde una pregunta distinta y evita sobrecargar una sola imagen.

## Examen parcial y aporte de Jharolym

| Gráfico | Uso y fuente |
| --- | --- |
| [Arquitectura del caso presencial](componentes-crm-erp-ep.svg) | C01–C08 e I01–I07 con iconos de identidad, CRM, documentos, inventario, aprobación, seguridad y persistencia; [fuente Mermaid](componentes-crm-erp-ep.mmd) |
| [Casos y puntos de control](casos-arquitectura-ep.svg) | Caso normal, faltante y excepción; respuestas leídas de las evidencias existentes de Benjamín |
| [Eventos de la arquitectura](eventos-crm-erp-ep.svg) | E01–E07, responsables, decisiones y enlace conceptual O2C–P2P; [fuente Mermaid](eventos-crm-erp-ep.mmd) y [PNG para Word](eventos-crm-erp-ep.png) |

La [especificación EP](../crm-erp-ep.md) explica los módulos y sus límites. Los tres SVG son composiciones nativas generadas por [generar_diagramas_ep.py](generar_diagramas_ep.py), con iconos propios y sin dependencias externas. Mermaid conserva la semántica de la arquitectura, no su composición gráfica exacta. El PNG es una exportación del SVG de eventos para insertarlo en Word.

```powershell
python arquitectura/diagramas/generar_diagramas_ep.py
python arquitectura/diagramas/generar_diagramas_ep.py --check
```

La nueva vista conserva el cliente nuevo en tienda física de PC2 y la señal conceptual P2P del recorrido de Benjamín. El diagrama anterior se mantiene como antecedente técnico; no es la vista usada para presentar el escenario presencial del parcial.

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
