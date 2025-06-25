// roles.js - Lógica de negocio para roles.html

// Constantes de servicio (se usa la misma URL para roles, permisos y conflictos)
const ROLES_API_URL = SERVICE_ROLES_URL || 'http://localhost:5007';

// --- Inicialización de la página ---
document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();

    // Inicializar modales
    inicializarModalPermiso();

    // Cargar datos iniciales
    await Promise.all([
        cargarRoles(),
        cargarPermisos(),
        cargarConflictos(),
        cargarLogsAuditoria()
    ]);

    // Listeners generales
    document.getElementById('btnNuevoRol').addEventListener('click', () => mostrarModalRol());
    document.getElementById('btnGuardarRol').addEventListener('click', guardarRol);
    document.getElementById('btnBuscarRol').addEventListener('click', () => cargarRoles());
    document.getElementById('inputBuscarRol').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') cargarRoles();
    });

    // Conflictos
    document.getElementById('btnNuevoConflicto').addEventListener('click', () => mostrarModalConflicto());
    document.getElementById('btnGuardarConflicto').addEventListener('click', guardarConflicto);

    // Auditoría
    document.getElementById('btnFiltrarAuditoria').addEventListener('click', cargarLogsAuditoria);

    // Select2 inicial
    $("#rolA, #rolB").select2({ placeholder: 'Seleccione un rol', theme: 'bootstrap-5' });
});

// ---------------------- ROLES ---------------------- //
async function cargarRoles() {
    try {
        toggleSpinner(true);
        const filtro = document.getElementById('inputBuscarRol').value.trim().toLowerCase();
        const res = await fetch(`${ROLES_API_URL}/roles`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json();
        const tbody = document.getElementById('tablaRoles');
        tbody.innerHTML = '';

        data.filter(r => r.nombre.toLowerCase().includes(filtro)).forEach(rol => {
            tbody.innerHTML += `
                <tr>
                    <td>${rol.id}</td>
                    <td>${rol.nombre}</td>
                    <td>${rol.descripcion || ''}</td>
                    <td>${rol.es_predefinido ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>'}</td>
                    <td>${formatearFecha(rol.fecha_creacion, true)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${rol.id}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${rol.id}"><i class="fas fa-trash-alt"></i></button>
                    </td>
                </tr>`;
        });

        // Delegación de eventos en la tabla
        tbody.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                const action = e.currentTarget.dataset.action;
                if (action === 'edit') {
                    editarRol(id);
                } else if (action === 'delete') {
                    eliminarRol(id);
                }
            });
        });
    } catch (err) {
        manejarError(err);
    } finally {
        toggleSpinner(false);
    }
}

function mostrarModalRol(rol = null) {
    limpiarFormulario('formRol');
    $('#modalRol').modal('show');
    if (rol) {
        document.getElementById('tituloModalRol').textContent = 'Editar Rol';
        rellenarFormulario('formRol', {
            id: rol.id,
            nombre: rol.nombre,
            descripcion: rol.descripcion,
            es_predefinido: rol.es_predefinido
        });
        // Permisos seleccionados
        if (rol.permisos && Array.isArray(rol.permisos)) {
            const ids = rol.permisos.map(p => p.id.toString());
            $("#todos-permisos-list input[type='checkbox']").each(function () {
                this.checked = ids.includes(this.value);
            });
        }
    } else {
        document.getElementById('tituloModalRol').textContent = 'Nuevo Rol';
    }
}

