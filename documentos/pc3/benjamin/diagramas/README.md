# Diagramas de cadena de suministro PC3

Los diagramas acompañan la sección 5B de Benjamín. Se recomienda insertar cada figura en una página horizontal para conservar la legibilidad.

| Figura | Archivo base | Notación y propósito |
| --- | --- | --- |
| 1 | `01_red_integral` | Red de suministro: actores, dos tiendas, Carabayllo, decisiones, materiales y compromisos económicos. |
| 2 | `02_asis_internacional` | BPMN de reconstrucción del abastecimiento internacional declarado. |
| 3 | `03_asis_reposicion` | BPMN de reconstrucción de la reposición interna mediante cuaderno y transporte contratado. |
| 4 | `04_tobe_reposicion` | BPMN propuesto: identificación, compatibilidad, saldo por ubicación, traslado, recepción, diferencias y compra bajo decisión humana. |

Cada base tiene exportaciones SVG y PNG. Las figuras 2–4 incluyen un archivo `.bpmn` con elementos semánticos BPMN 2.0 y coordenadas BPMN DI. Son modelos analíticos no ejecutables (`isExecutable="false"`), editables en una herramienta compatible con BPMN 2.0; no configuran un motor de automatización.

## Lectura y alcance

- En la red, las líneas azules representan producto; las discontinuas turquesa, información; las grises, compromisos económicos. El flujo económico es representativo del conjunto de proveedores.
- En los procesos, el círculo fino indica inicio; el grueso, fin; el rectángulo redondeado, actividad; el rombo con X, decisión exclusiva; la hoja, objeto de datos. El signo + identifica un subproceso contraído. Los mensajes discontinuos con círculo de origen y punta abierta cruzan hacia un participante externo; las secuencias permanecen en el proceso de MYS.
- Los carriles distribuyen responsabilidades. La coordinación familiar y el almacenero fijo corresponden al aporte vigente de Adrián. Las actividades y alternativas AS-IS son una reconstrucción analítica; no prueban controles formales de compra, conformidad o registro horario.
- El TO-BE devuelve una referencia incompatible o incierta para aclaración. Solo un faltante de una referencia validada alimenta la evaluación humana de compra. Una aprobación no satisface la necesidad ni acredita recepción. Las diferencias de entrega conservan la solicitud pendiente de conciliación.
- La red distingue tres vínculos comerciales con MYS documentados en 2025. Su vigencia, ruta exacta y recepción actual requieren comprobación. El documento P4 corresponde a otro consignatario, Importaciones SOTMA S.A.C.; permanece separado y no se usa para afirmar una relación con MYS.

Fuentes: S1 = [Adrián 5A](../../adrian/seccion_5a_activos_mantenimiento.md); S2 = [Adrián 5C](../../adrian/seccion_5c_relacion_activos_cadena.md); P1 = Guangdong Xuying; P2 = Meicanxin; P3 = Shenzhen Gearforce; P4 = CI OF SOTMA. Los cuatro últimos son documentos privados suministrados por el usuario, resumidos en la [trazabilidad de fuentes](../trazabilidad_fuentes.md); no se reproducen datos personales, bancarios ni importes.

## Reproducción

Requisitos: Python 3 con `lxml`; Node.js con `sharp`. Ejecutar desde la raíz del repositorio:

```powershell
python documentos/pc3/benjamin/diagramas/generar_diagramas.py
$env:SHARP_PATH = 'RUTA_AL_MODULO_SHARP'
node documentos/pc3/benjamin/diagramas/exportar_png.cjs
```

`SHARP_PATH` es opcional si `sharp` ya está disponible en la búsqueda de módulos del entorno. El generador es la fuente reproducible de la geometría y produce conjuntamente el SVG y el BPMN DI. Si se edita manualmente un `.bpmn` en otra herramienta, esa edición no se incorpora de forma automática al generador ni al SVG.

Para validar contra los esquemas oficiales, descargar en una misma carpeta `BPMN20.xsd`, `BPMNDI.xsd`, `DC.xsd`, `DI.xsd` y `Semantic.xsd` desde [OMG BPMN 2.0.2](https://www.omg.org/spec/BPMN/2.0.2), sección de documentos normativos legibles por máquina. Después:

```powershell
python documentos/pc3/benjamin/diagramas/validar_diagramas.py --schema-dir RUTA_A_ESQUEMAS_OMG
```

El argumento opcional `--output RUTA_JSON` conserva el resultado. Sin `--schema-dir`, se ejecutan solo las comprobaciones estructurales y de grafo, y el resultado declara `xsd_OMG: false`; no debe interpretarse como validación XSD.

La revisión del 12/11/2026 validó los tres modelos contra los cinco XSD oficiales, además de unicidad de identificadores, entradas y salidas, rutas desde inicio y hacia fin, asignación de carriles, posición de nodos, separación entre participantes y referencias DI. Resultado: cero errores. Se inspeccionaron las cuatro exportaciones PNG y se ajustaron etiquetas y conexiones. Esta validación acredita sintaxis y coherencia del modelo, no certificación de OMG ni confirmación empresarial del procedimiento.
