// acciones-correctivas.js – Vista dedicada a planes de acción y actividades
const SERVICE_AUDITORIAS_URL = 'http://localhost:5008';

const tablaPlanes = document.getElementById('tablaPlanesAccion');
const btnNuevoPlan = document.getElementById('btnNuevoPlanAccion');
const modalPlan = new bootstrap.Modal(document.getElementById('modalPlanAccion'));
const formPlan = document.getElementById('formPlanAccion');
const btnGuardarPlan = document.getElementById('btnGuardarPlan');
const inputBuscarPlan = document.getElementById('inputBuscarPlan');
const btnBuscarPlan = document.getElementById('btnBuscarPlan');
const filtroEstado = document.getElementById('filtroEstado');

// Actividades
const modalActividades = new bootstrap.Modal(document.getElementById('modalActividades'));
const actividadesContainer = document.getElementById('actividadesContainer');
const formActividad = document.getElementById('formActividad');
const btnAgregarActividad = document.getElementById('btnAgregarActividad');

let planes = [];

document.addEventListener('DOMContentLoaded', async ()=>{
    if(!verificarAutenticacion()) return;
    actualizarUIUsuario();
    $('.select2').select2({ dropdownParent: $('#modalPlanAccion') });

    await cargarHallazgosSelect();
    await cargarUsuariosSelect();
    await cargarPlanes();

    btnNuevoPlan?.addEventListener('click', ()=> abrirModalPlan());
    btnGuardarPlan?.addEventListener('click', guardarPlan);
    inputBuscarPlan?.addEventListener('keyup', e=> { if(e.key==='Enter') aplicarFiltros(); });
    btnBuscarPlan?.addEventListener('click', aplicarFiltros);
    filtroEstado?.addEventListener('change', aplicarFiltros);

    btnAgregarActividad?.addEventListener('click', guardarActividad);
});

async function api(url,opts={}){ const res=await fetch(url,{headers:{'Content-Type':'application/json','Authorization':`Bearer ${getToken()}`},...opts}); if(!res.ok) throw new Error((await res.json()).error||'Error'); if(res.status!==204) return res.json(); }

async function cargarPlanes(){ try{ toggleSpinner(true); planes = await api(`${SERVICE_AUDITORIAS_URL}/planes-accion`); renderTabla(planes);}catch(e){manejarError(e);}finally{toggleSpinner(false);} }

async function cargarHallazgosSelect(){ try{ const hallazgos=await api(`${SERVICE_AUDITORIAS_URL}/hallazgos`); const sel=formPlan.elements['hallazgo_id']; hallazgos.forEach(h=> sel.insertAdjacentHTML('beforeend',`<option value="${h.id}">${h.codigo}</option>`)); }catch(e){}
}
async function cargarUsuariosSelect(){ try{ const usuarios=await api(`${SERVICE_AUDITORIAS_URL}/usuarios`); const sels=[formPlan.elements['responsable'],formActividad.elements['responsable']]; sels.forEach(sel=> usuarios.forEach(u=> sel.insertAdjacentHTML('beforeend',`<option value="${u.id}">${u.nombre}</option>`))); }catch(e){}
}