async function editarRol(id) {
    try {
        const res = await fetch(`${ROLES_API_URL}/roles/${id}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const rol = await res.json();
        mostrarModalRol(rol);
    } catch (err) {
        manejarError(err);
    }
}

async function guardarRol() {
    const datos = obtenerDatosFormulario('formRol');
    const permisosSeleccionados = Array.from(document.querySelectorAll('#todos-permisos-list input[type="checkbox"]:checked')).map(c => parseInt(c.value));
    datos.permisos_ids = permisosSeleccionados;

    const id = datos.id;
    delete datos.id;

    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `${ROLES_API_URL}/roles/${id}` : `${ROLES_API_URL}/roles`;

    try {
        toggleSpinner(true);
        const res = await fetch(url, {
            method: metodo,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(datos)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar rol');

        mostrarNotificacion('Rol guardado correctamente');
        $('#modalRol').modal('hide');
        cargarRoles();
    } catch (err) {
        manejarError(err);
    } finally {
        toggleSpinner(false);
    }
}

async function eliminarRol(id) {
    if (!confirm('¿Seguro que desea eliminar este rol?')) return;
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/roles/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        // Verificar si la respuesta es exitosa sin intentar parsear JSON
        if (!res.ok) {
            throw new Error(`Error al eliminar rol: ${res.status} ${res.statusText}`);
        }
        
        mostrarNotificacion('Rol eliminado', 'warning');
        cargarRoles();
    } catch (err) {
        // Manejo personalizado del error para evitar problemas de JSON.parse
        console.error('Error:', err);
        mostrarNotificacion(err.message || 'Error al eliminar rol', 'danger');
    } finally {
        toggleSpinner(false);
    }
}

// ---------------------- PERMISOS ---------------------- //
// Modal de permiso
let modalPermiso;

// Inicializar modal de permiso
function inicializarModalPermiso() {
    if (!modalPermiso) {
        modalPermiso = new bootstrap.Modal(document.getElementById('modalPermiso'));
        
        // Configurar evento de guardar permiso
        document.getElementById('btnGuardarPermiso').addEventListener('click', guardarPermiso);
        
        // Configurar evento de nuevo permiso
        document.getElementById('btnNuevoPermiso').addEventListener('click', () => {
            document.getElementById('formPermiso').reset();
            document.getElementById('permisoId').value = '';
            document.getElementById('tituloModalPermiso').textContent = 'Nuevo Permiso';
            modalPermiso.show();
        });
    }
}

// Función para editar un permiso
async function editarPermiso(id) {
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/permisos/${id}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!res.ok) {
            throw new Error(`Error al cargar permiso: ${res.status} ${res.statusText}`);
        }
        
        const permiso = await res.json();
        
        // Llenar formulario
        document.getElementById('permisoId').value = permiso.id;
        document.getElementById('codigoPermiso').value = permiso.codigo || '';
        document.getElementById('nombrePermiso').value = permiso.nombre || '';
        document.getElementById('descripcionPermiso').value = permiso.descripcion || '';
        document.getElementById('moduloPermiso').value = permiso.modulo || '';
        document.getElementById('esCriticoPermiso').checked = permiso.es_critico || false;
        
        // Actualizar título y mostrar modal
        document.getElementById('tituloModalPermiso').textContent = 'Editar Permiso';
        modalPermiso.show();
    } catch (err) {
        console.error('Error en editarPermiso:', err);
        mostrarNotificacion(err.message || 'Error al cargar permiso', 'danger');
    } finally {
        toggleSpinner(false);
    }
}

// Función para guardar un permiso (crear o actualizar)
async function guardarPermiso() {
    try {
        toggleSpinner(true);
        
        // Obtener datos del formulario
        const permisoId = document.getElementById('permisoId').value;
        const formData = new FormData(document.getElementById('formPermiso'));
        const permisoData = {
            codigo: formData.get('codigo'),
            nombre: formData.get('nombre'),
            descripcion: formData.get('descripcion'),
            modulo: formData.get('modulo'),
            es_critico: formData.get('es_critico') === 'on'
        };
        
        // Validar campos requeridos
        if (!permisoData.codigo || !permisoData.nombre || !permisoData.modulo) {
            throw new Error('Por favor complete todos los campos requeridos');
        }
        
        // Determinar si es crear o actualizar
        const method = permisoId ? 'PUT' : 'POST';
        const url = permisoId ? `${ROLES_API_URL}/permisos/${permisoId}` : `${ROLES_API_URL}/permisos`;
        
        const res = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(permisoData)
        });
        
        if (!res.ok) {
            throw new Error(`Error al guardar permiso: ${res.status} ${res.statusText}`);
        }
        
        // Cerrar modal y recargar permisos
        modalPermiso.hide();
        await cargarPermisos();
        
        mostrarNotificacion(`Permiso ${permisoId ? 'actualizado' : 'creado'} correctamente`, 'success');
    } catch (err) {
        console.error('Error en guardarPermiso:', err);
        mostrarNotificacion(err.message || 'Error al guardar permiso', 'danger');
    } finally {
        toggleSpinner(false);
    }
}

// Función para eliminar un permiso
async function eliminarPermiso(id) {
    if (!confirm('¿Está seguro de eliminar este permiso? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/permisos/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!res.ok) {
            // Intentar obtener mensaje de error del servidor
            let errorMsg = `Error al eliminar permiso: ${res.status} ${res.statusText}`;
            try {
                const errorData = await res.json();
                if (errorData && errorData.error) {
                    errorMsg = errorData.error;
                }
            } catch (e) {
                // Si no se puede parsear la respuesta como JSON, usar el mensaje genérico
            }
            throw new Error(errorMsg);
        }
        
        // Recargar permisos
        await cargarPermisos();
        mostrarNotificacion('Permiso eliminado correctamente', 'success');
    } catch (err) {
        console.error('Error:', err);
        mostrarNotificacion(err.message || 'Error al eliminar permiso', 'danger');
    } finally {
        toggleSpinner(false);
    }
}

async function cargarPermisos() {
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/permisos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!res.ok) {
            throw new Error(`Error al cargar permisos: ${res.status} ${res.statusText}`);
        }
        
        const permisos = await res.json();
        console.log('Permisos cargados:', permisos);
        
        if (!Array.isArray(permisos)) {
            throw new Error('Formato de respuesta inválido: se esperaba un array de permisos');
        }
        
        // Cargar permisos en el modal de roles (para asignación)
        const contenedor = document.getElementById('todos-permisos-list');
        if (contenedor) {
            contenedor.innerHTML = '';
            permisos.forEach(p => {
                contenedor.innerHTML += `
                    <div class="form-check form-check-inline me-3 mb-2">
                        <input class="form-check-input" type="checkbox" id="perm-${p.id}" value="${p.id}">
                        <label class="form-check-label" for="perm-${p.id}">${p.nombre}</label>
                    </div>`;
            });

            // Check all
            const checkAllPermisos = document.getElementById('checkAllPermisos');
            if (checkAllPermisos) {
                // Eliminar listeners anteriores para evitar duplicados
                const newCheckAll = checkAllPermisos.cloneNode(true);
                checkAllPermisos.parentNode.replaceChild(newCheckAll, checkAllPermisos);
                
                newCheckAll.addEventListener('change', (e) => {
                    contenedor.querySelectorAll('input[type="checkbox"]').forEach(c => c.checked = e.target.checked);
                });
            }
        }
        
        // Cargar permisos en la tabla de permisos (pestaña Permisos)
        const tablaPermisos = document.getElementById('tablaPermisos');
        if (tablaPermisos) {
            const selectModulo = document.getElementById('selectModuloPermiso');
            const inputBuscar = document.getElementById('inputBuscarPermiso');
            
            const filtro = selectModulo ? selectModulo.value : '';
            const busqueda = inputBuscar ? inputBuscar.value.trim().toLowerCase() : '';
            
            // Extraer módulos únicos para el filtro
            if (selectModulo && !selectModulo.options.length) {
                const modulos = [...new Set(permisos.map(p => p.modulo).filter(m => m))];
                selectModulo.innerHTML = '<option value="">Todos los módulos</option>';
                modulos.forEach(modulo => {
                    selectModulo.innerHTML += `<option value="${modulo}">${modulo}</option>`;
                });
            }
            
            const permisosTabla = permisos.filter(p => {
                const moduloMatch = !filtro || (p.modulo && p.modulo.toLowerCase() === filtro.toLowerCase());
                const busquedaMatch = !busqueda || 
                    (p.nombre && p.nombre.toLowerCase().includes(busqueda)) || 
                    (p.codigo && p.codigo.toLowerCase().includes(busqueda)) || 
                    (p.descripcion && p.descripcion.toLowerCase().includes(busqueda));
                return moduloMatch && busquedaMatch;
            });
            
            tablaPermisos.innerHTML = '';
            
            if (permisosTabla.length === 0) {
                tablaPermisos.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">No se encontraron permisos</td>
                    </tr>`;
            } else {
                permisosTabla.forEach(p => {
                    tablaPermisos.innerHTML += `
                        <tr>
                            <td>${p.id || ''}</td>
                            <td>${p.codigo || ''}</td>
                            <td>${p.nombre || ''}</td>
                            <td>${p.descripcion || ''}</td>
                            <td>${p.modulo || ''}</td>
                            <td>${p.es_critico ? '<i class="fas fa-check text-danger"></i>' : '<i class="fas fa-times text-secondary"></i>'}</td>
                            <td>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-sm btn-outline-primary" onclick="editarPermiso(${p.id})">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="eliminarPermiso(${p.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>`;
                });
            }
            
            // Agregar listeners para filtrado de permisos
            if (selectModulo) {
                // Eliminar listeners anteriores para evitar duplicados
                const newSelectModulo = selectModulo.cloneNode(true);
                selectModulo.parentNode.replaceChild(newSelectModulo, selectModulo);
                newSelectModulo.addEventListener('change', cargarPermisos);
            }
            
            const btnBuscar = document.getElementById('btnBuscarPermiso');
            if (btnBuscar) {
                // Eliminar listeners anteriores para evitar duplicados
                const newBtnBuscar = btnBuscar.cloneNode(true);
                btnBuscar.parentNode.replaceChild(newBtnBuscar, btnBuscar);
                newBtnBuscar.addEventListener('click', cargarPermisos);
            }
            
            if (inputBuscar) {
                // Eliminar listeners anteriores para evitar duplicados
                const newInputBuscar = inputBuscar.cloneNode(true);
                inputBuscar.parentNode.replaceChild(newInputBuscar, inputBuscar);
                newInputBuscar.addEventListener('keyup', (e) => {
                    if (e.key === 'Enter') cargarPermisos();
                });
            }
        }
    } catch (err) {
        console.error('Error en cargarPermisos:', err);
        mostrarNotificacion(err.message || 'Error al cargar permisos', 'danger');
    } finally {
        toggleSpinner(false);
    }
}

