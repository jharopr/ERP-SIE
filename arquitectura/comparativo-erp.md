# Comparativo de arquitecturas ERP v0.1 mejorado

## Alcance de la evidencia

El taller S2, §§1-5 (12/09/2026), comparó StarSoft, Odoo y Dynamics 365 Business Central. La tabla conserva sus hallazgos como **información recopilada por el equipo**, con fuentes registradas allí. En este incremento no se revalidaron en línea versiones, precios ni capacidades actuales. Las fichas comerciales no prueban un flujo integrado funcionando.

| Criterio | StarSoft | Odoo | Business Central | Vacío decisivo |
| --- | --- | --- | --- | --- |
| Despliegue | S2 describe uso local y oferta cloud comercial sin detalle técnico público | S2 cita Odoo Online, Odoo.sh y on-premise | S2 cita Online y on-premises | Disponibilidad, responsabilidad operativa y conectividad de cada oferta cotizada |
| Arquitectura y extensión | S2 no halló documentación técnica pública de capas/API; señala consultoría del proveedor | S2 describe módulos Python y PostgreSQL con documentación pública | S2 describe extensiones AL y APIs documentadas | Acceso a sandbox, límites de personalización y costos |
| Integración | S2 no halló API pública documentada | S2 registra mecanismos y conectores externos | S2 registra REST/OData y ecosistema Azure | Probar conexión con el canal y sistemas **reales** de la empresa |
| Contexto peruano | S2 reporta foco en SUNAT/PLE desde material del proveedor | S2 encontró documentación de localización fiscal para Perú | S2 no encontró localización peruana oficial en las fuentes consultadas | Confirmar por escrito y demostrar comprobantes/libros requeridos con producto y partner concretos |
| Operación y soporte | S2 cita soporte del proveedor; mantenimiento específico por cotizar | Depende de la modalidad elegida | Depende de modalidad y partner | SLA, respaldos, administración de usuarios y costo total |

## Evidencia, interpretación y supuesto

- **Evidencia de fuente consultada:** S2, §1, lista páginas de proveedores y documentación técnica con fecha 12/09/2026. Ver [registro de fuentes](../fuentes/registro-fuentes.md).
- **Interpretación del equipo:** un servicio administrado podría reducir mantenimiento local si se confirma poca capacidad de TI; documentación pública facilita evaluar integraciones.
- **Supuestos no resueltos:** número de usuarios, sedes, presupuesto, conectividad, motor de datos, canales, sistemas existentes, cobertura SUNAT/PLE y precios. S2, §§3-5, reconoce varios de estos vacíos.
- **Límite:** la ausencia de información en las fuentes revisadas no prueba que una función no exista. Una localización publicada tampoco prueba que cubra todos los comprobantes requeridos.

## Mejora necesaria antes de elegir producto

Solicitar a cada proveedor/partner un mismo caso de demostración: pedido originado en un canal digital, reserva de stock, venta, factura o boleta electrónica, respuesta de aceptación/rechazo y actualización de estado para atención. Registrar versión, modalidad, configuración, intermediarios, tiempo, errores, costo y fuente de cada resultado. La [matriz de criterios](criterios-seleccion.md) define cómo usar esa evidencia.
