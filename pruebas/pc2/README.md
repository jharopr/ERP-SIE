# Prueba reproducible del contrato CRM–ERP · PC2

**Estado:** simulación local ejecutable, sin Odoo ni conexiones externas. **Revisión humana propuesta:** Adrian (casos) y Ballack (evidencia). [Contrato probado](../../arquitectura/contratos/crm-erp-v1.md).

## Ejecutar desde la raíz del repositorio

Requiere Python 3.10 o superior; solo biblioteca estándar. No requiere Docker, Odoo, una cuenta ni credenciales.

```powershell
python pruebas/pc2/generar_evidencias.py
```

Ejecuta las pruebas, verifica las cuatro decisiones y actualiza [ejecucion.json](evidencias/ejecucion.json), [unittest.txt](evidencias/unittest.txt) y un JSON por caso. Un fallo termina con código distinto de cero. La hora real de ejecución está en el manifiesto; `business_time` en fixtures es el reloj comercial fijo del escenario. Los hashes permiten comprobar qué archivos se ejecutaron. La evidencia fue producida por Codex, no por un integrante al que se le atribuya una validación todavía pendiente.

Para consultar un mensaje individual:

```powershell
python pruebas/pc2/simulador.py pruebas/pc2/fixtures/solicitud-normal.json
python pruebas/pc2/simulador.py pruebas/pc2/fixtures/solicitud-excepcion.json
```

Para conservar la decisión y verificar un reintento en otro proceso, ejecutar dos veces:

```powershell
python pruebas/pc2/simulador.py pruebas/pc2/fixtures/solicitud-normal.json --database pruebas/pc2/demo.sqlite3
```

La base local está ignorada por Git. No borrar una evidencia anterior sin conservar su versión; si se cambia una regla, volver a generar evidencia y revisar el diff. El prototipo `producto/frontend` es de PC1 y no ejecuta estas reglas.

## PC2-N01 · Escenario normal obligatorio

**Precondiciones:** sesión `VEN-DEMO-01`, compañía `MYS-DEMO`, oportunidad asignada, cliente revisado, cotización `COT-DEMO-001/v1` enviada y vigente, aceptación `ACE-DEMO-001` coincidente; cinco unidades a S/400.00, descuento 5 %, total S/1,900.00 y ocho disponibles.

1. Cargar [maestros sintéticos](fixtures/maestros.json) y [solicitud normal](fixtures/solicitud-normal.json).
2. Invocar I03 con identidad de Ventas fuera del payload.
3. Verificar lectura de snapshot I04, política I06, disponibilidad I05 y decisión I07.
4. Comparar salida con `ACEPTADA`, `VALIDADA`, total `1900.00`, `order_id: null` y una solicitud persistida.
5. Comprobar que maestros, stock y cotización no cambiaron; consultar la evidencia y sus eventos.

**Resultado obtenido:** véase [PC2-N01.json](evidencias/PC2-N01.json), generado por ejecución. El siguiente paso corresponde a Ventas; la confirmación operativa queda pendiente del incremento posterior.

## PC2-E01 · Excepción prioritaria obligatoria

**Precondiciones:** misma sesión/oportunidad del caso, alternativa `COT-DEMO-002/v1`, cinco unidades a S/400.00, descuento 10 %, total S/1,800.00, aceptación de esa versión y sin aprobación registrada por Gerencia.

1. Cargar la fixture de [solicitud de excepción](fixtures/solicitud-excepcion.json).
2. Invocar I03; C04 lee el snapshot y solicita verificación a C06 por I06.
3. Comparar salida con `RECHAZADA`, `DESCUENTO_SIN_APROBACION`, responsable `GERENCIA` y `order_id: null`.
4. Verificar que no se realizó una consulta/promesa de stock posterior al rechazo ni se alteraron maestros.
5. Escalar a Gerencia. Si se autoriza después, Ventas prepara nueva versión, aceptación y solicitud; no modifica la decisión rechazada.

**Resultado obtenido:** [PC2-E01.json](evidencias/PC2-E01.json), con eventos y acción. Este resultado no acredita una aprobación real de la empresa.

## Casos complementarios y regresión

| Caso / prueba | Condición | Resultado esperado y evidencia |
| --- | --- | --- |
| PC2-P01 | Disponible 3 de 5 | PROMESA_CONDICIONADA, requiere aceptación; sin fecha inventada → [resultado](evidencias/PC2-P01.json) |
| PC2-T01 | Consulta de stock no disponible | PENDIENTE, recuperar y reanudar misma solicitud → [resultado](evidencias/PC2-T01.json) |
| Repetición y reinicio | Mismo JSON, misma clave y base persistente | Misma decisión, una sola solicitud |
| Conflicto y doble clave | Cambiar payload o enviar otra clave para misma versión | Rechazo explícito; original intacto |
| Permisos y privacidad | Otro rol, compañía u oportunidad | Bloqueo incluso al consultar/repetir un resultado existente |
| Descuento y aceptación | Autoaprobación, versión/importe distinto o aprobación vencida | Rechazo; aprobación válida por gerencia permite evaluar |
| Recuperación | Servicio vuelve tras pendiente | Submit consulta estado existente; `resume` revalida datos actuales |
| Concurrencia y caída | Reintentos paralelos o excepción antes de commit | Una decisión; rollback sin solicitud/eventos parciales |

La suite está en [test_contrato.py](test_contrato.py). Los JSON Schema son contratos de intercambio; el simulador aplica sus restricciones de entrada con biblioteca estándar. También se puede ejecutar la validación formal con la dependencia opcional instalada solo en una carpeta local ignorada por Git:

```powershell
python -m pip install --target pruebas/pc2/.schema-runtime -r pruebas/pc2/requirements-schema.txt
python pruebas/pc2/validar_esquemas.py
```

Comprueba ambos schemas con Draft 2020-12, las solicitudes/resultados, un corpus de mensajes válidos/inválidos frente al validador del simulador y respuestas deliberadamente incoherentes. La ejecución obtenida está en [esquemas.json](evidencias/esquemas.json), con versión de herramienta y hashes; no es requisito para ejecutar el simulador.

## Límites y cierre humano

SQLite acredita solo persistencia local, atomicidad y concurrencia de la simulación. No acredita ORM, ACL, bloqueo de confirmación, inventario concurrente, despliegue, API ni configuración real de Odoo. Falta ejecutar esos mismos casos en una instalación y revisar los resultados con el equipo y la empresa. La rúbrica permite revisar la prueba y su evidencia sin publicar información sensible; no se presenta una captura ficticia del ERP como evidencia.
