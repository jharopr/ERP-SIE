/* Prueba de componentes en DOM simulado, con la misma biblioteca Owl de Odoo instalado.
 * Preparación: npm install --prefix .test-runs/owl jsdom@26.1.0 --ignore-scripts
 * No controla navegadores ni necesita credenciales.
 */
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const { JSDOM } = require(path.join(root, '.test-runs/owl/node_modules/jsdom'));
const dom = new JSDOM('<html><body><div id="app"></div></body></html>', { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window;
w.HTMLElement.prototype.scrollIntoView = function () {};
w.eval(execFileSync('docker', ['compose', 'exec', '-T', 'odoo', 'cat', '/usr/lib/python3/dist-packages/odoo/addons/web/static/lib/owl/owl.js'], { cwd: root }).toString());
Object.assign(w, w.owl);
const counts = {contacts: 8, leads: 6, opportunities: 5, products: 50, quotes: 9, evaluations: 1, decisions: 1};
const agent = {enabled: true, code: 'HABILITADO', message: 'API key verificada.'};
const calls = [];
w.rpc = async (route, data) => {
    calls.push({route, data});
    if (route === '/mys/session') return {name: 'Vendedor demo', role: 'VENTAS', agent};
    if (route === '/mys/workspace') return {counts, agent, evaluations: []};
    if (route === '/mys/trace') return {eventos: [{event_id:1, code:'VALIDADA', event_type:'EVALUACION', interface_id:'I03', actor_id:'VEN-DEMO-01', actor_type:'HUMANO', occurred_at:'2026-11-11'}]};
    if (route === '/mys/agent/chat') return {ok:true, message:'Respuesta de prueba', conversation:'a'.repeat(32)};
    throw Error('Ruta inesperada: '+route);
};
w.useService = () => ({doAction: a => calls.push({action:a})});
w.useBus = () => {};
w.registry = {category: () => ({add: () => {}})};
w.WebClient = class {};
const dir = path.join(root, 'odoo/addons/mys_erp/static/src');
const source = fs.readFileSync(path.join(dir, 'sistema.js'), 'utf8').replace(/^import .*\r?\n/gm, '').replace(/export class/g, 'class');
w.eval(source + '\nwindow.MysWorkspace = MysWorkspace; window.MysSidebar = MysSidebar;');
const xml = new w.DOMParser().parseFromString(fs.readFileSync(path.join(dir, 'sistema.xml'), 'utf8'), 'text/xml');
assert.equal(xml.querySelector('parsererror'), null, 'XML válido');
const serializer = new w.XMLSerializer();
const templates = '<templates>' + [...xml.documentElement.children].filter(n => !n.hasAttribute('t-inherit')).map(n => serializer.serializeToString(n)).join('') + '</templates>';
async function render(Component, props) {
    const target = w.document.querySelector('#app');
    const app = new w.owl.App(Component, {templates, props: props || {}, env:{bus:{trigger:()=>{}}}});
    const component = await app.mount(target);
    return {app, component, target};
}
(async () => {
    let r = await render(w.MysSidebar);
    assert.equal(r.target.querySelectorAll('nav button').length, 11);
    assert.match(r.target.textContent, /Contactos[\s\S]*Leads[\s\S]*Inventario[\s\S]*Agente SIE/);
    r.app.destroy();
    r = await render(w.MysWorkspace, {action:{params:{page:'home'}}});
    assert.equal(r.target.querySelectorAll('.mys_stats button').length, 6);
    assert.match(r.target.textContent, /50/);
    r.app.destroy();
    r = await render(w.MysWorkspace, {action:{params:{page:'agent'}}});
    r.component.state.message = 'Consulta de prueba';
    await r.component.send();
    await new Promise(resolve => w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
    assert.match(r.target.textContent, /Respuesta de prueba/);
    assert(calls.some(c => c.route === '/mys/agent/chat'));
    r.app.destroy();
    r = await render(w.MysWorkspace, {action:{params:{page:'trace', correlation_id:'COR-TEST'}}});
    assert.match(r.target.textContent, /VALIDADA/);
    r.app.destroy();
    Object.assign(agent, {enabled:false, code:'CUOTA_AGOTADA', message:'Sin cuota en el proveedor.'});
    r = await render(w.MysWorkspace, {action:{params:{page:'agent'}}});
    assert.equal(r.target.querySelector('textarea').disabled, true);
    assert.match(r.target.textContent, /Agente sin cuota/);
    r.app.destroy();
    console.log('OWL: menú de 11 accesos, vista general, chat, trazabilidad y estado sin cuota correctos en DOM simulado.');
    dom.window.close();
})().catch(e => {console.error(e); dom.window.close(); process.exitCode = 1;});
