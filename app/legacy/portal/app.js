'use strict';
const $ = (id) => document.getElementById(id);
const state = {page:'inicio', role:'VENTAS', products:[], summary:null};
const money = (n) => n == null ? 'Sin lectura' : new Intl.NumberFormat('es-PE',{style:'currency',currency:'PEN'}).format(Number(n));
const escape = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {inicio:'Vista general',catalogo:'Catálogo',casos:'Evaluación comercial',decisiones:'Decisiones del dueño',bitacora:'Trazabilidad'};
async function api(path, options={}) {
  const response = await fetch('/api/panel/'+path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...options.headers}});
  const body = await response.json();
  if (response.status===401 && path!=='sesion') { $('login').hidden=false;$('workspace').hidden=true; }
  if (!response.ok) throw Error(typeof body.detail==='string'?body.detail:'No se pudo completar la operación.');
  return body;
}
function notify(message){$('notice').textContent=message;$('notice').hidden=!message;}
function badge(status){return `<span class="pill ${status==='RECHAZADA'?'danger':status==='PROMESA_CONDICIONADA'||status==='PENDIENTE'?'warning':''}">${escape(status.replaceAll('_',' '))}</span>`;}
async function summary(){
  state.summary=await api('resumen');state.role=state.summary.rol;
  $('stat-requests').textContent=state.summary.solicitudes.length;$('stat-signals').textContent=state.summary.senales.length;
  $('stat-odoo').textContent=state.summary.odoo.disponible?'Conectado':'Sin conexión';
  $('odoo-version').textContent=state.summary.odoo.server_version?'Odoo '+state.summary.odoo.server_version:'Comprueba la conexión con el ERP';
  $('role-label').textContent=state.role==='GERENCIA'?'Dueño / Gerencia':'Asesor de ventas';
  const links=state.summary.enlaces||{};
  $('link-odoo').href=links.odoo||`http://${location.hostname}:8069`;
  $('link-agente').href=(links.n8n||`http://${location.hostname}:5678`)+'/webhook/6f1c2a10-5b8e-4c1d-9a51-0c3e9f2a7b01/chat';
}
async function navigate(page){
  state.page=page;notify('');document.querySelectorAll('.page').forEach(e=>e.hidden=e.id!=='page-'+page);
  document.querySelectorAll('[data-page]').forEach(e=>e.classList.toggle('active',e.dataset.page===page));
  $('breadcrumb').textContent=labels[page];
  try {if(page==='inicio')await summary();if(page==='catalogo')await catalog();if(page==='casos')await cases();if(page==='decisiones')await decisions();}
  catch(error){notify(error.message);}
}
async function catalog(){
  $('catalog-source').textContent='Consultando precio y disponibilidad en Odoo…';
  try {
    const data=await api('catalogo');state.products=data.productos;
    const selected=$('category').value;
    $('category').innerHTML='<option value="">Todas las categorías</option>'+[...new Set(state.products.map(p=>p.categoria))].map(c=>`<option>${escape(c)}</option>`).join('');
    $('category').value=selected;renderProducts();
    $('catalog-source').textContent='Fuente: Odoo · Consulta '+new Date(data.observado_en).toLocaleString('es-PE')+' · Disponible = físico − reservado';
  } catch(error){state.products=[];renderProducts();$('catalog-source').textContent='No hay lectura confiable de precio o inventario.';throw error;}
}
function renderProducts(){
  const term=$('search').value.toLocaleLowerCase('es');const category=$('category').value;
  const products=state.products.filter(p=>(!category||p.categoria===category)&&[p.nombre,p.sku,p.codigo_original,p.categoria].some(v=>v.toLocaleLowerCase('es').includes(term)));
  $('catalog-count').textContent=products.length+' referencias';
  $('products').innerHTML=products.map(p=>`<tr><td><strong>${escape(p.nombre)}</strong><small>${escape(p.sku)}${p.codigo_original!==p.sku?' · Código original: '+escape(p.codigo_original):''}</small></td><td>${escape(p.categoria)}<small>${escape(p.subcategoria)}</small></td><td>${money(p.precio)}</td><td>${p.fisico??'—'}</td><td>${p.reservado??'—'}</td><td><span class="pill ${p.disponible!=null&&p.disponible<5?'warning':''}">${p.disponible??'Sin lectura'}</span></td></tr>`).join('')||'<tr><td colspan="6">Sin productos para mostrar.</td></tr>';
}
async function cases(){
  const data=await api('casos');
  $('cases').innerHTML=data.casos.map(c=>`<article class="case-card"><span class="case-id">${escape(c.id)}</span><h3>${escape(c.titulo||({'CAT-001':'Producto de catálogo: caso normal','CAT-002':'Producto de catálogo: faltante','CAT-003':'Producto de catálogo: descuento excepcional'}[c.id]||c.id))}</h3><p>${escape(c.solicitud.quotation_id)} v${c.solicitud.quotation_version}<br>${escape(c.solicitud.customer_id)}${c.total_cotizado?'<br>Oferta: '+money(c.total_cotizado):''}</p><button class="primary evaluate" data-case="${escape(c.id)}" ${state.role!=='VENTAS'?'disabled title="La solicitud la envía Ventas"':''}>Evaluar solicitud →</button></article>`).join('')||'<div class="empty">Primero carga los datos de demostración.</div>';
  document.querySelectorAll('.evaluate').forEach(b=>b.onclick=()=>evaluateCase(b));
}
async function evaluateCase(button){
  button.disabled=true;notify('');
  try {
    const data=await api('casos/'+encodeURIComponent(button.dataset.case)+'/evaluar',{method:'POST'});const r=data.respuesta;
    const slot=$('case-result');slot.hidden=false;
    slot.innerHTML=`<article class="result-card">${badge(r.status)}<h2>${escape(r.code.replaceAll('_',' '))}</h2><p>${escape(r.message)}</p><div class="result-data"><div><span>Total validado</span><strong>${money(r.total)}</strong></div><div><span>Responsable</span><strong>${escape(r.responsible_role)}</strong></div><div><span>Pedido operativo</span><strong>Sin crear · order_id = null</strong></div></div><p>${escape(r.required_action)}</p>${(r.conditions||[]).map(c=>`<p class="pill warning">${escape(c.sku)}: ${c.available_quantity} disponibles de ${c.requested_quantity}. Sin fecha prometida.</p>`).join('')}<p class="table-note">${escape(r.request_id)} · ${escape(r.correlation_id)}</p>${['RECHAZADA','PROMESA_CONDICIONADA','PENDIENTE'].includes(r.status)?'<button id="escalate" class="primary">Solicitar revisión humana →</button>':''} <button id="view-audit" class="secondary">Ver trazabilidad</button></article>`;
    if($('escalate'))$('escalate').onclick=async()=>{try {await api('solicitudes/'+encodeURIComponent(r.request_id)+'/escalar',{method:'POST'});notify('Escalamiento registrado. El responsable humano debe revisar y decidir.');$('escalate').disabled=true;}catch(e){notify(e.message);}};
    $('view-audit').onclick=()=>{navigate('bitacora');$('correlation').value=r.correlation_id;loadAudit();};
    slot.scrollIntoView({behavior:'smooth',block:'nearest'});
  } catch(error){notify(error.message);}finally{button.disabled=false;}
}
async function decisions(){
  await summary();const records=state.summary.escalamientos;
  $('escalations').innerHTML=records.map(e=>{
    const expired=e.estado==='ESPERANDO_DECISION'&&new Date(e.plazo_hasta)<new Date();
    const open=e.estado==='ESPERANDO_DECISION'&&!expired;
    const options=e.tipo==='DESCUENTO'?['APROBADA','RECHAZADA']:e.tipo==='REPOSICION'?['OFRECER_PARCIAL','EVALUAR_REPOSICION','DESCARTAR']:[];
    return `<article class="decision-card">${badge(expired?'SIN_DECISION':e.estado)}<h3>${escape(e.escalation_id)} · ${escape(e.tipo)}</h3><p>${escape(e.request_id)} · ${escape(e.correlation_id)}<br>${e.signal_id?'Señal '+escape(e.signal_id):'Cotización '+escape(e.quotation_id)+' · La aprobación aplicaría a v'+e.version_aprobacion}${e.total?' · Oferta '+money(e.total):''}</p>${open&&state.role==='GERENCIA'&&options.length?`<form data-escalation="${escape(e.escalation_id)}"><select aria-label="Decisión">${options.map(o=>'<option value="'+o+'">'+escape(o.replaceAll('_',' '))+'</option>').join('')}</select><input aria-label="Motivo" name="motivo" required minlength="3" maxlength="280" placeholder="Motivo de la decisión"><button class="primary">Registrar decisión</button></form>`:`<p>${e.decision?'Decisión registrada: '+escape(e.decision):expired?'El plazo venció. El vendedor debe mantener seguimiento.':state.role==='VENTAS'?'Pendiente de revisión por el dueño.':'Este caso requiere atención del administrador.'}</p>`}</article>`;
  }).join('')||'<div class="empty">No hay escalamientos registrados.<br>Evalúa un caso de excepción y solicita la revisión humana.</div>';
  document.querySelectorAll('[data-escalation]').forEach(f=>f.onsubmit=async event=>{event.preventDefault();const b=f.querySelector('button');b.disabled=true;try{await api('escalamientos/'+encodeURIComponent(f.dataset.escalation)+'/decision',{method:'POST',body:JSON.stringify({decision:f.querySelector('select').value,motivo:f.querySelector('input').value})});await decisions();notify('Decisión registrada en la bitácora. No se creó pedido ni reserva.');}catch(e){notify(e.message);b.disabled=false;}});
}
async function loadAudit(){
  try {const data=await api('bitacora/'+encodeURIComponent($('correlation').value.trim()));
    $('audit-events').innerHTML=data.eventos.map(e=>`<article class="audit-row"><time>${escape(new Date(e.occurred_at).toLocaleTimeString('es-PE'))}</time><div><strong>${escape(e.event_type.replaceAll('_',' '))}</strong><p>${escape(e.code)} · ${escape(e.interface_id)}<br>${escape(e.actor_id)} / ${escape(e.actor_type)} · ${escape(e.request_id||'')}</p></div></article>`).join('')||'<div class="empty">No hay eventos para esta correlación.</div>';
  }catch(e){notify(e.message);}
}
$('login-form').onsubmit=async event=>{event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;$('login-error').textContent='';try{await api('sesion',{method:'POST',body:JSON.stringify({rol:$('role').value,password:$('password').value})});$('password').value='';await boot();}catch(e){$('login-error').textContent=e.message;}finally{button.disabled=false;}};
$('logout').onclick=async()=>{try{await api('sesion',{method:'DELETE'});}finally{location.reload();}};
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>navigate(b.dataset.page));
document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>navigate(b.dataset.open));
document.querySelectorAll('.refresh').forEach(b=>b.onclick=()=>navigate(state.page));
$('refresh-catalog').onclick=()=>catalog().catch(e=>notify(e.message));
$('search').oninput=renderProducts;$('category').onchange=renderProducts;
$('audit-form').onsubmit=e=>{e.preventDefault();loadAudit();};
async function boot(){await summary();$('login').hidden=true;$('workspace').hidden=false;await navigate('inicio');}
boot().catch(()=>{});
