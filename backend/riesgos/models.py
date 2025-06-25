from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

db = SQLAlchemy()

class EstadoRiesgo(enum.Enum):
    IDENTIFICADO = "IDENTIFICADO"
    EN_ANALISIS = "EN_ANALISIS"
    MITIGADO = "MITIGADO"
    ACEPTADO = "ACEPTADO"
    TRANSFERIDO = "TRANSFERIDO"
    EVITADO = "EVITADO"

class TipoActivo(enum.Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    DATOS = "DATOS"
    PERSONAL = "PERSONAL"
    SERVICIOS = "SERVICIOS"
    INFRAESTRUCTURA = "INFRAESTRUCTURA"

class NivelImpacto(enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"

class NivelProbabilidad(enum.Enum):
    IMPROBABLE = "IMPROBABLE"
    POSIBLE = "POSIBLE"
    PROBABLE = "PROBABLE"
    CASI_SEGURO = "CASI_SEGURO"

class Activo(db.Model):
    __tablename__ = 'activos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tipo = Column(Enum(TipoActivo), nullable=False)
    valor = Column(Integer, nullable=False)  # Valor del activo (1-5)
    propietario = Column(String(100), nullable=False)
    ubicacion = Column(String(150))
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    riesgos = relationship('Riesgo', back_populates='activo')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo.value,
            'valor': self.valor,
            'propietario': self.propietario,
            'ubicacion': self.ubicacion,
            'fecha_registro': self.fecha_registro.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class Amenaza(db.Model):
    __tablename__ = 'amenazas'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False)
    origen = Column(String(50), nullable=False)  # Interno/Externo/Natural
    
    riesgos = relationship('Riesgo', back_populates='amenaza')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'origen': self.origen
        }

class Vulnerabilidad(db.Model):
    __tablename__ = 'vulnerabilidades'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False)
    
    riesgos = relationship('Riesgo', back_populates='vulnerabilidad')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo
        }

class Riesgo(db.Model):
    __tablename__ = 'riesgos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo_id = Column(Integer, ForeignKey('activos.id'), nullable=False)
    amenaza_id = Column(Integer, ForeignKey('amenazas.id'), nullable=False)
    vulnerabilidad_id = Column(Integer, ForeignKey('vulnerabilidades.id'), nullable=False)
    impacto = Column(Enum(NivelImpacto), nullable=False)
    probabilidad = Column(Enum(NivelProbabilidad), nullable=False)
    nivel_riesgo = Column(Float, nullable=False)  # Calculado: impacto * probabilidad
    estado = Column(Enum(EstadoRiesgo), nullable=False, default=EstadoRiesgo.IDENTIFICADO)
    fecha_identificacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    activo = relationship('Activo', back_populates='riesgos')
    amenaza = relationship('Amenaza', back_populates='riesgos')
    vulnerabilidad = relationship('Vulnerabilidad', back_populates='riesgos')
    controles = relationship('Control', back_populates='riesgo')
    planes_tratamiento = relationship('PlanTratamiento', back_populates='riesgo')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'activo_id': self.activo_id,
            'activo': self.activo.nombre,
            'amenaza_id': self.amenaza_id,
            'amenaza': self.amenaza.nombre,
            'vulnerabilidad_id': self.vulnerabilidad_id,
            'vulnerabilidad': self.vulnerabilidad.nombre,
            'impacto': self.impacto.value,
            'probabilidad': self.probabilidad.value,
            'nivel_riesgo': self.nivel_riesgo,
            'estado': self.estado.value,
            'fecha_identificacion': self.fecha_identificacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class Control(db.Model):
    __tablename__ = 'controles'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False)  # Preventivo, Detectivo, Correctivo
    efectividad = Column(Integer, nullable=False)  # 0-100%
    riesgo_id = Column(Integer, ForeignKey('riesgos.id'), nullable=False)
    implementado = Column(Boolean, default=False)
    fecha_implementacion = Column(DateTime, nullable=True)
    responsable = Column(String(100), nullable=False)
    
    riesgo = relationship('Riesgo', back_populates='controles')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'efectividad': self.efectividad,
            'riesgo_id': self.riesgo_id,
            'implementado': self.implementado,
            'fecha_implementacion': self.fecha_implementacion.isoformat() if self.fecha_implementacion else None,
            'responsable': self.responsable
        }

class PlanTratamiento(db.Model):
    __tablename__ = 'planes_tratamiento'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    riesgo_id = Column(Integer, ForeignKey('riesgos.id'), nullable=False)
    estrategia = Column(String(50), nullable=False)  # Mitigar, Aceptar, Transferir, Evitar
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    responsable = Column(String(100), nullable=False)
    progreso = Column(Integer, default=0)  # 0-100%
    costo_estimado = Column(Float, nullable=True)
    
    riesgo = relationship('Riesgo', back_populates='planes_tratamiento')
    actividades = relationship('ActividadTratamiento', back_populates='plan_tratamiento')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'riesgo_id': self.riesgo_id,
            'estrategia': self.estrategia,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'responsable': self.responsable,
            'progreso': self.progreso,
            'costo_estimado': self.costo_estimado
        }

class ActividadTratamiento(db.Model):
    __tablename__ = 'actividades_tratamiento'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    plan_tratamiento_id = Column(Integer, ForeignKey('planes_tratamiento.id'), nullable=False)
    estado = Column(String(50), nullable=False, default='PENDIENTE')  # PENDIENTE, EN_PROCESO, COMPLETADO
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    responsable = Column(String(100), nullable=False)
    
    plan_tratamiento = relationship('PlanTratamiento', back_populates='actividades')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'plan_tratamiento_id': self.plan_tratamiento_id,
            'estado': self.estado,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'responsable': self.responsable
        }

class KRI(db.Model):
    __tablename__ = 'kris'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    formula = Column(String(200), nullable=False)
    umbral_aceptable = Column(Float, nullable=False)
    umbral_critico = Column(Float, nullable=False)
    frecuencia_medicion = Column(String(50), nullable=False)  # Diario, Semanal, Mensual, Trimestral
    responsable = Column(String(100), nullable=False)
    
    mediciones = relationship('MedicionKRI', back_populates='kri')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'formula': self.formula,
            'umbral_aceptable': self.umbral_aceptable,
            'umbral_critico': self.umbral_critico,
            'frecuencia_medicion': self.frecuencia_medicion,
            'responsable': self.responsable
        }

class MedicionKRI(db.Model):
    __tablename__ = 'mediciones_kri'
    
    id = Column(Integer, primary_key=True)
    kri_id = Column(Integer, ForeignKey('kris.id'), nullable=False)
    fecha_medicion = Column(DateTime, default=datetime.datetime.utcnow)
    valor = Column(Float, nullable=False)
    comentarios = Column(Text)
    
    kri = relationship('KRI', back_populates='mediciones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'kri_id': self.kri_id,
            'fecha_medicion': self.fecha_medicion.isoformat(),
            'valor': self.valor,
            'comentarios': self.comentarios
        }
