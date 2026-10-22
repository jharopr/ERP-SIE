# Aporte de Jharolym al examen parcial

**Responsable:** Jharolym Friendly Paucarcaja Ramos.  
**Apartado:** sección 2 Arquitectura integrada · 01:00–04:00 del comité del 24/10/2026.  
**Decisión:** mantener Odoo integrado con responsabilidades explícitas y controles antes de comprometer la operación.  
**Caso:** cliente nuevo del público general que visita la tienda física por iniciativa propia.

El aporte desarrolla en el repositorio la misma sección preparada para el Word del grupo. La [arquitectura](../../../arquitectura/crm-erp-ep.md) concentra los detalles técnicos; el [texto del aporte](aporte-jharolym.md) conserva la explicación, contribución y guion para defenderla. Los documentos se complementan sin duplicar las evidencias del simulador.

| Recurso | Uso |
| --- | --- |
| [Arquitectura integrada](../../../arquitectura/crm-erp-ep.md) | Continuidad de PC1/PC2, sistemas de registro, interfaces y límites |
| [Diagrama con iconos](../../../arquitectura/diagramas/componentes-crm-erp-ep.svg) | Explicar módulos, documentos, controles, seguridad y persistencia |
| [Casos y puntos de control](../../../arquitectura/diagramas/casos-arquitectura-ep.svg) | Relacionar la arquitectura con normal, faltante y descuento |
| [Eventos de la arquitectura](../../../arquitectura/diagramas/eventos-crm-erp-ep.svg) | Explicar E01–E07, responsables, respuestas y enlace conceptual O2C–P2P; [PNG para Word](../../../arquitectura/diagramas/eventos-crm-erp-ep.png) |
| [Fuente Mermaid](../../../arquitectura/diagramas/componentes-crm-erp-ep.mmd) | Editar la semántica de componentes y dependencias |
| [Generador SVG](../../../arquitectura/diagramas/generar_diagramas_ep.py) | Reproducir los gráficos con biblioteca estándar |
| [Fuentes y supuestos](../../../fuentes/ep-jharolym.md) | Atribuciones, diferencias de stock, fechas e IA |
| [Verificación](../../../pruebas/ep-jharolym/README.md) | Comprobar gráficos y reutilizar evidencia existente |
| [Recorrido de Benjamín](../benjamin/README.md) | Continuar la exposición con los mismos objetos y controles |

Los SVG pueden abrirse en un navegador y ampliarse sin perder nitidez. La ficha representa identidad; la red, CRM; el documento, cotización; las cajas, inventario; la aprobación, autorización; el escudo, seguridad; y el cilindro, datos. Las figuras tienen títulos y descripciones accesibles y no dependen solo del color.

## Reproducción

```powershell
python arquitectura/diagramas/generar_diagramas_ep.py
python arquitectura/diagramas/generar_diagramas_ep.py --check
```

No se requiere Odoo, conexión ni paquetes externos. Los SVG se generan junto a su fuente en `arquitectura/diagramas/`. Los resultados JSON se leen desde el bloque de Benjamín y no se copian a esta carpeta.

## Word con eventos

La copia local `GE703_EP_G7_JHAROLYM_ARQUITECTURA_INTEGRADA_CON_EVENTOS.docx`, en la raíz, incorpora el diagrama como figura 2.2 y la matriz de eventos dentro de la sección 2.6. Conserva la sección de Benjamín y la plantilla posterior. Se guarda con otro nombre porque el Word original estaba abierto y bloqueado para sobrescritura.

[actualizar_word_eventos.py](actualizar_word_eventos.py) reproduce esa edición a partir del Word original y el PNG vigente; requiere `python-docx`. Si cambia el SVG, exportar de nuevo el PNG antes de regenerar el Word. Los binarios y las páginas de revisión se mantienen como exportaciones locales.

**Revisión:** contenido preparado con asistencia de Codex el 22/10/2026; Jharolym debe revisar la defensa y el grupo debe validar reglas, fuentes y navegación. La aprobación humana no se da por realizada.
