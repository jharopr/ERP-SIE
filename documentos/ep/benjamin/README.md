# Aporte de Benjamin al examen parcial

**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C.  
**Caso:** cliente nuevo del público general, atención en tienda física.  
**Responsable académico:** Benjamín Francis Arancibia Ynga.  
**Bloque:** sección 3, Recorrido O2C, 04:00–06:00 del comité del 24/10/2026.

Abrir [panel-benjamin.html](panel-benjamin.html) en un navegador para navegar el mapa integrado, los journeys, el flujo, la línea de tiempo y tres casos. Funciona localmente sin servidor ni conexión; es el bloque de Benjamin para incorporar al panel único del grupo.

El [contenido editable completo](aporte-benjamin.md) incluye el texto de la plantilla, la fila de contribución, SIPOC, datos y controles, indicadores, guion de dos minutos, preparación de preguntas y matriz de los siete criterios de la rúbrica. El [informe HTML](informe-benjamin.html) conserva la versión imprimible; las figuras sustituyen las tablas que repiten el mismo contenido, cuyo detalle permanece en Markdown. El PDF puede exportarse desde ese informe cuando sea necesario.

## Artefactos

El aporte se mantiene en Markdown y HTML junto con sus diagramas y evidencias. Las copias Word, PDF y ZIP de `output/` se retiraron para reducir archivos redundantes.

| Archivo | Uso |
| --- | --- |
| diagramas/01-mapa-corporativo.svg | Mapa de procesos de nivel uno |
| diagramas/02-mapa-integrado-o2c-p2p.svg | Vista principal O2C y señal de reposición a P2P |
| diagramas/03-flujo-roles-validacion.svg | Responsables y controles de transición |
| diagramas/04-linea-tiempo-trazabilidad.svg | Eventos, identificadores y horas lógicas |
| diagramas/05-journey-actual.svg | Experiencia actual reconstruida y puntos de dolor por validar |
| diagramas/06-journey-propuesto.svg | Experiencia y evidencias propuestas |
| [Resultados](../../../pruebas/ep-benjamin/evidencias/resultados.md) | Esperado frente a observado de normal, faltante y descuento |
| [Reproducción](../../../pruebas/ep-benjamin/README.md) | Generador, entradas, trazas y límites de simulación |

Los seis gráficos tienen fuentes Mermaid y generadores editables. Los cuatro primeros se generan con `diagramas/generar_diagramas.py`; los journeys, el informe HTML y el panel se generan con `generar_material.py`.

## Reproducción

Desde la raíz del proyecto, con Python 3:

```powershell
python pruebas/ep-benjamin/generar_evidencias.py
python documentos/ep/benjamin/diagramas/generar_diagramas.py
python documentos/ep/benjamin/generar_material.py
```

Solo el último comando requiere la biblioteca `markdown`; los dos anteriores usan la biblioteca estándar. El panel captura los resultados JSON al generarse: después de cambiar fixtures se deben regenerar evidencias y panel, en ese orden.

El PDF se imprime desde el informe HTML con CSS de página A4 horizontal. Para conservar la composición, habilitar gráficos de fondo y respetar la orientación y márgenes definidos. Las exportaciones locales se guardan fuera del control de versiones.

## Límites y tareas del equipo

Se prepara un aporte individual y evidencias para el comité. Quedan por completar con el grupo el panel único accesible, el enlace de entrega, las intervenciones ajenas, la designación del vocal y el registro de su pregunta real.

Los valores de stock, precios, descuentos, cantidades, horas y emociones son académicos. El journey actual es una reconstrucción documental, no trabajo de campo nuevo. La regla del 5 % requiere confirmación del dueño; la disponibilidad normal 8 se declara como nueva fixture EP ante la discrepancia con el stock 5 del Word PC2. Odoo no está acreditado como desplegado; P2P se conecta mediante una señal conceptual, sin ejecutar compras. El límite es la respuesta de evaluación, con pedido nulo y sin reserva.

**Uso de IA y revisión:** Codex asistió en redacción, diagramas y simulación el 21/10/2026. Benjamin debe revisar y asumir la defensa; esa validación humana permanece pendiente. Fuentes académicas y referencias se detallan en el informe; los adjuntos originales no se redistribuyen.
