// auditorias.js - Gestión Auditorías SGSI
// Utiliza auth.js y utility.js

const AUD_API = 'http://localhost:5004';

document.addEventListener('DOMContentLoaded', ()=>{
    if(!verificarAutenticacion()) return;
    actualizarUIUsuario();

    initEventos();
    cargarAuditorias();
});

function initEventos(){
    document.getElementById('btnNuevaAuditoria').addEventListener('click', ()=> mostrarModalAuditoria());
    document.getElementById('btnGuardarAud').addEventListener('click', guardarAuditoria);

    document.getElementById('btnBuscarAud').addEventListener('click', cargarAuditorias);
    document.getElementById('inputBuscarAud').addEventListener('keyup', e=>{ if(e.key==='Enter') cargarAuditorias(); });
}

/* ---------- LISTADO ---------- */
async function cargarAuditorias(){
    try{
        toggleSpinner(true);
        const res = await fetch(`${AUD_API}/auditorias`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        let auds = await res.json();
        const filtro = document.getElementById('inputBuscarAud').value.toLowerCase();
        if(filtro) auds = auds.filter(a=> a.titulo.toLowerCase().includes(filtro));
        const tbody = document.getElementById('tablaAuditorias');
        tbody.innerHTML='';
        auds.forEach(a=>{
            tbody.innerHTML += `<tr>
                <td>${a.id}</td>
                <td>${a.titulo}</td>
                <td>${a.alcance}</td>
                <td>${crearBadgeEstado(a.estado,'estado')}</td>
                <td>${formatearFecha(a.fecha_inicio)}</td>
                <td>${formatearFecha(a.fecha_fin)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${a.id}"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${a.id}"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>`;});
        tbody.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const id=btn.dataset.id;
                if(btn.dataset.action==='edit') editarAuditoria(id);
                else eliminarAuditoria(id);
            });
        });
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

/* ---------- CRUD ---------- */
function mostrarModalAuditoria(datos=null){
    limpiarFormulario('formAuditoria');
    // Asegurarse de que el campo ID esté vacío al crear una nueva auditoría
    document.getElementById('audId').value = '';
    $('#modalAuditoria').modal('show');
    if(datos){
        document.getElementById('tituloModalAud').textContent='Editar Auditoría';
        rellenarFormulario('formAuditoria', datos);
    }else{
        document.getElementById('tituloModalAud').textContent='Nueva Auditoría';
    }
}

async function editarAuditoria(id){
    try{
        const res = await fetch(`${AUD_API}/auditorias/${id}`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        const data = await res.json();
        
        // Convertir estados antiguos a nuevos valores
        if (data.estado === 'PROGRAMADA') {
            data.estado = 'PLANIFICADA';
        } else if (data.estado === 'EN_PROCESO') {
            data.estado = 'EN_EJECUCION';
        }
        
        mostrarModalAuditoria(data);
    }catch(err){manejarError(err);} }

async function guardarAuditoria(){
    const datos = obtenerDatosFormulario('formAuditoria');
    const id = datos.id; delete datos.id;
    const metodo = id? 'PUT':'POST';
    const url = id? `${AUD_API}/auditorias/${id}` : `${AUD_API}/auditorias`;
    
    // Añadir campos requeridos por el backend si es una nueva auditoría
    if (metodo === 'POST') {
        // Generar un código único basado en la fecha
        datos.codigo = 'AUD-' + new Date().getTime().toString().slice(-6);
        // Establecer tipo por defecto si no existe
        datos.tipo = datos.tipo || 'INTERNA';
        // Establecer auditor líder como el usuario actual
        const identity = JSON.parse(localStorage.getItem('identity'));
        datos.auditor_lider = identity ? identity.usuario_id : 1;
    }
    
    try{
        toggleSpinner(true);
        const res = await fetch(url, {method:metodo, headers:{'Content-Type':'application/json','Authorization':`Bearer ${getToken()}`}, body:JSON.stringify(datos)});
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Auditoría guardada');
        $('#modalAuditoria').modal('hide');
        cargarAuditorias();
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

async function eliminarAuditoria(id){
    if(!confirm('¿Eliminar auditoría?')) return;
    try{
        toggleSpinner(true);
        const res = await fetch(`${AUD_API}/auditorias/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${getToken()}`}});
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Auditoría eliminada','warning');
        cargarAuditorias();
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

window.cargarAuditorias = cargarAuditorias;
