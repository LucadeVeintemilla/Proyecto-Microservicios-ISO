// hallazgos.js – Gestión de hallazgos y planes de acción
const SERVICE_AUDITORIAS_URL = 'http://localhost:5008';

const tablaHallazgos = document.getElementById('tablaHallazgos');
const btnNuevoHallazgo = document.getElementById('btnNuevoHallazgo');
const modalHallazgo = new bootstrap.Modal(document.getElementById('modalHallazgo'));
const formHallazgo = document.getElementById('formHallazgo');
const btnGuardarHallazgo = document.getElementById('btnGuardarHallazgo');
const inputBuscarHallazgo = document.getElementById('inputBuscarHallazgo');
const btnBuscarHallazgo = document.getElementById('btnBuscarHallazgo');
const filtroEstado = document.getElementById('filtroEstado');

// Planes de acción
const modalPlanes = new bootstrap.Modal(document.getElementById('modalPlanesAccion'));
const planesContainer = document.getElementById('planesContainer');
const formPlan = document.getElementById('formPlanAccion');
const btnAgregarPlan = document.getElementById('btnAgregarPlanAccion');

let hallazgos = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();
    $('.select2').select2({ dropdownParent: $('#modalHallazgo') });

    await cargarAuditoriasSelect();
    await cargarHallazgos();

    btnNuevoHallazgo?.addEventListener('click', ()=> abrirModalHallazgo());
    btnGuardarHallazgo?.addEventListener('click', guardarHallazgo);
    btnBuscarHallazgo?.addEventListener('click', ()=> aplicarFiltros());
    inputBuscarHallazgo?.addEventListener('keyup', e=> { if(e.key==='Enter') aplicarFiltros(); });
    filtroEstado?.addEventListener('change', aplicarFiltros);

    btnAgregarPlan?.addEventListener('click', guardarPlan);
});

async function api(url, opts={}){ const res= await fetch(url,{ headers:{ 'Content-Type':'application/json','Authorization':`Bearer ${getToken()}` }, ...opts}); if(!res.ok) throw new Error((await res.json()).error||'Error'); if(res.status!==204) return res.json(); }

async function cargarHallazgos(){ try{ toggleSpinner(true); hallazgos = await api(`${SERVICE_AUDITORIAS_URL}/hallazgos`); renderTabla(hallazgos);}catch(e){manejarError(e);}finally{toggleSpinner(false);} }

async function cargarAuditoriasSelect(){ try{ const auditorias = await api(`${SERVICE_AUDITORIAS_URL}/auditorias`); const sel = formHallazgo.elements['auditoria_id']; auditorias.forEach(a=> sel.insertAdjacentHTML('beforeend',`<option value="${a.id}">${a.codigo} - ${a.titulo}</option>`)); }catch(e){ console.warn('No auditorias',e);} }

function renderTabla(data){ tablaHallazgos.innerHTML=''; if(!data.length){ tablaHallazgos.innerHTML='<tr><td colspan="7" class="text-center">Sin hallazgos</td></tr>'; return;} data.forEach(h=>{ tablaHallazgos.insertAdjacentHTML('beforeend',`<tr>
    <td>${h.codigo}</td><td>${h.auditoria_codigo||''}</td><td>${h.tipo}</td><td>${h.descripcion}</td><td>${h.area_responsable||''}</td><td>${crearBadgeEstado(h.estado)}</td>
    <td><button class="btn btn-sm btn-outline-primary me-1" data-edit="${h.id}"><i class="fas fa-edit"></i></button>
        <button class="btn btn-sm btn-outline-danger me-1" data-del="${h.id}"><i class="fas fa-trash"></i></button>
        <button class="btn btn-sm btn-outline-secondary" data-plan="${h.id}"><i class="fas fa-tasks"></i></button></td></tr>`);}); tablaHallazgos.querySelectorAll('[data-edit]').forEach(b=>b.addEventListener('click',()=> abrirModalHallazgo(b.dataset.edit))); tablaHallazgos.querySelectorAll('[data-del]').forEach(b=>b.addEventListener('click',()=> eliminarHallazgo(b.dataset.del))); tablaHallazgos.querySelectorAll('[data-plan]').forEach(b=>b.addEventListener('click',()=> abrirModalPlanes(b.dataset.plan))); }