// ---------------------- CONFLICTOS ---------------------- //
async function cargarConflictos() {
    try {
        const res = await fetch(`${ROLES_API_URL}/conflictos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const conflictos = await res.json();
        const tbody = document.getElementById('tablaConflictos');
        tbody.innerHTML = '';

        conflictos.forEach(c => {
            tbody.innerHTML += `
                <tr>
                    <td>${c.id}</td>
                    <td>${c.rol_a?.nombre || ''}</td>
                    <td>${c.rol_b?.nombre || ''}</td>
                    <td>${c.descripcion}</td>
                    <td>${formatearFecha(c.fecha_creacion, true)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" data-id="${c.id}"><i class="fas fa-trash-alt"></i></button>
                    </td>
                </tr>`;
        });

        tbody.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', () => eliminarConflicto(btn.dataset.id));
        });

        // Poblar selects en modal conflicto
        const options = conflictos.reduce((set, c) => {
            set.add(c.rol_a?.id);
            set.add(c.rol_b?.id);
            return set;
        }, new Set());
        await cargarRolesSelect(Array.from(options));
    } catch (err) {
        manejarError(err);
    }
}

async function cargarRolesSelect(preselect = []) {
    try {
        const res = await fetch(`${ROLES_API_URL}/roles`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
        const roles = await res.json();
        const selectA = document.getElementById('rolA');
        const selectB = document.getElementById('rolB');
        [selectA, selectB].forEach(sel => sel.innerHTML = '<option value="">Seleccione un rol</option>');
        roles.forEach(r => {
            const opt = `<option value="${r.id}">${r.nombre}</option>`;
            selectA.insertAdjacentHTML('beforeend', opt);
            selectB.insertAdjacentHTML('beforeend', opt);
        });
        // Select2 refresh
        $(selectA).trigger('change');
        $(selectB).trigger('change');
        preselect.forEach(id => {
            $(`#rolA option[value='${id}'], #rolB option[value='${id}']`).prop('selected', true);
        });
    } catch (err) {
        manejarError(err);
    }
}

