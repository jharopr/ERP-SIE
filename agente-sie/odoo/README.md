# Odoo 18 · catálogo y datos de demostración

`seed_odoo.py` se ejecuta **dentro del contenedor `compuerta`**, que tiene red hacia Odoo y acceso al volumen SQLite de la compuerta. La carpeta se monta en `/seed`.

```sh
docker compose exec -T compuerta python /seed/seed_odoo.py              # carga o refresca (idempotente)
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar  # además borra solicitudes y bitácora
docker compose exec -T compuerta python /seed/seed_odoo.py --crear-v3   # E02: COT-DEMO-004 v3 + ACE-PC3-005 tras la aprobación
```

## Catálogo (`catalogo.csv`)
Se genera desde la lista de productos de la empresa (Excel) con:
```sh
pip install openpyxl
py -3.11 scripts/importar_catalogo.py ../LISTA_PRODUCTOS_EMPRESA_18717.xlsx   # o python3 en Linux/macOS
```
- **Del Excel se toma:** código interno (SKU), nombre, categoría/subcategoría, unidad, código de barras y precio de venta (lista por menor).
- **No se toma:** el precio de costo (dato sensible que el agente no necesita) ni la lista por mayor (el contrato v1.0 valida contra el precio de lista).
- **Stock:** el Excel no lo trae, así que se asigna uno **sintético**, fijo por SKU y por rango de categoría, con ajustes para que el escenario de `escenario_extra.json` muestre cada resultado. Con el inventario real, basta con cambiar la columna `stock_fisico`.
- **Correcciones automáticas** (el script las lista): 8 productos sin categoría se asignan por su descripción, 3 subcategorías truncadas, 2 nombres truncados y un código de barras con formato numérico erróneo (`0.10000125`).
- Se agregan RAD-7BT y RAD-10X (genéricos): los casos oficiales PC3 dependen de su precio y stock, y el seed lo verifica.
- Los servicios (instalación, mano de obra) se cargan como `type='service'`, sin stock. Los cables se venden por **metro**.
- Los productos de un catálogo anterior se **archivan**, no se borran.

## Qué hace
1. Espera a Odoo y crea la base `mys_demo` con el gestor de bases (`/xmlrpc/2/db`, `create_database`), **sin datos de demostración**, con el usuario `ODOO_USER` y la clave `ODOO_PASSWORD`. Usa `ODOO_MASTER_PASSWORD`.
2. Instala `crm`, `sale_management` y `stock` (`button_immediate_install`). `sale_crm` se instala solo y agrega `sale.order.opportunity_id`.
3. Configura la empresa en PEN y renombra el almacén a `TIENDA-DEMO`.
4. Crea el usuario `ven-demo-01`, que se mapea a VEN-DEMO-01 porque el motor exige `seller_id == actor`.
5. Crea las categorías (dos niveles) y los productos de `catalogo.csv`. Los almacenables usan `type='consu'` + `is_storable=True` en Odoo 18 (se detecta con `fields_get`) y van **sin impuestos**.
6. Fija el stock físico con `stock.quant` (`inventory_quantity` + `action_apply_inventory`, en un solo ajuste agrupado).
7. Confirma las ventas que generan reservas: RES-DEMO-001/002 de CLI-DEMO-002 (2 y 7 unidades de los casos PC3) y RES-DEMO-101…103 del escenario extra. Si el contenido cambió, anula la anterior y crea otra.
8. Crea las oportunidades OPP-DEMO-00x y OPP-DEMO-10x (`crm.lead`, `type='opportunity'`), dos **leads sin convertir** (para mostrar «lead → oportunidad») y las cotizaciones por versión (`client_order_ref = "COT-DEMO-xxx vN"`), en estado sent o cancel y con `validity_date` igual a hoy.
9. Registra en la compuerta los actores, la política (5 %), los clientes, el mapa de IDs y las aceptaciones ACE-PC3-001…004 (hora = ahora − 5 min).
10. Verifica físico, reservado y disponible de **todos** los productos almacenables (RAD-7BT 8 y RAD-10X 3 disponibles). Si algo no coincide, termina con error.

Las búsquedas son por `ref`, `default_code`, `client_order_ref` o el nombre de la oportunidad, así que volver a ejecutarlo **no duplica** registros. Las versiones creadas durante un ensayo (por ejemplo, COT-DEMO-004 v3) se anulan al refrescar.

Acceso web: `http://localhost:8069`, base `mys_demo`, usuario `ODOO_USER`, clave `ODOO_PASSWORD`.
