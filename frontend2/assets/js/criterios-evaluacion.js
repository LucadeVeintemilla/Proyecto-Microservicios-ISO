// criterios-evaluacion.js - Manejo de criterios de evaluación para proveedores

// URL del servicio de proveedores
const SERVICE_PROVEEDORES_URL = 'http://localhost:5006';

// Elementos del DOM
const tablaCriterios = document.getElementById('tablaCriterios');
const btnNuevoCriterio = document.getElementById('btnNuevoCriterio');
const modalCriterio = document.getElementById('modalCriterio');
const formCriterio = document.getElementById('formCriterio');
const btnGuardarCriterio = document.getElementById('btnGuardarCriterio');
const inputBuscarCriterio = document.getElementById('inputBuscarCriterio');
const btnBuscarCriterio = document.getElementById('btnBuscarCriterio');

// Instancia Bootstrap del modal
let criterioModal;

// Variables para seguimiento
let criterios = [];
let criterioEditando = null;

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    // Verificar autenticación
    if (!verificarAutenticacion()) return;
    
    // Actualizar UI con datos del usuario
    actualizarUIUsuario();
    
    // Inicializar el modal
    criterioModal = new bootstrap.Modal(modalCriterio);
    
    // Cargar criterios
    cargarCriterios();
    
    // Configurar eventos
    btnNuevoCriterio.addEventListener('click', abrirModalNuevoCriterio);
    btnGuardarCriterio.addEventListener('click', guardarCriterio);
    btnBuscarCriterio.addEventListener('click', () => buscarCriterios(inputBuscarCriterio.value));
    inputBuscarCriterio.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') buscarCriterios(inputBuscarCriterio.value);
    });
});

// Función para cargar criterios
async function cargarCriterios() {
    try {
        mostrarSpinner();
        
        const response = await fetch(`${SERVICE_PROVEEDORES_URL}/criterios-evaluacion`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar criterios');
        
        criterios = await response.json();
        renderizarTablaCriterios(criterios);
    } catch (error) {
        mostrarToast('Error: ' + error.message, 'danger');
        console.error('Error al cargar criterios:', error);
    } finally {
        ocultarSpinner();
    }
}

// Función para buscar criterios
function buscarCriterios(query) {
    query = query.toLowerCase();
    const criteriosFiltrados = criterios.filter(c => 
        c.nombre.toLowerCase().includes(query) || 
        c.categoria.toLowerCase().includes(query) ||
        (c.descripcion && c.descripcion.toLowerCase().includes(query))
    );
    renderizarTablaCriterios(criteriosFiltrados);
}

// Función para renderizar tabla de criterios
function renderizarTablaCriterios(datos) {
    tablaCriterios.innerHTML = '';
    
    if (datos.length === 0) {
        tablaCriterios.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No se encontraron criterios de evaluación</td>
            </tr>
        `;
        return;
    }
    
    datos.forEach(criterio => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${criterio.id}</td>
            <td>${criterio.nombre}</td>
            <td>${criterio.categoria}</td>
            <td>${criterio.peso}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary btn-editar" data-id="${criterio.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-eliminar" data-id="${criterio.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tablaCriterios.appendChild(row);
        
        // Agregar eventos a los botones
        row.querySelector('.btn-editar').addEventListener('click', () => abrirModalEditarCriterio(criterio.id));
        row.querySelector('.btn-eliminar').addEventListener('click', () => confirmarEliminarCriterio(criterio.id));
    });
}

// Función para abrir modal de nuevo criterio
function abrirModalNuevoCriterio() {
    formCriterio.reset();
    document.getElementById('criterioId').value = '';
    document.getElementById('tituloModalCriterio').textContent = 'Nuevo Criterio';
    criterioEditando = null;
    criterioModal.show();
}

// Función para abrir modal de editar criterio
function abrirModalEditarCriterio(id) {
    const criterio = criterios.find(c => c.id === id);
    if (!criterio) {
        mostrarToast('Criterio no encontrado', 'danger');
        return;
    }
    
    formCriterio.reset();
    document.getElementById('criterioId').value = criterio.id;
    document.getElementById('tituloModalCriterio').textContent = 'Editar Criterio';
    
    // Llenar formulario
    formCriterio.elements['nombre'].value = criterio.nombre;
    formCriterio.elements['categoria'].value = criterio.categoria;
    formCriterio.elements['descripcion'].value = criterio.descripcion || '';
    formCriterio.elements['peso'].value = criterio.peso;
    
    criterioEditando = criterio;
    criterioModal.show();
}

// Función para guardar criterio (crear o editar)
async function guardarCriterio() {
    try {
        if (!formCriterio.checkValidity()) {
            formCriterio.reportValidity();
            return;
        }
        
        const criterioData = {
            nombre: formCriterio.elements['nombre'].value,
            categoria: formCriterio.elements['categoria'].value,
            descripcion: formCriterio.elements['descripcion'].value,
            peso: parseFloat(formCriterio.elements['peso'].value)
        };
        
        mostrarSpinner();
        
        const criterioId = document.getElementById('criterioId').value;
        let url = `${SERVICE_PROVEEDORES_URL}/criterios-evaluacion`;
        let method = 'POST';
        
        if (criterioId) {
            url += `/${criterioId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(criterioData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al guardar criterio');
        }
        
        mostrarToast(`Criterio ${criterioId ? 'actualizado' : 'creado'} correctamente`, 'success');
        criterioModal.hide();
        cargarCriterios();
    } catch (error) {
        mostrarToast('Error: ' + error.message, 'danger');
        console.error('Error al guardar criterio:', error);
    } finally {
        ocultarSpinner();
    }
}

// Función para confirmar eliminación de criterio
function confirmarEliminarCriterio(id) {
    if (confirm('¿Está seguro de eliminar este criterio? Esta acción no se puede deshacer.')) {
        eliminarCriterio(id);
    }
}

// Función para eliminar criterio
async function eliminarCriterio(id) {
    try {
        mostrarSpinner();
        
        const response = await fetch(`${SERVICE_PROVEEDORES_URL}/criterios-evaluacion/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) throw new Error('Error al eliminar criterio');
        
        mostrarToast('Criterio eliminado correctamente', 'success');
        cargarCriterios();
    } catch (error) {
        mostrarToast('Error: ' + error.message, 'danger');
        console.error('Error al eliminar criterio:', error);
    } finally {
        ocultarSpinner();
    }
}

// Funciones auxiliares
function mostrarSpinner() {
    const spinnerHtml = `
        <div class="spinner-overlay" id="spinnerOverlay">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    
    if (!document.getElementById('spinnerOverlay')) {
        document.body.insertAdjacentHTML('beforeend', spinnerHtml);
    }
}

function ocultarSpinner() {
    const spinner = document.getElementById('spinnerOverlay');
    if (spinner) {
        spinner.remove();
    }
}

function mostrarToast(mensaje, tipo = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${mensaje}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Auto eliminar después de ocultarse
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
