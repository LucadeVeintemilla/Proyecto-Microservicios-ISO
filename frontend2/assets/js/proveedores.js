// proveedores.js - Gestión Proveedores SGSI
// Requiere auth.js y utility.js

const PROV_API = 'http://localhost:5006';

document.addEventListener('DOMContentLoaded', ()=>{
    if(!verificarAutenticacion()) return;
    actualizarUIUsuario();

    initEventos();
    cargarProveedores();
});

function initEventos(){
    document.getElementById('btnNuevoProv').addEventListener('click', ()=> mostrarModalProveedor());
    document.getElementById('btnGuardarProv').addEventListener('click', guardarProveedor);

    document.getElementById('btnBuscarProv').addEventListener('click', cargarProveedores);
    document.getElementById('inputBuscarProv').addEventListener('keyup', e=>{ if(e.key==='Enter') cargarProveedores(); });
}

/* -------- LISTADO -------- */
async function cargarProveedores(){
    try{
        toggleSpinner(true);
        const res = await fetch(`${PROV_API}/proveedores`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        let provs = await res.json();
        const filtro = document.getElementById('inputBuscarProv').value.toLowerCase();
        if(filtro) provs = provs.filter(p=> p.nombre.toLowerCase().includes(filtro) || (p.ruc && p.ruc.toLowerCase().includes(filtro)));
        const tbody = document.getElementById('tablaProveedores');
        tbody.innerHTML='';
        provs.forEach(p=>{
            tbody.innerHTML += `<tr>
                <td>${p.id}</td>
                <td>${p.nombre}</td>
                <td>${p.ruc || '-'}</td>
                <td>${p.tipo || '-'}</td>
                <td>${crearBadgeEstado(p.estado,'estado')}</td>
                <td>${crearBadgeNivelRiesgo(p.nivel_riesgo)}</td>
                <td>${formatearFecha(p.fecha_registro)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${p.id}"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${p.id}"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>`;});
        tbody.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const id = btn.dataset.id;
                if(btn.dataset.action==='edit') editarProveedor(id);
                else eliminarProveedor(id);
            });
        });
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

/* -------- CRUD -------- */
function mostrarModalProveedor(datos=null){
    limpiarFormulario('formProveedor');
    document.getElementById('provId').value = ''; // Asegurarse de que el ID esté vacío para nuevos proveedores
    $('#modalProveedor').modal('show');
    if(datos){
        document.getElementById('tituloModalProv').textContent='Editar Proveedor';
        document.getElementById('provId').value = datos.id;
        rellenarFormulario('formProveedor', datos);
    }else{
        document.getElementById('tituloModalProv').textContent='Nuevo Proveedor';
    }
}

async function editarProveedor(id){
    try{
        const res = await fetch(`${PROV_API}/proveedores/${id}`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        const data = await res.json();
        mostrarModalProveedor(data);
    }catch(err){ manejarError(err);} }

async function guardarProveedor(){
    const datos = obtenerDatosFormulario('formProveedor');
    const id = datos.id;
    
    // Si el ID está vacío, asegurarse de eliminarlo para crear un nuevo proveedor
    if (!id || id.trim() === '') {
        delete datos.id;
    }
    
    const metodo = id && id.trim() !== '' ? 'PUT' : 'POST';
    const url = id && id.trim() !== '' ? `${PROV_API}/proveedores/${id}` : `${PROV_API}/proveedores`;
    
    try{
        toggleSpinner(true);
        const res = await fetch(url, {
            method: metodo, 
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            }, 
            body: JSON.stringify(datos)
        });
        
        const r = await res.json();
        if(!res.ok) throw new Error(r.error || 'Error al guardar proveedor');
        
        mostrarNotificacion(id && id.trim() !== '' ? 'Proveedor actualizado' : 'Nuevo proveedor creado');
        $('#modalProveedor').modal('hide');
        cargarProveedores();
    }catch(err){ 
        manejarError(err);
    }finally{ 
        toggleSpinner(false);
    } 
}

async function eliminarProveedor(id){
    if(!confirm('¿Eliminar proveedor?')) return;
    try{
        toggleSpinner(true);
        const res = await fetch(`${PROV_API}/proveedores/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${getToken()}`}});
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Proveedor eliminado','warning');
        cargarProveedores();
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

// Función para crear badges de nivel de riesgo
function crearBadgeNivelRiesgo(nivel) {
    if (!nivel) return '<span class="badge bg-secondary">No definido</span>';
    
    const clases = {
        'BAJO': 'bg-success',
        'MEDIO': 'bg-warning text-dark',
        'ALTO': 'bg-danger',
        'CRITICO': 'bg-dark'
    };
    
    const clase = clases[nivel] || 'bg-secondary';
    return `<span class="badge ${clase}">${nivel}</span>`;
}

window.cargarProveedores = cargarProveedores;
