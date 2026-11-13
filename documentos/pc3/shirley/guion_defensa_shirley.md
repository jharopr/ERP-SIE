# Guion individual de defensa — Shirley Carrión Oré

**GE703 · Grupo 7 · Importaciones MYS Hermanos S.A.C.** Preparado el 12/11/2026 para la exposición del 14/11/2026. Duración objetivo: **1 min 50 s** dentro de los diez minutos grupales. Texto en primera persona para ensayar; adaptarlo con palabras propias.

## Apertura — 0:00 a 0:20

Soy Shirley Carrión. Consolidé el informe y analicé inventarios y nivel de servicio. Mi pregunta fue: si el cliente pide cinco radios, ¿cuántas podemos prometer de verdad, y cómo lo medimos?

## Inventario y servicio — 0:20 a 1:10

En MYS la mercadería está sobre todo en Carabayllo: audio en el primer piso y más de mil variantes de marcos, arneses y cables en el segundo. Hay un almacenero fijo, pero el stock se lleva en cuaderno y Excel, sin hora ni estado.

Por eso separo tres cantidades: lo **registrado**, lo **disponible**, que es registrado menos reservado, y lo **utilizable**, que además tiene que ser compatible con el vehículo. Una pantalla sin su arnés no sirve para instalar.

Propongo medir juntos dos indicadores. En los casos del prototipo, que son sintéticos, se atienden 8 de 10 unidades: 80 %. Pero solo 1 de 2 clientes recibe todo lo que pidió: 50 %. Un buen porcentaje de unidades puede esconder clientes mal atendidos.

## Prueba y límites — 1:10 a 1:50

Como QA hice una instalación limpia del prototipo: los casos normal, parcial y de descuento se reproducen desde cero. En el parcial el sistema responde 3 de 5, sin reservar, sin fecha y con una señal de reposición, sin comprar solo.

También encontré incoherencias con el parcial, como la ubicación de la empresa y decir que la bitácora es «inmutable»; el informe PC3 ya las corrige. La prueba del agente en vivo depende del paquete de Ballack.

Nuestra decisión es una aprobación condicionada: un piloto de cuatro semanas que empieza por arneses y Canbus, y sin dato confiable con hora, no hay fecha.

## Preguntas probables

| Pregunta | Respuesta corta |
| --- | --- |
| ¿El 80 % es el nivel de servicio de la empresa? | No. Sale de casos sintéticos del prototipo; sirve para probar la fórmula. La empresa aún no registra solicitudes ni respuestas. |
| ¿Por qué no calcularon cobertura o rotación? | La exportación de ventas no tiene fecha, así que no se puede convertir en demanda diaria. Inventarla sería falso. |
| ¿Por qué empezar por arneses y Canbus? | Porque son los que bloquean la instalación aunque exista la pantalla, y tienen la mayor variedad. |
| ¿Qué diferencia hay entre disponible y utilizable? | Disponible es registrado menos reservado. Utilizable además es compatible y está en el lugar y a la hora en que se necesita. |
| ¿El agente puede reservar o comprar? | No. Consulta, explica y escala. La reserva es al confirmar el pedido y la compra la decide la gestión familiar. |
| ¿Qué pasa si Odoo se cae? | La solicitud queda pendiente; no significa «sin stock». Se informa al cliente que se le confirmará. |
| ¿Qué diferencia tu parte de la de Benjamín? | Él explica cómo fluye la mercadería; yo, qué disponibilidad y servicio produce ese flujo. Usamos las mismas unidades. |
| ¿Hay Odoo instalado en la empresa? | No. Es un prototipo académico; no lo presentamos como sistema productivo. |
