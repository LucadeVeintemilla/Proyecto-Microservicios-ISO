// utility.js - Funciones de utilidad general para la aplicación

// Función para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo = 'success') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const newContainer = document.createElement('div');
        newContainer.className = 'toast-container';
        document.body.appendChild(newContainer);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast show bg-${tipo} text-white`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${tipo === 'success' ? 'Éxito' : tipo === 'warning' ? 'Advertencia' : 'Error'}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${mensaje}
        </div>
    `;
    
    document.querySelector('.toast-container').appendChild(toast);
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Función para manejar errores de API
function manejarError(error) {
    console.error('Error:', error);
    let mensaje = 'Error en la operación';
    
    if (error.response) {
        mensaje = error.response.data.error || mensaje;
    } else if (error.message) {
        mensaje = error.message;
    }
    
    mostrarNotificacion(mensaje, 'danger');
}

// Función para mostrar/ocultar indicador de carga
function toggleSpinner(show = true) {
    let spinner = document.querySelector('.spinner-overlay');
    
    if (show && !spinner) {
        spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `<div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Cargando...</span>
        </div>`;
        document.body.appendChild(spinner);
    } else if (!show && spinner) {
        spinner.remove();
    }
}

// Función para formatear fechas
function formatearFecha(fecha, incluirHora = false) {
    if (!fecha) return '';
    
    const date = new Date(fecha);
    
    if (isNaN(date.getTime())) {
        return '';
    }
    
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...(incluirHora ? { hour: '2-digit', minute: '2-digit' } : {})
    };
    
    return date.toLocaleDateString('es-ES', options);
}

// Función para crear un badge con estado
function crearBadgeEstado(estado, tipo = 'estado') {
    let className, text;
    
    if (tipo === 'estado') {
        switch (estado?.toUpperCase()) {
            case 'PENDIENTE':
                className = 'badge-pending';
                text = 'Pendiente';
                break;
            case 'PLANIFICADA':
                className = 'badge-pending';
                text = 'Planificada';
                break;
            case 'EN_PROCESO':
            case 'EN_ANALISIS':
            case 'EN_EJECUCION':
                className = 'badge-in-process';
                text = 'En ejecución';
                break;
            case 'COMPLETADO':
            case 'RESUELTO':
            case 'FINALIZADA':
                className = 'badge-completed';
                text = 'Finalizada';
                break;
            case 'IDENTIFICADO':
                className = 'badge-identified';
                text = 'Identificado';
                break;
            case 'MITIGADO':
                className = 'badge-mitigated';
                text = 'Mitigado';
                break;
            case 'CANCELADA':
                className = 'badge-danger';
                text = 'Cancelada';
                break;
            default:
                className = 'bg-secondary';
                text = estado || 'Desconocido';
        }
    } else if (tipo === 'prioridad' || tipo === 'severidad' || tipo === 'impacto') {
        switch (estado?.toUpperCase()) {
            case 'ALTA':
            case 'CRITICO':
                className = 'badge-high';
                text = estado;
                break;
            case 'MEDIA':
            case 'MODERADO':
                className = 'badge-medium';
                text = estado;
                break;
            case 'BAJA':
                className = 'badge-low';
                text = estado;
                break;
            default:
                className = 'bg-secondary';
                text = estado || 'Desconocido';
        }
    }
    
    return `<span class="badge ${className}">${text}</span>`;
}

// Función para limpiar formularios
function limpiarFormulario(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        
        // Limpiar selects con Select2 si existen
        form.querySelectorAll('select').forEach(select => {
            if (select.classList.contains('select2-hidden-accessible')) {
                $(select).val(null).trigger('change');
            }
        });
    }
}

// Función para rellenar un formulario con datos
function rellenarFormulario(formId, datos) {
    const form = document.getElementById(formId);
    if (!form || !datos) return;
    
    Object.keys(datos).forEach(key => {
        const input = form.elements[key];
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = Boolean(datos[key]);
            } else if (input.type === 'date' && datos[key]) {
                // Convertir a formato YYYY-MM-DD para inputs de tipo date
                const fecha = new Date(datos[key]);
                if (!isNaN(fecha.getTime())) {
                    input.value = fecha.toISOString().split('T')[0];
                }
            } else if (input.tagName === 'SELECT' && input.multiple) {
                // Manejar select múltiple
                if (Array.isArray(datos[key])) {
                    $(input).val(datos[key]).trigger('change');
                }
            } else if (input.tagName === 'SELECT') {
                // Comprobar si es un select2
                if ($(input).hasClass('select2-hidden-accessible')) {
                    $(input).val(datos[key]).trigger('change');
                } else {
                    input.value = datos[key] || '';
                }
            } else {
                input.value = datos[key] || '';
            }
        }
    });
}

// Función para obtener datos de un formulario como objeto
function obtenerDatosFormulario(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const formData = new FormData(form);
    const datos = {};
    
    for (const [key, value] of formData.entries()) {
        // Manejar checkboxes
        if (form.elements[key].type === 'checkbox') {
            datos[key] = form.elements[key].checked;
        } else {
            datos[key] = value;
        }
    }
    
    // Manejar selects múltiples que no son capturados bien por FormData
    form.querySelectorAll('select[multiple]').forEach(select => {
        datos[select.name] = Array.from(select.selectedOptions).map(option => option.value);
    });
    
    return datos;
}

// Exportar funciones
window.mostrarNotificacion = mostrarNotificacion;
window.manejarError = manejarError;
window.toggleSpinner = toggleSpinner;
window.formatearFecha = formatearFecha;
window.crearBadgeEstado = crearBadgeEstado;
window.limpiarFormulario = limpiarFormulario;
window.rellenarFormulario = rellenarFormulario;
window.obtenerDatosFormulario = obtenerDatosFormulario;
