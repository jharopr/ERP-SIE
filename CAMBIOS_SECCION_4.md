# Registro de Cambios Técnicos en la Sección 4 (Gabriel Chavez Mendoza)

Este documento registra de manera exhaustiva y línea por línea las modificaciones implementadas en la Sección 4 y en la celda correspondiente de la tabla de integrantes de `GE703_EP_G7_CONSOLIDADO_COMPLETO.md`, conforme al rol de ingeniero de integración del grupo G7 para el Examen Parcial de GE703 (24/10/2026, IMPORTACIONES MYS HERMANOS S.A.C.).

---

## 1. Modificaciones Línea por Línea (Qué decía | Qué dice | Por qué)

1. **Tabla de Integrantes (Fila 3, Celda de Gabriel Chavez):**  
   *Qué decía:* `|3|Chavez Mendoza, Gabriel Omar|Especificación Formal del Contrato CRM-ERP (Punto 4). Definición técnica del Contrato v1.0, especificación de 7 interfaces I01-I07, payload I03 con 9 campos de referencia inmutables, 12 reglas deterministas R01-R12, matriz de 15 códigos de respuesta, idempotencia SHA-256 y simulación compartida de 112 comprobaciones.|`  
   *Qué dice:* `|3|Chavez Mendoza, Gabriel Omar|Especificación Formal del Contrato CRM–ERP (Punto 4). Definición técnica del Contrato v1.0, especificación de 8 interfaces canónicas I01–I08, payload I03 con 9 campos de referencia estrictos, 12 reglas deterministas R01–R12 (R08 previa a R09/R10), matriz completa de 15 códigos de respuesta tipificados, idempotencia por huella SHA-256 en transacción atómica (UNIQUE condicionado a ACEPTADA) y validación de 112 comprobaciones compartidas (37/37/38) con order_id estrictamente nulo.|`  
   *Por qué:* Alinea la celda individual con la incorporación de la interfaz I08, la precedencia de R08, la unicidad condicionada a ACEPTADA y el desglose verificado de comprobaciones (37/37/38 = 112).

2. **Bloque inicial de la Sección 4:**  
   *Qué decía:* Bloque residual de plantilla `Fila para la Matriz Inicial de Integrantes y Contribuciones (Página 1 del Word Grupal) ... Texto exacto que se inserta en la tabla general de integrantes del informe grupal: ...`.  
   *Qué dice:* Bloque completamente eliminado; la sección inicia directamente con el encabezado `### **4. Especificación Técnica y Gobernanza del Contrato CRM–ERP**` seguido de `#### **4.1 Decisión que Defiende Gabriel y Justificación del Problema**`.  
   *Por qué:* Eliminación de texto auxiliar redundante en cumplimiento estricto de la instrucción de corrección E.

3. **Subsección 4.1 (Decisión que Defiende Gabriel y Delimitación de Alcance):**  
   *Qué decía:* Afirmaba que el contrato constituía una barrera absoluta que neutraliza fraudes y erradica errores operativos, empleando adjetivación promocional.  
   *Qué dice:* Plantea formalmente que el contrato técnico delimita la frontera SoE/SoR, culminando en una respuesta tipificada I08 con `order_id = null` en todos los casos, sin reserva de existencias, sin confirmación de venta, sin despacho físico, sin facturación electrónica ni descomposición de IGV en este corte.  
   *Por qué:* Delimitación rigurosa del alcance académico al corte del examen parcial y eliminación de lenguaje promocional ("riguroso", "neutraliza", "erradica").

4. **Subsección 4.2 y Tabla 4.1 (Frontera SoE vs. SoR y Propiedad de la Cotización):**  
   *Qué decía:* Señalaba de manera ambigua al CRM como sistema de registro de la cotización preliminar o la describía como entidad compartida entre CRM y ERP.  
   *Qué dice:* Establece categóricamente que Ventas/ERP (C03) es el System of Record (SoR) exclusivo de la Cotización oficial y sus versiones; el CRM (C01) únicamente conserva Lead, Oportunidad comercial y la referencia/vínculo a la cotización oficial.  
   *Por qué:* Cumplimiento de la Decisión de Diseño 1 y unificación semántica con la arquitectura de componentes C01–C08 y el payload I03.