function renderTabla(data){ tablaPlanes.innerHTML=''; if(!data.length){ tablaPlanes.innerHTML='<tr><td colspan="8" class="text-center">Sin planes</td></tr>'; return;} data.forEach(p=>{ tablaPlanes.insertAdjacentHTML('beforeend',`<tr>
    <td>${p.id}</td><td>${p.hallazgo_codigo||''}</td><td>${p.tipo_accion}</td><td>${p.responsable_nombre||''}</td><td>${formatearFecha(p.fecha_fin_planificada)}</td><td>${crearBadgeEstado(p.estado)}</td><td>${p.progreso||0}%</td><td>
        <button class="btn btn-sm btn-outline-primary me-1" data-edit="${p.id}"><i class="fas fa-edit"></i></button>
        <button class="btn btn-sm btn-outline-danger me-1" data-del="${p.id}"><i class="fas fa-trash"></i></button>
        <button class="btn btn-sm btn-outline-secondary" data-act="${p.id}"><i class="fas fa-list"></i></button>
    </td></tr>`); }); tablaPlanes.querySelectorAll('[data-edit]').forEach(b=>b.addEventListener('click',()=> abrirModalPlan(b.dataset.edit))); tablaPlanes.querySelectorAll('[data-del]').forEach(b=>b.addEventListener('click',()=> eliminarPlan(b.dataset.del))); tablaPlanes.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click',()=> abrirModalActividades(b.dataset.act))); }

function aplicarFiltros(){ const txt=inputBuscarPlan.value.toLowerCase(); const est=filtroEstado.value; renderTabla(planes.filter(p=> (p.id+''+p.tipo_accion).toLowerCase().includes(txt) && (est==''||p.estado===est))); }

function abrirModalPlan(id=null){ limpiarFormulario('formPlanAccion'); document.getElementById('tituloModalPlan').textContent= id?'Editar Plan':'Nuevo Plan de Acción'; if(id){ const p=planes.find(x=>x.id==id); rellenarFormulario('formPlanAccion',p);} modalPlan.show(); }

async function guardarPlan(){ if(!formPlan.checkValidity()){formPlan.reportValidity();return;} const datos=obtenerDatosFormulario('formPlanAccion'); try{ toggleSpinner(true); const id=datos.id; const url=id?`${SERVICE_AUDITORIAS_URL}/planes-accion/${id}`:`${SERVICE_AUDITORIAS_URL}/planes-accion`; const metodo=id?'PUT':'POST'; await api(url,{method:metodo,body:JSON.stringify(datos)}); mostrarNotificacion(`Plan ${id?'actualizado':'creado'}`); modalPlan.hide(); await cargarPlanes(); }catch(e){manejarError(e);}finally{toggleSpinner(false);} }

async function eliminarPlan(id){ if(!confirm('¿Eliminar plan?')) return; try{ await api(`${SERVICE_AUDITORIAS_URL}/planes-accion/${id}`,{method:'DELETE'}); mostrarNotificacion('Plan eliminado'); await cargarPlanes(); }catch(e){manejarError(e);} }

// ---- Actividades ----
let planActual=null;
async function abrirModalActividades(planId){ planActual=planId; formActividad.elements['plan_accion_id'].value=planId; await cargarActividades(planId); modalActividades.show(); }

async function cargarActividades(planId){ try{ toggleSpinner(true); const acts = await api(`${SERVICE_AUDITORIAS_URL}/planes-accion/${planId}/actividades`); renderActividades(acts);}catch(e){manejarError(e);}finally{toggleSpinner(false);} }

function renderActividades(acts){ actividadesContainer.innerHTML=''; if(!acts.length){ actividadesContainer.innerHTML='<p class="text-muted">Sin actividades</p>'; return;} acts.forEach(a=>{ actividadesContainer.insertAdjacentHTML('beforeend',`<div class="border p-2 mb-2"><div class="d-flex justify-content-between"><div><strong>${a.descripcion}</strong><br>${crearBadgeEstado(a.estado)}</div><button class="btn btn-sm btn-outline-danger" data-del-act="${a.id}"><i class="fas fa-trash"></i></button></div></div>`); }); actividadesContainer.querySelectorAll('[data-del-act]').forEach(b=> b.addEventListener('click',()=> eliminarActividad(b.dataset.delAct))); }

async function guardarActividad(){ if(!formActividad.checkValidity()){formActividad.reportValidity();return;} const datos=obtenerDatosFormulario('formActividad'); try{ await api(`${SERVICE_AUDITORIAS_URL}/planes-accion/${planActual}/actividades`,{method:'POST',body:JSON.stringify(datos)}); mostrarNotificacion('Actividad creada'); formActividad.reset(); await cargarActividades(planActual);}catch(e){manejarError(e);} }

async function eliminarActividad(id){ if(!confirm('¿Eliminar actividad?')) return; try{ await api(`${SERVICE_AUDITORIAS_URL}/actividades-plan/${id}`,{method:'DELETE'}); mostrarNotificacion('Actividad eliminada'); await cargarActividades(planActual);}catch(e){manejarError(e);} }
