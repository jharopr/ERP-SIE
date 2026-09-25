# MVP visual de MYS ERP para Odoo

Frontend estático y navegable para **IMPORTACIONES MYS HERMANOS S.A.C.**, basado en el alcance propuesto en S3: pedidos y atención, inventario, facturación y un canal digital. Usa patrones de módulos comerciales de Odoo como referencia funcional, sin incorporar código de Odoo. **No existe backend, base de datos, API, autenticación ni conexión con Odoo o SUNAT.** Los registros son ficticios y los cambios de la demo se guardan en `localStorage` del navegador.

## Pantallas y acciones

| Pantalla | Qué se puede probar |
| --- | --- |
| Resumen | KPIs ficticios, actividad ilustrativa, producto demo y pedidos recientes |
| Pedidos | Buscar, filtrar, crear pedido ficticio, ver detalle y cambiar estado visual |
| Inventario | Ver catálogo de tres artículos ficticios y descuento local al crear pedido |
| Facturación | Ver estado visual de comprobantes y crear un borrador local; no emite documentos |
| Canales | Seguir el flujo conceptual canal → ventas → inventario → facturación |

La demo impide crear pedidos con cantidad mayor al stock local. El botón **Restablecer demo** borra los cambios de esta aplicación en el navegador. Los precios, clientes, cantidades y gráficos son ejemplos; no proceden de la empresa.

## Ejecutar con Docker

Requisito: Docker con el subcomando `docker compose` disponible. Desde la raíz del repositorio:

```powershell
cd producto/frontend
docker compose up --build -d
```

Abrir **http://localhost:8080**. Para detener y retirar el contenedor:

```powershell
docker compose down
```

Si el puerto 8080 está ocupado, cambia `"8080:80"` por otro puerto local en [`compose.yaml`](compose.yaml). La imagen contiene únicamente Nginx y los archivos estáticos. No levanta Odoo ni PostgreSQL.

## Ejecutar sin Docker

Abre [`index.html`](index.html) en un navegador moderno. Para una revisión más fiel al despliegue, sirve la carpeta con un servidor estático local; no se necesitan dependencias npm ni acceso a internet. El código de interfaz está en [`app.js`](app.js) y [`styles.css`](styles.css).

## Imagen del prototipo

![Render PNG de un autoradio genérico usado como producto de demostración](imagenes/autoradio-demo.png)

El archivo [`imagenes/autoradio-demo.png`](imagenes/autoradio-demo.png) es un render ficticio generado con la herramienta integrada de imágenes de OpenAI para esta interfaz. Prompt usado: “Producto genérico de autoradio de doble DIN, fotografía de catálogo sobre fondo gris claro, vista tres cuartos, sin marca, texto, números ni personas”. No representa un artículo real de la empresa. Los demás elementos visuales se dibujan con HTML y CSS.

## Relación con PC1 y pasos siguientes

El diseño muestra el recorrido conceptual de [`arquitectura/erp-base.md`](../../arquitectura/erp-base.md) y permite discutir las preguntas de [`producto/backlog.md`](../backlog.md). Antes de integrar Odoo se deben confirmar el canal real, productos, roles, reglas de stock, comprobantes requeridos y la modalidad/licencia de Odoo. Las rutas para API, localización peruana y pruebas de sandbox pertenecen al incremento de backend posterior.
