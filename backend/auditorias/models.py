from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

db = SQLAlchemy()

class EstadoAuditoria(enum.Enum):
    PLANIFICADA = "PLANIFICADA"
    EN_EJECUCION = "EN_EJECUCION"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"

class TipoAuditoria(enum.Enum):
    INTERNA = "INTERNA"
    EXTERNA = "EXTERNA"
    SEGUIMIENTO = "SEGUIMIENTO"
    CUMPLIMIENTO = "CUMPLIMIENTO"

class EstadoHallazgo(enum.Enum):
    IDENTIFICADO = "IDENTIFICADO"
    EN_ANALISIS = "EN_ANALISIS"
    EN_TRATAMIENTO = "EN_TRATAMIENTO"
    CERRADO = "CERRADO"
    VERIFICADO = "VERIFICADO"

class Auditoria(db.Model):
    __tablename__ = 'auditorias'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    tipo = Column(Enum(TipoAuditoria), nullable=False)
    estado = Column(Enum(EstadoAuditoria), nullable=False, default=EstadoAuditoria.PLANIFICADA)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    auditor_lider = Column(Integer, nullable=False)  # ID del usuario
    equipo_auditores = Column(String(255))  # IDs de usuarios separados por comas
    alcance = Column(Text)
    objetivos = Column(Text)
    criterios = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    hallazgos = relationship('Hallazgo', back_populates='auditoria', cascade="all, delete-orphan")
    listas_verificacion = relationship('ListaVerificacion', back_populates='auditoria', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo.value,
            'estado': self.estado.value,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'auditor_lider': self.auditor_lider,
            'equipo_auditores': self.equipo_auditores,
            'alcance': self.alcance,
            'objetivos': self.objetivos,
            'criterios': self.criterios,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

class ListaVerificacion(db.Model):
    __tablename__ = 'listas_verificacion'
    
    id = Column(Integer, primary_key=True)
    auditoria_id = Column(Integer, ForeignKey('auditorias.id'), nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    
    auditoria = relationship('Auditoria', back_populates='listas_verificacion')
    criterios = relationship('CriterioVerificacion', back_populates='lista_verificacion', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'auditoria_id': self.auditoria_id,
            'titulo': self.titulo,
            'descripcion': self.descripcion
        }

class CriterioVerificacion(db.Model):
    __tablename__ = 'criterios_verificacion'
    
    id = Column(Integer, primary_key=True)
    lista_verificacion_id = Column(Integer, ForeignKey('listas_verificacion.id'), nullable=False)
    criterio = Column(Text, nullable=False)
    referencia = Column(String(200))  # Referencia a norma o requisito
    cumple = Column(Boolean, nullable=True)
    observaciones = Column(Text)
    evidencia = Column(String(255))
    
    lista_verificacion = relationship('ListaVerificacion', back_populates='criterios')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lista_verificacion_id': self.lista_verificacion_id,
            'criterio': self.criterio,
            'referencia': self.referencia,
            'cumple': self.cumple,
            'observaciones': self.observaciones,
            'evidencia': self.evidencia
        }

class Hallazgo(db.Model):
    __tablename__ = 'hallazgos'
    
    id = Column(Integer, primary_key=True)
    auditoria_id = Column(Integer, ForeignKey('auditorias.id'), nullable=False)
    codigo = Column(String(50), nullable=False)
    tipo = Column(String(50), nullable=False)  # No conformidad mayor, menor, observación, oportunidad de mejora
    descripcion = Column(Text, nullable=False)
    criterio_incumplido = Column(Text)
    evidencia = Column(Text)
    area_responsable = Column(String(100))
    estado = Column(Enum(EstadoHallazgo), nullable=False, default=EstadoHallazgo.IDENTIFICADO)
    fecha_identificacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    auditoria = relationship('Auditoria', back_populates='hallazgos')
    planes_accion = relationship('PlanAccion', back_populates='hallazgo', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'auditoria_id': self.auditoria_id,
            'codigo': self.codigo,
            'tipo': self.tipo,
            'descripcion': self.descripcion,
            'criterio_incumplido': self.criterio_incumplido,
            'evidencia': self.evidencia,
            'area_responsable': self.area_responsable,
            'estado': self.estado.value,
            'fecha_identificacion': self.fecha_identificacion.isoformat() if self.fecha_identificacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

class PlanAccion(db.Model):
    __tablename__ = 'planes_accion'
    
    id = Column(Integer, primary_key=True)
    hallazgo_id = Column(Integer, ForeignKey('hallazgos.id'), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_accion = Column(String(50), nullable=False)  # Correctiva, Preventiva, Mejora
    responsable = Column(Integer, nullable=False)  # ID del usuario
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin_planificada = Column(DateTime, nullable=False)
    fecha_fin_real = Column(DateTime, nullable=True)
    estado = Column(String(50), nullable=False, default='PENDIENTE')  # PENDIENTE, EN_PROCESO, COMPLETADO, VERIFICADO
    resultado = Column(Text)
    eficacia = Column(Boolean, nullable=True)
    
    hallazgo = relationship('Hallazgo', back_populates='planes_accion')
    actividades = relationship('ActividadPlanAccion', back_populates='plan_accion', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'hallazgo_id': self.hallazgo_id,
            'descripcion': self.descripcion,
            'tipo_accion': self.tipo_accion,
            'responsable': self.responsable,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin_planificada': self.fecha_fin_planificada.isoformat() if self.fecha_fin_planificada else None,
            'fecha_fin_real': self.fecha_fin_real.isoformat() if self.fecha_fin_real else None,
            'estado': self.estado,
            'resultado': self.resultado,
            'eficacia': self.eficacia
        }

class ActividadPlanAccion(db.Model):
    __tablename__ = 'actividades_plan_accion'
    
    id = Column(Integer, primary_key=True)
    plan_accion_id = Column(Integer, ForeignKey('planes_accion.id'), nullable=False)
    descripcion = Column(Text, nullable=False)
    responsable = Column(Integer, nullable=False)  # ID del usuario
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin_planificada = Column(DateTime, nullable=False)
    fecha_fin_real = Column(DateTime, nullable=True)
    estado = Column(String(50), nullable=False, default='PENDIENTE')  # PENDIENTE, EN_PROCESO, COMPLETADO
    evidencia = Column(String(255))
    
    plan_accion = relationship('PlanAccion', back_populates='actividades')
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_accion_id': self.plan_accion_id,
            'descripcion': self.descripcion,
            'responsable': self.responsable,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin_planificada': self.fecha_fin_planificada.isoformat() if self.fecha_fin_planificada else None,
            'fecha_fin_real': self.fecha_fin_real.isoformat() if self.fecha_fin_real else None,
            'estado': self.estado,
            'evidencia': self.evidencia
        }
