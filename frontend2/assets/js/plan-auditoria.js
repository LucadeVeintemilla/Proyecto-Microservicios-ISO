// plan-auditoria.js – Gestión de planes de auditoría y listas de verificación
// Base URL del microservicio de auditorías
const SERVICE_AUDITORIAS_URL = 'http://localhost:5008';

// ---------- Selección de elementos DOM ----------
const tablaAuditorias          = document.getElementById('tablaAuditorias');
const btnNuevaAuditoria        = document.getElementById('btnNuevaAuditoria');
const modalAuditoria           = new bootstrap.Modal(document.getElementById('modalAuditoria'));
const formAuditoria            = document.getElementById('formAuditoria');
const btnGuardarAuditoria      = document.getElementById('btnGuardarAuditoria');
const inputBuscarAuditoria     = document.getElementById('inputBuscarAuditoria');
const btnBuscarAuditoria       = document.getElementById('btnBuscarAuditoria');

// Lista verificación
const modalLista               = new bootstrap.Modal(document.getElementById('modalListaVerificacion'));
const formLista                = document.getElementById('formListaVerificacion');
const btnAgregarLista          = document.getElementById('btnAgregarListaVerificacion');
const listasContainer          = document.getElementById('listasContainer');

let auditorias = [];           // cache local

// --------------- Inicio ---------------
document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAutenticacion()) return;
    actualizarUIUsuario();

    // Select2 para los select del modal auditoría
    $('.select2').select2({ dropdownParent: $('#modalAuditoria') });

    await cargarOpcionesAuditores();
    await cargarAuditorias();

    // Eventos UI
    btnNuevaAuditoria?.addEventListener('click', () => abrirModalAuditoria());
    btnGuardarAuditoria?.addEventListener('click', guardarAuditoria);
    btnBuscarAuditoria?.addEventListener('click', () => filtrarAuditorias(inputBuscarAuditoria.value));
    inputBuscarAuditoria?.addEventListener('keyup', e => { if (e.key === 'Enter') filtrarAuditorias(e.target.value); });

    // Listas de verificación
    btnAgregarLista?.addEventListener('click', guardarListaVerificacion);
});

// --------- Utilidades de petición ---------
async function api(url, opts = {}) {
    const res = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`,
            ...(opts.headers || {})
        },
        ...opts
    });
    if (!res.ok) throw new Error((await res.json()).error || 'Error en la petición');
    if (res.status !== 204) return res.json(); // 204 No Content
}

// --------- Carga de datos ---------
async function cargarAuditorias() {
    try {
        toggleSpinner(true);
        auditorias = await api(`${SERVICE_AUDITORIAS_URL}/auditorias`);
        renderTabla(auditorias);
    } catch (e) { manejarError(e); } finally { toggleSpinner(false); }
}

async function cargarOpcionesAuditores() {
    try {
        const usuarios = await api(`${SERVICE_AUDITORIAS_URL}/auditores`);
        const selectLider   = formAuditoria.elements['auditor_lider'];
        const selectEquipo  = formAuditoria.elements['equipo_auditores'];
        [selectLider, selectEquipo].forEach(sel => sel.innerHTML = '<option value="">Seleccione...</option>');
        usuarios.forEach(u => {
            const opt = `<option value="${u.id}">${u.nombre}</option>`;
            selectLider.insertAdjacentHTML('beforeend', opt);
            selectEquipo.insertAdjacentHTML('beforeend', opt);
        });
    } catch (e) { manejarError(e); }
}

// --------- Render Tabla ---------
function renderTabla(data) {
    tablaAuditorias.innerHTML = '';
    if (!data.length) {
        tablaAuditorias.innerHTML = '<tr><td colspan="8" class="text-center">Sin auditorías</td></tr>';
        return;
    }
    data.forEach(aud => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${aud.codigo}</td>
            <td>${aud.titulo}</td>
            <td>${aud.tipo}</td>
            <td>${crearBadgeEstado(aud.estado)}</td>
            <td>${formatearFecha(aud.fecha_inicio)}</td>
            <td>${formatearFecha(aud.fecha_fin)}</td>
            <td>${aud.auditor_lider_nombre || ''}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" data-edit="${aud.id}"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-outline-danger me-1" data-del="${aud.id}"><i class="fas fa-trash"></i></button>
                <button class="btn btn-sm btn-outline-secondary" data-lista="${aud.id}"><i class="fas fa-list"></i></button>
            </td>`;
        tablaAuditorias.appendChild(row);
    });

    // Delegación de eventos
    tablaAuditorias.querySelectorAll('[data-edit]').forEach(btn => btn.addEventListener('click', () => abrirModalAuditoria(btn.dataset.edit)));
    tablaAuditorias.querySelectorAll('[data-del]').forEach(btn => btn.addEventListener('click', () => eliminarAuditoria(btn.dataset.del)));
    tablaAuditorias.querySelectorAll('[data-lista]').forEach(btn => btn.addEventListener('click', () => abrirModalListas(btn.dataset.lista)));
}

