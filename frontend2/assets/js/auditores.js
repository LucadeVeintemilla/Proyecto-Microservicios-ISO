// auditores.js – Gestión de auditores
const SERVICE_AUDITORIAS_URL = 'http://localhost:5008';

// Elementos DOM
const tablaAuditores = document.getElementById('tablaAuditores');
const btnNuevoAuditor = document.getElementById('btnNuevoAuditor');
const modalAuditor = new bootstrap.Modal(document.getElementById('modalAuditor'));
const formAuditor = document.getElementById('formAuditor');
const btnGuardarAuditor = document.getElementById('btnGuardarAuditor');
const inputBuscarAuditor = document.getElementById('inputBuscarAuditor');
const btnBuscarAuditor = document.getElementById('btnBuscarAuditor');

let auditores = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();

    await cargarUsuariosSistema();
    await cargarAuditores();

    btnNuevoAuditor?.addEventListener('click', () => abrirModalAuditor());
    btnGuardarAuditor?.addEventListener('click', guardarAuditor);
    btnBuscarAuditor?.addEventListener('click', () => filtrarAuditores(inputBuscarAuditor.value));
    inputBuscarAuditor?.addEventListener('keyup', e => { if (e.key === 'Enter') filtrarAuditores(e.target.value); });
});

// helper fetch
async function api(url, opts={}) {
    const res = await fetch(url, {
        headers: { 'Content-Type':'application/json', 'Authorization': `Bearer ${getToken()}` },
        ...opts
    });
    if(!res.ok) throw new Error((await res.json()).error || 'Error');
    if(res.status!==204) return res.json();
}

async function cargarAuditores() {
    try{ toggleSpinner(true); auditores = await api(`${SERVICE_AUDITORIAS_URL}/auditores`); renderTabla(auditores);}catch(e){manejarError(e);}finally{toggleSpinner(false);} }

async function cargarUsuariosSistema() {
    // Obtener lista de usuarios con rol auditor
    try {
        const usuarios = await api(`${SERVICE_AUDITORIAS_URL}/usuarios`); // asumir endpoint
        const selUsuario = formAuditor.elements['usuario_id'];
        usuarios.forEach(u=> selUsuario.insertAdjacentHTML('beforeend', `<option value="${u.id}">${u.nombre}</option>`));
    } catch (e){ console.warn('No se pudo cargar usuarios', e);} }

function renderTabla(data){
    tablaAuditores.innerHTML='';
    if(!data.length) { tablaAuditores.innerHTML='<tr><td colspan="6" class="text-center">Sin auditores</td></tr>'; return; }
    data.forEach(a => {
        tablaAuditores.insertAdjacentHTML('beforeend', `<tr>
            <td>${a.id}</td>
            <td>${a.nombre}</td>
            <td>${a.especialidad}</td>
            <td>${a.certificaciones||''}</td>
            <td>${crearBadgeEstado(a.estado)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" data-edit="${a.id}"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-outline-danger" data-del="${a.id}"><i class="fas fa-trash"></i></button>
            </td></tr>`);
    });
    tablaAuditores.querySelectorAll('[data-edit]').forEach(btn=>btn.addEventListener('click', ()=> abrirModalAuditor(btn.dataset.edit)));
    tablaAuditores.querySelectorAll('[data-del]').forEach(btn=>btn.addEventListener('click', ()=> eliminarAuditor(btn.dataset.del)));
}

function filtrarAuditores(txt){ txt=txt.toLowerCase(); renderTabla(auditores.filter(a=> a.nombre.toLowerCase().includes(txt))); }

function abrirModalAuditor(id=null){ limpiarFormulario('formAuditor'); document.getElementById('tituloModalAuditor').textContent = id? 'Editar Auditor':'Nuevo Auditor'; if(id){ const a=auditores.find(x=>x.id==id); rellenarFormulario('formAuditor', a);} modalAuditor.show(); }

async function guardarAuditor(){ if(!formAuditor.checkValidity()){formAuditor.reportValidity();return;} const datos=obtenerDatosFormulario('formAuditor'); try{ toggleSpinner(true); const id=datos.id; const metodo=id?'PUT':'POST'; const url=id? `${SERVICE_AUDITORIAS_URL}/auditores/${id}` : `${SERVICE_AUDITORIAS_URL}/auditores`; await api(url,{method:metodo,body:JSON.stringify(datos)}); mostrarNotificacion(`Auditor ${id?'actualizado':'creado'}`); modalAuditor.hide(); await cargarAuditores(); }catch(e){ manejarError(e);}finally{ toggleSpinner(false);} }

async function eliminarAuditor(id){ if(!confirm('¿Eliminar auditor?')) return; try{ await api(`${SERVICE_AUDITORIAS_URL}/auditores/${id}`,{method:'DELETE'}); mostrarNotificacion('Auditor eliminado'); await cargarAuditores(); }catch(e){ manejarError(e);} }
