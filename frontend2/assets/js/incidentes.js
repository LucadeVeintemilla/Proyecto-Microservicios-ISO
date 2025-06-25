// incidentes.js - Gestión Incidentes SGSI
// Requiere auth.js y utility.js

const INC_API = 'http://localhost:5005';

document.addEventListener('DOMContentLoaded', ()=>{
    if(!verificarAutenticacion()) return;
    actualizarUIUsuario();

    initEventos();
    cargarIncidentes();
});

function initEventos(){
    document.getElementById('btnNuevoInc').addEventListener('click', ()=> mostrarModalIncidente());
    document.getElementById('btnGuardarInc').addEventListener('click', guardarIncidente);

    document.getElementById('btnBuscarInc').addEventListener('click', cargarIncidentes);
    document.getElementById('inputBuscarInc').addEventListener('keyup', e=>{ if(e.key==='Enter') cargarIncidentes(); });
}

/* ---------- LISTADO ---------- */
async function cargarIncidentes(){
    try{
        toggleSpinner(true);
        const res = await fetch(`${INC_API}/incidentes`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        
        if(!res.ok) {
            let errorMsg = 'Error al cargar incidentes';
            try {
                const errorText = await res.text();
                if(errorText) {
                    const errorJson = JSON.parse(errorText);
                    errorMsg = errorJson.error || errorMsg;
                }
            } catch(e) {}
            throw new Error(errorMsg);
        }
        
        const text = await res.text();
        if(!text || !text.trim()) {
            throw new Error('No se recibieron datos del servidor');
        }
        
        let incs;
        try {
            incs = JSON.parse(text);
        } catch(parseError) {
            console.error('Error al parsear JSON de incidentes:', parseError);
            throw new Error('Error al procesar datos de incidentes');
        }
        
        const filtro = document.getElementById('inputBuscarInc').value.toLowerCase();
        if(filtro) incs = incs.filter(i=> i.titulo.toLowerCase().includes(filtro));
        const tbody = document.getElementById('tablaIncidentes');
        tbody.innerHTML='';
        incs.forEach(i=>{
            tbody.innerHTML += `<tr>
                <td>${i.id}</td>
                <td>${i.titulo}</td>
                <td>${crearBadgeEstado(i.severidad,'severidad')}</td>
                <td>${crearBadgeEstado(i.estado,'estado')}</td>
                <td>${formatearFecha(i.fecha_reporte,true)}</td>
                <td>${formatearFecha(i.fecha_cierre,true)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${i.id}"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${i.id}"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>`});
        tbody.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click',()=>{
                const id=btn.dataset.id;
                if(btn.dataset.action==='edit') editarIncidente(id);
                else eliminarIncidente(id);
            });
        });
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

/* ---------- CRUD ---------- */
function mostrarModalIncidente(datos=null){
    limpiarFormulario('formIncidente');
    $('#modalIncidente').modal('show');
    
    // Asegurarse de que el campo id esté vacío para nuevos incidentes
    const idField = document.createElement('input');
    idField.type = 'hidden';
    idField.name = 'id';
    
    // Eliminar cualquier campo id existente para evitar duplicados
    const existingIdField = document.querySelector('#formIncidente [name="id"]');
    if (existingIdField) {
        existingIdField.remove();
    }
    
    // Añadir el campo id al formulario
    document.getElementById('formIncidente').appendChild(idField);
    
    if(datos){
        document.getElementById('tituloModalInc').textContent='Editar Incidente';
        
        // Establecer el ID para edición
        idField.value = datos.id;
        console.log('ID del incidente a editar:', datos.id);
        
        // Manejar las fechas antes de rellenar el formulario
        const datosProcesados = {...datos};
        
        // Convertir fechas ISO a formato local para datetime-local
        if(datos.fecha_reporte){
            try {
                // Asegurar que la fecha tenga el formato correcto para datetime-local
                const fecha = new Date(datos.fecha_reporte);
                if(!isNaN(fecha.getTime())) {
                    // Formato YYYY-MM-DDThh:mm
                    const fechaLocal = fecha.toISOString().slice(0, 16);
                    datosProcesados.fecha_reporte = fechaLocal;
                    console.log('Fecha reporte procesada:', fechaLocal);
                }
            } catch(e) {
                console.error('Error al procesar fecha_reporte:', e);
            }
        }
        
        if(datos.fecha_cierre){
            try {
                const fecha = new Date(datos.fecha_cierre);
                if(!isNaN(fecha.getTime())) {
                    const fechaLocal = fecha.toISOString().slice(0, 16);
                    datosProcesados.fecha_cierre = fechaLocal;
                    console.log('Fecha cierre procesada:', fechaLocal);
                }
            } catch(e) {
                console.error('Error al procesar fecha_cierre:', e);
            }
        }
        
        // Rellenar el formulario con los datos procesados
        rellenarFormulario('formIncidente', datosProcesados);
        
        // Verificar que las fechas se hayan establecido correctamente
        console.log('Valor campo fecha_reporte:', document.querySelector('[name="fecha_reporte"]').value);
        console.log('Valor campo fecha_cierre:', document.querySelector('[name="fecha_cierre"]').value);
    } else {
        document.getElementById('tituloModalInc').textContent='Nuevo Incidente';
        // Para nuevo incidente, establecer fecha actual como fecha de reporte
        const ahora = new Date();
        const fechaLocal = ahora.toISOString().slice(0, 16);
        document.querySelector('[name="fecha_reporte"]').value = fechaLocal;
        
        // Asegurarse de que el ID esté vacío para nuevos incidentes
        idField.value = '';
    }
}