function filtrarAuditorias(texto) {
    texto = texto.toLowerCase();
    const filtradas = auditorias.filter(a => a.titulo.toLowerCase().includes(texto) || a.codigo.toLowerCase().includes(texto));
    renderTabla(filtradas);
}

// --------- Modal Auditoría ---------
async function abrirModalAuditoria(id = null) {
    limpiarFormulario('formAuditoria');
    document.getElementById('tituloModalAuditoria').textContent = id ? 'Editar Auditoría' : 'Nueva Auditoría';
    if (id) {
        const aud = auditorias.find(a => a.id == id) || await api(`${SERVICE_AUDITORIAS_URL}/auditorias/${id}`);
        rellenarFormulario('formAuditoria', aud);
    }
    modalAuditoria.show();
}

async function guardarAuditoria() {
    if (!formAuditoria.checkValidity()) { formAuditoria.reportValidity(); return; }
    const datos = obtenerDatosFormulario('formAuditoria');

    try {
        toggleSpinner(true);
        const id = datos.id;
        const metodo = id ? 'PUT' : 'POST';
        const url = id ? `${SERVICE_AUDITORIAS_URL}/auditorias/${id}` : `${SERVICE_AUDITORIAS_URL}/auditorias`;
        await api(url, { method: metodo, body: JSON.stringify(datos) });
        mostrarNotificacion(`Auditoría ${id ? 'actualizada' : 'creada'} correctamente`);
        modalAuditoria.hide();
        await cargarAuditorias();
    } catch(e) { manejarError(e); } finally { toggleSpinner(false); }
}

async function eliminarAuditoria(id) {
    if (!confirm('¿Eliminar auditoría?')) return;
    try { await api(`${SERVICE_AUDITORIAS_URL}/auditorias/${id}`, { method: 'DELETE' }); mostrarNotificacion('Auditoría eliminada'); await cargarAuditorias(); } catch(e){ manejarError(e);} }

// --------- Listas de Verificación ---------
let auditoriaActualListas = null;
async function abrirModalListas(auditoriaId) {
    auditoriaActualListas = auditoriaId;
    formLista.elements['auditoria_id'].value = auditoriaId;
    await cargarListasAuditoria(auditoriaId);
    modalLista.show();
}

async function cargarListasAuditoria(auditoriaId) {
    try {
        toggleSpinner(true);
        const listas = await api(`${SERVICE_AUDITORIAS_URL}/auditorias/${auditoriaId}/listas-verificacion`);
        renderListas(listas);
    } catch(e){ manejarError(e);} finally{ toggleSpinner(false);} }

function renderListas(listas) {
    listasContainer.innerHTML = '';
    if (!listas.length) { listasContainer.innerHTML = '<p class="text-muted">Sin listas de verificación</p>'; return; }
    listas.forEach(l => {
        listasContainer.insertAdjacentHTML('beforeend', `
            <div class="border rounded p-2 mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${l.titulo}</strong><br>
                        <small class="text-muted">${l.descripcion || ''}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" data-del-lista="${l.id}"><i class="fas fa-trash"></i></button>
                </div>
            </div>`);
    });
    listasContainer.querySelectorAll('[data-del-lista]').forEach(btn => btn.addEventListener('click', () => eliminarLista(btn.dataset.delLista)));
}

async function guardarListaVerificacion() {
    if (!formLista.checkValidity()) { formLista.reportValidity(); return; }
    const datos = obtenerDatosFormulario('formListaVerificacion');
    try {
        await api(`${SERVICE_AUDITORIAS_URL}/auditorias/${auditoriaActualListas}/listas-verificacion`, { method: 'POST', body: JSON.stringify(datos) });
        mostrarNotificacion('Lista agregada');
        formLista.reset();
        await cargarListasAuditoria(auditoriaActualListas);
    } catch(e){ manejarError(e); }
}

async function eliminarLista(id) {
    if (!confirm('¿Eliminar lista?')) return;
    try { await api(`${SERVICE_AUDITORIAS_URL}/listas-verificacion/${id}`, { method: 'DELETE' }); mostrarNotificacion('Lista eliminada'); await cargarListasAuditoria(auditoriaActualListas);} catch(e){ manejarError(e);} }
