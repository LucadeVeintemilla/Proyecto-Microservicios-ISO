// documentacion.js - Gestión de Documentos SGSI
// Usa: auth.js, utility.js

const DOC_API = 'http://localhost:5003'; // microservicio documentación

document.addEventListener('DOMContentLoaded', () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();

    initEventos();
    cargarDocumentos();
});

function initEventos(){
    document.getElementById('btnNuevoDoc').addEventListener('click', ()=> mostrarModalDoc());
    document.getElementById('btnGuardarDoc').addEventListener('click', guardarDocumento);

    document.getElementById('btnBuscarDoc').addEventListener('click', cargarDocumentos);
    document.getElementById('inputBuscarDoc').addEventListener('keyup', e=>{ if(e.key==='Enter') cargarDocumentos(); });
}

/* ---------------- LISTADO ---------------- */
async function cargarDocumentos(){
    try{
        toggleSpinner(true);
        const res = await fetch(`${DOC_API}/documentos`, { headers:{'Authorization':`Bearer ${getToken()}`} });
        let docs = await res.json();
        const filtro = document.getElementById('inputBuscarDoc').value.toLowerCase();
        if(filtro) docs = docs.filter(d=> d.titulo.toLowerCase().includes(filtro)||d.codigo.toLowerCase().includes(filtro));

        const tbody = document.getElementById('tablaDocs');
        tbody.innerHTML='';
        docs.forEach(d=>{
            tbody.innerHTML += `<tr>
                <td>${d.id}</td>
                <td>${d.codigo}</td>
                <td>${d.titulo}</td>
                <td>${d.tipo}</td>
                <td>${crearBadgeEstado(d.estado,'estado')}</td>
                <td>${formatearFecha(d.fecha_modificacion,true)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${d.id}"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${d.id}"><i class="fas fa-trash-alt"></i></button>
                    <a class="btn btn-sm btn-outline-secondary" href="${d.ruta_archivo}" target="_blank"><i class="fas fa-download"></i></a>
                </td>
            </tr>`;});
        tbody.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const id=btn.dataset.id;
                if(btn.dataset.action==='edit') editarDocumento(id);
                else eliminarDocumento(id);
            });
        });
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

/* ---------------- CRUD ---------------- */
function mostrarModalDoc(datos=null){
    limpiarFormulario('formDoc');
    // Asegurarse de que el campo ID esté vacío al crear un nuevo documento
    document.getElementById('docId').value = '';
    $('#modalDoc').modal('show');
    if(datos){
        document.getElementById('tituloModalDoc').textContent='Editar Documento';
        rellenarFormulario('formDoc', datos);
    }else{
        document.getElementById('tituloModalDoc').textContent='Nuevo Documento';
    }
}

async function editarDocumento(id){
    try{
        const res = await fetch(`${DOC_API}/documentos/${id}`, { headers:{'Authorization':`Bearer ${getToken()}`} });
        const data = await res.json();
        mostrarModalDoc(data);
    }catch(err){ manejarError(err);} }

async function guardarDocumento(){
    const datos = obtenerDatosFormulario('formDoc');
    // Verificar si el ID está vacío o no
    const id = datos.id && datos.id.trim() !== '' ? datos.id : null;
    
    // Eliminar el ID de los datos para evitar problemas
    delete datos.id;
    
    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `${DOC_API}/documentos/${id}` : `${DOC_API}/documentos`;
    
    try{
        toggleSpinner(true);
        const res = await fetch(url, {
            method: metodo,
            headers:{'Content-Type':'application/json','Authorization':`Bearer ${getToken()}`},
            body: JSON.stringify(datos)
        });
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Documento guardado');
        $('#modalDoc').modal('hide');
        cargarDocumentos();
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

async function eliminarDocumento(id){
    if(!confirm('¿Eliminar documento?')) return;
    try{
        toggleSpinner(true);
        const res = await fetch(`${DOC_API}/documentos/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${getToken()}`}});
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Documento eliminado','warning');
        cargarDocumentos();
    }catch(err){ manejarError(err);}finally{ toggleSpinner(false);} }

// Exponer para pruebas
window.cargarDocumentos = cargarDocumentos;
