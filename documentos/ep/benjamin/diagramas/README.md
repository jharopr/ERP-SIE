# Diagramas del bloque de Benjamin · examen parcial

Artefactos editables para IMPORTACIONES MYS HERMANOS S.A.C., comercializadora de autoradios. Alcance: cliente persona natural **nueva**, público general, canal **físico walk-in**, sin campaña atribuida; cinco autoradios para vehículos familiares. Continuidad de PC2 v2.1.

| Archivo | Uso |
| --- | --- |
| `01-mapa-corporativo.svg` / `.mmd` | Mapa corporativo nivel 1: estratégicos, core y soporte; no incluye manufactura. |
| `02-mapa-integrado-o2c-p2p.svg` / `.mmd` | Una vista del O2C evaluado, señal `REP-EP-001` y P2P completo en contexto tenue. |
| `03-flujo-roles-validacion.svg` / `.mmd` | Responsabilidades, validaciones y excepciones de descuento/disponibilidad. |
| `04-linea-tiempo-trazabilidad.svg` / `.mmd` | Orden cronológico e identificadores del caso normal, correlacionado por `COR-EP-001`. |

Los SVG contienen texto y formas vectoriales nativas. Pueden abrirse en el navegador o en un editor vectorial. Los `.mmd` conservan una representación Mermaid equivalente; el diseño visual puede variar según el renderizador. `generar_diagramas.py` regenera los SVG sin dependencias externas:

```powershell
python documentos/ep/benjamin/diagramas/generar_diagramas.py
```

La fecha `24/10/2026 -05:00` es lógica y didáctica; no representa una ejecución ya ocurrida. Los precios, las cantidades y el stock son sintéticos. Los diagramas describen **diseño / simulación local; Odoo no desplegado**.

El caso normal consulta ocho unidades para una necesidad de cinco y termina con `ACEPTADA` / `VALIDADA`, `order_id: null`. La aceptación de la cotización y la validación de la solicitud **no** crean pedido ni reservan stock. El caso alternativo `EP-S01` dispone de tres unidades para cinco solicitadas (déficit de dos): **tras los controles conformes y la evaluación de disponibilidad**, produce `PROMESA_CONDICIONADA` y una necesidad de reposición `REP-EP-001` para evaluación del dueño/compras; no se ejecuta una orden de compra ni se promete fecha. En el flujo por roles, el enlace conceptual `[1]` conecta esta rama con la evaluación, evitando implicar que la consulta inicial ya dispara compras. El descuento de 5% está permitido; 10% sin aprobación del dueño se rechaza.

La solicitud transmite referencias `CLI / OPP / COT`, versión y referencias `ACE / SOL / COR`. Los importes se leen del snapshot de cotización; la identidad del actor se maneja fuera del payload.

El resto del O2C se presenta únicamente como contexto hasta cobro aplicado. El P2P completo también es contexto; su recepción permitiría actualizar stock futuro y no cambia las existencias de la demostración.
