# Backlog de desarrollo: Odoo + UBLHUB

**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C.  
**Grupo:** 7  
**Versión propuesta:** 0.4  
**Fecha:** 25/09/2026

## 1. Objetivo y punto de partida

Organizar el trabajo necesario para implementar una primera versión que permita registrar clientes y pedidos presenciales o recibidos por WhatsApp, controlar inventario y gestionar documentos electrónicos mediante la integración propuesta entre Odoo y UBLHUB.

El repositorio contiene documentación y un frontend de demostración con datos locales. Este prototipo no constituye una instalación de Odoo ni acredita una conexión con UBLHUB.

La primera versión mantendrá la atención manual de WhatsApp: el vendedor registrará el pedido en Odoo y conservará su canal de origen. La automatización del canal queda para una etapa posterior.

La incorporación de UBLHUB está condicionada a verificar su documentación, cobertura y acceso de pruebas. El tratamiento del requisito PLE mencionado en S3 debe resolverse expresamente antes de cerrar el alcance.

## 2. Reglas de priorización y seguimiento

- **P0 — Bloqueante:** resuelve una incertidumbre que impide diseñar o implementar con fundamento.
- **P1 — Primera versión:** capacidad necesaria para completar el flujo comercial acordado.
- **P2 — Evolución:** mejora que puede realizarse después del piloto.

Una tarea pasa a **Lista para iniciar** cuando sus dependencias están resueltas, tiene un responsable confirmado y un criterio de aceptación revisado. Pasa a **Terminada** cuando existe evidencia del resultado y otra persona lo revisa.

Las prioridades no representan duración. No se asignan fechas de implementación hasta confirmar disponibilidad del equipo, modalidad de Odoo y acceso a UBLHUB.

## 3. Backlog priorizado

Los responsables indicados son roles propuestos. “Por verificar” significa que debe comprobarse si existe trabajo realizado fuera del repositorio.

| ID | Trabajo y resultado esperado | Prioridad | Depende de | Responsable propuesto | Estado inicial |
|---|---|---|---|---|---|
| BL-01 | Confirmar el proceso actual, herramientas utilizadas y alcance inicial. Resolver los cambios respecto de S3. | P0 | Acceso a información del negocio | Análisis funcional y representante de la empresa | Por validar |
| BL-02 | Definir versión, edición y alojamiento de Odoo, ubicación del adaptador y responsabilidades de operación. | P0 | BL-01; restricciones de presupuesto, conectividad y soporte | Arquitectura | Pendiente |
| BL-03 | Verificar la viabilidad de UBLHUB: proveedor, documentos cubiertos, API, autenticación, estados, ambiente de pruebas y condiciones de servicio. | P0 | BL-01; documentación del proveedor | Integración y responsable de facturación | Pendiente de información externa |
| BL-04 | Completar el modelo de datos y las reglas de clientes, productos, pedidos, stock y documentos. | P0 | BL-01 | Datos y análisis funcional | Modelo preliminar; por completar |
| BL-05 | Preparar un ambiente de pruebas de Odoo y configurar usuarios y permisos básicos. | P1 | BL-02 | Configuración ERP | Por verificar |
| BL-06 | Configurar y cargar clientes y productos sintéticos, con reglas de identificación y duplicados. | P1 | BL-04 y BL-05 | Datos y configuración ERP | Pendiente |
| BL-07 | Configurar el registro de pedidos presenciales y de WhatsApp, incluyendo canal de origen y seguimiento. | P1 | BL-06; casos de uso revisados | Configuración ERP y ventas | Pendiente |
| BL-08 | Configurar existencias, reservas, salidas y reglas ante stock insuficiente. | P1 | BL-04, BL-05 y BL-06 | Configuración ERP y almacén | Pendiente |
| BL-09 | Diseñar el contrato del adaptador: datos, correspondencia de campos, identificadores, estados y errores. | P1 | BL-03, BL-04, BL-07 y BL-08 | Integración | Bloqueado por validación de API |
| BL-10 | Implementar y probar la solicitud y consulta de boletas y facturas mediante el adaptador. | P1 | BL-09; credenciales de pruebas | Integración | Bloqueado |
| BL-11 | Implementar y probar las guías de remisión vinculadas con el traslado correspondiente. | P1 | BL-09; reglas de traslado y cobertura confirmadas | Integración y almacén | Bloqueado |
| BL-12 | Implementar controles de duplicación, recuperación ante fallos y conciliación de estados documentales. | P1 | BL-10 y BL-11 | Integración | Bloqueado |
| BL-13 | Configurar consultas de pedidos por canal y documentos pendientes o rechazados. | P1 | BL-07, BL-08 y BL-12 | Configuración ERP y usuarios clave | Pendiente |
| BL-14 | Ejecutar las pruebas integrales y preparar un piloto con usuarios, instrucciones y procedimiento de contingencia. | P1 | BL-06 a BL-13 | Validación y usuarios clave | No ejecutado |
| BL-15 | Evaluar la automatización de WhatsApp a partir del volumen y reproceso observados. | P2 | Proceso inicial validado y datos operativos disponibles | Análisis funcional e integración | Fuera de la primera versión |

## 4. Criterios de aceptación y evidencias

Estos criterios describen resultados que deberán comprobarse. No representan pruebas ya ejecutadas.

