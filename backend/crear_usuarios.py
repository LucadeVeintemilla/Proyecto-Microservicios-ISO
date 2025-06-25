import sys
import os
from flask import Flask
import datetime

# Añadir el directorio actual al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
from auth.models import db, Usuario, Rol, RolUsuario

# Crear una aplicación Flask para usar el contexto de la base de datos
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def crear_usuario(nombre, apellido, email, password, roles_nombres):
    """
    Crea un nuevo usuario con los roles especificados
    """
    # Verificar si el usuario ya existe
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        print(f"El usuario con email {email} ya existe.")
        return usuario_existente
    
    # Crear el nuevo usuario
    nuevo_usuario = Usuario(
        nombre=nombre,
        apellido=apellido,
        email=email,
        activo=True
    )
    nuevo_usuario.set_password(password)
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    # Asignar roles al usuario
    for rol_nombre in roles_nombres:
        rol = Rol.query.filter_by(nombre=rol_nombre).first()
        if rol:
            rol_usuario = RolUsuario(usuario_id=nuevo_usuario.id, rol_id=rol.id)
            db.session.add(rol_usuario)
        else:
            print(f"Rol {rol_nombre} no encontrado.")
    
    db.session.commit()
    print(f"Usuario {nombre} {apellido} ({email}) creado exitosamente con roles: {', '.join(roles_nombres)}")
    return nuevo_usuario

def main():
    """
    Función principal que crea usuarios de ejemplo para diferentes roles
    """
    with app.app_context():
        # Lista de usuarios a crear con sus roles
        usuarios = [
            {
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan.perez@sgsi.com',
                'password': 'Usuario123!',
                'roles': ['GestorRiesgos']
            },
            {
                'nombre': 'María',
                'apellido': 'González',
                'email': 'maria.gonzalez@sgsi.com',
                'password': 'Usuario123!',
                'roles': ['Auditor']
            },
            {
                'nombre': 'Carlos',
                'apellido': 'Rodríguez',
                'email': 'carlos.rodriguez@sgsi.com',
                'password': 'Usuario123!',
                'roles': ['Usuario']
            },
            {
                'nombre': 'Ana',
                'apellido': 'Martínez',
                'email': 'ana.martinez@sgsi.com',
                'password': 'Usuario123!',
                'roles': ['GestorRiesgos', 'Auditor']
            },
            {
                'nombre': 'Luis',
                'apellido': 'Sánchez',
                'email': 'luis.sanchez@sgsi.com',
                'password': 'Usuario123!',
                'roles': ['Usuario', 'Auditor']
            }
        ]
        
        print("Iniciando creación de usuarios...")
        for usuario_data in usuarios:
            crear_usuario(
                usuario_data['nombre'],
                usuario_data['apellido'],
                usuario_data['email'],
                usuario_data['password'],
                usuario_data['roles']
            )
        
        print("\nUsuarios creados exitosamente. Resumen:")
        todos_usuarios = Usuario.query.all()
        for usuario in todos_usuarios:
            roles_usuario = RolUsuario.query.filter_by(usuario_id=usuario.id).all()
            roles_nombres = [Rol.query.get(ru.rol_id).nombre for ru in roles_usuario]
            print(f"- {usuario.nombre} {usuario.apellido} ({usuario.email}): {', '.join(roles_nombres)}")

if __name__ == "__main__":
    main()
