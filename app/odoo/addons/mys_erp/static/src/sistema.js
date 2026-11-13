/** @odoo-module **/
import { Component, onWillStart, useState, useRef, onPatched } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { useBus, useService } from '@web/core/utils/hooks';
import { WebClient } from '@web/webclient/webclient';

const NAV = [
    ['home', 'Vista general', 'fa-th-large', 'mys_erp.action_workspace'],
    ['contacts', 'Contactos', 'fa-address-book-o', 'mys_erp.action_contactos_mys'],
    ['leads', 'Leads', 'fa-user-plus', 'mys_erp.action_leads'],
    ['crm', 'CRM / Oportunidades', 'fa-filter', 'mys_erp.action_opportunities'],
    ['inventory', 'Inventario', 'fa-cubes', 'mys_erp.action_inventory'],
    ['quotes', 'Cotizaciones', 'fa-file-text-o', 'mys_erp.action_cotizaciones_mys'],
    ['sales', 'Ventas', 'fa-shopping-cart', 'mys_erp.action_ventas_mys'],
    ['catalog', 'Catálogo', 'fa-th-list', 'mys_erp.action_catalogo_mys'],
    ['evaluations', 'Evaluación comercial', 'fa-exchange', 'mys_erp.action_evaluations'],
    ['decisions', 'Decisiones del dueño', 'fa-check-square-o', 'mys_erp.action_decisions'],
    ['trace', 'Trazabilidad', 'fa-history', 'mys_erp.action_trace'],
    ['agent', 'Agente SIE', 'fa-commenting-o', 'mys_erp.action_agent'],
];

export class MysSidebar extends Component {
    static template = 'mys.Sidebar';
    static props = {};
    setup() {
        this.action = useService('action');
        this.state = useState({ session: null, active: 'home', mobile: false });
        useBus(this.env.bus, 'MYS:NAVIGATE', ({ detail }) => { this.state.active = detail; });
        useBus(this.env.bus, 'MYS:AGENT_STATE', ({ detail }) => {
            if (this.state.session) { this.state.session.agent = detail; }
        });
        this.nav = NAV;
        onWillStart(async () => {
            try { this.state.session = await rpc('/mys/session'); } catch { /* Otros usuarios conservan el backend habitual. */ }
        });
    }
    async go(item) {
        this.state.active = item[0];
        this.state.mobile = false;
        await this.action.doAction(item[3]);
    }
}
WebClient.components = { ...WebClient.components, MysSidebar };