| ID | Criterio de aceptación | Evidencia de cierre |
|---|---|---|
| BL-01 | El documento distingue situación actual y propuesta, identifica herramientas conocidas y registra qué entra o queda fuera, incluido WhatsApp y PLE. Los datos sin confirmar aparecen como pendientes. | Ficha de alcance revisada y registro de validación o de preguntas abiertas. |
| BL-02 | Se identifica la modalidad concreta de Odoo, dónde funcionará el adaptador y quién administrará cada componente. La elección explica sus restricciones y dependencias. | Decisión de arquitectura con fuentes y diagrama actualizado. |
| BL-03 | Cada capacidad requerida de UBLHUB tiene respaldo identificable o se declara no confirmada. Se registra una conclusión de viabilidad; si es negativa, se revisa la solución antes de desarrollar. | Matriz de cobertura y documentación o respuesta del proveedor. |
| BL-04 | Las entidades tienen identificadores, relaciones, cardinalidades y reglas de integridad. Se diferencia pedido, movimiento de stock y documento electrónico. | Modelo de datos y diccionario revisados. |
| BL-05 | El ambiente puede ponerse en funcionamiento siguiendo instrucciones y se comprueba una operación permitida y otra restringida para los roles definidos. | Versión y configuración registradas; resultados de acceso sin exponer credenciales. |
| BL-06 | Se cargan clientes y productos sintéticos identificables. Al repetir una importación o registrar un identificador existente, se aplica la regla aprobada sin crear duplicados inadvertidos. | Datos de prueba y reporte de carga y validación. |
| BL-07 | Se registra un pedido por cada canal, con cliente, productos, cantidades y estado. Ambos pueden localizarse por su identificador y canal. | Casos ejecutados y capturas anonimizadas. |
| BL-08 | Con 10 unidades iniciales, un pedido de 2 reserva la cantidad según la regla acordada; al validar su salida, las existencias quedan en 8. Una solicitud superior al disponible aplica la restricción o excepción definida. | Registro de existencias, reserva y movimiento; caso de stock insuficiente. |
| BL-09 | El contrato define los campos de cada documento, identificadores de correlación, mecanismo de consulta o respuesta, estados y tratamiento de errores según la API verificada. | Especificación del adaptador y ejemplos sintéticos de mensajes. |
| BL-10 | En pruebas, una boleta y una factura conservan la relación con su operación de origen, identificador externo y estado. Una solicitud inválida deja un error visible y trazable. | Solicitudes y respuestas anonimizadas y resultados por caso. |
| BL-11 | Una guía de prueba contiene los datos de traslado exigidos por la interfaz validada y conserva la relación con la operación correspondiente. | Caso ejecutado, identificadores y respuesta del servicio. |
| BL-12 | Repetir una solicitud no genera otro documento. Si se pierde la respuesta después del envío, se consulta o concilia el resultado antes de reenviar. Los fallos quedan visibles y no producen reintentos indefinidos. | Pruebas de duplicación, pérdida de respuesta y recuperación, con registros técnicos. |
| BL-13 | El usuario autorizado puede localizar pedidos por canal y documentos pendientes o rechazados, y acceder a la operación de origen. | Consultas verificadas contra los datos de prueba. |
| BL-14 | Los escenarios de ambos canales, inventario y documentos tienen resultado, ejecutor, fecha y evidencia. No se autoriza el piloto con fallos que causen duplicación, pérdida de trazabilidad o movimientos incorrectos de stock. | Informe de pruebas, incidencias y decisión de avance o corrección. |
| BL-15 | La evaluación describe el problema medido, opciones, costos y requisitos de automatización, y concluye si conviene implementarla. | Caso de mejora revisado; no exige construir un conector para cerrar esta evaluación. |

## 5. Secuencia de ejecución

**Primera etapa: cerrar decisiones.** Resolver BL-01 a BL-04. La definición de Odoo, la investigación de UBLHUB y el modelo de datos pueden avanzar en paralelo una vez aclarado el alcance.

**Segunda etapa: configurar la operación comercial.** Preparar Odoo, cargar datos de prueba y configurar pedidos e inventario. El equipo debe comprobar este recorrido antes de incorporar la integración documental.

**Tercera etapa: integrar y controlar documentos.** Diseñar el contrato del adaptador, implementar los documentos confirmados y verificar duplicación, errores y recuperación.

**Cuarta etapa: validar el flujo completo.** Preparar consultas operativas, ejecutar pruebas y decidir si procede un piloto.

La automatización de WhatsApp se evalúa después y no bloquea el alcance inicial de registro manual.

## 6. Dependencias y límites

La integración depende de documentación y acceso de pruebas de UBLHUB. Mientras no estén disponibles, pueden prepararse contratos y simulaciones claramente identificadas, pero no declararse probada la integración real.

Las reglas de inventario y emisión deben validarse con los responsables del negocio. Confirmar un pedido, reservar existencias y registrar una salida se tratarán como eventos diferenciados.

La pérdida de internet en el local requiere un procedimiento operativo específico. Una cola en el adaptador no resuelve por sí sola la imposibilidad de acceder a un ERP alojado fuera del local.

Los casos utilizarán datos sintéticos. El prototipo actual servirá para revisar pantallas y necesidades con usuarios; su almacenamiento local no se utilizará como evidencia de funcionamiento del ERP.
