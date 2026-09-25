# Plan de desarrollo para PC1

## Objetivo y alcance

Preparar para el 26/09/2026 una propuesta revisable de arquitectura ERP base para IMPORTACIONES MYS HERMANOS S.A.C. La PC1 exige contexto, problema de integración, comparativo ERP v0.1 mejorado, diagrama de actores/sistemas/interfaces/flujos/límites, criterios de adecuación, repositorio de evidencias, backlog y declaración de fuentes e IA. **No exige construir ni desplegar el ERP**.

La primera liberación propuesta en el taller de semana 3 comprende ventas, inventario, facturación electrónica y un canal digital integrado. Compras/importación aparece en la visión de negocio, pero su implementación queda fuera de esa primera liberación hasta que la empresa acuerde el alcance.

## Secuencia de trabajo

| Etapa | Fecha objetivo | Trabajo verificable | Responsable provisional según S1 | Criterio de cierre |
| --- | --- | --- | --- | --- |
| 1. Ordenar evidencias | 24/09 | Consolidar S1, S2, S3, plantilla PC1, rúbrica y ficha RUC; separar hechos, declaraciones, hipótesis y pendientes | Facilitación: Shirley Carrión | Cada afirmación central tiene referencia y estado de validación |
| 2. Modelar proceso y datos | 24-25/09 | Describir pedido digital → atención → venta → stock → comprobante; levantar campos y sistemas reales | Procesos: Ballack Quintanilla; datos: Jharolym Paucarcaja | Flujo actual marcado como pendiente donde falte entrevista; datos sensibles excluidos |
| 3. Comparar y decidir | 25/09 | Actualizar matriz StarSoft/Odoo/Business Central con fuentes oficiales, criterios y condiciones de cambio | Arquitectura: Benjamin Arancibia | Recomendación provisional explicada; cobertura SUNAT/PLE sin dar por probada |
| 4. Diseñar arquitectura | 25/09 | Revisar diagrama, interfaces, actores, despliegue, límites y riesgos; definir prueba de concepto | Arquitectura y producto: Benjamin Arancibia y Adrián Mansilla | El diagrama corresponde al alcance y cada interfaz tiene estado propuesto o confirmado |
| 5. Validar y empaquetar | 25-26/09 | Revisar contra rúbrica, registrar aportes, completar plantilla y presentación, ensayar defensa | Validación: Gabriel Chávez; facilitación: Shirley Carrión | Guion completo, enlaces funcionales, fuentes e IA declarados, dos expositores registrados |

Los roles provienen de la ficha de conformación y son **provisionales**. Las tareas de esta tabla son una propuesta, no constancia de trabajo ya realizado.

## Ruta de implementación posterior a PC1

Esta secuencia adapta la ruta de S3, §3, visible también en la captura facilitada. Son **compuertas de decisión**, no fases ejecutadas ni un cronograma aprobado.

| Fase | Objetivo | Decisión de salida y evidencia mínima |
| --- | --- | --- |
| Alinear | Acordar resultado de negocio, alcance inicial y roles | Aprobar o ajustar alcance mediante acta con gerencia; reduce el riesgo de tratar una intención como aprobación |
| Preparar | Cerrar vacíos de usuarios, sedes, presupuesto, conectividad, sistemas y datos | Decidir SaaS o arquitectura mixta y opciones a evaluar; inventario y respuestas de proveedores por escrito |
| Explorar | Probar en demo el pedido, stock, comprobante y canal digital | Elegir o descartar producto y partner con casos comparables y cotizaciones |
| Construir | Configurar módulos, depurar y migrar maestros, implementar la interfaz priorizada | Autorizar pruebas con configuración documentada y conciliación de datos |
| Validar y desplegar | Ejecutar aceptación, capacitación y arranque controlado | Decisión de puesta en marcha con actas, comprobantes válidos y plan de retorno |
| Operar y mejorar | Estabilizar, medir indicadores y priorizar mejoras | Continuar, ajustar o ampliar con tablero e incidencias |

Si alguna prueba crítica de integración o facturación falla, se detiene el paso a la fase siguiente y se registra la causa. Los riesgos, controles y responsables propuestos están en S3, §5; deben revalidarse con la empresa.

## Dependencias y decisiones de salida

1. **Datos de negocio:** confirmar productos, canales, usuarios, sedes, sistemas, volumen de operaciones, conectividad, presupuesto y calidad de maestros. Sin esa información, conservar el diagrama como conceptual.
2. **Adecuación ERP:** verificar con demostración o respuesta escrita el soporte de comprobantes electrónicos, libros electrónicos, integración y costos para la versión y modalidad ofrecidas. Comparar bajo el mismo escenario.
3. **Prueba de flujo:** usar un artículo sintético; si la empresa confirma el catálogo, puede representar un autoradio. Comprobar que pedido, stock, atención y comprobante mantienen identificadores trazables.
4. **Decisión:** presentar recomendación provisional, condiciones de cambio y pendientes priorizados. La aprobación de producto, presupuesto y despliegue corresponde a la empresa.

## Prioridad de pendientes antes de exponer

| Prioridad | Pregunta | Evidencia esperada |
| --- | --- | --- |
| Alta | ¿Qué sistemas y canales utiliza realmente la empresa y dónde se duplica el registro? | Entrevista autorizada, captura anonimizada o descripción validada del flujo |
| Alta | ¿Qué comprobantes y libros deben soportarse en el alcance inicial? | Lista acordada con facturación y demostración del ERP/partner |
| Alta | ¿Cuáles son las restricciones de conectividad, usuarios, sedes, plazo y presupuesto? | Registro de reunión o respuesta escrita |
| Media | ¿Cuál es la calidad de productos, clientes, proveedores y stock? | Muestra sintética y criterios de conciliación |
| Media | ¿Qué opción resuelve la integración con menor dependencia de personalizaciones? | Prueba comparable en demo/sandbox y cotizaciones |

## Paquete de salida

El paquete se compone de este repositorio y la presentación construida con la plantilla del grupo. Antes de enviarlo, recorrer el [guion](guion-entrega.md), comprobar enlaces y diagrama, completar [contribuciones](contribuciones.md), registrar la versión y revisar datos personales. Los dos expositores consignados en la plantilla PC1 son Jharolym Paucarcaja y Benjamin Arancibia; el registro oficial debe comprobarse por separado.

**Base:** rúbrica PC1, pp. 1-2; plantilla PC1, secciones 1-5; ficha S1, secciones 1, 3 y 4; comparativo S2, secciones 2-5; estrategia S3, secciones 2-6. Consulta de archivos facilitados: 24/09/2026. Véase el [registro detallado](../fuentes/registro-fuentes.md).
