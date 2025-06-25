from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import datetime
import enum

db = SQLAlchemy()

class SeveridadIncidente(enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"

class PrioridadIncidente(enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"

class EstadoIncidente(enum.Enum):
    ABIERTO = "ABIERTO"
    EN_INVESTIGACION = "EN_INVESTIGACION"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"

class Incidente(db.Model):
    __tablename__ = 'incidentes'
    id = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(100), nullable=False)
    severidad = Column(Enum(SeveridadIncidente), nullable=False)
    prioridad = Column(Enum(PrioridadIncidente), nullable=False)
    estado = Column(Enum(EstadoIncidente), nullable=False, default=EstadoIncidente.ABIERTO)
    fecha_reporte = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)
    reportado_por = Column(Integer, nullable=False)  # ID usuario
    responsable = Column(Integer, nullable=True)  # ID usuario
    causa_raiz = Column(Text)

    actividades = relationship('ActividadIncidente', back_populates='incidente', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'categoria': self.categoria,
            'severidad': self.severidad.value,
            'prioridad': self.prioridad.value,
            'estado': self.estado.value,
            'fecha_reporte': self.fecha_reporte.isoformat(),
            'fecha_cierre': self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            'reportado_por': self.reportado_por,
            'responsable': self.responsable,
            'causa_raiz': self.causa_raiz
        }

class ActividadIncidente(db.Model):
    __tablename__ = 'actividades_incidente'
    id = Column(Integer, primary_key=True)
    incidente_id = Column(Integer, ForeignKey('incidentes.id'), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
    responsable = Column(Integer, nullable=False)

    incidente = relationship('Incidente', back_populates='actividades')

    def to_dict(self):
        return {
            'id': self.id,
            'incidente_id': self.incidente_id,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat(),
            'responsable': self.responsable
        }
