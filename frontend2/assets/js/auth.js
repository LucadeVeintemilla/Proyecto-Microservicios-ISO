// auth.js - Funciones de autenticación y manejo de sesiones

// URLs de servicios
const SERVICE_AUTH_URL = 'http://localhost:5001';
const SERVICE_ROLES_URL = 'http://localhost:5007';

// Función para verificar si el usuario está autenticado
function verificarAutenticacion() {
    // Si estamos en la página de login, no es necesario verificar autenticación
    if (window.location.pathname.includes('login.html')) {
        return false;
    }
    
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return false;
    }
    
    // Verificar si el token no está expirado
    const tokenData = parseJwt(token);
    if (tokenData && tokenData.exp && tokenData.exp < Date.now() / 1000) {
        cerrarSesion();
        return false;
    }
    
    return true;
}

// Función para iniciar sesión
async function iniciarSesion(username, password) {
    try {
        // Validación local de usuario y contraseña
        if (!username || !password) {
            throw new Error('Se requiere usuario y contraseña');
        }

        const response = await fetch(`${SERVICE_AUTH_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // El backend acepta 'email' o 'usuario'
                email: username, // Enviamos username como email
                password: password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Error al iniciar sesión');
        }
        
        // Guardar token y datos de usuario
        localStorage.setItem('token', data.token);
        localStorage.setItem('usuario', JSON.stringify({
            id: data.usuario.id,
            nombre_usuario: data.usuario.nombre_usuario,
            nombre: data.usuario.nombre,
            apellido: data.usuario.apellido,
            email: data.usuario.email,
            roles: data.usuario.roles,
            permisos: data.usuario.permisos || []
        }));
        
        return data;
    } catch (error) {
        console.error('Error en inicio de sesión:', error);
        throw error;
    }
}

// Función para cerrar sesión
function cerrarSesion() {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = 'login.html';
}

// Función para decodificar el token JWT
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

// Función para obtener el token de autenticación
function getToken() {
    return localStorage.getItem('token');
}

// Función para obtener datos del usuario actual
function getUsuarioActual() {
    const usuarioStr = localStorage.getItem('usuario');
    return usuarioStr ? JSON.parse(usuarioStr) : null;
}

// Función para actualizar la UI con los datos del usuario
function actualizarUIUsuario() {
    const usuario = getUsuarioActual();
    if (usuario) {
        const nombreElement = document.getElementById('nombreUsuario');
        if (nombreElement) {
            nombreElement.textContent = usuario.nombre;
        }
    }
}

// Verificar permisos del usuario para una funcionalidad específica
function tienePermiso(codigoPermiso) {
    const usuario = getUsuarioActual();
    if (!usuario || !usuario.permisos) return false;
    
    return usuario.permisos.some(p => p.codigo === codigoPermiso);
}

// Cargar navbar común desde partial y luego inicializar autenticación
async function cargarNavbar() {
    // No cargar el navbar en la página de login
    if (window.location.pathname.includes('login.html')) {
        return;
    }
    
    // Solo cargar el navbar si el usuario está autenticado
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    
    try {
        const res = await fetch('partials/navbar.html');
        if (!res.ok) throw new Error('No se pudo cargar navbar');
        const html = await res.text();
        // Eliminar cualquier navbar existente para evitar duplicados
        document.querySelectorAll('nav.navbar').forEach(n => n.remove());
        // Insertar navbar recién cargado al inicio del body
        document.body.insertAdjacentHTML('afterbegin', html);
    } catch (e) {
        console.warn('[navbar]', e);
    }
}

// Inicializar elementos de autenticación al cargar la página
document.addEventListener('DOMContentLoaded', async () => {
    // Verificar si estamos en la página de login
    const isLoginPage = window.location.pathname.includes('login.html');
    
    // Obtener el token
    const token = localStorage.getItem('token');
    
    // Si estamos en la página de login y hay un token válido, redirigir al dashboard
    if (isLoginPage && token) {
        // Verificar si el token está expirado
        const tokenData = parseJwt(token);
        if (!tokenData || !tokenData.exp || tokenData.exp >= Date.now() / 1000) {
            window.location.href = 'index.html';
            return;
        }
    }
    
    // Si no estamos en la página de login y no hay token, redirigir al login
    if (!isLoginPage && !token) {
        window.location.href = 'login.html';
        return;
    }
    
    // Si no estamos en la página de login y hay token, verificar expiración
    if (!isLoginPage && token) {
        const tokenData = parseJwt(token);
        if (tokenData && tokenData.exp && tokenData.exp < Date.now() / 1000) {
            // Token expirado, eliminar y redirigir al login
            localStorage.removeItem('token');
            localStorage.removeItem('usuario');
            window.location.href = 'login.html';
            return;
        }
        
        // Token válido, cargar navbar y actualizar UI
        await cargarNavbar();
        actualizarUIUsuario();
        
        // Configurar evento de cierre de sesión
        const btnCerrarSesion = document.getElementById('btnCerrarSesion');
        if (btnCerrarSesion) {
            btnCerrarSesion.addEventListener('click', (e) => {
                e.preventDefault();
                cerrarSesion();
            });
        }
    }
});
