// riesgos.js - Gestión de riesgos SGSI
// Depende de auth.js y utility.js

const RIESGOS_API = 'http://localhost:5002'; // Ajusta si cambia env

let cacheActivos = [], cacheAmenazas = [], cacheVulnerabilidades = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();

    inicializarEventos();

    await Promise.all([
        cargarListasReferencia(),
        cargarRiesgos()
    ]);
});

function inicializarEventos() {
    document.getElementById('btnNuevoRiesgo').addEventListener('click', () => mostrarModalRiesgo());
    document.getElementById('btnGuardarRiesgo').addEventListener('click', guardarRiesgo);

    document.getElementById('btnBuscarRiesgo').addEventListener('click', cargarRiesgos);
    document.getElementById('inputBuscarRiesgo').addEventListener('keyup', (e)=>{ if(e.key==='Enter') cargarRiesgos(); });

    // Select2
    $('#activo, #amenaza, #vulnerabilidad').select2({theme:'bootstrap-5', dropdownParent: $('#modalRiesgo')});
}

/* ------------------ LISTAS REF ------------------ */
async function cargarListasReferencia() {
    try {
        toggleSpinner(true);
        const headers = { 'Authorization': `Bearer ${getToken()}` };
        const [activos, amenazas, vulnerabilidades] = await Promise.all([
            fetch(`${RIESGOS_API}/activos`, {headers}).then(r=>r.json()),
            fetch(`${RIESGOS_API}/amenazas`, {headers}).then(r=>r.json()),
            fetch(`${RIESGOS_API}/vulnerabilidades`, {headers}).then(r=>r.json())
        ]);
        cacheActivos = activos; cacheAmenazas = amenazas; cacheVulnerabilidades = vulnerabilidades;

        poblarSelect('#activo', activos);
        poblarSelect('#amenaza', amenazas);
        poblarSelect('#vulnerabilidad', vulnerabilidades);
    } catch(err){ manejarError(err);} finally { toggleSpinner(false);} }

function poblarSelect(selector, data){
    const sel = document.querySelector(selector);
    sel.innerHTML = '<option value="">Seleccione</option>';
    data.forEach(d=> sel.innerHTML += `<option value="${d.id}">${d.nombre}</option>`);
    $(sel).trigger('change');
}

/* ------------------ RIESGOS CRUD ------------------ */
async function cargarRiesgos(){
    try{
        toggleSpinner(true);
        const res = await fetch(`${RIESGOS_API}/riesgos`, { headers:{'Authorization':`Bearer ${getToken()}`} });
        let riesgos = await res.json();
        const filtro = document.getElementById('inputBuscarRiesgo').value.trim().toLowerCase();
        if(filtro) riesgos = riesgos.filter(r=> r.nombre.toLowerCase().includes(filtro));
        const tbody = document.getElementById('tablaRiesgos');
        tbody.innerHTML = '';
        riesgos.forEach(r=>{
            // Buscar el nombre del activo usando el activo_id y el caché de activos
            const activoNombre = r.activo_id ? 
                (cacheActivos.find(a => a.id === r.activo_id)?.nombre || 'No especificado') : 
                (r.activo?.nombre || 'No especificado');
                
            tbody.innerHTML += `<tr>
                <td>${r.id}</td>
                <td>${r.nombre}</td>
                <td>${activoNombre}</td>
                <td>${r.nivel_riesgo || ''}</td>
                <td>${crearBadgeEstado(r.estado)}</td>
                <td>${formatearFecha(r.fecha_identificacion)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" data-id="${r.id}" data-action="edit"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" data-id="${r.id}" data-action="delete"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>`;
        });
        // Eventos
        tbody.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const id = btn.dataset.id;
                if(btn.dataset.action==='edit') editarRiesgo(id);
                else eliminarRiesgo(id);
            });
        });
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

function mostrarModalRiesgo(datos=null){
    limpiarFormulario('formRiesgo');
    $('#modalRiesgo').modal('show');
    if(datos){
        document.getElementById('tituloModalRiesgo').textContent='Editar Riesgo';
        rellenarFormulario('formRiesgo', datos);
        $('#activo').val(datos.activo_id).trigger('change');
        $('#amenaza').val(datos.amenaza_id).trigger('change');
        $('#vulnerabilidad').val(datos.vulnerabilidad_id).trigger('change');
    }else{
        document.getElementById('tituloModalRiesgo').textContent='Nuevo Riesgo';
    }
}

async function editarRiesgo(id){
    try{
        const res = await fetch(`${RIESGOS_API}/riesgos/${id}`, { headers:{'Authorization':`Bearer ${getToken()}`} });
        const data = await res.json();
        mostrarModalRiesgo(data);
    }catch(err){ manejarError(err);} }

async function guardarRiesgo(){
    const datos = obtenerDatosFormulario('formRiesgo');
    const id = datos.id; delete datos.id;
    const metodo = id? 'PUT':'POST';
    const url = id? `${RIESGOS_API}/riesgos/${id}` : `${RIESGOS_API}/riesgos`;
    try{
        toggleSpinner(true);
        const res = await fetch(url, {
            method: metodo,
            headers:{ 'Content-Type':'application/json', 'Authorization':`Bearer ${getToken()}`},
            body: JSON.stringify(datos)
        });
        const d = await res.json();
        if(!res.ok) throw new Error(d.error||'Error al guardar');
        mostrarNotificacion('Riesgo guardado');
        $('#modalRiesgo').modal('hide');
        cargarRiesgos();
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

async function eliminarRiesgo(id){
    if(!confirm('¿Eliminar riesgo?')) return;
    try{
        toggleSpinner(true);
        const res = await fetch(`${RIESGOS_API}/riesgos/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${getToken()}`}});
        const d=await res.json();
        if(!res.ok) throw new Error(d.error||'Error');
        mostrarNotificacion('Riesgo eliminado','warning');
        cargarRiesgos();
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

// Exponer para depuración
window.cargarRiesgos = cargarRiesgos;
