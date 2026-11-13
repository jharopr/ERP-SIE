# Revisión de C01/C02 (Contactos y CRM/Lead)

| Campo | Registro |
|---|---|
| Objeto revisado | Sistema Odoo 18 + addon `mys_erp`, rama `sistema-agente` (carpeta `app/`) |
| Datos | **Sintéticos.** Clientes `CLI-DEMO-001…008`, leads `LEAD-MYS-001…006`, oportunidades `OPP-DEMO-*` y `OPP-CAT-*` |

## 1. Alcance y método
Se revisó la línea base de **C01 (CRM: leads y oportunidades)** y **C02 (Contactos)** en dos pasos:

1. **Recorrido funcional** en el sistema en ejecución local (Docker, `http://localhost:8088`) con la cuenta `vendedor01`. Se recorrieron Contactos, Leads, CRM/Oportunidades y Ventas/Cotizaciones, y se hizo una prueba de creación de clientes duplicados.
2. **Contraste con el código:** `app/odoo/addons/mys_erp/models/contacto.py`, `models/sistema.py` y `app/odoo/seed_sistema.py`.

Límites: no se probaron cambios de código en Odoo; todas las mejoras son **propuestas**. Los datos no son reales.

## 2. Qué se verificó y funciona
| # | Verificación | Resultado | Evidencia |
|---|---|---|---|
| V1 | Hay 8 clientes de prueba, cada uno con referencia, bandera «Datos de prueba MYS», segmento e «Identidad sintética revisada» (se comprobó en la ficha de `CLI-DEMO-002`) | Correcto | 01, 03 |
| V2 | Los contadores de la tarjeta (leads + oportunidades) cuadran: cliente 001 = 3 (LEAD-MYS-001 + OPP-DEMO-001 + OPP-DEMO-002); cliente 003 = 4 (LEAD-MYS-003 + 3 OPP-CAT) | Correcto | 01, 05, 07 |
| V3 | Hay 6 leads (uno por cliente 001–006), con vendedor asignado y nota «Visita espontánea en tienda. Datos sintéticos de demostración.»; el lead ofrece «Convertir a oportunidad» | Correcto | 05, 06 |
| V4 | Hay 5 oportunidades, todas en la etapa «Nuevo» (3 de catálogo para el cliente 003 y 2 demo para el cliente 001) | Correcto | 07 |
| V5 | Las 8 cotizaciones (S00003–S00010, total S/ 17,590.00) coinciden con los datos cargados: COT-DEMO-001 a 004 (la v1 de la 004 aparece **anulada**, y la v2 vigente) y 3 cotizaciones de catálogo; todas «Nada que facturar» | Correcto | 08 |
| V6 | Trazabilidad: el historial de cada contacto registra su creación y cambios de nombre, y el lead registra «Lead/oportunidad creada» | Correcto | 02, 06 |
| V7 | Controles en el código (lectura): una cotización exige que la oportunidad sea de tipo oportunidad y **del mismo cliente** (`sistema.py`, ~l.199); exige «Identidad revisada» antes de evaluar (~l.217); si el cliente no tiene referencia se le asigna `CLI-MYS-<id>` (~l.201) | Presente en código; **no ejecutado** en esta revisión | código |

## 3. Hallazgos
| ID | Hallazgo | Pasos y entrada | Esperado | Observado | Evidencia | Prioridad | Recomendación |
|---|---|---|---|---|---|---|---|
| **H1** | Odoo permite crear clientes duplicados sin ningún aviso | Contactos → Nuevo → nombre «Cliente de prueba 002» → Guardar (repetido unas 4 veces) | Aviso o bloqueo ante un cliente ya existente | Se guardaron todos sin aviso; la lista pasó de 8 a 11 o más tarjetas, con varias «Cliente de prueba 002» (0 oportunidades, 0 ventas) | 04 | **Alta** | Aviso al crear un cliente con el mismo nombre |
| **H2** | No existe restricción de referencia única por cliente | Lectura de `contacto.py` | `ref` única por empresa | El modelo solo añade `mys_demo`, `mys_segmento` y `mys_identidad_revisada`; no hay `_sql_constraints` ni `@api.constrains` | código | **Alta** | Restricción de unicidad de `ref` por compañía (cuando no esté vacía) |
| **H3** | La referencia del cliente solo se ve dentro de la pestaña «MYS» | Lista de clientes, leads, oportunidades y cotizaciones | Referencia visible donde se elige al cliente | Solo aparece el nombre; con duplicados el vendedor no distingue a quién cotiza | 01, 03, 05, 07, 08 | Media | Mostrar la referencia en el nombre visible y en la búsqueda |
| **H4** | Leads y oportunidades sin datos comerciales | Lista de leads y kanban de oportunidades | Ingreso esperado y probabilidad para el embudo | Todos con S/ 0.00, 0 % y etapa «Nuevo»; el encabezado «0» de la columna «Nuevo» parece ser la suma del ingreso esperado y no la cantidad de tarjetas | 05, 06, 07 | Baja | Cargar importes de ejemplo y aclarar el contador |
| **H5** | Clientes y leads sin datos de contacto | Ficha del cliente y del lead | Teléfono, correo, dirección e identificación fiscal | Todos vacíos | 02, 06 | Baja | Aceptable por ser datos sintéticos; declararlo |

## 4. Pruebas pendientes (no ejecutadas en esta versión)
No se declaran como realizadas.

| Prueba | Resultado esperado según el código |
|---|---|
| Cotizar a un cliente **sin** «Identidad revisada» | `CLIENTE_NO_VALIDADO` |
| Cotizar con 3 % de descuento | `VALIDADA` |
| Cotizar con 10 % de descuento sin autorización | `RECHAZADA / DESCUENTO_SIN_APROBACION` |
| Cotizar desde una oportunidad de **otro** cliente | Error «La oportunidad debe estar convertida y corresponder al mismo cliente» |

*(Completar «observado» y la evidencia si se ejecutan; en caso contrario, mantener como pendientes.)*

## 5. Mejora propuesta (no ejecutada)
Para H1 y H2 se propone, en `models/contacto.py`, una restricción de referencia única por compañía y un aviso por nombre repetido. **No se implementó ni se probó en Odoo**; debe validarse en el entorno real antes de integrarse.

## 6. Limitaciones
- Datos sintéticos; la revisión no certifica el comportamiento con datos reales.
- El recorrido se hizo solo con el rol vendedor. No se revisaron los roles `gerente` ni `admin`.
- La revisión de código fue de lectura; las comprobaciones V7 no se ejecutaron.
- Se crearon clientes duplicados durante la prueba de H1; deben eliminarse o archivarse para no alterar la demostración.

## 7. Contribución verificable
Revisión funcional de C01/C02 con las capturas 01–08, ficha de hallazgos H1–H5 con evidencia y recomendaciones, y contraste con el código del addon `mys_erp`.

## 8. Uso de IA y validación humana
| Elemento | Registro |
|---|---|
| Herramienta de IA | Claude (Claude Code): análisis del repositorio, interpretación de capturas y redacción de este borrador |
| Validación humana | El recorrido y las capturas fueron realizados por el autor en el sistema en ejecución; los hallazgos se contrastaron con el código |
| Datos sensibles | No se incluyen claves, `.env` ni datos personales reales |
