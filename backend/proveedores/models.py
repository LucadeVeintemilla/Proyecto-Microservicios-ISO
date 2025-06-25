from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

db = SQLAlchemy()

class TipoProveedor(enum.Enum):
    CRITICO = "CRITICO"
    IMPORTANTE = "IMPORTANTE"
    ESTANDAR = "ESTANDAR"

class EstadoProveedor(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    EN_EVALUACION = "EN_EVALUACION"
    SUSPENDIDO = "SUSPENDIDO"

class NivelRiesgoProveedor(enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    ruc = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(255))
    telefono = Column(String(20))
    email = Column(String(100))
    sitio_web = Column(String(200))
    tipo = Column(Enum(TipoProveedor), nullable=False)
    estado = Column(Enum(EstadoProveedor), nullable=False, default=EstadoProveedor.EN_EVALUACION)
    nivel_riesgo = Column(Enum(NivelRiesgoProveedor), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    contactos = relationship('ContactoProveedor', back_populates='proveedor', cascade="all, delete-orphan")
    contratos = relationship('ContratoProveedor', back_populates='proveedor', cascade="all, delete-orphan")
    evaluaciones = relationship('EvaluacionProveedor', back_populates='proveedor', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'sitio_web': self.sitio_web,
            'tipo': self.tipo.value,
            'estado': self.estado.value,
            'nivel_riesgo': self.nivel_riesgo.value if self.nivel_riesgo else None,
            'fecha_registro': self.fecha_registro.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class ContactoProveedor(db.Model):
    __tablename__ = 'contactos_proveedor'
    
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    cargo = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))
    es_principal = Column(Boolean, default=False)
    
    proveedor = relationship('Proveedor', back_populates='contactos')
    
    def to_dict(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'nombre': self.nombre,
            'cargo': self.cargo,
            'telefono': self.telefono,
            'email': self.email,
            'es_principal': self.es_principal
        }

class ContratoProveedor(db.Model):
    __tablename__ = 'contratos_proveedor'
    
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    servicio = Column(String(200), nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    valor = Column(Float)
    moneda = Column(String(10), default='USD')
    incluye_acuerdo_confidencialidad = Column(Boolean, default=False)
    incluye_acuerdo_nivel_servicio = Column(Boolean, default=False)
    ruta_documento = Column(String(255))
    
    proveedor = relationship('Proveedor', back_populates='contratos')
    slas = relationship('AcuerdoNivelServicio', back_populates='contrato', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'servicio': self.servicio,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'valor': self.valor,
            'moneda': self.moneda,
            'incluye_acuerdo_confidencialidad': self.incluye_acuerdo_confidencialidad,
            'incluye_acuerdo_nivel_servicio': self.incluye_acuerdo_nivel_servicio,
            'ruta_documento': self.ruta_documento
        }

class AcuerdoNivelServicio(db.Model):
    __tablename__ = 'acuerdos_nivel_servicio'
    
    id = Column(Integer, primary_key=True)
    contrato_id = Column(Integer, ForeignKey('contratos_proveedor.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    metrica = Column(String(100), nullable=False)
    valor_objetivo = Column(Float, nullable=False)
    unidad = Column(String(50))
    frecuencia_medicion = Column(String(50))
    penalizacion = Column(String(200))
    
    contrato = relationship('ContratoProveedor', back_populates='slas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'contrato_id': self.contrato_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'metrica': self.metrica,
            'valor_objetivo': self.valor_objetivo,
            'unidad': self.unidad,
            'frecuencia_medicion': self.frecuencia_medicion,
            'penalizacion': self.penalizacion
        }

class CriterioEvaluacion(db.Model):
    __tablename__ = 'criterios_evaluacion'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(100), nullable=False)
    peso = Column(Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'categoria': self.categoria,
            'peso': self.peso
        }

class EvaluacionProveedor(db.Model):
    __tablename__ = 'evaluaciones_proveedor'
    
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    fecha_evaluacion = Column(DateTime, default=datetime.datetime.utcnow)
    evaluador = Column(Integer, nullable=False)  # ID del usuario
    puntuacion_total = Column(Float, nullable=False)
    observaciones = Column(Text)
    
    proveedor = relationship('Proveedor', back_populates='evaluaciones')
    criterios_evaluados = relationship('CriterioEvaluado', back_populates='evaluacion', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'fecha_evaluacion': self.fecha_evaluacion.isoformat(),
            'evaluador': self.evaluador,
            'puntuacion_total': self.puntuacion_total,
            'observaciones': self.observaciones
        }

class CriterioEvaluado(db.Model):
    __tablename__ = 'criterios_evaluados'
    
    id = Column(Integer, primary_key=True)
    evaluacion_id = Column(Integer, ForeignKey('evaluaciones_proveedor.id'), nullable=False)
    criterio_id = Column(Integer, ForeignKey('criterios_evaluacion.id'), nullable=False)
    puntuacion = Column(Float, nullable=False)
    comentario = Column(Text)
    
    evaluacion = relationship('EvaluacionProveedor', back_populates='criterios_evaluados')
    criterio = relationship('CriterioEvaluacion')
    
    def to_dict(self):
        return {
            'id': self.id,
            'evaluacion_id': self.evaluacion_id,
            'criterio_id': self.criterio_id,
            'puntuacion': self.puntuacion,
            'comentario': self.comentario
        }
