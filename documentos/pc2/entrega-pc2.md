# PC2 · Entrega Consolidada del Grupo 7

**Curso:** GE703, Sistemas Integrados Empresariales, 2026-2  
**Empresa:** IMPORTACIONES MYS HERMANOS S.A.C.  
**Versión de Entrega:** PC2 v2.1 (Alineada con consigna vigente y corte a diapositiva 12 de Sesión 6)  
**Fecha de Entrega:** 16/10/2026 · **Fecha de Exposición:** 17/10/2026 (Expositor único, máx. 10 minutos)  
**Enlace al repositorio:** [github.com/jharopr/ERP-SIE](https://github.com/jharopr/ERP-SIE)  
**Documento oficial consolidado Word:** [`GE703_PC2_G7_ENTREGA_CONSOLIDADA_FINAL.docx`](../../GE703_PC2_G7_ENTREGA_CONSOLIDADA_FINAL.docx)

---

## Cuadro Inicial: Integrantes y Aportes Verificables

| Integrante | Responsabilidad Ajustada | Entregable Concreto y Aporte Verificable | Estado de Revisión |
| :--- | :--- | :--- | :--- |
| **Benjamín Francis Arancibia Ynga** | Continuidad de PC1 y delimitación del incremento | Matriz de decisiones que se mantienen o ajustan; justificación del canal presencial y del alcance previo al pedido. Mapa y SIPOC solo como contexto (Sección 1). | Contenido preparado e integrado |
| **Shirley Carrión Oré** | Escenario CRM y contexto del cliente | Cuenta, contacto, canal, fuente, interacción, necesidad, lead, oportunidad, probabilidad, competidores, actividades y cotización con versión, precio, descuento y vigencia (Sección 2). | Contenido completado e integrado |
| **Gabriel Omar Chavez Mendoza** | Decisiones comerciales y frontera conceptual CRM–ERP | Descuento excepcional, disponibilidad o promesa y condición de facturación, con responsables y evidencia; explicación de qué conserva CRM y qué ejecutará ERP (Sección 3). | Contenido completado e integrado |
| **Adrián Antony Mansilla Soto** | Caso normal y excepción prioritaria | Dos casos con decisión, responsable, evidencia esperada, impacto para el cliente y respuesta propuesta. Flujo comercial documentado como apoyo opcional en BPMN D01–D05 (Sección 4). | Contenido preparado e integrado |
| **Jharolym Friendly Paucarcaja Ramos** | Fuentes, límites y consolidación del documento | Fuentes y fechas, supuestos didácticos, vacíos, declaración de IA y continuidad. Verificación de enlaces, versión y coherencia general de la entrega (Sección 5). | Contenido completado e integrado |
| **Ballack Zidane Quintanilla Huamanraime** | Revisión de datos comerciales y evidencias | Comprobación y cuadre de cifras (5 unidades, S/ 400 unitario, base S/ 2,000, 5% descuento vendedor = S/ 1,900, 10% excepción = S/ 1,800), versiones, condiciones y evidencias de los dos casos; registro de observaciones y validación cruzada. | Revisado, auditado y verificado |

---

## 1. Incremento desde PC1

En PC1 se seleccionó conceptualmente **Odoo** como núcleo ERP para clientes, ventas e inventarios, y **UBLHUB** para una futura emisión tributaria electrónica. La documentación histórica de PC1 contemplaba atención presencial y canal WhatsApp manual.

En esta **PC2 v2.1**, se delimita y unifica el caso principal a un **cliente nuevo del público general que visita la tienda física**, analizando su necesidad, seguimiento y oferta comercial antes de comprometer cualquier transacción en el ERP. La frontera evaluable se ajusta estrictamente hasta la **diapositiva 12 de la sesión 6**, excluyendo contratos técnicos de integración, interfaces transaccionales y ejecución del pedido (facturación, despacho o entrega).

### Matriz de Continuidad y Decisiones de Arquitectura

| Decisión PC1 | Tratamiento PC2 v2.1 | Justificación y Efecto Comercial |
| :--- | :--- | :--- |
| **Odoo ERP central** | Se mantiene | Conserva referencias oficiales de catálogo, precios e inventario; sin despliegue verificado en producción. |
| **UBLHUB** | Se mantiene fuera de PC2 | La condición de facturación se explica conceptualmente; no se emiten comprobantes de pago dentro de PC2. |
| **Clientes prioritarios** | Se delimita | Público general NUEVO (persona natural); venta mayorista queda fuera del caso evaluable. |
| **Canal prioritario** | Se delimita | **Atención presencial (tienda física)**; el canal WhatsApp queda como antecedente de PC1. |
| **Capa CRM** | Se incorpora | Cuenta, contacto, fuente comercial, interacción, lead calificado, oportunidad, cotización versionada y seguimiento. |
| **Frontera CRM–ERP** | Se explica conceptualmente | El CRM conserva la intención, interacción y oferta comercial; el ERP comprometerá recursos operativos al confirmar pedidos en incrementos posteriores. |
| **O2C y P2P / Importaciones** | Se mantienen como contexto | Macroprocesos de Semana 5; sustentan el flujo global pero no amplían el alcance evaluado de PC2. |
| **Modelado BPMN comercial** | Apoyo visual | Diagramas D01 a D05 apoyan la explicación del tramo comercial. No se exige un modelo ejecutable. |

### SIPOC del Tramo Comercial Previo al Pedido
* **Proveedores:** Cliente (necesidades y preferencias); Vendedor (registro comercial y asesoría); Dueño (reglas comerciales y autorizaciones); Catálogo/Inventario (referencia disponible).
* **Entradas:** Consulta presencial en local, datos mínimos autorizados, producto y cantidad solicitada, precio de lista referencial y disponibilidad observada.
* **Proceso:** Identificar y calificar lead; preparar cotización versionada; resolver decisiones de descuento y facturación; presentar oferta y registrar respuesta.
* **Salidas:** Cotización aceptada (versión vigente), recotización, seguimiento pendiente o cierre por abandono. **No hay creación de pedido operativo en este incremento.**
* **Destinatarios:** Cliente (recibe condiciones claras de la oferta) y Vendedor (conserva contexto para actividades de seguimiento).

---

## 2. Escenario CRM Previo al Pedido

### Historia Comercial y Contexto del Cliente (Aporte Shirley Carrión)
Una persona natural visita la tienda física de Importaciones MYS Hermanos S.A.C. interesada en adquirir autoradios. Al tratarse de un cliente del público general (consumidor final), el vendedor averigua su necesidad específica: se proyecta el uso en cinco vehículos familiares (sin fines de reventa comercial), requiriendo confirmar compatibilidad técnica con las consolas.

* **Cuenta y Contacto:** En el segmento de consumidor final (persona natural), la cuenta y el contacto coinciden en la misma persona física (`CLI-DEMO-001`). El vendedor busca en el sistema antes de registrar para evitar duplicidad; si no existe, recopila únicamente datos mínimos indispensables autorizados (nombre y medio preferido de comunicación).
* **Canal y Fuente:** Canal presencial (mostrador de tienda física). Fuente: **visita espontánea** (walk-in). No se atribuye a una campaña publicitaria ejecutada (se declara que no aplica campaña activa).
* **Interacción y Necesidad:** Consulta realizada el 16/10/2026 a las 09:45. El cliente solicita cotización por **cinco autoradios** de 7" pantalla táctil con soporte Bluetooth/USB. El vendedor registra la consulta y valida compatibilidad.
* **Lead y Calificación:** Se registra el lead con necesidad concreta, cantidad identificada (5 unidades) y viabilidad de atención en mostrador. Cumple criterios observables para continuar la gestión.
* **Oportunidad y Probabilidad:** El lead califica a oportunidad (`OPP-DEMO-001`) al existir intención firme de compra, capacidad de suministro y una acción de seguimiento asignada al vendedor. La probabilidad asignada es didáctica (estimada en 60% por interés presencial en tienda).
* **Competidores:** Alternativas comerciales no identificadas en la interacción; el vendedor indaga si evalúa otras marcas y registra que no se conocen competidores directos en la consulta (no se inventan marcas).
* **Actividades de Seguimiento:** Presentar cotización formal, absolver consultas de compatibilidad técnica y registrar la respuesta del cliente antes de las 18:00 del mismo día.
* **Cotización:** Oferta formal `COT-DEMO-001 v1`. Precio base unitario didáctico de **S/ 400.00**; subtotal base para 5 unidades: **S/ 2,000.00**. Descuento del vendedor del 5% (**S/ 100.00**); Importe total cotizado: **S/ 1,900.00**. Vigencia académica: 16/10/2026 hasta las 18:00.
* **Consentimiento y Direcciones:** No se requiere dirección de despacho a domicilio, ya que el supuesto didáctico acuerda retiro posterior directamente en tienda física. Consentimiento verbal registrado para contacto telefónico.

---

## 3. Decisiones Comerciales y Frontera Conceptual CRM–ERP

### Decisiones Comerciales y Responsabilidades (Aporte Gabriel Chavez)
El sistema CRM y ERP apoyan el registro, pero la responsabilidad de decidir recae en roles de negocio con evidencia verificable:

1. **Descuento Excepcional:**
   * *Dentro del umbral (≤ 5%):* Autorizado al vendedor de tienda según política comercial didáctica (descuento de S/ 100 sobre base de S/ 2,000, resultando en S/ 1,900). Evidencia: lista de precios y versión emitida de cotización.
   * *Superior al umbral (10% = S/ 200 de descuento):* Facultad exclusiva del **Dueño / Gerencia**. El vendedor registra la solicitud y versión v2 en evaluación, pero no puede confirmarla por sí mismo. Evidencia: solicitud formal, justificación y registro de autorización o rechazo por el dueño.
2. **Disponibilidad o Promesa al Cliente:**
   * El vendedor consulta existencias en el inventario (se observan 8 unidades a las 09:50).
   * *Principio clave:* **Una consulta de stock no equivale a una reserva de inventario ni garantiza entrega futura.** La promesa de disponibilidad se condiciona al stock observado; si fuera insuficiente, el dueño evalúa reposición o entrega parcial, sin inventar fechas de entrega.
3. **Condición de Facturación:**
   * El vendedor recoge la necesidad documental del cliente: se acuerda la emisión de una **Boleta de Venta única** por las 5 unidades al contado (pago íntegro sin crédito).
   * *Principio clave:* Indicar "pago al contado" no resuelve por sí solo la condición de facturación. El responsable administrativo valida los requisitos del comprobante. **La emisión y registro contable de la factura/boleta quedan fuera del alcance de PC2.**

### Frontera Conceptual CRM vs. ERP (Corte hasta diapositiva 12, Sesión 6)

| Dimensión | CRM (Contexto Comercial y Relación) | ERP (Compromiso Operativo y Ejecución) |
| :--- | :--- | :--- |
| **Entidades que gestiona** | Cuenta, contacto, lead, oportunidad, interacciones, versiones de cotización y respuesta del cliente. | Pedido de venta confirmado (`sale.order`), reserva de stock, movimientos de almacén, cobranza y contabilidad. |
| **Propósito de negocio** | Mantener la trazabilidad de la relación comercial, captar la necesidad y emitir ofertas claras y vigentes. | Ejecutar la operación transaccional, comprometer recursos físicos/financieros y garantizar el cumplimiento. |
| **Alcance en PC2** | **Dentro del alcance:** La cotización aceptada se conserva vinculada a la oportunidad en CRM/Ventas. | **Fuera de PC2:** La confirmación del pedido, reserva de stock, facturación electrónica y despacho no se ejecutan. |

---

## 4. Caso de Análisis

### Comparativa: Caso Normal vs. Excepción Prioritaria (Aporte Adrián Mansilla)

| Criterio | Caso Normal (CRM-N01) | Excepción Prioritaria (CRM-E01) |
| :--- | :--- | :--- |
| **Situación** | Cliente nuevo solicita 5 autoradios a S/ 400. Total base S/ 2,000. Descuento del vendedor del 5% (S/ 100), total **S/ 1,900**. Existen 8 unidades observadas. Cotización `v1` vigente. | El mismo cliente solicita 10% de descuento (S/ 200), total **S/ 1,800**, superando la facultad del 5% del vendedor, sin aprobación previa del dueño. |
| **Decisión** | Vendedor aplica el descuento del 5% dentro de su límite autorizado y presenta la cotización v1. | El vendedor **no confirma el descuento de forma anticipada**; eleva la solicitud a Gerencia/Dueño para evaluación y emite versión en consulta. |
| **Responsable Principal** | **Vendedor de tienda física.** | **Dueño de MYS** evalúa y decide; Vendedor comunica y versiona la oferta. |
| **Evidencia Esperada** | Ficha sintética de cliente, lead calificado, oportunidad, cotización `COT-DEMO-001 v1`, consulta de stock y registro de aceptación formal del cliente. | Solicitud de descuento excepcional, motivo comercial, versión v2 generada y registro de autorización o rechazo del dueño. |
| **Impacto para el Cliente** | Oferta clara y transparente con precio, descuento y vigencia definida; cliente acepta dentro del plazo sin demoras. | El cliente conoce que su solicitud está en evaluación gerencial; se evita prometer un beneficio que la empresa no pueda respaldar. |
| **Respuesta Propuesta** | Se registra la aceptación formal de las condiciones de la versión v1. **El caso concluye sin crear pedido operativo ni reservar inventario.** | Se comunica la espera al cliente y se acuerda seguimiento. Si se aprueba, se presenta v2 (S/ 1,800); si se rechaza, se ratifica v1 (S/ 1,900). La oportunidad se mantiene activa. |

*Nota sobre modelos BPMN:* El aporte de Adrián Mansilla incluye los diagramas documentales **BPMN 2.0.2 (D01 a D05)** incorporados en el documento Word final, que estructuran gráficamente la captación de leads, preparación de cotizaciones, autorización de descuentos excepcionales y registro de respuesta del cliente.

---

## 5. Fuentes, Límites y Continuidad

### Fuentes Oficiales y Metodología (Aporte Jharolym Paucarcaja)
* **Fuentes Académicas:** Guía de Rúbrica oficial PC2 v2.1 (16/10/2026); Plantilla oficial PC2 Grupo 7 v2.1; Diapositivas de Sesión 5 y Sesión 6 (límite formal: diapositiva 12).
* **Declaración de Supuestos:** Precios didácticos (S/ 400 unitario), descuento máximo del vendedor (5%), stock observado (8 unidades) y fechas simuladas (16/10/2026) corresponden a supuestos académicos para modelar el proceso y no representan inventario ni políticas contractuales reales de Importaciones MYS Hermanos S.A.C.
* **Uso Responsable de IA:** Se utilizó asistencia de modelos de lenguaje (ChatGPT / Codex) para contraste de rúbrica, redacción estructurada y validación de sintaxis BPMN. La revisión y criterio de negocio corresponden a los integrantes del grupo. No se incluyen datos personales ni credenciales reales en el repositorio.
* **Límites y Trabajo Pendiente:** Queda fuera de PC2 el diseño de contratos técnicos de integración CRM–ERP, esquemas JSON transaccionales, confirmación y ejecución del pedido de venta, reserva de inventario, integración tributaria con UBLHUB, facturación y despacho físico.

---

## 6. Auditoría de Cifras, Datos y Evidencias (Aporte Ballack Quintanilla)

Ballack Quintanilla realizó la comprobación integral de coherencia numérica, documental y comercial en todo el repositorio:

1. **Cuadre Numérico Exacto:**
   * Cantidad solicitada: 5 autoradios.
   * Precio unitario de lista didáctico: S/ 400.00.
   * Subtotal base: $5 \times 400 = \text{S/ } 2,000.00$.
   * Descuento vendedor (5%): $2,000 \times 0.05 = \text{S/ } 100.00 \longrightarrow \text{Total: } \mathbf{\text{S/ } 1,900.00}$ (Caso Normal).
   * Descuento excepcional solicitado (10%): $2,000 \times 0.10 = \text{S/ } 200.00 \longrightarrow \text{Total: } \mathbf{\text{S/ } 1,800.00}$ (Diferencia de S/ 100 vs. normal).
2. **Coherencia de Identificadores y Versiones:**
   * Cliente / Cuenta: `CLI-DEMO-001` (Persona natural, público general, tienda física).
   * Oportunidad: `OPP-DEMO-001`.
   * Cotización Caso Normal: `COT-DEMO-001 v1` (vigente al 16/10/2026 18:00).
   * Cotización Excepción: `COT-DEMO-001 v2` (en evaluación gerencial).
   * Stock observado en inventario: 8 unidades (suficiente para cubrir 5 unidades sin generar reserva).
3. **Alineación con la Consigna del Docente:**
   * Se retiró el contrato técnico CRM–ERP del cuerpo evaluable, delimitando el trabajo a las 5 secciones oficiales de la plantilla v2.1.
   * Se ratificó el esquema de un único expositor (máximo 10 minutos) para la sustentación del 17/10/2026.
