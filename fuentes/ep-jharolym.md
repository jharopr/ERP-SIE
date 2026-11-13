# Fuentes del aporte de arquitectura de Jharolym

**Consulta y elaboración:** 22/10/2026. **Autor académico:** Jharolym Friendly Paucarcaja Ramos. **Estado:** preparación para revisión humana.

## Insumos y alcance de uso

| Fuente | Localización | Uso en el aporte |
| --- | --- | --- |
| Reparto Parcial G7 Shirley Decisión Benjamín O2C | PDF de avance del equipo, páginas 4 y 6; consultado localmente | Sección 2 de Jharolym, arquitectura integrada y tres minutos; propuesta de organización del equipo |
| GE703 EP G7 Benjamín parte 3 completa | DOCX de referencia, sección 3; exportación local | Estructura del Word, caso presencial, mismos objetos y variantes |
| [PC2 consolidada](../documentos/pc2/entrega-pc2.md) | Secciones 1 a 5 | Cliente nuevo, persona natural, canal físico, visita espontánea, cifras y frontera comercial |
| [Arquitectura técnica anterior](../arquitectura/crm-erp-pc2.md) | Componentes y sistemas de registro; interfaces; reglas | Identificadores C01–C08 e I01–I07 y distinción entre estándar y extensión propuesta |
| [Contrato local 1.0](../arquitectura/contratos/crm-erp-v1.md) | Interfaces, validación y respuestas | Alcance de solicitud/respuesta, referencias confiables y controles |
| [Desarrollo de Benjamín](../documentos/ep/benjamin/aporte-benjamin.md) | Alcance, datos/controles, casos y fuentes | Articulación con O2C–P2P y cadena documental del ejemplo |
| [Fixtures y método EP](../pruebas/ep-benjamin/README.md) | Casos, fecha lógica y límites | Caso normal, faltante y excepción como corridas independientes |
| [Resultados EP](../pruebas/ep-benjamin/evidencias/resultados.md) y [manifiesto](../pruebas/ep-benjamin/evidencias/ejecucion.json) | Resultados existentes y hashes | Respuestas observadas, tres casos y 112 comprobaciones reportadas |

El reparto es una propuesta del grupo que cita material docente; no sustituye una nueva revisión de la rúbrica oficial. Los nombres de modelos Odoo y las responsabilidades técnicas se reutilizan del diseño y referencias ya registrados en [fuentes PC2](pc2.md). No se afirma una nueva verificación de versión o compatibilidad de Odoo.

Los PDF/DOCX locales son insumos de trabajo. Las fuentes versionadas son los textos, diagramas y generadores; no es necesario añadir copias binarias para reproducir los gráficos de este aporte.

## Parámetros que deben permanecer consistentes

| Elemento | Tratamiento |
| --- | --- |
| Segmento y origen | Público general nuevo, persona natural, tienda física y visita espontánea; continuidad de PC2 |
| Cantidad y producto | Cinco autoradios; SKU sintético RAD-7BT; uso familiar como supuesto |
| Base comercial | 5 × S/ 400 = S/ 2,000; descuento normal 5 % = S/ 1,900; excepción 10 % = S/ 1,800 |
| Política comercial | Umbral 5 % como regla didáctica pendiente de validar con el dueño; no se acredita la entrevista primaria citada por el reparto |
| Disponibilidad | Word histórico PC2: 5; Markdown PC2 y caso normal EP: 8; variante EP-S01: 3. Se adopta explícitamente el dato EP de Benjamín sin mezclar corridas |
| Vigencia | 16/10 para PC2 histórico; 24/10/2026 hasta 18:00 para la recreación EP. La hora de ejecución real se consulta en el manifiesto |
| Aprobación y aceptación | Aceptación del cliente ligada a la versión; no sustituye autorización del dueño |
| Señal P2P | REP-EP-001 documentada por el arnés tras la respuesta parcial; fuera del contrato 1.0, sin compra, reserva ni fecha automática |
| Comprobaciones | Evidencia local existente del bloque de Benjamín; no se presentan como ejecución productiva o autoría exclusiva de Jharolym |

## Uso de IA y revisión

Codex de OpenAI asistió el 22/10/2026 en redacción, organización del diagrama con iconos, generación SVG e incorporación a las carpetas del repositorio. Los iconos son trazos SVG originales del generador, sin imágenes o fuentes de iconos externas. Los identificadores y valores son sintéticos.

No se realizaron nuevas entrevistas, despliegues ni transacciones en Odoo. Jharolym debe revisar el contenido y ensayar la defensa; el grupo debe validar reglas comerciales y completar el panel único. La revisión humana permanece pendiente.