5. **Subsección 4.3 y Tabla 4.2 (Payload I03 y Supresión de Tokens de Aprobación):**  
   *Qué decía:* Mencionaba o dejaba abierta la posibilidad de que el payload I03 transportara tokens de aprobación del dueño (`owner_approval_token` o `owner_token`).  
   *Qué dice:* Fija exactamente 9 referencias canónicas inmutables en I03 (`contract_version`, `company_id`, `request_id`, `correlation_id`, `opportunity_id`, `customer_id`, `quotation_id`, `quotation_version`, `acceptance_id`), prohibiendo campos adicionales (`additionalProperties: false`). Se suprime cualquier mención a `owner_approval_token` en el payload, aclarando que la aprobación del dueño se consulta en Autorizaciones (C06) vía I06.  
   *Por qué:* Cumplimiento estricto de la Decisión de Diseño 3 y principio de desconfianza de entrada (datos confiables en servidor).

6. **Subsección 4.4 y Tabla 4.3 (Separación de Interfaces I04 e I08, y llamada a C02):**  
   *Qué decía:* La interfaz I04 se utilizaba con doble sentido (lectura de snapshot en Ventas y retorno de respuesta al CRM), y se omitía la llamada de C04 a C02 para validar identidad.  
   *Qué dice:* Mantiene I04 exclusivamente para la lectura del snapshot comercial en Ventas (C03); crea formalmente la interfaz I08 para la respuesta tipificada desde C04 hacia el CRM (C01); e incorpora la interfaz I02 para la consulta de validación de cliente/contacto en Contactos (C02).  
   *Por qué:* Cumplimiento de las Decisiones de Diseño 4 y 5, completando la matriz con 8 interfaces estructuradas (I01–I08).

7. **Subsección 4.5 y Tabla 4.4 (Justificación Técnica de la Precedencia de R08):**  
   *Qué decía:* Justificaba evaluar la regla R08 antes de R09/R10 apelando a "eficiencia computacional, evitar fuga de stock hacia competidores y prevenir saturación de la base de datos".  
   *Qué dice:* Justifica que el sistema no debe prometer disponibilidad de inventario sobre un precio que carece de autorización comercial de Gerencia, y que el rechazo informa de inmediato la causa comercial real y asigna a Gerencia la responsabilidad de resolver la solicitud antes de consultar almacén.  
   *Por qué:* Cumplimiento de la corrección F, reemplazando argumentos informales o de seguridad adversarial por criterios de coherencia operativa y gobernanza empresarial.

8. **Subsección 4.6 y Tabla 4.5 (Matriz Completa de Estados y 15 Códigos de Respuesta):**  
   *Qué decía:* La matriz de respuestas contenía únicamente 8 códigos tipificados.  
   *Qué dice:* Expande y documenta la totalidad de los 15 códigos de respuesta tipificados implementados en el simulador (`VALIDADA`, `CONTRATO_INVALIDO`, `NO_AUTORIZADO`, `IDEMPOTENCIA_CONFLICTO`, `COTIZACION_YA_EVALUADA`, `DATOS_INCONSISTENTES`, `CLIENTE_NO_VALIDADO`, `VERSION_OBSOLETA`, `COTIZACION_NO_ENVIADA`, `COTIZACION_VENCIDA`, `ACEPTACION_INVALIDA`, `PRECIO_INVALIDO`, `DESCUENTO_SIN_APROBACION`, `DEPENDENCIA_NO_DISPONIBLE`, `DISPONIBILIDAD_PARCIAL`), unificando `VERSION_OBSOLETA` y `COTIZACION_VENCIDA` bajo la verificación de la cotización en R06.  
   *Por qué:* Cumplimiento de la corrección A y sincronización 1:1 con el contrato JSON Schema y `pruebas/pc2/simulador.py`.

9. **Subsección 4.6 (Reemplazo del término "Microservicio"):**  
   *Qué decía:* Se refería a la consulta de existencias como invocación al "microservicio de inventario".  
   *Qué dice:* Sustituye el término por "módulo de Inventario (C05)".  
   *Por qué:* Cumplimiento de la corrección H; el alcance académico y la plataforma propuesta corresponden a módulos funcionales y no a una malla de microservicios.

10. **Subsección 4.7 (Huella SHA-256 e Inmutabilidad de Bitácora):**  
    *Qué decía:* Afirmaba que el hash SHA-256 constituía una "firma digital que garantiza no repudio legal" y que la bitácora era "inmutable".  
    *Qué dice:* Precisa que el resumen SHA-256 es una huella de integridad técnica e idempotencia para control transaccional local, aclarando que no es una firma digital bajo la Ley 27269 (requeriría PKI con certificados acreditados). Para la bitácora señala: "append-only por diseño; la inmutabilidad real requiere permisos de base de datos a nivel de motor, por validar en PC3".  
    *Por qué:* Corrección de rigor conceptual y precisión técnico-legal conforme a la corrección G.

