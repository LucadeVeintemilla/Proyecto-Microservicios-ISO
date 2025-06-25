from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
import datetime

db = SQLAlchemy()

# Tabla de asociación para la relación muchos a muchos entre roles y permisos
rol_permiso = Table('rol_permiso', db.Model.metadata,
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permiso_id', Integer, ForeignKey('permisos.id'), primary_key=True)
)

# Tabla de asociación para la relación muchos a muchos entre usuarios y roles
usuario_rol = Table('usuario_rol', db.Model.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    es_predefinido = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    permisos = relationship('Permiso', secondary=rol_permiso, back_populates='roles')
    usuarios = relationship('Usuario', secondary=usuario_rol, back_populates='roles')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'es_predefinido': self.es_predefinido,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'permisos': [p.to_dict_simple() for p in self.permisos]
        }
    
    def to_dict_simple(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

class Permiso(db.Model):
    __tablename__ = 'permisos'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(100), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    modulo = Column(String(50), nullable=False)
    es_critico = Column(Boolean, default=False)
    
    roles = relationship('Rol', secondary=rol_permiso, back_populates='permisos')
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'modulo': self.modulo,
            'es_critico': self.es_critico,
            'roles': [r.to_dict_simple() for r in self.roles]
        }
    
    def to_dict_simple(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'modulo': self.modulo
        }

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime)
    creado = Column(DateTime, default=datetime.datetime.utcnow)
    modificado = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    roles = relationship('Rol', secondary=usuario_rol, back_populates='usuarios')
    sesiones = relationship('SesionUsuario', back_populates='usuario', cascade="all, delete-orphan")
    logs_auditoria = relationship('LogAuditoria', back_populates='usuario', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre_usuario': self.nombre_usuario,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'roles': [r.to_dict_simple() for r in self.roles]
        }

class SesionUsuario(db.Model):
    __tablename__ = 'sesiones_usuario'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    token = Column(String(1024), nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    fecha_inicio = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_fin = Column(DateTime)
    activa = Column(Boolean, default=True)
    
    usuario = relationship('Usuario', back_populates='sesiones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'activa': self.activa
        }

class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
    accion = Column(String(100), nullable=False)
    modulo = Column(String(50), nullable=False)
    entidad = Column(String(50))
    entidad_id = Column(Integer)
    detalles = Column(Text)
    ip_address = Column(String(50))
    
    usuario = relationship('Usuario', back_populates='logs_auditoria')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.usuario.nombre_usuario if self.usuario else None,
            'fecha': self.fecha.isoformat(),
            'accion': self.accion,
            'modulo': self.modulo,
            'entidad': self.entidad,
            'entidad_id': self.entidad_id,
            'detalles': self.detalles,
            'ip_address': self.ip_address
        }

class ConflictoSegregacion(db.Model):
    __tablename__ = 'conflictos_segregacion'
    
    id = Column(Integer, primary_key=True)
    rol_a_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    rol_b_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    
    rol_a = relationship('Rol', foreign_keys=[rol_a_id])
    rol_b = relationship('Rol', foreign_keys=[rol_b_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'rol_a_id': self.rol_a_id,
            'rol_a_nombre': self.rol_a.nombre,
            'rol_b_id': self.rol_b_id,
            'rol_b_nombre': self.rol_b.nombre,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }
