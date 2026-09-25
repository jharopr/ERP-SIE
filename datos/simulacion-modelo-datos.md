# Prueba de Integridad del Modelo de Datos (Simulación)

Para validar que las relaciones y cardinalidades del modelo de datos son correctas, a continuación hacemos una simulación de un escenario completo ("gran interacción") tal como si la base de datos estuviera funcionando. 

## Escenario: Compra múltiple y facturación electrónica

**Contexto:** Un cliente hace un pedido por WhatsApp que incluye dos productos diferentes. El pedido se aprueba, se deduce del inventario, se registra la venta en el ERP (Odoo) y finalmente se emite la factura electrónica a la SUNAT (vía UBLHUB).

---

### Paso 1: Creación del Cliente y los Productos (Catálogo)
Primero, la base de datos debe tener existencias y el cliente registrado.

**Tabla: `CLIENTE`**
| ID | tipo | documento_RUC | nombre_razon_social | contacto_autorizado | estado |
|----|------|---------------|---------------------|---------------------|--------|
| CLI-001 | B2B | 20123456789 | Tech Solutions SAC | Juan Pérez | Activo |

**Tabla: `PRODUCTO`**
| SKU | descripcion | unidad | precio | impuestos | estado |
|-----|-------------|--------|--------|-----------|--------|
| PROD-A1 | Laptop XYZ | Unidad | 1000.00 | 18% | Activo |
| PROD-B2 | Mouse Óptico | Unidad | 50.00 | 18% | Activo |

**Tabla: `INVENTARIO`**
| SKU | ubicacion | disponible | reservado | movimiento |
|-----|-----------|------------|-----------|------------|
| PROD-A1 | Almacén Central | 10 | 0 | Entrada Inicial |
| PROD-B2 | Almacén Central | 50 | 0 | Entrada Inicial |

✅ *Check de relación:* `INVENTARIO` referencia al `SKU` de `PRODUCTO` (Relación N:1 funciona).

---

### Paso 2: Interacción y Creación del Pedido
El cliente contacta a la empresa por WhatsApp y se registra el pedido.

**Tabla: `INTERACCION`**
| referencia_pedido | canal | fechas | estado |
|-------------------|-------|--------|--------|
| PED-2023-001 | WhatsApp | 2023-10-25 10:00:00 | Completado |

**Tabla: `PEDIDO`**
| ID | fecha | canal | total | estado | ID_Cliente |
|----|-------|-------|-------|--------|------------|
| PED-2023-001 | 2023-10-25 | WhatsApp | 1239.00 | Pendiente | CLI-001 |

✅ *Check de relación:* `PEDIDO` está enlazado a `CLIENTE` mediante `ID_Cliente` (Relación N:1 funciona). `INTERACCION` se asocia al `PEDIDO` (N:1 funciona).

---

### Paso 3: Desglose del Pedido (Líneas de Pedido)
El pedido PED-2023-001 tiene dos productos. Aquí es donde se valida la relación Muchos a Muchos (M:N) resuelta con la tabla `LINEA_PEDIDO`.

**Tabla: `LINEA_PEDIDO`**
| ID_Pedido | SKU_Producto | cantidad | subtotal (con IGV) |
|-----------|--------------|----------|--------------------|
| PED-2023-001 | PROD-A1 | 1 | 1180.00 |
| PED-2023-001 | PROD-B2 | 1 | 59.00 |

✅ *Check de relación:* `LINEA_PEDIDO` une a `PEDIDO` (ID_Pedido) y a `PRODUCTO` (SKU_Producto). Permite que un pedido tenga muchos productos y que un producto esté en muchos pedidos.

---

### Paso 4: Actualización de Inventario
El sistema reserva los ítems mientras se procesa la venta.

**Tabla: `INVENTARIO` (Actualizado)**
| SKU | ubicacion | disponible | reservado | movimiento |
|-----|-----------|------------|-----------|------------|
| PROD-A1 | Almacén Central | 9 | 1 | Reserva PED-2023-001 |
| PROD-B2 | Almacén Central | 49 | 1 | Reserva PED-2023-001 |

---

### Paso 5: Confirmación de Venta (Odoo)
El pedido se paga y se convierte en una venta en el ERP.

**Tabla: `VENTA`**
| ID_Odoo | ID_Pedido | ID_Cliente | total | pago | estado |
|---------|-----------|------------|-------|------|--------|
| SO-0099 | PED-2023-001 | CLI-001 | 1239.00 | Transferencia | Pagado |

✅ *Check de relación:* La `VENTA` referencia unívocamente al `PEDIDO` (1:1 o 1:N si se factura parcial) y al `CLIENTE`.

---

### Paso 6: Facturación Electrónica (UBLHUB)
Una vez pagada la venta, Odoo llama a la API de UBLHUB para generar la factura electrónica.

**Tabla: `DOCUMENTO_ELECTRONICO`**
| ID_Venta | tipo | serie_numero | ID_UBLHUB | estado | archivos | error |
|----------|------|--------------|-----------|--------|----------|-------|
| SO-0099 | Factura | F001-0000045 | UBL-998877 | Aceptado | F001-0000045.xml | Ninguno |

✅ *Check de relación:* `DOCUMENTO_ELECTRONICO` se vincula estrictamente 1:1 con la `VENTA` (ID_Venta), asegurando que una venta solo tenga una factura y permitiendo trazabilidad perfecta en caso de error tributario.

---

### Conclusión de la Prueba
La trazabilidad de los datos funciona perfectamente de principio a fin:
**Interacción (WhatsApp) ➔ Pedido ➔ Líneas de pedido ➔ Producto ➔ Inventario ➔ Venta (Odoo) ➔ Documento Electrónico (UBLHUB / SUNAT)**.

Las relaciones planteadas (1 a N para catálogos y 1 a 1 para documentos financieros) soportan el flujo completo sin redundancia de datos ni pérdida de integridad referencial.
