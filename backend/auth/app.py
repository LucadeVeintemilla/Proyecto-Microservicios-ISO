from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Usuario, Rol, RolUsuario, Permiso, RolPermiso, SesionUsuario

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure CORS to allow requests from frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
jwt = JWTManager(app)
db.init_app(app)

@app.route('/inicializar_db', methods=['POST'])
def inicializar_db():
    db.create_all()
    
    roles_iniciales = [
        {'nombre': 'Administrador', 'descripcion': 'Administrador del sistema con acceso total'},
        {'nombre': 'GestorRiesgos', 'descripcion': 'Gestión de riesgos e impacto'},
        {'nombre': 'Auditor', 'descripcion': 'Acceso a los módulos de auditoría'},
        {'nombre': 'Usuario', 'descripcion': 'Usuario básico del sistema'}
    ]
    
    for rol_data in roles_iniciales:
        if not Rol.query.filter_by(nombre=rol_data['nombre']).first():
            rol = Rol(nombre=rol_data['nombre'], descripcion=rol_data['descripcion'])
            db.session.add(rol)
    
    if not Usuario.query.filter_by(email='admin@sgsi.com').first():
        admin = Usuario(
            nombre='Administrador',
            apellido='Sistema',
            email='admin@sgsi.com',
            activo=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        
        rol_admin = Rol.query.filter_by(nombre='Administrador').first()
        if rol_admin and admin:
            rol_usuario = RolUsuario(usuario_id=admin.id, rol_id=rol_admin.id)
            db.session.add(rol_usuario)
    
    db.session.commit()
    return jsonify({'mensaje': 'Base de datos inicializada correctamente'}), 201

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user_input = data.get('email') or data.get('usuario')  # Accept either email or usuario parameter
        password = data.get('password')
        
        if not user_input or not password:
            return jsonify({'error': 'Se requiere email/usuario y contraseña'}), 400
        
        # Try to find user by email first
        usuario = Usuario.query.filter_by(email=user_input).first()
        
        # If not found by email, we should handle it as a username
        # But since your model doesn't have a username field, we're using email
        
        if not usuario or not usuario.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 401
            
        roles_usuario = RolUsuario.query.filter_by(usuario_id=usuario.id).all()
        roles = [Rol.query.get(ru.rol_id).nombre for ru in roles_usuario]
        
        usuario.ultimo_acceso = datetime.datetime.utcnow()
        
        sesion = SesionUsuario(
            usuario_id=usuario.id,
            token="",
            ip=request.remote_addr,
            navegador=request.headers.get('User-Agent', '')
        )
        db.session.add(sesion)
        db.session.commit()
        
        access_token = create_access_token(
            identity={
                'usuario_id': usuario.id,
                'email': usuario.email,
                'roles': roles,
                'sesion_id': sesion.id
            }
        )
        
        sesion.token = access_token
        db.session.commit()
        
        return jsonify({
            'token': access_token,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.email,
                'roles': roles
            }
        }), 200
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado'}), 403
    
    usuarios = Usuario.query.all()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200

@app.route('/usuarios', methods=['POST'])
@jwt_required()
def crear_usuario():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Se requieren todos los campos'}), 400
    
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'El email ya está en uso'}), 400
    
    usuario = Usuario(
        nombre=data.get('nombre'),
        apellido=data.get('apellido'),
        email=data.get('email'),
        activo=data.get('activo', True)
    )
    usuario.set_password(data['password'])
    db.session.add(usuario)
    db.session.commit()
    
    roles_solicitados = data.get('roles', [])
    for rol_nombre in roles_solicitados:
        rol = Rol.query.filter_by(nombre=rol_nombre).first()
        if rol:
            rol_usuario = RolUsuario(usuario_id=usuario.id, rol_id=rol.id)
            db.session.add(rol_usuario)
    
    db.session.commit()
    return jsonify(usuario.to_dict()), 201

@app.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(usuario_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    
    if 'Administrador' not in roles and identity.get('usuario_id') != usuario_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    if data.get('nombre'):
        usuario.nombre = data['nombre']
    if data.get('apellido'):
        usuario.apellido = data['apellido']
    if data.get('email'):
        if Usuario.query.filter_by(email=data['email']).first() and data['email'] != usuario.email:
            return jsonify({'error': 'El email ya está en uso'}), 400
        usuario.email = data['email']
    if data.get('password'):
        usuario.set_password(data['password'])
    if 'activo' in data:
        usuario.activo = data['activo']
    
    db.session.commit()
    
    if 'Administrador' in roles and data.get('roles'):
        RolUsuario.query.filter_by(usuario_id=usuario_id).delete()
        for rol_nombre in data['roles']:
            rol = Rol.query.filter_by(nombre=rol_nombre).first()
            if rol:
                rol_usuario = RolUsuario(usuario_id=usuario_id, rol_id=rol.id)
                db.session.add(rol_usuario)
        db.session.commit()
    
    return jsonify(usuario.to_dict()), 200

@app.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(usuario_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado'}), 403
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    RolUsuario.query.filter_by(usuario_id=usuario_id).delete()
    SesionUsuario.query.filter_by(usuario_id=usuario_id).delete()
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({'mensaje': 'Usuario eliminado correctamente'}), 200

@app.route('/roles', methods=['GET'])
@jwt_required()
def obtener_roles():
    roles = Rol.query.all()
    return jsonify([rol.to_dict() for rol in roles]), 200

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    identity = get_jwt_identity()
    sesion_id = identity.get('sesion_id')
    
    if sesion_id:
        sesion = SesionUsuario.query.get(sesion_id)
        if sesion:
            sesion.cierre_sesion = datetime.datetime.utcnow()
            db.session.commit()
    
    return jsonify({'mensaje': 'Sesión cerrada correctamente'}), 200

@app.route('/verificar_token', methods=['GET'])
@jwt_required()
def verificar_token():
    identity = get_jwt_identity()
    return jsonify({
        'usuario_id': identity.get('usuario_id'),
        'email': identity.get('email'),
        'roles': identity.get('roles', [])
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
