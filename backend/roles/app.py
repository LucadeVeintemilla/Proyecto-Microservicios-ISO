from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import text
import sys
import os
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Rol, Permiso, Usuario, SesionUsuario, LogAuditoria, ConflictoSegregacion

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
jwt = JWTManager(app)
db.init_app(app)

@app.route('/inicializar_db', methods=['POST'])
@jwt_required()
def inicializar_db():
    try:
        identity = get_jwt_identity()
        roles = identity.get('roles', [])
        if 'Administrador' not in roles:
            return jsonify({'error': 'No autorizado'}), 403
            
        try:
            # Primero intentamos eliminar las tablas existentes
            # Usamos SQL directo para evitar problemas de dependencias
            with app.app_context():
                # Desactivar verificación de claves foráneas temporalmente
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                
                # Eliminar tablas en orden para evitar problemas de dependencias
                db.session.execute(text("DROP TABLE IF EXISTS conflictos_segregacion"))
                db.session.execute(text("DROP TABLE IF EXISTS rol_permiso"))
                db.session.execute(text("DROP TABLE IF EXISTS permisos"))
                db.session.execute(text("DROP TABLE IF EXISTS roles"))
                
                # Reactivar verificación de claves foráneas
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                db.session.commit()
                
                # Crear todas las tablas desde cero
                db.create_all()
                db.session.commit()
                
        except Exception as e:
            app.logger.error(f"Error al recrear tablas: {str(e)}")
            db.session.rollback()
            return jsonify({'error': f'Error al recrear tablas de la base de datos: {str(e)}'}), 500
        
        # Crear permisos predefinidos si no existen
        permisos_predefinidos = [
            # Permisos para Auth
            {'codigo': 'AUTH_ADMIN', 'nombre': 'Administración de autenticación', 'descripcion': 'Permite administrar todos los usuarios y roles', 'modulo': 'Auth', 'es_critico': True},
            {'codigo': 'AUTH_READ', 'nombre': 'Consulta de autenticación', 'descripcion': 'Permite consultar usuarios y roles', 'modulo': 'Auth', 'es_critico': False},
            
            # Permisos para Riesgos
            {'codigo': 'RIESGO_ADMIN', 'nombre': 'Administración de riesgos', 'descripcion': 'Permite administrar todos los riesgos', 'modulo': 'Riesgos', 'es_critico': True},
            {'codigo': 'RIESGO_CREATE', 'nombre': 'Creación de riesgos', 'descripcion': 'Permite crear nuevos riesgos', 'modulo': 'Riesgos', 'es_critico': False},
            {'codigo': 'RIESGO_READ', 'nombre': 'Consulta de riesgos', 'descripcion': 'Permite consultar riesgos', 'modulo': 'Riesgos', 'es_critico': False},
            {'codigo': 'RIESGO_UPDATE', 'nombre': 'Actualización de riesgos', 'descripcion': 'Permite actualizar riesgos existentes', 'modulo': 'Riesgos', 'es_critico': False},
            {'codigo': 'RIESGO_DELETE', 'nombre': 'Eliminación de riesgos', 'descripcion': 'Permite eliminar riesgos', 'modulo': 'Riesgos', 'es_critico': True},
            
            # Permisos para Documentación
            {'codigo': 'DOC_ADMIN', 'nombre': 'Administración de documentos', 'descripcion': 'Permite administrar toda la documentación', 'modulo': 'Documentacion', 'es_critico': True},
            {'codigo': 'DOC_CREATE', 'nombre': 'Creación de documentos', 'descripcion': 'Permite crear nuevos documentos', 'modulo': 'Documentacion', 'es_critico': False},
            {'codigo': 'DOC_READ', 'nombre': 'Consulta de documentos', 'descripcion': 'Permite consultar documentos', 'modulo': 'Documentacion', 'es_critico': False},
            {'codigo': 'DOC_UPDATE', 'nombre': 'Actualización de documentos', 'descripcion': 'Permite actualizar documentos existentes', 'modulo': 'Documentacion', 'es_critico': False},
            {'codigo': 'DOC_DELETE', 'nombre': 'Eliminación de documentos', 'descripcion': 'Permite eliminar documentos', 'modulo': 'Documentacion', 'es_critico': True},
            {'codigo': 'DOC_APPROVE', 'nombre': 'Aprobación de documentos', 'descripcion': 'Permite aprobar documentos', 'modulo': 'Documentacion', 'es_critico': True},
            
            # Permisos para Auditorías
            {'codigo': 'AUDIT_ADMIN', 'nombre': 'Administración de auditorías', 'descripcion': 'Permite administrar todas las auditorías', 'modulo': 'Auditorias', 'es_critico': True},
            {'codigo': 'AUDIT_CREATE', 'nombre': 'Creación de auditorías', 'descripcion': 'Permite crear nuevas auditorías', 'modulo': 'Auditorias', 'es_critico': False},
            {'codigo': 'AUDIT_READ', 'nombre': 'Consulta de auditorías', 'descripcion': 'Permite consultar auditorías', 'modulo': 'Auditorias', 'es_critico': False},
            {'codigo': 'AUDIT_UPDATE', 'nombre': 'Actualización de auditorías', 'descripcion': 'Permite actualizar auditorías existentes', 'modulo': 'Auditorias', 'es_critico': False},
            {'codigo': 'AUDIT_DELETE', 'nombre': 'Eliminación de auditorías', 'descripcion': 'Permite eliminar auditorías', 'modulo': 'Auditorias', 'es_critico': True},
            
            # Permisos para Incidentes
            {'codigo': 'INC_ADMIN', 'nombre': 'Administración de incidentes', 'descripcion': 'Permite administrar todos los incidentes', 'modulo': 'Incidentes', 'es_critico': True},
            {'codigo': 'INC_CREATE', 'nombre': 'Creación de incidentes', 'descripcion': 'Permite crear nuevos incidentes', 'modulo': 'Incidentes', 'es_critico': False},
            {'codigo': 'INC_READ', 'nombre': 'Consulta de incidentes', 'descripcion': 'Permite consultar incidentes', 'modulo': 'Incidentes', 'es_critico': False},
            {'codigo': 'INC_UPDATE', 'nombre': 'Actualización de incidentes', 'descripcion': 'Permite actualizar incidentes existentes', 'modulo': 'Incidentes', 'es_critico': False},
            {'codigo': 'INC_DELETE', 'nombre': 'Eliminación de incidentes', 'descripcion': 'Permite eliminar incidentes', 'modulo': 'Incidentes', 'es_critico': True},
            
            # Permisos para Proveedores
            {'codigo': 'PROV_ADMIN', 'nombre': 'Administración de proveedores', 'descripcion': 'Permite administrar todos los proveedores', 'modulo': 'Proveedores', 'es_critico': True},
            {'codigo': 'PROV_CREATE', 'nombre': 'Creación de proveedores', 'descripcion': 'Permite crear nuevos proveedores', 'modulo': 'Proveedores', 'es_critico': False},
            {'codigo': 'PROV_READ', 'nombre': 'Consulta de proveedores', 'descripcion': 'Permite consultar proveedores', 'modulo': 'Proveedores', 'es_critico': False},
            {'codigo': 'PROV_UPDATE', 'nombre': 'Actualización de proveedores', 'descripcion': 'Permite actualizar proveedores existentes', 'modulo': 'Proveedores', 'es_critico': False},
            {'codigo': 'PROV_DELETE', 'nombre': 'Eliminación de proveedores', 'descripcion': 'Permite eliminar proveedores', 'modulo': 'Proveedores', 'es_critico': True},
            
            # Permisos para Roles
            {'codigo': 'ROL_ADMIN', 'nombre': 'Administración de roles', 'descripcion': 'Permite administrar todos los roles y permisos', 'modulo': 'Roles', 'es_critico': True},
            {'codigo': 'ROL_CREATE', 'nombre': 'Creación de roles', 'descripcion': 'Permite crear nuevos roles', 'modulo': 'Roles', 'es_critico': True},
            {'codigo': 'ROL_READ', 'nombre': 'Consulta de roles', 'descripcion': 'Permite consultar roles', 'modulo': 'Roles', 'es_critico': False},
            {'codigo': 'ROL_UPDATE', 'nombre': 'Actualización de roles', 'descripcion': 'Permite actualizar roles existentes', 'modulo': 'Roles', 'es_critico': True},
            {'codigo': 'ROL_DELETE', 'nombre': 'Eliminación de roles', 'descripcion': 'Permite eliminar roles', 'modulo': 'Roles', 'es_critico': True},
        ]
        
        for permiso_data in permisos_predefinidos:
            if not Permiso.query.filter_by(codigo=permiso_data['codigo']).first():
                permiso = Permiso(
                    codigo=permiso_data['codigo'],
                    nombre=permiso_data['nombre'],
                    descripcion=permiso_data['descripcion'],
                    modulo=permiso_data['modulo'],
                    es_critico=permiso_data['es_critico']
                )
                db.session.add(permiso)
        
        # Crear roles predefinidos si no existen
        roles_predefinidos = [
            {'nombre': 'Administrador', 'descripcion': 'Control total del sistema', 'es_predefinido': True, 'permisos_codigos': ['AUTH_ADMIN', 'RIESGO_ADMIN', 'DOC_ADMIN', 'AUDIT_ADMIN', 'INC_ADMIN', 'PROV_ADMIN', 'ROL_ADMIN']},
            {'nombre': 'Analista', 'descripcion': 'Consulta y análisis general', 'es_predefinido': True, 'permisos_codigos': ['AUTH_READ', 'RIESGO_READ', 'DOC_READ', 'AUDIT_READ', 'INC_READ', 'PROV_READ', 'ROL_READ']},
            {'nombre': 'Gestor de Riesgos', 'descripcion': 'Gestión completa de riesgos', 'es_predefinido': True, 'permisos_codigos': ['RIESGO_CREATE', 'RIESGO_READ', 'RIESGO_UPDATE']},
            {'nombre': 'Gestor de Documentos', 'descripcion': 'Gestión completa de documentos', 'es_predefinido': True, 'permisos_codigos': ['DOC_CREATE', 'DOC_READ', 'DOC_UPDATE']},
            {'nombre': 'Gestor de Incidentes', 'descripcion': 'Gestión completa de incidentes', 'es_predefinido': True, 'permisos_codigos': ['INC_CREATE', 'INC_READ', 'INC_UPDATE']},
            {'nombre': 'Auditor', 'descripcion': 'Gestión completa de auditorías', 'es_predefinido': True, 'permisos_codigos': ['AUDIT_CREATE', 'AUDIT_READ', 'AUDIT_UPDATE', 'DOC_READ', 'INC_READ']},
            {'nombre': 'Gestor de Proveedores', 'descripcion': 'Gestión completa de proveedores', 'es_predefinido': True, 'permisos_codigos': ['PROV_CREATE', 'PROV_READ', 'PROV_UPDATE']}
        ]
        
        for rol_data in roles_predefinidos:
            if not Rol.query.filter_by(nombre=rol_data['nombre']).first():
                rol = Rol(
                    nombre=rol_data['nombre'],
                    descripcion=rol_data['descripcion'],
                    es_predefinido=rol_data['es_predefinido']
                )
                db.session.add(rol)
                db.session.flush()  # Para obtener el ID del rol
                
                # Asignar permisos al rol
                for codigo in rol_data['permisos_codigos']:
                    permiso = Permiso.query.filter_by(codigo=codigo).first()
                    if permiso:
                        rol.permisos.append(permiso)
        
        # Crear conflictos de segregación predefinidos
        conflictos_predefinidos = [
            {
                'rol_a_nombre': 'Gestor de Documentos',
                'rol_b_nombre': 'Auditor',
                'descripcion': 'Segregación de deberes: un usuario no debe gestionar documentos y realizar auditorías'
            },
            {
                'rol_a_nombre': 'Gestor de Riesgos',
                'rol_b_nombre': 'Gestor de Proveedores',
                'descripcion': 'Segregación de deberes: un usuario no debe gestionar riesgos y proveedores simultáneamente'
            }
        ]

        for conflicto_data in conflictos_predefinidos:
            rol_a = Rol.query.filter_by(nombre=conflicto_data['rol_a_nombre']).first()
            rol_b = Rol.query.filter_by(nombre=conflicto_data['rol_b_nombre']).first()
            if rol_a and rol_b and not ConflictoSegregacion.query.filter_by(rol_a_id=rol_a.id, rol_b_id=rol_b.id).first():
                conflicto = ConflictoSegregacion(
                    rol_a_id=rol_a.id,
                    rol_b_id=rol_b.id,
                    descripcion=conflicto_data['descripcion']
                )
                db.session.add(conflicto)

        db.session.commit()
        return jsonify({'mensaje': 'Base de datos de roles inicializada'}), 201

    except Exception as e:
        db.session.rollback()  # Rollback any changes si ocurre un error
        app.logger.error(f"Error al inicializar la base de datos: {str(e)}")
        return jsonify({'error': f'Error al inicializar la base de datos: {str(e)}'}), 500