11. **Subsección 4.7 (Frontera Transaccional y Reintentos con UNIQUE Condicionado):**  
    *Qué decía:* Verificación de idempotencia fuera de transacción y restricción UNIQUE incondicional sobre `(quotation_id, quotation_version)` que impedía cualquier reintento tras un rechazo previo.  
    *Qué dice:* La verificación de huella ocurre dentro de la transacción atómica (`BEGIN IMMEDIATE`). La restricción UNIQUE sobre `(quotation_id, quotation_version)` aplica exclusivamente si ya existe una decisión previa en estado `ACEPTADA` (emitiendo `COTIZACION_YA_EVALUADA`). Decisiones `RECHAZADA`, `PENDIENTE` y `PROMESA_CONDICIONADA` no consumen la versión y admiten reevaluarse con un `request_id` nuevo tras subsanar la causa.  
    *Por qué:* Cumplimiento de las Decisiones de Diseño 2 y 6.

12. **Subsección 4.7 y 4.12 (Aclaración del Entorno Tecnológico y Reporte del Simulador):**  
    *Qué decía:* Hacía referencia a "Odoo productivo", despliegues en Docker aislados e implementaciones en producción.  
    *Qué dice:* Declara con transparencia que las pruebas corresponden a una simulación local en SQLite con fixtures preconfiguradas, y que el diseño relacional para PostgreSQL y servicios REST es una especificación propuesta, sin Odoo desplegado en producción. Se reporta el comportamiento del simulador local y la propuesta de ajuste.  
    *Por qué:* Cumplimiento de la corrección I y honestidad metodológica.

13. **Subsección 4.8 (Calibración con Caso Andina Manufactura - Sesión 7):**  
    *Qué decía:* Dedicaba múltiples páginas a sostener que el contrato era "neutral al segmento" y que compartía "reglas idénticas" con el caso Andina B2B.  
    *Qué dice:* Reducido a un único párrafo técnico; señala que el parcial cubre ventas de mostrador minorista al contado (Sesión 6) y que el Contrato v1.0 no modela crédito comercial ni entregas diferidas (Sesión 7). Explica que adaptar el contrato a Andina exigiría reglas adicionales (`R_CREDITO`, `R_CONDICION_PAGO`, `R_DESPACHO_PARCIAL`).  
    *Por qué:* Cumplimiento de la corrección D y sinceramiento de los límites teóricos del parcial.

14. **Subsección 4.9 y Tabla 4.6 (Conteo Certificado de Comprobaciones):**  
    *Qué decía:* En gráficos previos se consignaban conteos discordantes (38/36/38).  
    *Qué dice:* Registra los valores exactos certificados por la ejecución de `pruebas/ep-benjamin/generar_evidencias.py`: EP-N01 con 37 comprobaciones, EP-S01 con 37 comprobaciones y EP-E01 con 38 comprobaciones, totalizando 112 comprobaciones aprobadas.  
    *Por qué:* Cumplimiento de la corrección B y concordancia empírica con el repositorio.

15. **Subsección 4.10 y Tabla 4.7 (Reformulación del Indicador de Eficiencia de Consulta a Stock):**  
    *Qué decía:* Indicador "Eficiencia de Consulta a Stock" formulado con narrativa de seguridad ("evitar fuga de stock hacia competidores").  
    *Qué dice:* Reformulado como "Rechazos R01–R08 que no llegaron a consultar inventario", midiendo objetivamente la contención de consultas innecesarias sin conjeturas adversariales.  
    *Por qué:* Cumplimiento de la corrección F.

16. **Subsección 4.14 (Sustitución de Autocalificación 20/20):**  
    *Qué decía:* Tabla de autocalificación pretendiendo 20/20 puntos bajo afirmaciones de perfección no fundamentadas.  
    *Qué dice:* Tabla técnica de 7 filas "Qué defiendo en este examen parcial, con qué evidencia técnica se demuestra y qué límite reconozco objetivamente".  
    *Por qué:* Cumplimiento de la corrección C, adoptando una postura de defensa profesional y autocrítica de ingeniería.

17. **Subsección 4.15 (Pies de Figura y Autoría Responsable de IA):**  
    *Qué decía:* Pies de figura rotulados como "Elaboración propia", y declaración general afirmando que los seis integrantes validaron toda la entrega.  
    *Qué dice:* Pies de figura actualizados a "Elaboración propia asistida por IA", y se registra honestamente: "revisión humana de Gabriel Chavez: por completar".  
    *Por qué:* Cumplimiento de la corrección J y transparencia académica sobre el estado de revisión.