async function editarIncidente(id){
    try{
        toggleSpinner(true);
        const res = await fetch(`${INC_API}/incidentes/${id}`, {headers:{'Authorization':`Bearer ${getToken()}`}});
        
        let responseText = await res.text();
        console.log('Respuesta del servidor (editar):', responseText);
        
        if(!res.ok) {
            // Intentar obtener mensaje de error
            let errorMsg = 'Error al obtener el incidente';
            try {
                if(responseText && responseText.trim()) {
                    // Verificar si la respuesta es HTML (error 500)
                    if(responseText.includes('<!doctype') || responseText.includes('<html')) {
                        errorMsg = 'Error interno del servidor';
                    } else {
                        const errorJson = JSON.parse(responseText);
                        errorMsg = errorJson.error || errorMsg;
                    }
                }
            } catch(e) {
                console.error('Error al parsear respuesta de error:', e);
            }
            throw new Error(errorMsg);
        }
        
        // Solo intentar parsear JSON si la respuesta fue exitosa
        let data = {};
        if(responseText && responseText.trim()) {
            try {
                if(!responseText.includes('<!doctype') && !responseText.includes('<html')) {
                    data = JSON.parse(responseText);
                    console.log('Datos del incidente:', data);
                }
            } catch (parseError) {
                console.error('Error al parsear respuesta JSON:', parseError);
                throw new Error('Error al procesar la respuesta del servidor');
            }
        }
        
        mostrarModalIncidente(data);
    }catch(err){
        manejarError(err);
    }finally{
        toggleSpinner(false);
    } }

async function guardarIncidente(){
    const datos = obtenerDatosFormulario('formIncidente');
    
    // Obtener el ID del campo oculto
    const idField = document.querySelector('#formIncidente [name="id"]');
    const id = idField && idField.value ? idField.value : null;
    console.log('ID del incidente a guardar:', id);
    
    // Verificar campos requeridos
    const camposRequeridos = ['titulo', 'categoria', 'severidad', 'prioridad'];
    const camposFaltantes = camposRequeridos.filter(campo => !datos[campo]);
    
    if (camposFaltantes.length > 0) {
        mostrarNotificacion(`Campos requeridos faltantes: ${camposFaltantes.join(', ')}`, 'danger');
        return;
    }
    
    // Convertir datetime-local a ISO
    if(datos.fecha_reporte) {
        try {
            datos.fecha_reporte = new Date(datos.fecha_reporte).toISOString();
            console.log('Fecha reporte convertida:', datos.fecha_reporte);
        } catch(e) {
            console.error('Error al convertir fecha_reporte:', e);
            mostrarNotificacion('Formato de fecha inválido', 'danger');
            return;
        }
    }
    
    if(datos.fecha_cierre) {
        try {
            datos.fecha_cierre = new Date(datos.fecha_cierre).toISOString();
            console.log('Fecha cierre convertida:', datos.fecha_cierre);
        } catch(e) {
            console.error('Error al convertir fecha_cierre:', e);
            mostrarNotificacion('Formato de fecha inválido', 'danger');
            return;
        }
    }

    console.log('Datos a enviar:', datos);
    
    const metodo = id? 'PUT':'POST';
    const url = id? `${INC_API}/incidentes/${id}` : `${INC_API}/incidentes`;
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
        
        let responseText = await res.text();
        console.log('Respuesta del servidor:', responseText);
        
        if(!res.ok) {
            // Intentar obtener mensaje de error
            let errorMsg = 'Error en la operación';
            try {
                if(responseText && responseText.trim()) {
                    // Verificar si la respuesta es HTML (error 500)
                    if(responseText.includes('<!doctype') || responseText.includes('<html')) {
                        errorMsg = 'Error interno del servidor';
                    } else {
                        const errorJson = JSON.parse(responseText);
                        errorMsg = errorJson.error || errorMsg;
                    }
                }
            } catch(e) {
                console.error('Error al parsear respuesta de error:', e);
            }
            throw new Error(errorMsg);
        }
        
        // Solo intentar parsear JSON si la respuesta fue exitosa y parece JSON
        let r = {};
        if(responseText && responseText.trim()) {
            try {
                if(!responseText.includes('<!doctype') && !responseText.includes('<html')) {
                    r = JSON.parse(responseText);
                }
            } catch (parseError) {
                console.warn('Respuesta no es JSON válido, pero la operación fue exitosa');
            }
        }
        
        mostrarNotificacion('Incidente guardado');
        $('#modalIncidente').modal('hide');
        cargarIncidentes();
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

async function eliminarIncidente(id){
    if(!confirm('¿Eliminar incidente?')) return;
    try{
        toggleSpinner(true);
        const res = await fetch(`${INC_API}/incidentes/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${getToken()}`}});
        const r = await res.json();
        if(!res.ok) throw new Error(r.error||'Error');
        mostrarNotificacion('Incidente eliminado','warning');
        cargarIncidentes();
    }catch(err){manejarError(err);}finally{toggleSpinner(false);} }

window.cargarIncidentes = cargarIncidentes;
