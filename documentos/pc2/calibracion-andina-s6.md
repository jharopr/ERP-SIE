# Calibración documental Andina · Semana 6

Fuente: `GE703_S6_Presentacion.pdf`, pp. 25–30. Esta calibración precede a la adaptación MYS y mantiene separados los hechos del material y los supuestos de la empresa del grupo. [Evidencia regenerable](../../pruebas/pc2/evidencias/andina-s6.json); generador [calibrar_andina.py](../../pruebas/pc2/calibrar_andina.py).

**Datos del caso:** se solicitan 1,000 unidades, hay 650 disponibles y 350 en reposición; el cliente acepta entrega parcial y pide una factura al completar; el descuento excede la autoridad comercial. No se especifican porcentaje/umbral de descuento, aprobador concreto, precio, crédito, identidad fiscal ni fecha de reposición. No se traslada el 5 % ficticio de MYS a Andina.

| Escenario S6 | Respuesta de contrato / seguimiento | Responsable y acción | Vacío conservado |
| --- | --- | --- | --- |
| Descuento fuera de autoridad | PENDIENTE_APROBACION; bloquear confirmación, conservar oportunidad | Responsable comercial identifica autoridad y registra decisión antes de continuar | Autoridad, porcentaje y plazo de atención por acordar |
| Disponibilidad parcial | Propuesta de 650 + saldo 350; promesa por validar | Ventas/Almacén documentan plan parcial y validan fecha del saldo; conservar aceptación del cliente | La aceptación de entrega parcial no acredita una fecha; `promised_date=null` |
| Una factura al completar | Regla propuesta de continuidad posterior a PC2, sin factura emitida | Facturación verifica entrega completa de 1,000 y aceptación antes de la emisión única acordada | Identidad fiscal y condiciones de facturación pendientes; no se ofrece asesoría tributaria |
| Retraso de reposición | Atención abierta en CRM con causa, saldo y próxima acción | Ventas informa retraso y renegocia con apoyo de Almacén; conserva historial de nuevas condiciones | Nueva fecha y plazo de respuesta desconocidos; no inventar compromiso |

En esta calibración los plazos faltantes permanecen nulos y se declaran como brechas por resolver antes de operar. El simulador MYS, separado, usa 24 horas **solo como supuesto didáctico**. La prueba documental comprueba conciliación de cantidades y que no se conviertan vacíos en aprobaciones, fechas, facturas o pedidos confirmados. No ejecuta las validaciones de precio/crédito de MYS contra datos inventados de Andina.
