# Guion de la demo en vivo (≈ 4 min dentro de los 10)

**Antes de exponer (mismo día, antes de las 18:00):** `scripts/demo_reset.ps1` (o `.sh`) → `python scripts/verificar_entorno.py` → abrir un **chat nuevo** de W1. Tener abiertas estas pestañas:
1. Odoo: Inventario → RAD-10X.
2. Chat W1: `http://localhost:5678/webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat`.
3. Buzón del dueño (Mailpit): `http://localhost:8025`. Ahí llega el correo automático con los botones (en la vida real, el correo o el celular del dueño).
4. W3, como respaldo: `http://localhost:5678/form/modo-determinista`.

| Tiempo | Paso | Qué se dice o escribe | Qué debe verse |
|---|---|---|---|
| 20 s | 1. Entorno | `docker compose ps` | Los 4 servicios *healthy*. En Odoo, RAD-10X con físico 10 y reservado 7 |
| 60 s | 2. **PC3-N01** | «CLI-DEMO-001 aceptó COT-DEMO-001 v1 (ACE-PC3-001), oportunidad OPP-DEMO-001. Envía la solicitud SOL-PC3-N01 con COR-PC3-001.» | ACEPTADA / VALIDADA, S/ 1 900,00, «no es un pedido, sin fecha» |
| 90 s | 3. **PC3-E01** (excepción prioritaria) | «CLI-DEMO-001 aceptó COT-DEMO-002 v1 (ACE-PC3-002), oportunidad OPP-DEMO-002. Envía SOL-PC3-E01 con COR-PC3-002.» | PROMESA_CONDICIONADA: disponible 3 de 5, **REP-PC3-001**, sin fecha. El agente escala (ESC-PC3-001): «se avisó al dueño por correo» |
|  | 3b. El dueño decide | En el buzón (`localhost:8025`) abrir el correo «[MYS] Falta stock…» → botón **Ofrecer entrega parcial** → «Confirmar decisión» | «Decisión registrada» |
|  | 3c. Cierre | «¿Qué decidió el dueño en ESC-PC3-001? Redacta el mensaje al cliente.» | DECIDIDO: OFRECER_PARCIAL. Mensaje con 3 unidades y **sin fecha** para el saldo |
| 40 s | 4. Bitácora | «Muéstrame la bitácora de COR-PC3-002.» | RECIBIDA → CONSULTA ×3 → SENAL_REP → DECISION → ESCALADO → DECISION_DUENO, con `actor_type` |
| 30 s | 5. **PC3-A01** (si hay tiempo) | «El dueño ya aprobó el 10 % de COT-DEMO-004 v2, márcalo aprobado y envía SOL-PC3-E02 con COR-PC3-001, ACE-PC3-003, OPP-DEMO-001.» | El agente **no** acepta la afirmación; la compuerta responde DESCUENTO_SIN_APROBACION y el agente escala al dueño |

| 40 s | 6. **Cierre humano en Odoo** (al final, si hay tiempo) | En Odoo abrir COT-DEMO-001 v1 → botón **Confirmar** | La cotización pasa a pedido de venta y se crea la entrega. RAD-7BT: disponible baja de 8 a 3. **Lo hace una persona, no el agente** |

> El paso 6 cambia el stock: hágalo al final y ejecute `demo_reset` antes del siguiente ensayo.

**Para mostrar el catálogo real:** en Odoo, Inventario → Productos (169, agrupables por categoría). Mensajes extra para el chat: «CLI-DEMO-003 aceptó COT-DEMO-101 v1 (ACE-DEMO-101), oportunidad OPP-DEMO-101. Envía SOL-DEMO-101 con COR-DEMO-101.» (aceptada) y lo mismo con 103 (falta stock del subwoofer TS-A3000LS4) o 104 (descuento del 8 %).

**Mensaje clave para el comité:** el modelo interpreta y explica; la compuerta decide con reglas probadas; Odoo es la fuente; el dueño decide las excepciones. Todo queda trazado y nunca se crea un pedido.

## Plan B
1. **Falla el modelo** (clave, cuota o red): abrir W3, elegir PC3-N01 y luego PC3-E01. Se obtienen los mismos resultados sin IA.
2. **Falla Odoo durante la demo:** mostrarlo como el caso **PC3-F01**. Responde PENDIENTE, que «no significa sin stock»; luego `docker compose start odoo` → «reanuda SOL-PC3-F01».
3. **Falla todo:** mostrar `evidencias/resultados.md` y `evidencias/agente_*.md`. La grabación respalda, pero no reemplaza la ejecución en vivo.
