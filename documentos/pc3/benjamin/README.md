# Aporte de Benjamín para PC3

Sección 5B de cadena de suministro Parte I de Importaciones MYS Hermanos S.A.C., para GE703, UNI FIIS, Grupo 7. Responsable académico: Benjamín Francis Arancibia Ynga. Corte documental: 12/11/2026, Lima.

El aporte caracteriza el abastecimiento que sostiene la atención de clientes nuevos del público general en tiendas físicas. Distingue compra internacional y reposición interna; incorpora los documentos de proveedores y propone trazabilidad con decisión humana. No acredita implantación de Odoo ni resultados empresariales de servicio.

## Archivos

| Archivo | Uso |
| --- | --- |
| [Sección principal](seccion_5b_cadena_suministro.md) | Texto, tablas, fuentes y figuras; fuente única del Word. |
| [Word editable](GE703_PC3_G7_Cadena_Suministro_Parte_I_Benjamin.docx) | Capítulo para integrar al informe general; texto y tablas editables, figuras con fuentes separadas. |
| [Diagramas](diagramas/) | Red integral y tres procesos BPMN, con XML editable, SVG y PNG. |
| [Trazabilidad de fuentes](trazabilidad_fuentes.md) | Relación de hallazgos, fuentes, decisiones y tratamiento de datos. |
| [Generador del Word](construir_word.py) | Reproduce el documento desde Markdown y PNG, sin leer los adjuntos privados. |

## Base y continuidad

Se verificó `origin=https://github.com/jharopr/ERP-SIE.git`, `main` sin modificaciones locales, se ejecutó `git fetch origin --prune` y se actualizó mediante `git pull --ff-only origin main`. Base completa: **`f8613b65993ab8d489fe7f17d8c0ae7785a4daf7`**. Rama de contribución: `docs/pc3-benjamin-cadena-suministro`.

Se revisaron README, documentos PC2/EP/PC3, aportes de Adrián y Shirley, arquitectura, procesos, datos, fuentes, macroprocesos y pruebas. Las otras ramas técnicas no se consideran fusionadas. ADR-PC3-001 permanece como antecedente técnico, fuera del problema empresarial de suministro.

Los documentos de 2025 acreditan tres relaciones históricas de MYS; la factura de SOTMA corresponde a otro comprador. No se publica como proveedor confirmado de MYS. El reporte original VEN-01 no está en el material disponible: su caracterización se atribuye al análisis previo de Adrián, sin recalcular demanda diaria ni inventar KPI.

## Integración al informe general

1. Reemplazar el marcador `PENDIENTE_5B_BENJAMIN` del [consolidado de Shirley](../shirley/informe_pc3_consolidado.md) con el aporte revisado. No se modificó ese archivo ni su generador.
2. Usar 5B.1–5B.4 y 5B.6 como núcleo de 5B-I. Integrar 5B.5, 5B.7 y 5B.8 con 5B-II, conservando una sola exposición de estados e indicadores. Mantener demanda perdida, compatibilidad y abastecimiento como interfaces entre ambos aportes.
3. Unificar las definiciones antes de consolidar: aquí el tiempo se expresa en **horas corridas**, mientras 5B-II propone horas de apertura; no son intercambiables sin calendario. La exactitud aquí usa **pares SKU–ubicación**. El cumplimiento usa cohortes de ventanas que vencen en el periodo e incluye pendientes vencidas. No copiar metas o porcentajes sintéticos como medición real.
4. Remitir a 5A y 5C para criticidad, mantenimiento y cálculos de activos. No duplicar esos apartados. Conservar las figuras en páginas apaisadas y adaptar su numeración al informe completo.
5. Trasladar las fuentes y límites a las secciones 6 y 9 de la plantilla; la matriz de decisión a la 7; resultados y limitaciones a la 8; los diagramas a la 10 si se prefieren como anexos. Este capítulo no sustituye los tres entregables grupales ni la demostración en vivo.

El Word conserva el análisis del Markdown y agrupa las cuatro figuras al final en páginas apaisadas. Las imágenes son representaciones del proceso y las fuentes `.bpmn`/`.svg` permiten editarlas. El ensamblador actual de Shirley no incorpora automáticamente las imágenes de este capítulo; la integración debe preservar las figuras y sus leyendas.

## Reproducción y control de calidad

Usar el Python del runtime de documentos con `python-docx` y Pillow:

```text
python documentos/pc3/benjamin/diagramas/generar_diagramas.py
python documentos/pc3/benjamin/diagramas/validar_diagramas.py
python documentos/pc3/benjamin/construir_word.py
```

El generador produce SVG y BPMN; para actualizar PNG se debe ejecutar también `exportar_png.cjs` con `sharp`, según el [README de diagramas](diagramas/README.md). La validación XSD completa requiere `--schema-dir` y los cinco esquemas oficiales; sin ese argumento se comprueban estructura y grafo. El entorno de producción de este aporte usa Python 3.12 del runtime de Codex. El Word se incorpora expresamente a Git por solicitud del usuario, aunque la política general de `.gitignore` excluye archivos `.docx`; no se cambió esa política.

Comprobaciones aplicadas: cobertura de los nueve subapartados; trazabilidad de hallazgos y propuestas; revisión independiente de proveedores y privacidad; enlaces relativos; fórmulas y unidades; correspondencia de 171 párrafos y celdas entre Markdown y Word; cuatro figuras y ocho tablas; tres BPMN sin errores XSD/grafo/DI. Se revisaron todas las páginas renderizadas del Word. El renderizador habitual no encontró LibreOffice y la exportación PDF nativa se bloqueó; se verificó la paginación real mediante la representación de páginas `Page.EnhMetaFileBits` de Microsoft Word, convertida a PNG para inspección. No se entrega un PDF adicional. Las cifras operativas no se presentan como resultados medidos y la revisión humana del contenido corresponde al equipo antes de la entrega académica.

## Fuentes y privacidad

Se utilizaron rúbrica y plantilla oficiales, parcial, Word preliminar, QA de ramas, fuentes del repositorio actualizado y cuatro documentos de proveedores entregados por el usuario. Los originales permanecen fuera de Git. Se publican razón social, ciudad/país, referencias de mercancía verificables y alcance documental. Se excluyen contactos, firmas, cuentas, códigos de pago, precios e importes de negociación. La trazabilidad amplía el criterio de selección.

Asistencia de ChatGPT/Codex de OpenAI, 12/11/2026: contraste documental, redacción, diagramas y comprobaciones. No equivale a aprobación humana o empresarial.