function mostrarModalConflicto() {
    limpiarFormulario('formConflicto');
    cargarRolesSelect();
    $('#modalConflicto').modal('show');
}

async function guardarConflicto() {
    const datos = obtenerDatosFormulario('formConflicto');
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/conflictos-segregacion`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(datos)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al registrar conflicto');
        mostrarNotificacion('Conflicto registrado');
        $('#modalConflicto').modal('hide');
        cargarConflictos();
    } catch (err) {
        manejarError(err);
    } finally {
        toggleSpinner(false);
    }
}

async function eliminarConflicto(id) {
    if (!confirm('¿Eliminar este conflicto?')) return;
    try {
        toggleSpinner(true);
        const res = await fetch(`${ROLES_API_URL}/conflictos-segregacion/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al eliminar conflicto');
        mostrarNotificacion('Conflicto eliminado', 'warning');
        cargarConflictos();
    } catch (err) {
        manejarError(err);
    } finally {
        toggleSpinner(false);
    }
}

// ---------------------- AUDITORÍA ---------------------- //
async function cargarLogsAuditoria() {
    const fecha = document.getElementById('fechaAuditoria').value;
    const params = fecha ? `?fecha=${fecha}` : '';
    try {
        const res = await fetch(`${ROLES_API_URL}/auditoria${params}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const logs = await res.json();
        const tbody = document.getElementById('tablaAuditoria');
        tbody.innerHTML = '';
        logs.forEach(l => {
            tbody.innerHTML += `
                <tr>
                    <td></td>
                    <td>${l.usuario}</td>
                    <td>${formatearFecha(l.fecha_hora, true)}</td>
                    <td>${l.accion}</td>
                    <td>${l.modulo || ''}</td>
                    <td>${l.entidad || ''}</td>
                    <td>${l.detalles}</td>
                    <td>${l.ip_address || ''}</td>
                </tr>`;
        });
    } catch (err) {
        manejarError(err);
    }
}

// Exportar funciones (opcional para depuración)
window.cargarRoles = cargarRoles;
