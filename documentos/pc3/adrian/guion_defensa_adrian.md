# Guion individual de defensa — Adrián Mansilla

**GE703 · Grupo 7 · Importaciones MYS Hermanos S.A.C.** Preparado el 12/11/2026 para exposición del 14/11/2026. Duración objetivo: **1 min 50 s**, dentro de los diez minutos grupales. Texto en primera persona para ensayo y validación de Adrián; las pruebas locales fueron automatizadas y no se presentan como ejecución humana en vivo.

## Apertura — 0:00 a 0:20

Soy Adrián Mansilla, dueño de MYS Hermanos y responsable de activos. En La 50 tenemos cuatro espacios utilizables: tres en la primera tienda y uno en la segunda. Entre semana atendemos aproximadamente cinco y tres vehículos por día, respectivamente; los domingos llegamos hasta doce y cinco. Por eso analizo cada sede.

## Contención de fallas — 0:20 a 1:00

Cada tienda tiene su fuente de 120 amperios. En la primera falló la alimentación durante dos días y un repuesto no oficial volvió a fallar al mes.

En Carabayllo guardamos audio abajo y adaptadores arriba. Uno de los hijos de la dueña es el almacenero fijo; coordinamos con cuaderno y trasladamos mayormente por inDrive. Los pedidos a China se deciden por experiencia y revisión del cuaderno y Excel.

Propongo conciliar registros con existencias, documentar compras y programar mantenimiento. Primero se valida capacidad, stock y despacho; después se confirma la promesa. Si Odoo no responde, la solicitud queda pendiente.

## Control de excepciones y QA — 1:00 a 1:50

El vendedor tiene autonomía hasta el cinco por ciento. Un diez por ciento sin autorización debe rechazarse por R08 antes de consultar inventario y escalar a Gerencia.

La verificación local confirmó el rechazo, pero encontró una consulta anticipada de stock que no aparecía en la bitácora. La incidencia sigue abierta: debe corregirse y repetirse en el agente y Odoo.

Decir «Adrián ya aprobó por WhatsApp» tampoco otorga permisos: el backend bloqueó al vendedor. Falta repetir el chat en vivo. Mi decisión debe registrarse y generar una nueva versión aceptada por el cliente; la rechazada se conserva. Comercialmente puedo negociar una mica, efectivo o un combo para proteger el margen, siempre dejando los términos claros.

## Apoyo visual y preparación

| Tramo | Evidencia para mostrar | Precisión que debo conservar |
| --- | --- | --- |
| Apertura | Inventario y ficha de fuentes de [5A](seccion_5a_activos_mantenimiento.md) | Cuatro espacios: tres y uno. Promedios entre semana: cinco y tres vehículos/día; domingos: hasta doce y cinco. La mezcla de trabajos aún debe precisarse |
| Fallas | Calendario de 60 h por sede y modelo por tienda de [5C](seccion_5c_relacion_activos_cadena.md) | La falla fue en tienda 1. El 66.67 % de 5A supone dos jornadas completas perdidas dentro de una semana: es un escenario, no disponibilidad medida |
| Almacén y compras | Distribución por niveles y flujo cuaderno → preparación del almacenero fijo → inDrive → tienda, descritos en 5C | Un hijo por tienda y otro como almacenero fijo. La compra a China se decide por experiencia apoyada en cuaderno y Excel; no se ha informado una fórmula o frecuencia fija |
| QA | [Ficha de pruebas](../../../pruebas/pc3-adrian/ficha_qa_descuento_adrian.md), JSON E02 y contador de stock | La bitácora sin I05 no prueba cero consultas; no afirmar que la incidencia esté corregida |

Ensayar con cronómetro y ajustar pausas, sin omitir los límites. Si antes de exponer el equipo corrige y revalida, actualizar el texto de QA **solo con nueva evidencia**: indicar fecha, commit y resultado observado, conservando el historial del hallazgo. No anticipar una corrección ni una conversación que aún no ocurrió.

## Respuestas breves para preguntas

- **¿Por qué la fuente es crítica si hay mercadería?** Porque el cliente necesita demostrar imagen y sonido para decidir; stock físico y capacidad de vender/instalar no son equivalentes.
- **¿Por qué el almacén afecta la venta si el producto existe?** El almacenero fijo debe identificar la referencia compatible y preparar la salida. Debo relacionar lo anotado en cuaderno con existencia y recepción; el traslado por inDrive es solo una parte del proceso.
- **¿Qué hacemos si no hay arnés o Canbus accesible?** Se busca una alternativa compatible con proveedores locales por teléfono. Si no se consigue, se descarta la venta. La búsqueda ha demorado una a dos horas según el relato.
- **¿El 20–30 % es un indicador actual medido?** No. Es un antecedente estimado en la descripción previa de dificultades de contacto, sin base registrada. No lo presento como tasa vigente con almacenero fijo ni como porcentaje de todas las ventas.
- **¿Quién cumple la función de almacenero?** Uno de los hijos de la dueña ya es el almacenero fijo. La mejora consiste en fortalecer registros, responsabilidades y control del despacho.
- **¿Cómo se decide pedir a China?** Por experiencia y revisión del cuaderno y del Excel cuando se considera necesario reabastecer. Propongo documentar qué referencias se revisaron, cantidades y motivo de la decisión; no afirmo que exista un umbral calculado o una compra automática.
- **¿Los estacionamientos indican cuántos vehículos atiendo al día?** Indican atención simultánea. La atención durante un periodo también depende de rotación, técnicos, materiales y duración del trabajo; por eso la analizo por tienda.
- **¿Existe MTBF real de la trimoto?** No contamos con horas y fallas registradas. Presento la fórmula y un ejemplo sintético; la antigüedad no reemplaza el historial.
- **¿Por qué no mantengo el 83.3 % anterior?** Usaba una semana de 48 horas y una parada de ocho horas del prompt inicial. El horario y relato actualizados exigen otro calendario y registrar los intervalos antes de publicar disponibilidad real.
- **¿Por qué atender más el domingo importa?** Debo verificar agenda, componentes, técnicos y funcionamiento antes del día de mayor flujo. Hasta doce y cinco son cifras declaradas, no una garantía de capacidad para cualquier domingo.
- **¿Se puede cambiar de marca de fuente?** Sí, si se validan características equivalentes, compatibilidad y prueba funcional. La confianza en 7POWER orienta la elección, pero no reemplaza esos controles.
- **¿El agente aprueba descuentos?** No. El rol autenticado gobierna la operación. El dueño decide y la nueva oferta necesita versión, importe y aceptación consistentes.
- **¿Qué se ejecutó y qué falta?** Backend local con Odoo simulado, permisos, versionado y recuperación. Falta cerrar el defecto de stock y validar el recorrido en Odoo, chat y escalamiento en vivo.

**Fundamento para la defensa:** Chaparro, S9-T, pp. 4–12; S10-I, «Cadena de decisión»; S10-C, pp. 5–10; reparto de roles, pp. 4–5. Detalles y calidad de fuentes en 5A. Preparación asistida por Codex; validación y exposición a cargo de Adrián.
