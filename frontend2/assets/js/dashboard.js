// dashboard.js - Funcionalidades para la página de inicio/dashboard

// URLs de servicios
const SERVICE_RIESGOS_URL = 'http://localhost:5002';
const SERVICE_INCIDENTES_URL = 'http://localhost:5005';
const SERVICE_AUDITORIAS_URL = 'http://localhost:5004';
const SERVICE_DOCUMENTACION_URL = 'http://localhost:5003';

// Variables para almacenar datos y gráficos
let riesgosChart = null;
let incidentesChart = null;
let auditoriasChart = null;
let documentosChart = null;

// Función para ajustar la visualización de los paneles según el tamaño de la ventana
function ajustarPaneles() {
    const anchoPantalla = window.innerWidth;
    const paneles = document.querySelectorAll('.card');
    
    if (anchoPantalla < 768) { // Dispositivos móviles
        paneles.forEach(panel => {
            panel.classList.add('mb-4');
        });
    } else {
        paneles.forEach(panel => {
            panel.classList.remove('mb-4');
        });
    }
    
    // Ajustar altura de las listas para mantener consistencia
    const listasItems = document.querySelectorAll('.list-group');
    listasItems.forEach(lista => {
        const contenedor = lista.closest('.card-body');
        if (contenedor) {
            const alturaDisponible = contenedor.clientHeight - 40; // Restar espacio para título
            lista.style.maxHeight = `${alturaDisponible}px`;
            lista.style.overflowY = 'auto';
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    // Verificar autenticación
    if (!verificarAutenticacion()) return;
    
    // Actualizar UI con información del usuario
    actualizarUIUsuario();
    
    try {
        toggleSpinner(true);
        
        // Cargar datos para el dashboard
        await Promise.all([
            cargarContadores(),
            cargarResumenRiesgos(),
            cargarIncidentesRecientes(),
            cargarProximasAuditorias(),
            cargarDocumentosRecientes()
        ]);
        
        toggleSpinner(false);
    } catch (error) {
        toggleSpinner(false);
        console.error('Error cargando datos del dashboard:', error);
        mostrarNotificacion('Error al cargar los datos del dashboard', 'danger');
    }

    // Detectar y actualizar el contenido del dashboard según el tamaño de la ventana
    window.addEventListener('resize', ajustarPaneles);
    ajustarPaneles();
    
    // Configurar actualización automática cada 5 minutos
    setInterval(async () => {
        try {
            await Promise.all([
                cargarContadores(),
                cargarResumenRiesgos(),
                cargarIncidentesRecientes(),
                cargarProximasAuditorias(),
                cargarDocumentosRecientes()
            ]);
        } catch (error) {
            console.error('Error en actualización automática:', error);
        }
    }, 300000); // 5 minutos
});

// Función para cargar los contadores de los diferentes módulos
async function cargarContadores() {
    try {
        // Cargar contador de riesgos
        const responseRiesgos = await fetch(`${SERVICE_RIESGOS_URL}/riesgos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (responseRiesgos.ok) {
            const riesgos = await responseRiesgos.json();
            const contadorRiesgos = document.getElementById('contadorRiesgos');
            if (contadorRiesgos) {
                contadorRiesgos.textContent = riesgos.length || 0;
            }
        }
        
        // Cargar contador de incidentes
        const responseIncidentes = await fetch(`${SERVICE_INCIDENTES_URL}/incidentes`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (responseIncidentes.ok) {
            const incidentes = await responseIncidentes.json();
            const incidentesAbiertos = incidentes.filter(inc => 
                inc.estado === 'ABIERTO' || inc.estado === 'EN_INVESTIGACION'
            );
            const contadorIncidentes = document.getElementById('contadorIncidentes');
            if (contadorIncidentes) {
                contadorIncidentes.textContent = incidentesAbiertos.length || 0;
            }
        }
        
        // Cargar contador de documentos
        const responseDocumentos = await fetch(`${SERVICE_DOCUMENTACION_URL}/documentos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (responseDocumentos.ok) {
            const documentos = await responseDocumentos.json();
            const contadorDocumentos = document.getElementById('contadorDocumentos');
            if (contadorDocumentos) {
                contadorDocumentos.textContent = documentos.length || 0;
            }
        }
        
        // Cargar contador de auditorías
        const responseAuditorias = await fetch(`${SERVICE_AUDITORIAS_URL}/auditorias`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (responseAuditorias.ok) {
            const auditorias = await responseAuditorias.json();
            const auditoriasProximasOEnProceso = auditorias.filter(aud => 
                aud.estado === 'PLANIFICADA' || aud.estado === 'EN_EJECUCION'
            );
            const contadorAuditorias = document.getElementById('contadorAuditorias');
            if (contadorAuditorias) {
                contadorAuditorias.textContent = auditoriasProximasOEnProceso.length || 0;
            }
        }
    } catch (error) {
        console.error('Error cargando contadores:', error);
    }
}

// Función para cargar resumen de riesgos y mostrar gráfico
async function cargarResumenRiesgos() {
    try {
        const response = await fetch(`${SERVICE_RIESGOS_URL}/riesgos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) throw new Error('Error al obtener datos de riesgos');
        
        const riesgos = await response.json();
        
        // Procesar datos para el gráfico
        const riesgosPorNivel = {
            'ALTO': 0,
            'MEDIO': 0,
            'BAJO': 0
        };
        
        // Clasificar riesgos por nivel
        riesgos.forEach(riesgo => {
            const nivelRiesgo = riesgo.nivel_riesgo || 0;
            
            if (nivelRiesgo >= 9) {
                riesgosPorNivel['ALTO']++;
            } else if (nivelRiesgo >= 4) {
                riesgosPorNivel['MEDIO']++;
            } else {
                riesgosPorNivel['BAJO']++;
            }
        });
        
        // Crear o actualizar gráfico de distribución de riesgos por nivel
        const ctxRiesgos = document.getElementById('graficoRiesgos');
        if (ctxRiesgos) {
            // Destruir gráfico anterior si existe
            if (riesgosChart) {
                riesgosChart.destroy();
            }
            
            // Crear nuevo gráfico
            riesgosChart = new Chart(ctxRiesgos, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(riesgosPorNivel),
                    datasets: [{
                        data: Object.values(riesgosPorNivel),
                        backgroundColor: [
                            '#e74a3b',  // Alto
                            '#f6c23e',  // Medio
                            '#1cc88a'   // Bajo
                        ],
                        hoverOffset: 4
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
            // Añadir interactividad al gráfico
            ctxRiesgos.onclick = function(evt) {
                const points = riesgosChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
                
                if (points.length) {
                    const firstPoint = points[0];
                    const label = riesgosChart.data.labels[firstPoint.index];
                    window.location.href = `riesgos.html?nivel=${label}`;
                }
            };
            ctxRiesgos.style.cursor = 'pointer';
        }
    } catch (error) {
        console.error('Error cargando resumen de riesgos:', error);
    }
}

// Función para cargar los incidentes recientes
async function cargarIncidentesRecientes() {
    try {
        const response = await fetch(`${SERVICE_INCIDENTES_URL}/incidentes`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) throw new Error('Error al obtener incidentes');
        
        const incidentes = await response.json();
        const listaIncidentes = document.getElementById('listaIncidentes');
        
        if (listaIncidentes) {
            if (incidentes.length === 0) {
                listaIncidentes.innerHTML = '<li class="list-group-item">No hay incidentes recientes</li>';
                return;
            }
            
            // Ordenar incidentes por fecha (más recientes primero)
            const incidentesOrdenados = [...incidentes].sort((a, b) => {
                return new Date(b.fecha_reporte || b.fecha_creacion || 0) - 
                       new Date(a.fecha_reporte || a.fecha_creacion || 0);
            });
            
            // Filtrar incidentes abiertos o en investigación
            const incidentesActivos = incidentesOrdenados.filter(inc => 
                inc.estado === 'ABIERTO' || inc.estado === 'EN_INVESTIGACION'
            );
            
            listaIncidentes.innerHTML = '';
            
            // Mostrar los 5 incidentes más recientes
            const incidentesMostrar = incidentesActivos.length > 0 ? 
                incidentesActivos.slice(0, 5) : 
                incidentesOrdenados.slice(0, 5);
                
            incidentesMostrar.forEach(incidente => {
                const badgeEstado = crearBadgeEstado(incidente.estado);
                const badgePrioridad = crearBadgeEstado(incidente.prioridad, 'prioridad');
                
                listaIncidentes.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${incidente.titulo}</strong>
                            <div class="small text-muted">${formatearFecha(incidente.fecha_reporte || incidente.fecha_creacion, true)}</div>
                        </div>
                        <div>
                            ${badgePrioridad} ${badgeEstado}
                        </div>
                    </li>
                `;
            });
            
            // Añadir interactividad a la lista
            const items = listaIncidentes.querySelectorAll('li');
            items.forEach((item, index) => {
                item.style.cursor = 'pointer';
                item.addEventListener('click', () => {
                    window.location.href = `incidentes.html?id=${incidentesMostrar[index].id}`;
                });
            });
        }
    } catch (error) {
        console.error('Error cargando incidentes recientes:', error);
        const listaIncidentes = document.getElementById('listaIncidentes');
        if (listaIncidentes) {
            listaIncidentes.innerHTML = '<li class="list-group-item">Error al cargar incidentes</li>';
        }
    }
}

// Función para cargar próximas auditorías
async function cargarProximasAuditorias() {
    try {
        const response = await fetch(`${SERVICE_AUDITORIAS_URL}/auditorias`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) throw new Error('Error al obtener auditorías');
        
        const auditorias = await response.json();
        const listaAuditorias = document.getElementById('listaAuditorias');
        
        if (listaAuditorias) {
            if (auditorias.length === 0) {
                listaAuditorias.innerHTML = '<li class="list-group-item">No hay auditorías programadas</li>';
                return;
            }
            
            // Filtrar auditorías planificadas o en ejecución
            const auditoriasActivas = auditorias.filter(aud => 
                aud.estado === 'PLANIFICADA' || aud.estado === 'EN_EJECUCION'
            );
            
            // Ordenar por fecha de inicio (las más próximas primero)
            const auditoriasOrdenadas = [...auditoriasActivas].sort((a, b) => {
                return new Date(a.fecha_inicio) - new Date(b.fecha_inicio);
            });
            
            if (auditoriasOrdenadas.length === 0) {
                listaAuditorias.innerHTML = '<li class="list-group-item">No hay auditorías programadas próximamente</li>';
                return;
            }
            
            listaAuditorias.innerHTML = '';
            auditoriasOrdenadas.slice(0, 3).forEach(auditoria => {
                // Crear badge para el estado
                let badgeClase = '';
                switch(auditoria.estado) {
                    case 'PLANIFICADA':
                        badgeClase = 'bg-primary';
                        break;
                    case 'EN_EJECUCION':
                        badgeClase = 'bg-warning text-dark';
                        break;
                    default:
                        badgeClase = 'bg-info';
                }
                
                listaAuditorias.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${auditoria.titulo}</strong>
                            <div class="small text-muted">${formatearFecha(auditoria.fecha_inicio)} - ${formatearFecha(auditoria.fecha_fin)}</div>
                        </div>
                        <div>
                            <span class="badge ${badgeClase}">${auditoria.tipo}</span>
                            <span class="badge bg-secondary">${auditoria.estado}</span>
                        </div>
                    </li>
                `;
            });
            
            // Añadir interactividad a la lista
            const items = listaAuditorias.querySelectorAll('li');
            items.forEach((item, index) => {
                item.style.cursor = 'pointer';
                item.addEventListener('click', () => {
                    window.location.href = `auditorias.html?id=${auditoriasOrdenadas[index].id}`;
                });
            });
        }
    } catch (error) {
        console.error('Error cargando próximas auditorías:', error);
        const listaAuditorias = document.getElementById('listaAuditorias');
        if (listaAuditorias) {
            listaAuditorias.innerHTML = '<li class="list-group-item">Error al cargar auditorías</li>';
        }
    }
}

// Función para cargar documentos recientes
async function cargarDocumentosRecientes() {
    try {
        const response = await fetch(`${SERVICE_DOCUMENTACION_URL}/documentos`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (!response.ok) throw new Error('Error al obtener documentos');
        
        const documentos = await response.json();
        const listaDocumentos = document.getElementById('listaDocumentos');
        
        if (listaDocumentos) {
            if (documentos.length === 0) {
                listaDocumentos.innerHTML = '<li class="list-group-item">No hay documentos disponibles</li>';
                return;
            }
            
            // Ordenar documentos por fecha de actualización (más recientes primero)
            const documentosOrdenados = [...documentos].sort((a, b) => {
                return new Date(b.fecha_actualizacion || b.fecha_creacion || 0) - 
                       new Date(a.fecha_actualizacion || a.fecha_creacion || 0);
            });
            
            listaDocumentos.innerHTML = '';
            documentosOrdenados.slice(0, 4).forEach(documento => {
                // Determinar el icono según el tipo de documento
                let icono = 'fa-file-alt';
                if (documento.tipo) {
                    const tipo = documento.tipo.toLowerCase();
                    if (tipo.includes('pdf')) {
                        icono = 'fa-file-pdf';
                    } else if (tipo.includes('excel') || tipo.includes('xlsx') || tipo.includes('xls')) {
                        icono = 'fa-file-excel';
                    } else if (tipo.includes('word') || tipo.includes('docx') || tipo.includes('doc')) {
                        icono = 'fa-file-word';
                    } else if (tipo.includes('power') || tipo.includes('pptx') || tipo.includes('ppt')) {
                        icono = 'fa-file-powerpoint';
                    } else if (tipo.includes('image') || tipo.includes('jpg') || tipo.includes('png')) {
                        icono = 'fa-file-image';
                    }
                }
                
                listaDocumentos.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <i class="fas ${icono} me-2 text-primary"></i>
                            <div>
                                <strong>${documento.nombre}</strong>
                                <div class="small text-muted">${formatearFecha(documento.fecha_actualizacion || documento.fecha_creacion, true)}</div>
                            </div>
                        </div>
                        <div>
                            <span class="badge bg-secondary">${documento.categoria || 'Sin categoría'}</span>
                        </div>
                    </li>
                `;
            });
            
            // Añadir interactividad a la lista
            const items = listaDocumentos.querySelectorAll('li');
            items.forEach((item, index) => {
                item.style.cursor = 'pointer';
                item.addEventListener('click', () => {
                    window.location.href = `documentos.html?id=${documentosOrdenados[index].id}`;
                });
            });
        }
    } catch (error) {
        console.error('Error cargando documentos recientes:', error);
        const listaDocumentos = document.getElementById('listaDocumentos');
        if (listaDocumentos) {
            listaDocumentos.innerHTML = '<li class="list-group-item">Error al cargar documentos</li>';
        }
    }
}

// Función para ajustar los paneles según el tamaño de la ventana
function ajustarPaneles() {
    const esMobile = window.innerWidth < 768;
    const contenedores = document.querySelectorAll('.dashboard-panel');
    
    contenedores.forEach(contenedor => {
        if (esMobile) {
            contenedor.classList.remove('col-md-6', 'col-lg-3');
            contenedor.classList.add('col-12');
        } else {
            contenedor.classList.remove('col-12');
            contenedor.classList.add('col-md-6', 'col-lg-3');
        }
    });
}
