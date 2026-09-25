"use strict";

// MVP de interfaz: todos los datos son ficticios y permanecen en localStorage.
// No existen llamadas HTTP, conexión a Odoo ni emisión a SUNAT.
const STORAGE_KEY = "mys-erp-frontend-demo-v1";
const PRODUCT_IMAGE = "./imagenes/autoradio-demo.png";
const baseProducts = [
  { sku: "DEMO-001", name: "Autoradio multimedia", category: "Audio y multimedia", price: 680, stock: 42, minimum: 12, visual: "image" },
  { sku: "DEMO-002", name: "Cámara de retroceso", category: "Accesorios", price: 165, stock: 8, minimum: 10, visual: "◉" },
  { sku: "DEMO-003", name: "Parlantes coaxiales", category: "Audio y multimedia", price: 240, stock: 26, minimum: 8, visual: "♫" },
];
const baseOrders = [
  { id: "PED-1006", customer: "Cliente demo 06", channel: "Tienda digital", sku: "DEMO-001", qty: 1, status: "Pendiente", invoice: "Sin emitir", date: "2026-09-24" },
  { id: "PED-1005", customer: "Cliente demo 05", channel: "WhatsApp", sku: "DEMO-002", qty: 2, status: "En preparación", invoice: "Borrador", date: "2026-09-24" },
  { id: "PED-1004", customer: "Cliente demo 04", channel: "Tienda digital", sku: "DEMO-003", qty: 1, status: "Completado", invoice: "Simulado", date: "2026-09-23" },
  { id: "PED-1003", customer: "Cliente demo 03", channel: "Mostrador", sku: "DEMO-001", qty: 1, status: "Completado", invoice: "Simulado", date: "2026-09-23" },
  { id: "PED-1002", customer: "Cliente demo 02", channel: "WhatsApp", sku: "DEMO-001", qty: 2, status: "En preparación", invoice: "Borrador", date: "2026-09-22" },
  { id: "PED-1001", customer: "Cliente demo 01", channel: "Tienda digital", sku: "DEMO-002", qty: 1, status: "Completado", invoice: "Simulado", date: "2026-09-22" },
];
const initialState = () => ({ products: structuredClone(baseProducts), orders: structuredClone(baseOrders), nextOrder: 1007 });
function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && Array.isArray(saved.products) && Array.isArray(saved.orders) && Number.isInteger(saved.nextOrder)) return saved;
  } catch (_) { /* El demo funciona aunque el almacenamiento esté deshabilitado. */ }
  return initialState();
}
let state = loadState();
let view = ["resumen", "pedidos", "inventario", "facturacion", "canales"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "resumen";
let query = "";
let filter = "Todos";
let toastTimer;

const viewEl = document.getElementById("view");
const modalRoot = document.getElementById("modal-root");
const toastEl = document.getElementById("toast");
const money = (n) => new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN", maximumFractionDigits: 0 }).format(n);
const safe = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const productFor = (sku) => state.products.find((p) => p.sku === sku);
const orderTotal = (o) => o.qty * (productFor(o.sku)?.price ?? 0);
const dateText = (iso) => new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${iso}T12:00:00`));
function persist() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) { /* Modo sin persistencia. */ } }
function notify(message) { toastEl.textContent = message; toastEl.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3300); }
function demoStrip() { return `<div class="demo-strip"><span class="strip-icon">ⓘ</span><strong>Prototipo visual</strong><span>Los datos son ficticios. Los cambios se guardan solo en este navegador; no hay conexión con Odoo ni SUNAT.</span></div>`; }
function header(eyebrow, title, subtitle, actions = "") { return `<div class="page-header"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${subtitle}</p></div>${actions ? `<div class="header-actions">${actions}</div>` : ""}</div>`; }
function badge(label) { const colors = { "Pendiente": "orange", "En preparación": "blue", "Completado": "green", "Sin emitir": "gray", "Borrador": "orange", "Simulado": "green", "Bajo stock": "red", "Disponible": "green" }; return `<span class="badge ${colors[label] ?? "gray"}">${safe(label)}</span>`; }
function kpi(label, value, glyph, note) { return `<div class="kpi-card"><div class="kpi-top"><span>${label}</span><span class="kpi-glyph">${glyph}</span></div><div class="kpi-value">${value}</div><div class="kpi-foot">${note}</div></div>`; }
function orderRows(orders, compact = false) {
  if (!orders.length) return `<tr><td colspan="${compact ? 5 : 7}"><div class="empty"><strong>Sin resultados</strong>Prueba otra búsqueda o filtro.</div></td></tr>`;
  return orders.map((o) => {
    const p = productFor(o.sku);
    return `<tr><td><span class="table-main">${safe(o.id)}</span><span class="table-sub">${dateText(o.date)}</span></td><td><span class="table-main">${safe(o.customer)}</span><span class="table-sub">${safe(o.channel)}</span></td><td>${safe(p?.name ?? o.sku)}<span class="table-sub">${o.qty} unidad${o.qty === 1 ? "" : "es"}</span></td>${compact ? "" : `<td>${money(orderTotal(o))}</td>`}<td>${badge(o.status)}</td>${compact ? "" : `<td>${badge(o.invoice)}</td>`}<td><button class="text-button" type="button" data-action="detail" data-id="${safe(o.id)}">Ver detalle →</button></td></tr>`;
  }).join("");
}
function renderSummary() {
  const pending = state.orders.filter((o) => o.status === "Pendiente").length;
  const inProgress = state.orders.filter((o) => o.status === "En preparación").length;
  const low = state.products.filter((p) => p.stock < p.minimum).length;
  const total = state.orders.reduce((sum, o) => sum + orderTotal(o), 0);
  const mainProduct = productFor("DEMO-001");
  const bars = [42, 67, 50, 76, 58, 84, 62].map((height, i) => `<div class="bar-col"><div class="bar ${i === 5 ? "strong" : ""}" style="height:${height}%"></div><span>${["L", "M", "M", "J", "V", "S", "D"][i]}</span></div>`).join("");
  const recent = state.orders.slice(0, 4);
  return `${header("Panel de control", "Resumen de operaciones", "Vista inicial inspirada en el flujo comercial propuesto para Odoo.", `<button class="button secondary" type="button" data-view="pedidos">Ver pedidos</button><button class="button primary" type="button" data-action="new-order">＋ Nuevo pedido demo</button>`)}${demoStrip()}
    <section class="kpi-grid" aria-label="Indicadores simulados">${kpi("Pedidos registrados", state.orders.length, "▤", "Total de la sesión de demostración")}${kpi("Por atender", pending + inProgress, "◷", `${pending} pendiente${pending === 1 ? "" : "s"} · ${inProgress} en preparación`)}${kpi("Valor referencial", money(total), "↗", "No representa ventas reales")}${kpi("Alertas de stock", low, "▦", "Productos bajo mínimo demo")}</section>
    <div class="dashboard-grid"><section class="panel"><div class="panel-head"><div><h2>Actividad comercial</h2><p>Gráfico ilustrativo · últimos 7 días</p></div><span class="badge gray">Simulado</span></div><div class="panel-body"><div class="chart" aria-label="Barras ilustrativas sin datos reales">${bars}</div><div class="chart-legend"><span class="legend-dot"></span>Actividad de ejemplo para validar la interfaz</div></div></section><section class="panel"><div class="panel-head"><div><h2>Producto de demostración</h2><p>Catálogo ficticio para el flujo de pedidos</p></div><button class="panel-link" type="button" data-view="inventario">Inventario →</button></div><div class="product-feature"><img class="product-visual" src="${PRODUCT_IMAGE}" alt="Render de un autoradio genérico de demostración" /><div class="product-meta"><div><strong>${safe(mainProduct.name)}</strong><small>${safe(mainProduct.sku)} · ${mainProduct.stock} unidades disponibles</small></div><span class="product-price">${money(mainProduct.price)}</span></div><div class="stock-mini"><span style="width:${Math.min(100, mainProduct.stock * 2)}%"></span></div><small style="font-size:10px;color:#9a919c">Nivel de stock ilustrativo</small></div></section></div>
    <div class="subgrid"><section class="panel"><div class="panel-head"><div><h2>Pedidos recientes</h2><p>Datos ficticios del navegador</p></div><button class="panel-link" type="button" data-view="pedidos">Ver todos →</button></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Pedido</th><th>Cliente / canal</th><th>Producto</th><th>Estado</th><th></th></tr></thead><tbody>${orderRows(recent, true)}</tbody></table></div></section><section class="panel"><div class="panel-head"><div><h2>Flujo del MVP</h2><p>Alcance de la primera liberación propuesta</p></div></div><div class="steps"><div class="step"><span class="step-number">1</span><div><strong>Capturar pedido</strong><p>Un canal digital y atención comercial.</p></div></div><div class="step"><span class="step-number">2</span><div><strong>Consultar inventario</strong><p>Mostrar disponibilidad y alerta de stock.</p></div></div><div class="step"><span class="step-number">3</span><div><strong>Preparar comprobante</strong><p>Solo vista de borrador, sin emisión tributaria.</p></div></div></div></section></div>`;
}
function renderOrders() {
  const filters = ["Todos", "Pendiente", "En preparación", "Completado"];
  const list = state.orders.filter((o) => (filter === "Todos" || o.status === filter) && `${o.id} ${o.customer} ${o.channel} ${productFor(o.sku)?.name ?? ""}`.toLowerCase().includes(query.toLowerCase()));
  return `${header("Ventas", "Pedidos", "Sigue cada pedido de prueba desde el canal hasta su preparación.", `<button class="button primary" type="button" data-action="new-order">＋ Nuevo pedido demo</button>`)}${demoStrip()}<div class="toolbar"><label class="search-wrap"><span class="sr-only">Buscar pedidos</span><input id="search-input" type="search" placeholder="Buscar pedido, cliente o canal" value="${safe(query)}" /></label><div class="filter-row">${filters.map((f) => `<button class="filter-chip ${filter === f ? "is-active" : ""}" type="button" data-filter="${safe(f)}">${safe(f)}</button>`).join("")}</div></div><section class="panel"><div class="panel-head"><div><h2>Listado de pedidos</h2><p>${list.length} de ${state.orders.length} registros simulados</p></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Pedido</th><th>Cliente / canal</th><th>Producto</th><th>Total</th><th>Estado</th><th>Comprobante</th><th></th></tr></thead><tbody>${orderRows(list)}</tbody></table></div></section>`;
}
function renderInventory() {
  return `${header("Almacén", "Inventario", "Catálogo y disponibilidad ficticios para validar el flujo comercial.", `<button class="button secondary" type="button" data-action="stock-info">¿Cómo funciona la demo?</button>`)}${demoStrip()}<div class="inventory-grid">${state.products.map((p) => `<article class="inventory-card">${p.visual === "image" ? `<img class="inventory-img" src="${PRODUCT_IMAGE}" alt="Render de ${safe(p.name)} de demostración" />` : `<div class="inventory-placeholder" aria-hidden="true">${p.visual}</div>`}<div class="inventory-top"><div><strong>${safe(p.name)}</strong><small>${safe(p.sku)} · ${safe(p.category)}</small></div>${badge(p.stock < p.minimum ? "Bajo stock" : "Disponible")}</div><p>Artículo de ejemplo. El catálogo y sus existencias no provienen de la empresa.</p><div class="inventory-bottom"><div><strong>${p.stock}</strong><small> unidades · mínimo ${p.minimum}</small></div><span class="product-price">${money(p.price)}</span></div></article>`).join("")}</div><div class="note-box">Al crear un pedido demo, el stock se descuenta únicamente en el navegador. Usa “Restablecer demo” para volver a los valores iniciales.</div>`;
}
function renderInvoices() {
  const rows = state.orders.filter((o) => `${o.id} ${o.customer} ${o.invoice}`.toLowerCase().includes(query.toLowerCase()));
  return `${header("Contabilidad", "Facturación", "Previsualización del estado de comprobantes; no emite documentos reales.")}${demoStrip()}<div class="toolbar"><label class="search-wrap"><span class="sr-only">Buscar comprobantes</span><input id="search-input" type="search" placeholder="Buscar pedido o cliente" value="${safe(query)}" /></label></div><section class="panel"><div class="panel-head"><div><h2>Comprobantes de demostración</h2><p>El estado “Simulado” solo representa una pantalla del flujo.</p></div><span class="badge gray">Sin SUNAT</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Referencia</th><th>Cliente demo</th><th>Tipo propuesto</th><th>Importe</th><th>Estado visual</th><th></th></tr></thead><tbody>${rows.length ? rows.map((o) => `<tr><td><span class="table-main">${safe(o.id)}</span><span class="table-sub">${dateText(o.date)}</span></td><td>${safe(o.customer)}</td><td>Boleta / factura por definir</td><td>${money(orderTotal(o))}</td><td>${badge(o.invoice)}</td><td><button class="text-button" type="button" data-action="detail" data-id="${safe(o.id)}">Ver detalle →</button></td></tr>`).join("") : `<tr><td colspan="6"><div class="empty"><strong>Sin resultados</strong>Prueba otra búsqueda.</div></td></tr>`}</tbody></table></div></section><div class="note-box">La emisión electrónica, validación SUNAT, numeración real, PLE y reglas tributarias quedan fuera de este frontend. Se deberán probar con Odoo y su localización/partner cuando exista backend y autorización.</div>`;
}
function renderChannels() {
  return `${header("Integraciones", "Canales de venta", "Mapa conceptual de la relación entre canal, atención y módulos del ERP.")}${demoStrip()}<div class="info-grid"><div class="info-card"><span class="mini-icon">◇</span><strong>Canal digital piloto</strong><p>Un canal por definir con la empresa. La tienda digital de esta demo es un ejemplo visual.</p></div><div class="info-card"><span class="mini-icon">▤</span><strong>Ventas y atención</strong><p>Un pedido con identificador externo, estado visible y respuesta al cliente.</p></div><div class="info-card"><span class="mini-icon">▦</span><strong>Inventario y comprobante</strong><p>Disponibilidad y borrador de facturación vinculados al mismo pedido.</p></div></div><section class="panel"><div class="panel-head"><div><h2>Recorrido propuesto</h2><p>La interfaz técnica se define después de evaluar API o conector real.</p></div></div><div class="flow-strip"><div class="flow-node"><strong>Canal digital</strong><small>Origen del pedido</small></div><span class="flow-arrow">→</span><div class="flow-node"><strong>Ventas Odoo</strong><small>Atención y estado</small></div><span class="flow-arrow">→</span><div class="flow-node"><strong>Inventario Odoo</strong><small>Disponibilidad</small></div><span class="flow-arrow">→</span><div class="flow-node"><strong>Facturación Odoo</strong><small>Comprobante por validar</small></div></div></section><div class="note-box">Esta pantalla no sincroniza datos con un canal ni con Odoo. El documento de arquitectura ERP base del repositorio enumera las interfaces, controles y preguntas pendientes.</div>`;
}
const views = { resumen: renderSummary, pedidos: renderOrders, inventario: renderInventory, facturacion: renderInvoices, canales: renderChannels };
const names = { resumen: "Resumen", pedidos: "Pedidos", inventario: "Inventario", facturacion: "Facturación", canales: "Canales" };
function render() {
  viewEl.innerHTML = views[view]();
  document.getElementById("breadcrumb").textContent = `Operaciones / ${names[view]}`;
  document.getElementById("nav-pending").textContent = state.orders.filter((o) => o.status !== "Completado").length;
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("is-active", button.dataset.view === view));
}
function navigate(to) { if (!views[to]) return; view = to; query = ""; filter = "Todos"; location.hash = to; render(); document.querySelector(".sidebar").classList.remove("open"); window.scrollTo(0, 0); }
function closeModal() { modalRoot.innerHTML = ""; }
function showModal(title, subtitle, body, footer = "") { modalRoot.innerHTML = `<div class="modal-backdrop"><section class="modal" role="dialog" aria-modal="true" aria-label="${safe(title)}"><div class="modal-head"><div><h2>${safe(title)}</h2><p>${safe(subtitle)}</p></div><button class="close-button" type="button" data-action="close-modal" aria-label="Cerrar">×</button></div><div class="modal-body">${body}</div><div class="modal-foot">${footer || `<button class="button secondary" type="button" data-action="close-modal">Cerrar</button>`}</div></section></div>`; modalRoot.querySelector(".modal input, .modal select, .close-button")?.focus(); }
function newOrderModal() {
  showModal("Nuevo pedido de demostración", "Se guardará solo en este navegador.", `<form id="order-form" class="form-grid"><label class="field full"><span>Cliente ficticio</span><input name="customer" maxlength="55" required placeholder="Ej. Cliente demo 07" autocomplete="off" /></label><label class="field"><span>Canal</span><select name="channel"><option>Tienda digital</option><option>WhatsApp</option><option>Mostrador</option></select></label><label class="field"><span>Producto</span><select name="sku">${state.products.map((p) => `<option value="${safe(p.sku)}">${safe(p.name)} · ${p.stock} disp.</option>`).join("")}</select></label><label class="field"><span>Cantidad</span><input name="qty" type="number" min="1" max="99" value="1" required /></label><div class="field"><span>Importante</span><small style="color:#968c99;line-height:1.5">No ingreses datos personales reales. No se genera un comprobante válido.</small></div></form>`, `<button class="button secondary" type="button" data-action="close-modal">Cancelar</button><button class="button primary" type="submit" form="order-form">Crear pedido demo</button>`);
}
function detailModal(id) {
  const o = state.orders.find((item) => item.id === id); if (!o) return;
  const p = productFor(o.sku);
  const body = `<div class="detail-list"><div class="detail-item"><small>Cliente</small><strong>${safe(o.customer)}</strong></div><div class="detail-item"><small>Canal</small><strong>${safe(o.channel)}</strong></div><div class="detail-item"><small>Producto</small><strong>${safe(p?.name ?? o.sku)}</strong></div><div class="detail-item"><small>Cantidad</small><strong>${o.qty}</strong></div><div class="detail-item"><small>Total referencial</small><strong>${money(orderTotal(o))}</strong></div><div class="detail-item"><small>Comprobante visual</small>${badge(o.invoice)}</div></div><div class="note-box">Acciones locales de demostración. No cambian Odoo, inventario real ni SUNAT.</div>`;
  const buttons = `<button class="button secondary" type="button" data-action="close-modal">Cerrar</button>${o.status === "Pendiente" ? `<button class="button primary" type="button" data-action="prepare-order" data-id="${safe(o.id)}">Marcar en preparación</button>` : ""}${o.status === "En preparación" ? `<button class="button primary" type="button" data-action="complete-order" data-id="${safe(o.id)}">Marcar completado</button>` : ""}${o.invoice === "Sin emitir" ? `<button class="button secondary" type="button" data-action="draft-invoice" data-id="${safe(o.id)}">Crear borrador visual</button>` : ""}`;
  showModal(o.id, `${dateText(o.date)} · ${o.status}`, body, buttons);
}
function submitOrder(form) {
  const values = new FormData(form); const customer = String(values.get("customer") ?? "").trim(); const sku = String(values.get("sku") ?? ""); const qty = Number(values.get("qty")); const p = productFor(sku);
  if (customer.length < 3 || !p || !Number.isInteger(qty) || qty < 1 || qty > p.stock) { notify("Revisa el cliente y la cantidad disponible."); return; }
  const order = { id: `PED-${state.nextOrder++}`, customer, channel: String(values.get("channel")), sku, qty, status: "Pendiente", invoice: "Sin emitir", date: new Date().toISOString().slice(0, 10) };
  p.stock -= qty; state.orders.unshift(order); persist(); closeModal(); navigate("pedidos"); notify(`${order.id} creado en modo demostración.`);
}
document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-view], [data-action], [data-filter]"); if (!target) { if (event.target.classList?.contains("modal-backdrop")) closeModal(); return; }
  if (target.dataset.view) { navigate(target.dataset.view); return; }
  if (target.dataset.filter) { filter = target.dataset.filter; render(); return; }
  const action = target.dataset.action;
  if (action === "new-order") newOrderModal();
  if (action === "close-modal") closeModal();
  if (action === "detail") detailModal(target.dataset.id);
  if (action === "stock-info") showModal("Inventario de demostración", "Sin sincronización con almacenes reales.", `<p style="font-size:12px;line-height:1.6;color:#746b77">Los tres artículos, precios y cantidades son ficticios. Crear un pedido reduce el stock local para ensayar estados visuales. Para probar una integración real se requiere confirmar el catálogo y configurar Odoo en una etapa posterior.</p>`);
  if (["prepare-order", "complete-order", "draft-invoice"].includes(action)) {
    const o = state.orders.find((item) => item.id === target.dataset.id); if (!o) return;
    if (action === "prepare-order") o.status = "En preparación";
    if (action === "complete-order") o.status = "Completado";
    if (action === "draft-invoice") o.invoice = "Borrador";
    persist(); closeModal(); render(); notify("Estado visual actualizado en este navegador.");
  }
});
document.addEventListener("submit", (event) => { if (event.target.id === "order-form") { event.preventDefault(); submitOrder(event.target); } });
document.addEventListener("input", (event) => { if (event.target.id === "search-input") { const start = event.target.selectionStart; query = event.target.value; render(); const next = document.getElementById("search-input"); next?.focus(); next?.setSelectionRange(start, start); } });
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeModal(); });
document.getElementById("menu-toggle").addEventListener("click", () => document.querySelector(".sidebar").classList.toggle("open"));
document.getElementById("reset-demo").addEventListener("click", () => { state = initialState(); persist(); closeModal(); navigate("resumen"); notify("Datos de demostración restablecidos."); });
window.addEventListener("hashchange", () => { const next = location.hash.slice(1); if (views[next] && next !== view) navigate(next); });
document.getElementById("today-label").textContent = new Intl.DateTimeFormat("es-PE", { day: "numeric", month: "long", year: "numeric" }).format(new Date());
render();
