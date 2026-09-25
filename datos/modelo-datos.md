# Modelo de Datos

Este documento define las entidades principales, sus atributos mínimos y las relaciones que conforman el modelo de datos del proyecto (integración Odoo + UBLHUB).

## Diagrama Entidad-Relación (ERD)

A continuación se presenta el diagrama de bloques/ER del modelo de datos:

```mermaid
erDiagram
    CLIENTE ||--o{ PEDIDO : "realiza"
    CLIENTE ||--o{ VENTA : "facturado a"
    PRODUCTO ||--o{ INVENTARIO : "almacenado en"
    PRODUCTO ||--o{ LINEA_PEDIDO : "incluido en"
    PEDIDO ||--|{ LINEA_PEDIDO : "contiene"
    PEDIDO ||--o| VENTA : "genera"
    VENTA ||--o| DOCUMENTO_ELECTRONICO : "registra como"
    PEDIDO ||--o{ INTERACCION : "referenciado por"

    CLIENTE {
        string ID
        string tipo
        string documento_RUC "Documento/RUC"
        string nombre_razon_social "Nombre o Razón Social"
        string contacto_autorizado "Contacto Autorizado"
        string estado
    }

    PRODUCTO {
        string SKU "SKU (Único)"
        string descripcion
        string unidad
        float precio
        float impuestos
        string estado
    }

    PEDIDO {
        string ID
        date fecha
        string canal "ERP/presencial o WhatsApp"
        float total
        string estado
    }

    LINEA_PEDIDO {
        int cantidad
        float subtotal
    }

    INVENTARIO {
        string SKU
        string ubicacion
        int disponible
        int reservado
        string movimiento
    }

    VENTA {
        string ID_Odoo
        float total
        string pago
        string estado
    }

    DOCUMENTO_ELECTRONICO {
        string tipo
        string serie_numero "Serie/Número"
        string ID_UBLHUB
        string estado
        string archivos
        string error
    }

    INTERACCION {
        string referencia_pedido
        string canal
        date fechas
        string estado
    }
```

## Diccionario de Entidades

| Entidad | Descripción | Cardinalidad y Relaciones |
| --- | --- | --- |
| **Cliente** | Representa a una persona o empresa. Se controla por documento o RUC para evitar duplicados. | Un `Cliente` puede realizar múltiples `Pedidos` y tener múltiples `Ventas`. (1:N) |
| **Producto** | Catálogo de bienes o servicios con su información base y precio. Identificado de forma única por su SKU. | Un `Producto` puede tener múltiples registros de `Inventario` y aparecer en múltiples `Líneas de Pedido`. (1:N) |
| **Pedido** | Solicitud de compra proveniente de canales autorizados (presencial o WhatsApp). | Un `Pedido` pertenece a un único `Cliente` (N:1), contiene una o más `Líneas de Pedido` (1:N) y puede generar una `Venta` (1:1). |
| **Línea de Pedido** | Entidad intermedia que desglosa los productos y cantidades solicitadas en un pedido. | Pertenece a un único `Pedido` y referencia a un único `Producto`. |
| **Inventario** | Registro de las existencias, ubicación y movimientos de un producto. | Asociado directamente a un `Producto` (N:1). |
| **Venta** | Registro transaccional en Odoo una vez que un pedido es procesado y pagado. | Generada a partir de un `Pedido` (1:1), asociada a un `Cliente` (N:1) y genera un único `Documento Electrónico` (1:1). |
| **Documento Electrónico** | Comprobante tributario (boleta/factura) procesado a través de UBLHUB. | Corresponde a una única `Venta` (1:1). |
| **Interacción** | Registro de la comunicación en canales (ej. WhatsApp). | Se asocia referencialmente a un `Pedido` (N:1). |

