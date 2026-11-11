"""Genera n8n/workflows/W1, W2 y W3 (JSON importable, SIN credenciales ni claves).

    python scripts/generar_workflows.py

El system prompt se toma de n8n/prompts/system_prompt_agente.md (fuente única).
Los nodos referencian credenciales por nombre e id fijo; scripts/importar_n8n.* las
crea desde .env, o el docente las crea a mano con esos mismos nombres (README).
"""

from __future__ import annotations

import sys

import json
from pathlib import Path
import re
import uuid

# Consolas de Windows (cp1252) no imprimen «✓»: se fuerza UTF-8 sin abortar.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "n8n" / "workflows"
COMPUERTA = "http://compuerta:8000"
# Valores por defecto; scripts/importar_n8n.py los reemplaza con N8N_URL_PUBLICA, CORREO_DUENO y CORREO_REMITENTE de .env.
N8N_PUBLICO = "http://localhost:5678"
CORREO_DUENO = "dueno@mys-demo.local"
CORREO_REMITENTE = "agente-sie@mys-demo.local"
AGENT_VERSION = "w1-1.1"

IDS = {"W1": "agSIEw1Agente001", "W2": "agSIEw2Escalam01", "W3": "agSIEw3Determ001"}
CRED = {
    "ventas": {"id": "cmpVentasAgSIE01", "name": "Compuerta VENTAS"},
    "gerencia": {"id": "cmpGerenciaSIE01", "name": "Compuerta GERENCIA"},
    "gemini": {"id": "geminiAgenteSIE1", "name": "Gemini (Agente SIE)"},
    "smtp": {"id": "smtpCorreoSIE001", "name": "Correo SIE (SMTP)"},
}
WEBHOOKS = {"chat": "6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01", "dueno": "6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b02",
            "w3": "6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b03"}


def prompt():
    texto = (RAIZ / "n8n" / "prompts" / "system_prompt_agente.md").read_text(encoding="utf-8")
    version = re.search(r"prompt_version:\s*(\S+)", texto).group(1)
    return re.sub(r"^<!--.*?-->\s*", "", texto, flags=re.S).strip(), version


def nodo(nombre, tipo, version, posicion, parametros, **extra):
    return {"parameters": parametros, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"agente-sie/{nombre}")), "name": nombre, "type": tipo,
            "typeVersion": version, "position": posicion, **extra}


def ai(nombre_destino, tipo):
    return {tipo: [[{"node": nombre_destino, "type": tipo, "index": 0}]]}


def main_(*destinos):
    return {"main": [[{"node": d, "type": "main", "index": 0} for d in destinos]]}


def cabeceras(herramienta, prompt_version, tipo_actor="AGENTE"):
    valores = [{"name": "X-Actor-Type", "value": tipo_actor}]
    if tipo_actor == "AGENTE":
        valores += [{"name": "X-Agent-Tool", "value": herramienta}, {"name": "X-Agent-Version", "value": AGENT_VERSION},
                    {"name": "X-Prompt-Version", "value": prompt_version}]
    return {"parameters": valores}


def herramienta_http(nombre, descripcion, metodo, url, posicion, prompt_version, cuerpo=None):
    p = {"toolDescription": descripcion, "method": metodo, "url": url,
         "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
         "sendHeaders": True, "headerParameters": cabeceras(nombre, prompt_version),
         "options": {"response": {"response": {"neverError": True}}}}
    if cuerpo is not None:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": cuerpo})
    return nodo(nombre, "n8n-nodes-base.httpRequestTool", 4.2, posicion, p,
                credentials={"httpHeaderAuth": CRED["ventas"]})


def ia(nombre, descripcion, tipo="string"):
    assert "'" not in descripcion
    return f"$fromAI('{nombre}', '{descripcion}', '{tipo}')"


