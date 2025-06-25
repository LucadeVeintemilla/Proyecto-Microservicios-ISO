from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

db = SQLAlchemy()

class EstadoDocumento(enum.Enum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    PUBLICADO = "PUBLICADO"
    OBSOLETO = "OBSOLETO"

class TipoDocumento(enum.Enum):
    POLITICA = "POLITICA"
    PROCEDIMIENTO = "PROCEDIMIENTO"
    INSTRUCTIVO = "INSTRUCTIVO"
    FORMATO = "FORMATO"
    MANUAL = "MANUAL"
    EVIDENCIA = "EVIDENCIA"
    OTRO = "OTRO"

class Documento(db.Model):
    __tablename__ = 'documentos'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    tipo = Column(Enum(TipoDocumento), nullable=False)
    estado = Column(Enum(EstadoDocumento), nullable=False, default=EstadoDocumento.BORRADOR)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    creado_por = Column(Integer, nullable=False)  # ID del usuario
    propietario = Column(Integer, nullable=False)  # ID del usuario
    ruta_archivo = Column(String(255))
    palabras_clave = Column(String(255))
    
    versiones = relationship('VersionDocumento', back_populates='documento', cascade="all, delete-orphan")
    revisiones = relationship('RevisionDocumento', back_populates='documento', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo.value,
            'estado': self.estado.value,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_modificacion': self.fecha_modificacion.isoformat(),
            'creado_por': self.creado_por,
            'propietario': self.propietario,
            'ruta_archivo': self.ruta_archivo,
            'palabras_clave': self.palabras_clave
        }

class VersionDocumento(db.Model):
    __tablename__ = 'versiones_documentos'
    
    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey('documentos.id'), nullable=False)
    numero_version = Column(String(20), nullable=False)
    fecha_version = Column(DateTime, default=datetime.datetime.utcnow)
    creado_por = Column(Integer, nullable=False)  # ID del usuario
    ruta_archivo = Column(String(255))
    cambios = Column(Text)
    
    documento = relationship('Documento', back_populates='versiones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'documento_id': self.documento_id,
            'numero_version': self.numero_version,
            'fecha_version': self.fecha_version.isoformat(),
            'creado_por': self.creado_por,
            'ruta_archivo': self.ruta_archivo,
            'cambios': self.cambios
        }

class RevisionDocumento(db.Model):
    __tablename__ = 'revisiones_documentos'
    
    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey('documentos.id'), nullable=False)
    revisor_id = Column(Integer, nullable=False)  # ID del usuario
    fecha_asignacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_revision = Column(DateTime, nullable=True)
    estado = Column(String(50), nullable=False, default='PENDIENTE')  # PENDIENTE, APROBADO, RECHAZADO
    comentarios = Column(Text)
    
    documento = relationship('Documento', back_populates='revisiones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'documento_id': self.documento_id,
            'revisor_id': self.revisor_id,
            'fecha_asignacion': self.fecha_asignacion.isoformat(),
            'fecha_revision': self.fecha_revision.isoformat() if self.fecha_revision else None,
            'estado': self.estado,
            'comentarios': self.comentarios
        }

class CategoriaDocumento(db.Model):
    __tablename__ = 'categorias_documentos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    
    documentos_categorias = relationship('DocumentoCategoria', back_populates='categoria')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

class DocumentoCategoria(db.Model):
    __tablename__ = 'documentos_categorias'
    
    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey('documentos.id'), nullable=False)
    categoria_id = Column(Integer, ForeignKey('categorias_documentos.id'), nullable=False)
    
    documento = relationship('Documento')
    categoria = relationship('CategoriaDocumento', back_populates='documentos_categorias')

class EvidenciaCumplimiento(db.Model):
    __tablename__ = 'evidencias_cumplimiento'
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    requisito = Column(String(100), nullable=False)  # Requisito ISO 27001 relacionado
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    registrado_por = Column(Integer, nullable=False)  # ID del usuario
    ruta_archivo = Column(String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'requisito': self.requisito,
            'fecha_registro': self.fecha_registro.isoformat(),
            'registrado_por': self.registrado_por,
            'ruta_archivo': self.ruta_archivo
        }