function aplicarFiltros(){ let txt=inputBuscarHallazgo.value.toLowerCase(); let est=filtroEstado.value; let datos=hallazgos.filter(h=> (h.codigo.toLowerCase().includes(txt)||h.descripcion.toLowerCase().includes(txt)) && (est==''||h.estado===est)); renderTabla(datos);} 

function abrirModalHallazgo(id=null){ limpiarFormulario('formHallazgo'); document.getElementById('tituloModalHallazgo').textContent=id?'Editar Hallazgo':'Nuevo Hallazgo'; if(id){ const h = hallazgos.find(x=>x.id==id); rellenarFormulario('formHallazgo',h);} modalHallazgo.show(); }

async function guardarHallazgo(){ if(!formHallazgo.checkValidity()){formHallazgo.reportValidity();return;} const datos=obtenerDatosFormulario('formHallazgo'); try{ toggleSpinner(true); const id=datos.id; const metodo=id?'PUT':'POST'; const url=id?`${SERVICE_AUDITORIAS_URL}/hallazgos/${id}`:`${SERVICE_AUDITORIAS_URL}/hallazgos`; await api(url,{method:metodo,body:JSON.stringify(datos)}); mostrarNotificacion(`Hallazgo ${id?'actualizado':'creado'}`); modalHallazgo.hide(); await cargarHallazgos(); }catch(e){ manejarError(e);}finally{toggleSpinner(false);} }

async function eliminarHallazgo(id){ if(!confirm('¿Eliminar hallazgo?')) return; try{ await api(`${SERVICE_AUDITORIAS_URL}/hallazgos/${id}`,{method:'DELETE'}); mostrarNotificacion('Hallazgo eliminado'); await cargarHallazgos(); }catch(e){ manejarError(e);} }

// -------------- Planes de acción --------------
let hallazgoActual=null;
async function abrirModalPlanes(hId){ hallazgoActual=hId; formPlan.elements['hallazgo_id'].value=hId; await cargarPlanes(hId); modalPlanes.show(); }

async function cargarPlanes(hId){ try{ toggleSpinner(true); const planes= await api(`${SERVICE_AUDITORIAS_URL}/hallazgos/${hId}/planes-accion`); renderPlanes(planes);}catch(e){manejarError(e);}finally{toggleSpinner(false);} }

function renderPlanes(planes){ planesContainer.innerHTML=''; if(!planes.length){ planesContainer.innerHTML='<p class="text-muted">Sin planes de acción</p>'; return;} planes.forEach(p=>{ planesContainer.insertAdjacentHTML('beforeend',`<div class="border p-2 mb-2"><div class="d-flex justify-content-between"><div><strong>${p.tipo_accion}</strong> - ${crearBadgeEstado(p.estado)}<br><small>${p.descripcion}</small></div><button class="btn btn-sm btn-outline-danger" data-del-plan="${p.id}"><i class="fas fa-trash"></i></button></div></div>`);}); planesContainer.querySelectorAll('[data-del-plan]').forEach(b=> b.addEventListener('click', ()=> eliminarPlan(b.dataset.delPlan))); }

async function guardarPlan(){ if(!formPlan.checkValidity()){formPlan.reportValidity();return;} const datos=obtenerDatosFormulario('formPlanAccion'); try{ await api(`${SERVICE_AUDITORIAS_URL}/hallazgos/${hallazgoActual}/planes-accion`,{method:'POST',body:JSON.stringify(datos)}); mostrarNotificacion('Plan creado'); formPlan.reset(); await cargarPlanes(hallazgoActual);}catch(e){manejarError(e);} }

async function eliminarPlan(id){ if(!confirm('¿Eliminar plan?')) return; try{ await api(`${SERVICE_AUDITORIAS_URL}/planes-accion/${id}`,{method:'DELETE'}); mostrarNotificacion('Plan eliminado'); await cargarPlanes(hallazgoActual);}catch(e){manejarError(e);} }