18. **Subsección 4.15.1 (Nueva Subsección: Guion Oral y Banco de Preguntas del Vocal):**  
    *Qué decía:* No existía un guion oral calibrado ni un banco de preguntas probables del vocal dentro de la sección 4.  
    *Qué dice:* Incorpora un guion hablado de exactamente 405 palabras (minutos 06:00 a 09:00) centrado en tres ideas clave (I03 con 9 referencias, R08 previa a R10, y 3 casos con 112 comprobaciones y límite order_id nulo), y añade 3 preguntas probables de vocal respondidas en 2-3 frases (reintento tras aprobación de Gerencia, hash SHA-256 vs firma digital, y order_id estrictamente nulo).  
    *Por qué:* Cumplimiento de la corrección K.

19. **Figuras de la Sección 4 (Figuras 4.1 a 4.6):**  
    *Qué decía:* Títulos internos de 4.2 y 4.3 intercambiados; Figura 4.1 sin flecha C04→C02 ni I08; Figura 4.3 con texto recortado en R08; Figura 4.6 con conteos desalineados (38/36/38).  
    *Qué dice:* Regeneradas en alta resolución (300 DPI) con numeración y referencias unificadas: Figura 4.1 con SoR en C03, flecha a C02 e interfaz I08; Figura 4.2 con secuencia I02/I08; Figura 4.3 con salidas legibles R01–R07; Figura 4.4 con UNIQUE condicionado a ACEPTADA; Figura 4.5 con límites conceptuales frente a Andina; y Figura 4.6 con 37/37/38 comprobaciones (112 en total).  
    *Por qué:* Cumplimiento integral del pliego de figuras de la sección 4.

---

## 2. Reporte Técnico de Discrepancia en el Simulador y Propuesta Mínima de Código

### A. Situación Observada en `pruebas/pc2/simulador.py`
En el archivo `pruebas/pc2/simulador.py`, la tabla SQLite `requests` (líneas 67–74) define una restricción incondicional:
```sql
UNIQUE (company_id, quotation_id, quotation_version)
```
Adicionalmente, en la línea 139 se ejecuta:
```python
duplicate = self.db.execute(
    "SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=?",
    (request["company_id"], request["quotation_id"], request["quotation_version"])
).fetchone()
if duplicate:
    self._event(request, actor, "I03", "CONFLICTO", "COTIZACION_YA_EVALUADA")
    return self._response(request, "COTIZACION_YA_EVALUADA", "La versión ya tiene una solicitud.", "Consultar la solicitud original autorizada.")
```
Este comportamiento del simulador bloquea como `COTIZACION_YA_EVALUADA` cualquier solicitud posterior para esa cotización y versión, incluso si la evaluación original fue `RECHAZADA` (como en EP-E01 por descuento sin aprobación).

### B. Especificación del Diseño Arquitectónico (Decisión de Diseño 2)
El diseño arquitectónico formal establece que una cotización rechazada, pendiente o con promesa condicionada **no consume la versión comercial**. Por consiguiente, si el dueño registra posteriormente la aprobación del descuento en C06, el vendedor puede reintentar la evaluación con un `request_id` nuevo. El bloqueo `COTIZACION_YA_EVALUADA` debe activarse **únicamente si ya existe una decisión previa en estado `ACEPTADA`**.

### C. Propuesta de Cambio Mínimo de Código (Diff)
Sin alterar la ejecución de los tres casos evaluados (que utilizan un único envío por caso), se propone el siguiente cambio mínimo en `pruebas/pc2/simulador.py`:

```diff
--- a/pruebas/pc2/simulador.py
+++ b/pruebas/pc2/simulador.py
@@ -70,7 +70,6 @@ class TransitionSimulator:
                 payload_hash TEXT NOT NULL, quotation_id TEXT NOT NULL,
                 quotation_version INTEGER NOT NULL, opportunity_id TEXT NOT NULL,
                 response_json TEXT NOT NULL,
-                PRIMARY KEY (company_id, request_id),
-                UNIQUE (company_id, quotation_id, quotation_version)
+                PRIMARY KEY (company_id, request_id)
             );
@@ -139,3 +138,4 @@ class TransitionSimulator:
         else:
             duplicate = self.db.execute(
-                "SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=?",
+                "SELECT request_id FROM requests WHERE company_id=? AND quotation_id=? AND quotation_version=? AND json_extract(response_json, '$.status') = 'ACEPTADA'",
                 (request["company_id"], request["quotation_id"], request["quotation_version"])
             ).fetchone()
```

Para la base de datos de producción propuesta en PostgreSQL, la restricción se implementa mediante un índice parcial:
```sql
CREATE UNIQUE INDEX idx_requests_accepted_version 
ON requests (company_id, quotation_id, quotation_version) 
WHERE status = 'ACEPTADA';
```
Esto permite reevaluaciones legítimas ante excepciones comerciales subsanadas sin vulnerar la idempotencia de las solicitudes aceptadas.