# --- Roles ---
@app.route('/roles', methods=['GET'])
@jwt_required()
def obtener_roles():
    roles = Rol.query.all()
    return jsonify([r.to_dict() for r in roles]), 200

@app.route('/roles/<int:rol_id>', methods=['GET'])
@jwt_required()
def obtener_rol(rol_id):
    rol = Rol.query.get(rol_id)
    if not rol:
        return jsonify({'error': 'Rol no encontrado'}), 404
    return jsonify(rol.to_dict()), 200

@app.route('/roles', methods=['POST'])
@jwt_required()
def crear_rol():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'ROL_CREATE' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre de rol requerido'}), 400
    
    if Rol.query.filter_by(nombre=data['nombre']).first():
        return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400
    
    rol = Rol(
        nombre=data['nombre'],
        descripcion=data.get('descripcion', ''),
        es_predefinido=False
    )
    db.session.add(rol)
    
    # Asignar permisos si se proporcionan
    if 'permisos_ids' in data and isinstance(data['permisos_ids'], list):
        for permiso_id in data['permisos_ids']:
            permiso = Permiso.query.get(permiso_id)
            if permiso:
                rol.permisos.append(permiso)
    
    # Registrar acción en log de auditoría
    log = LogAuditoria(
        usuario_id=identity.get('usuario_id'),
        accion='CREAR_ROL',
        modulo='Roles',
        entidad='Rol',
        detalles=f"Rol creado: {data['nombre']}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    return jsonify(rol.to_dict()), 201

@app.route('/roles/<int:rol_id>', methods=['PUT'])
@jwt_required()
def actualizar_rol(rol_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'ROL_UPDATE' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    rol = Rol.query.get(rol_id)
    if not rol:
        return jsonify({'error': 'Rol no encontrado'}), 404
    
    # No permitir actualizar roles predefinidos excepto si es administrador
    if rol.es_predefinido and 'Administrador' not in roles:
        return jsonify({'error': 'No se pueden modificar roles predefinidos'}), 403
    
    data = request.get_json()
    
    # Actualizar campos básicos
    if 'nombre' in data:
        rol_existente = Rol.query.filter_by(nombre=data['nombre']).first()
        if rol_existente and rol_existente.id != rol_id:
            return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400
        rol.nombre = data['nombre']
    
    if 'descripcion' in data:
        rol.descripcion = data['descripcion']
    
    # Actualizar permisos si se proporcionan
    if 'permisos_ids' in data and isinstance(data['permisos_ids'], list):
        # Eliminar todos los permisos actuales
        rol.permisos = []
        
        # Asignar nuevos permisos
        for permiso_id in data['permisos_ids']:
            permiso = Permiso.query.get(permiso_id)
            if permiso:
                rol.permisos.append(permiso)
    
    # Registrar acción en log de auditoría
    log = LogAuditoria(
        usuario_id=identity.get('usuario_id'),
        accion='ACTUALIZAR_ROL',
        modulo='Roles',
        entidad='Rol',
        entidad_id=rol_id,
        detalles=f"Rol actualizado: {rol.nombre}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    return jsonify(rol.to_dict()), 200

@app.route('/roles/<int:rol_id>', methods=['DELETE'])
@jwt_required()
def eliminar_rol(rol_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'ROL_DELETE' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    rol = Rol.query.get(rol_id)
    if not rol:
        return jsonify({'error': 'Rol no encontrado'}), 404
    
    # No permitir eliminar roles predefinidos
    if rol.es_predefinido:
        return jsonify({'error': 'No se pueden eliminar roles predefinidos'}), 403
    
    # Verificar si hay usuarios con este rol usando SQL directo para evitar problemas con el ORM
    try:
        # Consulta directa para verificar si hay usuarios con este rol
        result = db.session.execute(text("SELECT COUNT(*) FROM usuario_rol WHERE rol_id = :rol_id"), {"rol_id": rol_id})
        count = result.scalar()
        
        if count > 0:
            return jsonify({'error': 'No se puede eliminar el rol porque tiene usuarios asignados'}), 400
    except Exception as e:
        app.logger.error(f"Error al verificar usuarios del rol: {str(e)}")
        return jsonify({'error': f'Error al verificar usuarios del rol: {str(e)}'}), 500
    
    # Registrar acción en log de auditoría
    log = LogAuditoria(
        usuario_id=identity.get('usuario_id'),
        accion='ELIMINAR_ROL',
        modulo='Roles',
        entidad='Rol',
        entidad_id=rol_id,
        detalles=f"Rol eliminado: {rol.nombre}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    try:
        # Eliminar las relaciones del rol con permisos usando SQL directo
        db.session.execute(text("DELETE FROM rol_permiso WHERE rol_id = :rol_id"), {"rol_id": rol_id})
        
        # Eliminar el rol
        db.session.execute(text("DELETE FROM roles WHERE id = :rol_id"), {"rol_id": rol_id})
        
        # Confirmar los cambios
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar rol: {str(e)}")
        return jsonify({'error': f'Error al eliminar rol: {str(e)}'}), 500
    return jsonify({'mensaje': 'Rol eliminado correctamente'}), 200

# --- Permisos ---
@app.route('/permisos', methods=['GET'])
@jwt_required()
def obtener_permisos():
    permisos = Permiso.query.all()
    return jsonify([p.to_dict_simple() for p in permisos]), 200

@app.route('/permisos/<int:permiso_id>', methods=['GET'])
@jwt_required()
def obtener_permiso(permiso_id):
    permiso = Permiso.query.get(permiso_id)
    if not permiso:
        return jsonify({'error': 'Permiso no encontrado'}), 404
    return jsonify(permiso.to_dict()), 200

@app.route('/permisos/modulo/<string:modulo>', methods=['GET'])
@jwt_required()
def obtener_permisos_por_modulo(modulo):
    permisos = Permiso.query.filter_by(modulo=modulo).all()
    return jsonify([p.to_dict_simple() for p in permisos]), 200

# --- Conflictos de Segregación ---
@app.route('/conflictos-segregacion', methods=['GET'])
@jwt_required()
def obtener_conflictos_segregacion():
    conflictos = ConflictoSegregacion.query.all()
    return jsonify([c.to_dict() for c in conflictos]), 200

# Alias para mantener compatibilidad con el frontend
@app.route('/conflictos', methods=['GET'])
@jwt_required()
def obtener_conflictos():
    # Redirigir a la función existente
    return obtener_conflictos_segregacion()

@app.route('/conflictos-segregacion', methods=['POST'])
@jwt_required()
def crear_conflicto_segregacion():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'ROL_ADMIN' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    if not data.get('rol_a_id') or not data.get('rol_b_id') or not data.get('descripcion'):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    rol_a = Rol.query.get(data['rol_a_id'])
    rol_b = Rol.query.get(data['rol_b_id'])
    if not rol_a or not rol_b:
        return jsonify({'error': 'Alguno de los roles no existe'}), 404
    
    if rol_a.id == rol_b.id:
        return jsonify({'error': 'Los roles deben ser diferentes'}), 400
    
    # Verificar si ya existe el conflicto
    if ConflictoSegregacion.query.filter(
        ((ConflictoSegregacion.rol_a_id == rol_a.id) & (ConflictoSegregacion.rol_b_id == rol_b.id)) | 
        ((ConflictoSegregacion.rol_a_id == rol_b.id) & (ConflictoSegregacion.rol_b_id == rol_a.id))
    ).first():
        return jsonify({'error': 'Ya existe un conflicto entre estos roles'}), 400
    
    conflicto = ConflictoSegregacion(
        rol_a_id=rol_a.id,
        rol_b_id=rol_b.id,
        descripcion=data['descripcion']
    )
    db.session.add(conflicto)
    
    # Registrar acción en log de auditoría
    log = LogAuditoria(
        usuario_id=identity.get('usuario_id'),
        accion='CREAR_CONFLICTO_SEGREGACION',
        modulo='Roles',
        detalles=f"Conflicto creado entre {rol_a.nombre} y {rol_b.nombre}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    return jsonify(conflicto.to_dict()), 201

@app.route('/conflictos-segregacion/<int:conflicto_id>', methods=['DELETE'])
@jwt_required()
def eliminar_conflicto_segregacion(conflicto_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'ROL_ADMIN' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    conflicto = ConflictoSegregacion.query.get(conflicto_id)
    if not conflicto:
        return jsonify({'error': 'Conflicto no encontrado'}), 404
    
    # Registrar acción en log de auditoría
    log = LogAuditoria(
        usuario_id=identity.get('usuario_id'),
        accion='ELIMINAR_CONFLICTO_SEGREGACION',
        modulo='Roles',
        entidad='ConflictoSegregacion',
        entidad_id=conflicto_id,
        detalles=f"Conflicto eliminado entre roles {conflicto.rol_a_id} y {conflicto.rol_b_id}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(conflicto)
    db.session.commit()
    return jsonify({'mensaje': 'Conflicto eliminado correctamente'}), 200

# --- Verificación de conflictos ---
@app.route('/verificar-conflictos/<int:usuario_id>/<int:rol_id>', methods=['GET'])
@jwt_required()
def verificar_conflictos(usuario_id, rol_id):
    usuario = Usuario.query.get(usuario_id)
    rol_nuevo = Rol.query.get(rol_id)
    
    if not usuario or not rol_nuevo:
        return jsonify({'error': 'Usuario o rol no encontrado'}), 404
    
    # Verificar si el usuario ya tiene el rol
    if rol_nuevo in usuario.roles:
        return jsonify({'tiene_conflictos': False, 'mensaje': 'El usuario ya tiene este rol'}), 200
    
    conflictos = []
    
    # Verificar conflictos entre los roles actuales del usuario y el nuevo rol
    for rol_actual in usuario.roles:
        conflicto = ConflictoSegregacion.query.filter(
            ((ConflictoSegregacion.rol_a_id == rol_actual.id) & (ConflictoSegregacion.rol_b_id == rol_nuevo.id)) | 
            ((ConflictoSegregacion.rol_a_id == rol_nuevo.id) & (ConflictoSegregacion.rol_b_id == rol_actual.id))
        ).first()
        
        if conflicto:
            conflictos.append({
                'id': conflicto.id,
                'descripcion': conflicto.descripcion,
                'rol_actual': rol_actual.nombre,
                'rol_nuevo': rol_nuevo.nombre
            })
    
    return jsonify({
        'tiene_conflictos': len(conflictos) > 0,
        'conflictos': conflictos
    }), 200

# --- Logs de Auditoría ---
@app.route('/auditoria', methods=['GET'])
@jwt_required()
def obtener_auditoria():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'AUDIT_READ' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    # Soportar filtro por fecha
    fecha = request.args.get('fecha')
    
    query = LogAuditoria.query
    
    if fecha:
        # Si se proporciona fecha, filtrar por ese día
        fecha_dt = datetime.datetime.fromisoformat(fecha)
        fecha_siguiente = fecha_dt + datetime.timedelta(days=1)
        query = query.filter(LogAuditoria.fecha >= fecha_dt, LogAuditoria.fecha < fecha_siguiente)
    
    # Ordenar por fecha descendente (más reciente primero)
    query = query.order_by(LogAuditoria.fecha.desc())
    
    # Limitar resultados para evitar sobrecarga
    logs = query.limit(100).all()
    
    # Formatear los resultados como espera el frontend
    resultado = []
    for log in logs:
        try:
            # Usar SQL directo para obtener el nombre del usuario si es necesario
            usuario_nombre = "Sistema"
            if log.usuario_id:
                # Consulta directa para evitar problemas con el ORM
                user_query = db.session.execute(text("SELECT nombre, apellido FROM usuarios WHERE id = :user_id"), {"user_id": log.usuario_id})
                user_result = user_query.fetchone()
                if user_result:
                    usuario_nombre = f"{user_result.nombre} {user_result.apellido}"
            
            resultado.append({
                'fecha_hora': log.fecha.isoformat(),
                'usuario': usuario_nombre,
                'accion': log.accion,
                'detalles': log.detalles,
                'id': log.id,
                'modulo': log.modulo,
                'entidad': log.entidad,
                'ip': log.ip
            })
        except Exception as e:
            app.logger.error(f"Error al procesar log de auditoría: {str(e)}")
            # Continuar con el siguiente log
    
    return jsonify(resultado), 200
@app.route('/logs-auditoria', methods=['GET'])
@jwt_required()
def obtener_logs_auditoria():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles and 'AUDIT_READ' not in identity.get('permisos', []):
        return jsonify({'error': 'No autorizado'}), 403
    
    # Soportar filtros
    filtros = {}
    if request.args.get('usuario_id'):
        filtros['usuario_id'] = int(request.args.get('usuario_id'))
    if request.args.get('modulo'):
        filtros['modulo'] = request.args.get('modulo')
    if request.args.get('accion'):
        filtros['accion'] = request.args.get('accion')
    if request.args.get('entidad'):
        filtros['entidad'] = request.args.get('entidad')
    
    # Filtrar por rango de fechas
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = LogAuditoria.query.filter_by(**filtros)
    
    if fecha_desde:
        query = query.filter(LogAuditoria.fecha >= datetime.datetime.fromisoformat(fecha_desde))
    if fecha_hasta:
        query = query.filter(LogAuditoria.fecha <= datetime.datetime.fromisoformat(fecha_hasta))
    
    # Ordenar por fecha descendente (más reciente primero)
    query = query.order_by(LogAuditoria.fecha.desc())
    
    # Paginación
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    pagination = query.paginate(page=page, per_page=per_page)
    
    logs = pagination.items
    
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007)