export class MysWorkspace extends Component {
    static template = 'mys.Workspace';
    static props = ['*'];
    setup() {
        this.action = useService('action');
        const params = this.props.action?.params || {};
        this.state = useState({ page: params.page || 'home', data: null, error: '',
            query: params.query || params.correlation_id || '', traceOrderId: params.order_id || false,
            traceFilters: {partner_id: '', user_id: '', date_from: '', date_to: '', version: '', event_type: '', actor_id: ''},
            traceOptions: {customers: [], sellers: [], versions: [], types: [], actors: []},
            events: [], traceOrders: [], traceWarning: '', queried: false, tracing: false,
            message: '', messages: [], conversation: null, sending: false });
        this.chatEnd = useRef('chatEnd');
        onPatched(() => this.chatEnd.el?.scrollIntoView({ block: 'nearest' }));
        onWillStart(async () => {
            try {
                this.state.data = await rpc('/mys/workspace');
                this.env.bus.trigger('MYS:AGENT_STATE', this.state.data.agent);
                if (this.state.page === 'trace') { await this.trace(); }
            } catch (e) { this.state.error = e.data?.message || e.message; }
        });
    }
    get cards() {
        const c = this.state.data?.counts || {};
        return [['Contactos', c.contacts, 'contacts'], ['Leads', c.leads, 'leads'],
            ['Oportunidades', c.opportunities, 'crm'], ['Productos de catálogo', c.products, 'catalog'],
            ['Cotizaciones', c.quotes, 'quotes'], ['Ventas', c.sales || 0, 'sales'], ['Por decidir', c.decisions, 'decisions']];
    }
    go(key) { this.env.bus.trigger('MYS:NAVIGATE', key); return this.action.doAction(NAV.find(n => n[0] === key)[3]); }
    openEvaluation(id) {
        this.env.bus.trigger('MYS:NAVIGATE', 'evaluations');
        return this.action.doAction({ type: 'ir.actions.act_window', res_model: 'mys.evaluation', res_id: id, views: [[false, 'form']] });
    }
    async trace() {
        if (this.state.tracing) { return; }
        this.state.error = '';
        this.state.tracing = true;
        try {
            const r = await rpc('/mys/trace', {query: this.state.query.trim(), order_id: this.state.traceOrderId, ...this.state.traceFilters});
            this.state.events = r.eventos;
            this.state.traceOrders = r.orders || [];
            this.state.traceOptions = r.options || {customers: [], sellers: [], versions: [], types: [], actors: []};
            this.state.traceWarning = r.warning || '';
            this.state.queried = true;
        } catch (e) { this.state.error = e.data?.message || e.message; }
        finally { this.state.tracing = false; }
    }
    changeTraceQuery() { this.state.traceOrderId = false; }
    async resetTrace() {
        this.state.query = '';
        this.state.traceOrderId = false;
        Object.keys(this.state.traceFilters).forEach(key => { this.state.traceFilters[key] = ''; });
        await this.trace();
    }
    openOrder(id) {
        return this.action.doAction({type: 'ir.actions.act_window', res_model: 'sale.order', res_id: id, views: [[false, 'form']]});
    }
    formatTraceDate(value) {
        return new Intl.DateTimeFormat('es-PE', {dateStyle: 'short', timeStyle: 'medium', timeZone: 'America/Lima'}).format(new Date(value));
    }
    traceLabel(value) {
        const labels = {COTIZACION: 'Cotización', VENTA: 'Venta', ACEPTACION: 'Aceptación del cliente',
            EVALUACION: 'Evaluación', RECIBIDA: 'Solicitud recibida', CONSULTA: 'Reglas consultadas',
            DECISION: 'Resultado de evaluación', APROBACION: 'Decisión de descuento', ESCALADO: 'Solicitud al dueño',
            DECISION_DUENO: 'Decisión del dueño', PLAZO_VENCIDO: 'Plazo vencido', REVALIDACION_VENTA: 'Revalidación para venta',
            HUMANO: 'Persona', SISTEMA: 'Sistema', AGENTE: 'Agente', draft: 'Borrador', sent: 'Enviada', sale: 'Venta confirmada', cancel: 'Cancelada',
            VALIDADA: 'Validada', CREADA: 'Creada', PRESENTADA: 'Presentada', CONFIRMADA: 'Confirmada', CANCELADA: 'Cancelada',
            REGISTRADA: 'Registrada', APROBADA: 'Aprobada', RECHAZADA: 'Rechazada', DESCUENTO_SIN_APROBACION: 'Descuento sin aprobación',
            DISPONIBILIDAD_PARCIAL: 'Disponibilidad parcial', SIN_DECISION: 'Sin decisión', COTIZACION_VENCIDA: 'Cotización vencida'};
        return labels[value] || value.replaceAll('_', ' ');
    }
    async send() {
        const text = this.state.message.trim();
        if (!text || this.state.sending || !this.state.data?.agent.enabled) { return; }
        this.state.message = '';
        this.state.messages.push({ id: Date.now(), role: 'user', text });
        this.state.sending = true;
        try {
            const r = await rpc('/mys/agent/chat', { message: text, conversation: this.state.conversation });
            this.state.conversation = r.conversation || this.state.conversation;
            if (!r.ok && ['CUOTA_AGOTADA', 'API_KEY_RECHAZADA', 'MODELO_NO_DISPONIBLE'].includes(r.code)) {
                Object.assign(this.state.data.agent, {enabled: false, code: r.code, message: r.message});
                this.env.bus.trigger('MYS:AGENT_STATE', this.state.data.agent);
            }
            this.state.messages.push({ id: Date.now() + 1, role: r.ok ? 'agent' : 'error', text: r.message });
        } catch (e) {
            this.state.messages.push({ id: Date.now() + 1, role: 'error', text: e.data?.message || 'No se pudo contactar al agente. Reintente.' });
        } finally { this.state.sending = false; }
    }
    keydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); this.send(); }
    }
}
registry.category('actions').add('mys.workspace', MysWorkspace);
