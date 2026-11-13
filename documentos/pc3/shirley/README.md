# PC3 · Mi aporte (Shirley Carrión Oré)

Según el reparto PC3 del Grupo 7, me encargo de la cadena de suministro (inventarios, disponibilidad, servicio e indicadores), de consolidar el informe y su PDF, y de la QA de instalación limpia, navegación, caso normal y stock/servicio. En esta carpeta dejo mi trabajo.

| Archivo | Contenido |
| --- | --- |
| [informe_pc3_consolidado.md](informe_pc3_consolidado.md) | Informe ordenado con las 10 secciones y tablas de la plantilla oficial PC3/PC4. Las secciones 1–4, 8 y 9 son mías; 5C.S, 6 y 7 son compartidas; 5A/5C se incorporan desde los archivos de Adrián; 5B-I (Benjamín) queda marcada como pendiente |
| [seccion_5b_inventarios_servicio.md](seccion_5b_inventarios_servicio.md) | 5B-II: ubicaciones, cantidades (registrado, disponible, utilizable), indicadores IND-01 a IND-09, casos sintéticos, equilibrio servicio-costo y decisiones D-5B-01 a 05 |
| [guion_defensa_shirley.md](guion_defensa_shirley.md) | Mi intervención de 1 min 50 s y preguntas probables |
| [construir_informe.py](construir_informe.py) | Genera el Word sobre la plantilla oficial y su PDF en `output/pc3/` (solo Python; LibreOffice para el PDF) |
| [../../../pruebas/pc3-shirley/](../../../pruebas/pc3-shirley/ficha_qa_usabilidad_shirley.md) | Ficha QA, lista de usabilidad, registro de defectos SHI-PC3-001 a 005, script y evidencias |

## Cómo regenerar

```sh
python pruebas/pc3-shirley/ejecutar_qa_shirley.py        # QA, indicadores y coherencia
python documentos/pc3/shirley/construir_informe.py --plantilla GE703_PC3_PC4_Plantilla_Informe_General_Agente_SIE.docx
```

## Lo que me falta para cerrar el 13/11

1. Incorporar la 5B-I de Benjamín (reemplazar el marcador `PENDIENTE_5B_BENJAMIN` por la ruta de su archivo).
2. Ejecutar SHI-U01, U03, U04 y U05 sobre el ZIP del agente de Ballack y completar mi lista de usabilidad.
3. Completar la URL del repositorio en la sección 1 y comprobar los enlaces.
4. Volver a probar ADR-PC3-001 cuando Gabriel/Jharolym lo corrijan.
5. Firmar mi ficha QA; Adrián valida los datos de la empresa.