def w1():
    sistema, pv = prompt()
    agente = "Agente SIE"
    i03 = ("={\n"
           '  "contract_version": "1.0",\n'
           '  "company_id": "MYS-DEMO",\n'
           f'  "request_id": "{{{{ {ia("request_id", "ID de solicitud dado por el vendedor, p. ej. SOL-PC3-N01")} }}}}",\n'
           f'  "correlation_id": "{{{{ {ia("correlation_id", "ID de correlación, p. ej. COR-PC3-001")} }}}}",\n'
           f'  "opportunity_id": "{{{{ {ia("opportunity_id", "Oportunidad OPP-…")} }}}}",\n'
           f'  "customer_id": "{{{{ {ia("customer_id", "Cliente CLI-…")} }}}}",\n'
           f'  "quotation_id": "{{{{ {ia("quotation_id", "Cotización COT-…")} }}}}",\n'
           f'  "quotation_version": {{{{ {ia("quotation_version", "Versión de la cotización (entero)", "number")} }}}},\n'
           f'  "acceptance_id": "{{{{ {ia("acceptance_id", "Aceptación ACE-…")} }}}}"\n'
           "}")
    y = 520
    herramientas = [
        herramienta_http("consultar_cliente", "Estado del cliente (activo, identidad revisada, segmento). Sin datos personales.",
                         "GET", f"={COMPUERTA}/clientes/{{{{ {ia('customer_id', 'Código del cliente, p. ej. CLI-DEMO-001')} }}}}",
                         [0, y], pv),
        herramienta_http("consultar_cotizacion", "Líneas, total calculado por Odoo, vigencia, estado, versión vigente, oportunidad y aceptaciones de una versión de cotización.",
                         "GET", f"={COMPUERTA}/cotizaciones/{{{{ {ia('quotation_id', 'Cotización, p. ej. COT-DEMO-001')} }}}}/{{{{ {ia('version', 'Versión (entero)', 'number')} }}}}",
                         [180, y], pv),
        herramienta_http("consultar_disponibilidad", "Físico, reservado y disponible (físico − reservado) de un SKU en TIENDA-DEMO. Un 503 significa que no se pudo verificar, NO que no haya stock.",
                         "GET", f"={COMPUERTA}/disponibilidad/{{{{ {ia('sku', 'SKU, p. ej. RAD-10X')} }}}}", [360, y], pv),
        herramienta_http("enviar_solicitud_i03", "Envía la solicitud I03 (9 referencias) a la compuerta CRM–ERP v1.0 y devuelve la respuesta tipificada y las señales REP. No crea pedidos.",
                         "POST", f"={COMPUERTA}/solicitudes", [540, y], pv, i03),
        herramienta_http("consultar_solicitud", "Respuesta guardada de una solicitud (SOL-…).",
                         "GET", f"={COMPUERTA}/solicitudes/{{{{ {ia('request_id', 'Solicitud SOL-…')} }}}}", [720, y], pv),
        herramienta_http("reanudar_solicitud", "Reanuda una solicitud PENDIENTE cuando el administrador confirma que Odoo volvió.",
                         "POST", f"={COMPUERTA}/solicitudes/{{{{ {ia('request_id', 'Solicitud PENDIENTE SOL-…')} }}}}/reanudar", [900, y], pv),
        herramienta_http("ver_bitacora", "Eventos de la bitácora de una correlación (COR-…), en orden, con actor_type.",
                         "GET", f"={COMPUERTA}/bitacora?correlation_id={{{{ {ia('correlation_id', 'Correlación COR-…')} }}}}", [1080, y], pv),
        herramienta_http("consultar_escalamiento", "Estado de un escalamiento ESC-…: esperando, decidido (y qué decidió el dueño) o sin decisión tras 10 minutos. Única prueba válida de una decisión del dueño.",
                         "GET", f"={COMPUERTA}/escalamientos/{{{{ {ia('escalation_id', 'Escalamiento ESC-…')} }}}}", [1260, y], pv),
    ]
    escalar = nodo("escalar_al_dueno", "@n8n/n8n-nodes-langchain.toolWorkflow", 2, [1440, y], {
        "name": "escalar_al_dueno",
        "description": "Escala al dueño una excepción (tipo DESCUENTO para DESCUENTO_SIN_APROBACION, REPOSICION para DISPONIBILIDAD_PARCIAL). Registra el escalamiento y AVISA AL DUEÑO POR CORREO con botones de decisión. Devuelve el ESC y si el correo salió. No aprueba nada.",
        "workflowId": {"__rl": True, "value": IDS["W2"], "mode": "id"},
        "workflowInputs": {
            "mappingMode": "defineBelow",
            "value": {"tipo": f"={{{{ {ia('tipo', 'DESCUENTO o REPOSICION')} }}}}",
                      "request_id": f"={{{{ {ia('request_id', 'Solicitud SOL-… que originó la excepción')} }}}}",
                      "resumen": f"={{{{ {ia('resumen', 'Resumen breve de la excepción, sin datos personales')} }}}}"},
            "matchingColumns": [],
            "schema": [{"id": c, "displayName": c, "required": True, "defaultMatch": False, "display": True,
                        "canBeUsedToMatch": True, "type": "string", "removed": False} for c in ("tipo", "request_id", "resumen")],
            "attemptToConvertTypes": False, "convertFieldsToString": False}})
    nodos = [
        nodo("Chat del vendedor", "@n8n/n8n-nodes-langchain.chatTrigger", 1.3, [0, 0], {
            "public": True, "mode": "hostedChat",
            "initialMessages": "Hola, soy el Agente SIE (datos de demostración). Indícame cliente, cotización, versión, aceptación, SOL y COR.",
            # «streaming»: la respuesta aparece mientras el modelo la escribe, no al final.
            "options": {"title": "Agente SIE · MYS (demo)", "subtitle": "Acompaña al ERP; no confirma pedidos.",
                        "inputPlaceholder": "Ej.: CLI-DEMO-001 aceptó COT-DEMO-001 v1 (ACE-PC3-001)…",
                        "responseMode": "streaming"}},
             webhookId=WEBHOOKS["chat"]),
        nodo(agente, "@n8n/n8n-nodes-langchain.agent", 3.1, [400, 0],
             {"promptType": "auto", "text": "={{ $json.chatInput }}",
              "options": {"systemMessage": sistema, "maxIterations": 10, "enableStreaming": True}}),
        nodo("Modelo Gemini", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1, [120, 260],
             {"modelName": "models/gemini-3.5-flash-lite", "options": {"temperature": 0.1}},
             credentials={"googlePalmApi": CRED["gemini"]}),
        nodo("Memoria (10 mensajes)", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, [300, 260],
             {"contextWindowLength": 10}),
        *herramientas, escalar,
    ]
    conexiones = {"Chat del vendedor": main_(agente), "Modelo Gemini": ai(agente, "ai_languageModel"),
                  "Memoria (10 mensajes)": ai(agente, "ai_memory")}
    for h in [*herramientas, escalar]:
        conexiones[h["name"]] = ai(agente, "ai_tool")
    return flujo("W1", "W1 · Agente SIE (chat del vendedor)", nodos, conexiones)


