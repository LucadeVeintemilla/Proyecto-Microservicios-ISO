from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime
import bcrypt

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime, nullable=True)
    creado = Column(DateTime, default=datetime.datetime.utcnow)
    modificado = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    roles_usuarios = relationship('RolUsuario', back_populates='usuario')
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'creado': self.creado.isoformat(),
            'modificado': self.modificado.isoformat()
        }

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(200))
    
    roles_usuarios = relationship('RolUsuario', back_populates='rol')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

class RolUsuario(db.Model):
    __tablename__ = 'roles_usuarios'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    
    usuario = relationship('Usuario', back_populates='roles_usuarios')
    rol = relationship('Rol', back_populates='roles_usuarios')

class Permiso(db.Model):
    __tablename__ = 'permisos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    modulo = Column(String(50), nullable=False)
    descripcion = Column(String(200))
    
    roles_permisos = relationship('RolPermiso', back_populates='permiso')

class RolPermiso(db.Model):
    __tablename__ = 'roles_permisos'
    
    id = Column(Integer, primary_key=True)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    permiso_id = Column(Integer, ForeignKey('permisos.id'), nullable=False)
    
    rol = relationship('Rol')
    permiso = relationship('Permiso', back_populates='roles_permisos')

class SesionUsuario(db.Model):
    __tablename__ = 'sesiones_usuarios'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    token = Column(String(1024), nullable=False)
    ip = Column(String(45), nullable=False)
    navegador = Column(String(255), nullable=True)
    inicio_sesion = Column(DateTime, default=datetime.datetime.utcnow)
    ultimo_acceso = Column(DateTime, default=datetime.datetime.utcnow)
    cierre_sesion = Column(DateTime, nullable=True)
    
    usuario = relationship('Usuario')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'ip': self.ip,
            'navegador': self.navegador,
            'inicio_sesion': self.inicio_sesion.isoformat(),
            'ultimo_acceso': self.ultimo_acceso.isoformat(),
            'cierre_sesion': self.cierre_sesion.isoformat() if self.cierre_sesion else None
        }
