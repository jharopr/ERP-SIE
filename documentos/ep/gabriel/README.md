# Aporte de Gabriel al examen parcial

**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C.  
**Caso:** cliente nuevo del público general, atención en tienda física.  
**Responsable académico:** Gabriel Omar Chavez Mendoza.  
**Bloque:** sección 4, Contrato de integración CRM–ERP, 06:00–09:00 del comité del 24/10/2026.

El [contenido editable completo](aporte-gabriel.md) incluye el texto de la plantilla, la fila de contribución, la matriz del contrato de transición, la calibración con el caso Andina de la Sesión 7, la adaptación a MYS Hermanos, el guion de tres minutos, preparación de preguntas y la matriz de los siete criterios de la rúbrica. El [informe HTML](informe-gabriel.html) conserva la versión imprimible y navegable; el PDF puede exportarse desde ese informe cuando sea necesario.

## Artefactos

| Archivo | Uso |
| --- | --- |
| [GE703_EP_G7_GABRIEL_CONTRATO_CRM_ERP.docx](GE703_EP_G7_GABRIEL_CONTRATO_CRM_ERP.docx) | Documento Word formal exhaustivo (~15 páginas) con 6 figuras incrustadas y 10 tablas |
| [aporte-gabriel.md](aporte-gabriel.md) | Texto completo editable para la sección 4 con las 6 figuras incrustadas |
| [informe-gabriel.html](informe-gabriel.html) | Versión web imprimible y navegable con tablas y figuras de alta resolución |
| [diagramas/](diagramas/) | Las 6 figuras de alta resolución (300 DPI) generadas para el contrato |
| [generar_word_gabriel.py](generar_word_gabriel.py) | Script generador del documento Word formal con python-docx |
| [generar_diagramas_gabriel.py](generar_diagramas_gabriel.py) | Script generador de los 6 diagramas con matplotlib |
| [Contrato v1.0](../../../arquitectura/contratos/crm-erp-v1.md) | Especificación formal de las 7 interfaces y 12 reglas |
| [Schema solicitud](../../../arquitectura/contratos/solicitud-pedido-v1.schema.json) | JSON Schema de I03 (entrada inmutable) |
| [Schema respuesta](../../../arquitectura/contratos/respuesta-pedido-v1.schema.json) | JSON Schema de respuesta (salida tipificada) |
| [Resultados EP](../../../pruebas/ep-benjamin/evidencias/resultados.md) | Evidencia compartida: 3 casos y 112 comprobaciones |
| [Simulador](../../../pruebas/pc2/simulador.py) | Motor de validación local reutilizado |

## Reproducción

Desde la raíz del proyecto, con Python 3:

```powershell
python pruebas/ep-benjamin/generar_evidencias.py
python pruebas/pc2/simulador.py pruebas/pc2/fixtures/solicitud-normal.json
python pruebas/pc2/simulador.py pruebas/pc2/fixtures/solicitud-excepcion.json
```

Solo biblioteca estándar. El simulador valida el schema de entrada, aplica las 12 reglas en orden, persiste la decisión en SQLite y registra la bitácora atómicamente. El segundo y tercer comando permiten observar directamente la respuesta del contrato para el caso normal y la excepción.

## Límites y tareas del equipo

Se prepara un aporte individual y evidencias para el comité. Quedan por completar con el grupo el panel único accesible, el enlace de entrega, las intervenciones ajenas, la designación del vocal y el registro de su pregunta real.

Los valores de stock, precios, descuentos, cantidades y horas son académicos. El contrato 1.0 es un diseño propuesto, no un módulo instalado en Odoo. La implementación productiva requiere configurar extensiones en PostgreSQL/ORM, ACL reales, versionado de cotizaciones y auditoría verificada. El límite del parcial es la respuesta de evaluación, con pedido nulo y sin reserva.

**Uso de IA y revisión:** Codex asistió en redacción y organización el 22/10/2026. Gabriel debe revisar y asumir la defensa; esa validación humana permanece pendiente. Fuentes académicas y referencias se detallan en el aporte; los adjuntos originales no se redistribuyen.