def w2():
    nodos = [
        nodo("Desde el agente", "n8n-nodes-base.executeWorkflowTrigger", 1.1, [0, 0],
             {"workflowInputs": {"values": [{"name": "tipo"}, {"name": "request_id"}, {"name": "resumen"}]}}),
        nodo("Registrar escalamiento", "n8n-nodes-base.httpRequest", 4.2, [240, 0], {
            "method": "POST", "url": f"{COMPUERTA}/escalamientos", "authentication": "genericCredentialType",
            "genericAuthType": "httpHeaderAuth", "sendHeaders": True, "headerParameters": cabeceras("escalar_al_dueno", "p-1.0"),
            "sendBody": True, "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ tipo: $json.tipo, request_id: $json.request_id, resumen: $json.resumen }) }}",
            "options": {"response": {"response": {"neverError": True}}}},
             credentials={"httpHeaderAuth": CRED["ventas"]}),
        nodo("Preparar aviso", "n8n-nodes-base.code", 2, [480, 0], {"jsCode": (
            "const e = $input.first().json;\n"
            "const pedido = $('Desde el agente').first().json;\n"
            "if (!e.escalation_id) {\n"
            "  return [{ json: { avisar: false, estado: 'NO_ESCALADO', motivo: e.detail || e, siguiente_paso: 'Revisar la solicitud; no se notificó al dueño.' } }];\n"
            "}\n"
            "const etiquetas = { APROBADA: 'Aprobar', RECHAZADA: 'Rechazar', OFRECER_PARCIAL: 'Ofrecer entrega parcial',\n"
            "  EVALUAR_REPOSICION: 'Evaluar reposición', DESCARTAR: 'Descartar' };\n"
            "const opciones = e.tipo === 'DESCUENTO' ? ['APROBADA', 'RECHAZADA'] : ['OFRECER_PARCIAL', 'EVALUAR_REPOSICION', 'DESCARTAR'];\n"
            f"const base = `{N8N_PUBLICO}/form/decision-dueno?escalation_id=${{e.escalation_id}}`;\n"
            "// Un enlace por decisión: el formulario abre con ESC y decisión ya marcados; el dueño confirma con un clic.\n"
            "// No se registra con solo abrir el enlace: los lectores de correo abren enlaces automáticamente.\n"
            "const enlaces = Object.fromEntries(opciones.map(o => [o, `${base}&decision=${o}`]));\n"
            "const esc = s => String(s ?? '—').replace(/[&<>\"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;' }[c]));\n"
            "const que = e.tipo === 'DESCUENTO' ? 'Descuento mayor al 5 % (requiere su aprobación)' : 'Falta stock (decida cómo atender)';\n"
            "const botones = opciones.map((o, i) => `<a href=\"${enlaces[o]}\" style=\"display:inline-block;margin:4px 6px 4px 0;padding:10px 16px;border-radius:6px;text-decoration:none;color:#fff;background:${i === 0 ? '#1a7f37' : (o === 'RECHAZADA' || o === 'DESCARTAR' ? '#b42318' : '#475467')}\">${etiquetas[o]}</a>`).join('');\n"
            "const fila = (k, v) => `<tr><td style=\"padding:4px 12px 4px 0;color:#475467\">${k}</td><td style=\"padding:4px 0\"><b>${esc(v)}</b></td></tr>`;\n"
            "const html = `<div style=\"font-family:Arial,sans-serif;font-size:14px;color:#101828;max-width:560px\">\n"
            "<h2 style=\"margin:0 0 8px\">${que}</h2>\n"
            "<p style=\"margin:0 0 12px\">${esc(pedido.resumen)}</p>\n"
            "<table>${fila('Cotización', `${e.quotation_id} v${e.quotation_version}`)}${fila('Total verificado en Odoo', `S/ ${e.total}`)}\n"
            "${fila('Escalamiento', e.escalation_id)}${fila('Solicitud', e.request_id)}${e.signal_id ? fila('Señal de reposición', e.signal_id) : ''}\n"
            "${fila('Responder antes de', e.plazo_hasta)}</table>\n"
            "<p style=\"margin:16px 0 4px\">Elija una opción (se abre una confirmación de un clic):</p>${botones}\n"
            "<p style=\"margin:16px 0 0;color:#667085;font-size:12px\">Agente SIE · datos de demostración. Ninguna opción crea pedidos ni reservas en Odoo. Si no responde en 10 minutos, la oportunidad queda en seguimiento.</p></div>`;\n"
            "return [{ json: {\n"
            "  avisar: true, estado: 'ESPERANDO_DECISION_DEL_DUENO', escalation_id: e.escalation_id, tipo: e.tipo,\n"
            "  destinatario: e.destinatario, signal_id: e.signal_id, aprobacion_aplicaria_a_version: e.version_aprobacion,\n"
            "  total_verificado: e.total, plazo_hasta: e.plazo_hasta, enlaces, html,\n"
            "  asunto: `[MYS] ${e.tipo === 'DESCUENTO' ? 'Aprobar descuento' : 'Falta stock'}: ${e.quotation_id} v${e.quotation_version} · S/ ${e.total} (${e.escalation_id})`\n"
            "} }];")}),
        nodo("¿Avisar al dueño?", "n8n-nodes-base.if", 2.2, [700, 0], {
            "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                           "conditions": [{"id": "avisar", "leftValue": "={{ $json.avisar }}", "rightValue": True,
                                           "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                           "combinator": "and"}, "options": {}}),
        nodo("Correo al dueño", "n8n-nodes-base.emailSend", 2.1, [920, -100], {
            "fromEmail": f"Agente SIE MYS <{CORREO_REMITENTE}>", "toEmail": CORREO_DUENO,
            "subject": "={{ $json.asunto }}", "emailFormat": "html", "html": "={{ $json.html }}",
            "options": {"appendAttribution": False}},
             credentials={"smtp": CRED["smtp"]}, onError="continueRegularOutput"),
        nodo("Respuesta al agente", "n8n-nodes-base.code", 2, [1140, 0], {"jsCode": (
            "const a = $('Preparar aviso').first().json;\n"
            "if (!a.avisar) { const { avisar, ...resto } = a; return [{ json: resto }]; }\n"
            "let correo = { enviado: false, detalle: 'no se intentó' };\n"
            "try {\n"
            "  const r = $('Correo al dueño').first().json;\n"
            "  correo = r.error ? { enviado: false, detalle: String(r.error.message || r.error).slice(0, 160) } : { enviado: true };\n"
            "} catch (err) {}\n"
            "const salida = {\n"
            "  estado: a.estado, escalation_id: a.escalation_id, tipo: a.tipo, signal_id: a.signal_id,\n"
            "  aprobacion_aplicaria_a_version: a.aprobacion_aplicaria_a_version, total_verificado: a.total_verificado, plazo_hasta: a.plazo_hasta,\n"
            "  aviso_al_dueno: correo.enviado ? 'Correo enviado automáticamente al dueño con los botones de decisión.'\n"
            "    : `No se pudo enviar el correo (${correo.detalle}). Reenvíe al dueño estos enlaces.`,\n"
            "  nota: 'Si no hay respuesta en 10 minutos: sin decisión, la oportunidad queda en seguimiento.'\n"
            "};\n"
            "if (!correo.enviado) salida.enlaces_para_el_dueno = a.enlaces;\n"
            "return [{ json: salida }];")}),
        nodo("Formulario del dueño", "n8n-nodes-base.formTrigger", 2.2, [0, 300], {
            "formTitle": "Decisión del dueño · Agente SIE (demo)",
            "formDescription": "Solo el dueño (GER-DEMO-01) usa este formulario. Revise la decisión ya marcada y pulse «Confirmar decisión». El motivo es opcional. Ninguna opción crea pedidos ni reservas.",
            "formFields": {"values": [
                {"fieldLabel": "escalation_id", "placeholder": "ESC-PC3-001", "requiredField": True},
                {"fieldLabel": "decision", "fieldType": "dropdown", "requiredField": True,
                 "fieldOptions": {"values": [{"option": o} for o in
                                             ("APROBADA", "RECHAZADA", "OFRECER_PARCIAL", "EVALUAR_REPOSICION", "DESCARTAR")]}},
                {"fieldLabel": "motivo", "fieldType": "textarea", "requiredField": False,
                 "placeholder": "Motivo breve, sin datos personales"}]},
            "options": {"path": "decision-dueno", "buttonLabel": "Confirmar decisión"}}, webhookId=WEBHOOKS["dueno"]),
        nodo("Registrar decisión (GERENCIA)", "n8n-nodes-base.httpRequest", 4.2, [240, 300], {
            "method": "POST", "url": f"={COMPUERTA}/escalamientos/{{{{ $json.escalation_id.trim() }}}}/decision",
            "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
            "sendBody": True, "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ decision: $json.decision, motivo: ($json.motivo || '').trim().length >= 3 ? $json.motivo : 'Decisión del dueño sin comentario' }) }}",
            "options": {"response": {"response": {"neverError": True}}}},
             credentials={"httpHeaderAuth": CRED["gerencia"]}),
        nodo("Confirmación al dueño", "n8n-nodes-base.form", 1, [480, 300], {
            "operation": "completion",
            "completionTitle": "={{ $json.resultado ? 'Decisión registrada' : 'No se registró la decisión' }}",
            "completionMessage": "={{ $json.resultado ? `${$json.escalation_id}: ${$json.resultado.status || $json.resultado.decision}. Queda en la bitácora; no se creó pedido ni reserva.` : JSON.stringify($json.detail || $json) }}",
            "options": {}}),
    ]
    conexiones = {"Desde el agente": main_("Registrar escalamiento"), "Registrar escalamiento": main_("Preparar aviso"),
                  "Preparar aviso": main_("¿Avisar al dueño?"),
                  "¿Avisar al dueño?": {"main": [[{"node": "Correo al dueño", "type": "main", "index": 0}],
                                                [{"node": "Respuesta al agente", "type": "main", "index": 0}]]},
                  "Correo al dueño": main_("Respuesta al agente"),
                  "Formulario del dueño": main_("Registrar decisión (GERENCIA)"),
                  "Registrar decisión (GERENCIA)": main_("Confirmación al dueño")}
    return flujo("W2", "W2 · Escalamiento al dueño", nodos, conexiones)


def w3():
    casos = json.loads((RAIZ / "datos_prueba" / "casos_pc3.json").read_text(encoding="utf-8"))["casos"]
    solicitudes = {c["id"]: c["solicitud"] for c in casos if "solicitud" in c}
    opciones = [*solicitudes, "PC3-F01 · reanudar"]
    codigo = (
        f"const SOLICITUDES = {json.dumps(solicitudes, ensure_ascii=False)};\n"
        "const caso = $input.first().json.caso;\n"
        "if (caso === 'PC3-F01 · reanudar') {\n"
        f"  return [{{ json: {{ caso, url: '{COMPUERTA}/solicitudes/SOL-PC3-F01/reanudar', body: {{}} }} }}];\n"
        "}\n"
        f"return [{{ json: {{ caso, url: '{COMPUERTA}/solicitudes', body: SOLICITUDES[caso] }} }}];")
    formato = (
        "const r = $input.first().json;\n"
        "const caso = $('Preparar solicitud').first().json.caso;\n"
        "if (!r.respuesta) { return [{ json: { titulo: `${caso}: sin respuesta tipificada`, texto: JSON.stringify(r) } }]; }\n"
        "const x = r.respuesta;\n"
        "const rep = (r.senales_reposicion || []).map(s => `${s.signal_id} (faltan ${s.faltante} de ${s.sku})`).join(', ') || '—';\n"
        "const cond = (x.conditions || []).map(c => `${c.sku}: pedido ${c.requested_quantity}, disponible ${c.available_quantity}, fecha prometida: ninguna`).join('; ') || '—';\n"
        "const texto = [\n"
        "  `Resultado: ${x.status} / ${x.code}`, `Motivo: ${x.message}`, `Quién actúa: ${x.responsible_role}`,\n"
        "  `Siguiente paso: ${x.required_action}`, `Total: ${x.total ?? '—'} ${x.currency ?? ''}`,\n"
        "  `Condiciones: ${cond}`, `order_id: ${x.order_id} (no se creó pedido)`,\n"
        "  `IDs: ${x.request_id} · ${x.correlation_id} · REP: ${rep}`].join('\\n');\n"
        "return [{ json: { titulo: `${caso} · modo determinista (sin IA)`, texto, respuesta: x } }];")
    nodos = [
        nodo("Formulario de casos", "n8n-nodes-base.formTrigger", 2.2, [0, 0], {
            "formTitle": "Modo determinista · Agente SIE (respaldo sin IA)",
            "formDescription": "Ejecuta los casos PC3 directamente contra la compuerta, sin modelo de lenguaje.",
            "formFields": {"values": [{"fieldLabel": "caso", "fieldType": "dropdown", "requiredField": True,
                                       "fieldOptions": {"values": [{"option": o} for o in opciones]}}]},
            "options": {"path": "modo-determinista"}}, webhookId=WEBHOOKS["w3"]),
        nodo("Preparar solicitud", "n8n-nodes-base.code", 2, [220, 0], {"jsCode": codigo}),
        nodo("Compuerta (VENTAS)", "n8n-nodes-base.httpRequest", 4.2, [440, 0], {
            "method": "POST", "url": "={{ $json.url }}", "authentication": "genericCredentialType",
            "genericAuthType": "httpHeaderAuth", "sendHeaders": True,
            "headerParameters": cabeceras("w3", "-", tipo_actor="HUMANO"),
            "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.body) }}",
            "options": {"response": {"response": {"neverError": True}}}},
             credentials={"httpHeaderAuth": CRED["ventas"]}),
        nodo("Formatear respuesta", "n8n-nodes-base.code", 2, [660, 0], {"jsCode": formato}),
        nodo("Mostrar resultado", "n8n-nodes-base.form", 1, [880, 0], {
            "operation": "completion", "completionTitle": "={{ $json.titulo }}",
            "completionMessage": "={{ $json.texto }}", "options": {}}),
    ]
    conexiones = {"Formulario de casos": main_("Preparar solicitud"), "Preparar solicitud": main_("Compuerta (VENTAS)"),
                  "Compuerta (VENTAS)": main_("Formatear respuesta"), "Formatear respuesta": main_("Mostrar resultado")}
    return flujo("W3", "W3 · Modo determinista (respaldo sin IA)", nodos, conexiones)


def flujo(clave, nombre, nodos, conexiones):
    return {"id": IDS[clave], "name": nombre, "nodes": nodos, "connections": conexiones, "active": False,
            "settings": {"executionOrder": "v1", "timezone": "America/Lima", "saveManualExecutions": True},
            "pinData": {}, "tags": [], "meta": {"generado_por": "scripts/generar_workflows.py", "datos": "sintéticos"}}


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    for archivo, datos in (("W1_agente_sie.json", w1()), ("W2_escalamiento_dueno.json", w2()),
                           ("W3_modo_determinista.json", w3())):
        texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
        assert "Bearer " not in texto and "apiKey" not in texto, "Un workflow no debe contener secretos"
        (SALIDA / archivo).write_text(texto, encoding="utf-8")
        print(f"escrito n8n/workflows/{archivo} ({len(datos['nodes'])} nodos)")


if __name__ == "__main__":
    main()
