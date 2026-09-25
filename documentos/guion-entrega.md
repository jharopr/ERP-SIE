# Lista de verificación de la solución

| Área | Evidencia | Criterio de revisión |
| --- | --- | --- |
| Empresa y problema | [Ficha de la empresa](contexto-y-alcance.md) | Los dos canales y las dificultades actuales están descritos |
| Proceso | [Flujo comercial](../procesos/flujos-prioritarios.md) | El proceso une cliente, pedido, stock, venta y documento |
| Comparación | [Ficha de comparación](../arquitectura/comparativo-erp.md) | Las alternativas y el rol distinto de UBLHUB están claros |
| Decisión | [Criterios](../arquitectura/criterios-seleccion.md) | Odoo + UBLHUB aparece como decisión, no como candidato abierto |
| Arquitectura | [Implementación base](../arquitectura/erp-base.md) | Actores, interfaces, límites, errores y seguridad son coherentes |
| Datos | [Inventario de datos](../datos/inventario-fuentes.md) | Existen claves, reglas de duplicado y tratamiento de privacidad |
| Producto | [Backlog](../producto/backlog.md) | Las tareas tienen prioridad y evidencia de cierre |
| Pruebas | [Casos](../pruebas/casos-aceptacion.md) | Se cubren ambos canales y los tres documentos electrónicos |
| Fuentes | [Registro](../fuentes/registro-fuentes.md) | Solo contiene fuentes de productos y comparación |
| Trazabilidad | [Versiones](versiones.md) | Las decisiones vigentes están registradas |

## Revisión previa al piloto

- validar usuarios, catálogos, tipos de cliente y stock inicial;
- completar la documentación oficial y el sandbox de UBLHUB;
- probar autenticación, idempotencia, errores y reintentos;
- ejecutar ventas por ERP/presencial y WhatsApp móvil;
- verificar boleta, factura y guía de remisión;
- capacitar usuarios y documentar contingencia;
- excluir datos personales y secretos de las evidencias.
