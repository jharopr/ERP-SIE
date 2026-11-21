# Odoo 18 · carga de datos sintéticos

`seed_odoo.py` se ejecuta **dentro del contenedor `compuerta`**, que tiene red hacia Odoo y acceso al volumen SQLite de la compuerta. La carpeta se monta en `/seed`.

```sh
docker compose exec -T compuerta python /seed/seed_odoo.py              # carga o refresca (idempotente)
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar  # además borra solicitudes y bitácora
docker compose exec -T compuerta python /seed/seed_odoo.py --crear-v3   # E02: COT-DEMO-004 v3 + ACE-PC3-005 tras la aprobación
```

## Qué hace
1. Espera a Odoo y crea la base `mys_demo` con el gestor de bases (`/xmlrpc/2/db`, `create_database`), **sin datos de demostración**, con el usuario `ODOO_USER` y la clave `ODOO_PASSWORD`. Usa `ODOO_MASTER_PASSWORD`.
2. Instala `crm`, `sale_management` y `stock` (`button_immediate_install`). `sale_crm` se instala solo y agrega `sale.order.opportunity_id`.
3. Configura la empresa en PEN y renombra el almacén a `TIENDA-DEMO`.
4. Crea el usuario `vendedor01`, que se mapea a VEN-DEMO-01 porque el motor exige `seller_id == actor`.
5. Crea los productos RAD-7BT y RAD-10X. Son almacenables (`type='consu'` + `is_storable=True` en Odoo 18; se detecta con `fields_get`) y van **sin impuestos**.
6. Fija el stock físico en 10 y 10 con `stock.quant` (`inventory_quantity` + `action_apply_inventory`).
7. Confirma RES-DEMO-001 y RES-DEMO-002 de CLI-DEMO-002, lo que reserva 2 y 7 unidades.
8. Crea OPP-DEMO-001 y OPP-DEMO-002 (`crm.lead`, `type='opportunity'`) y las cotizaciones por versión (`client_order_ref = "COT-DEMO-00x vN"`), en estado sent o cancel y con `validity_date` igual a hoy.
9. Registra en la compuerta los actores, la política (5 %), los clientes, el mapa de IDs y las aceptaciones ACE-PC3-001…004 (hora = ahora − 5 min).
10. Verifica que el disponible sea 8 y 3. Si no coincide, termina con error.

Las búsquedas son por `ref`, `default_code`, `client_order_ref` o el nombre de la oportunidad, así que volver a ejecutarlo **no duplica** registros. Las versiones creadas durante un ensayo (por ejemplo, COT-DEMO-004 v3) se anulan al refrescar.

Acceso web: `http://localhost:8069`, base `mys_demo`, usuario `ODOO_USER`, clave `ODOO_PASSWORD`.
