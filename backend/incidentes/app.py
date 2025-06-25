from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Incidente, ActividadIncidente, SeveridadIncidente, PrioridadIncidente, EstadoIncidente

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure CORS to allow requests from frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
jwt = JWTManager(app)
db.init_app(app)

@app.route('/inicializar_db', methods=['POST'])
@jwt_required()
def inicializar_db():
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado'}), 403
    db.create_all()
    return jsonify({'mensaje': 'Base de datos de incidentes inicializada'}), 201

@app.route('/incidentes', methods=['GET'])
@jwt_required()
def obtener_incidentes():
    incidentes = Incidente.query.all()
    return jsonify([i.to_dict() for i in incidentes]), 200

@app.route('/incidentes', methods=['POST'])
@jwt_required()
def crear_incidente():
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    data = request.get_json()
    requerido = ['titulo', 'categoria', 'severidad', 'prioridad']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    incidente = Incidente(
        titulo=data['titulo'],
        descripcion=data.get('descripcion', ''),
        categoria=data['categoria'],
        severidad=SeveridadIncidente[data['severidad']],
        prioridad=PrioridadIncidente[data['prioridad']],
        estado=EstadoIncidente.ABIERTO,
        reportado_por=usuario_id,
        responsable=data.get('responsable')
    )
    db.session.add(incidente)
    db.session.commit()
    
    # Registrar actividad inicial
    actividad = ActividadIncidente(
        incidente_id=incidente.id,
        descripcion=f"Incidente reportado: {data['titulo']}",
        responsable=usuario_id
    )
    db.session.add(actividad)
    db.session.commit()
    
    return jsonify(incidente.to_dict()), 201

@app.route('/incidentes/<int:incidente_id>', methods=['GET'])
@jwt_required()
def obtener_incidente(incidente_id):
    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({'error': 'Incidente no encontrado'}), 404
    
    resultado = incidente.to_dict()
    actividades = ActividadIncidente.query.filter_by(incidente_id=incidente_id).all()
    resultado['actividades'] = [a.to_dict() for a in actividades]
    
    return jsonify(resultado), 200

@app.route('/incidentes/<int:incidente_id>', methods=['PUT'])
@jwt_required()
def actualizar_incidente(incidente_id):
    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({'error': 'Incidente no encontrado'}), 404
    
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    # Campos básicos que pueden actualizarse
    for campo in ['titulo', 'descripcion', 'categoria', 'causa_raiz', 'responsable']:
        if campo in data:
            setattr(incidente, campo, data[campo])
    
    # Campos de fecha
    if 'fecha_reporte' in data and data['fecha_reporte']:
        try:
            incidente.fecha_reporte = datetime.datetime.fromisoformat(data['fecha_reporte'].replace('Z', '+00:00'))
            print(f"Actualizando fecha_reporte a: {incidente.fecha_reporte}")
        except Exception as e:
            print(f"Error al procesar fecha_reporte: {e}")
    
    if 'fecha_cierre' in data and data['fecha_cierre']:
        try:
            incidente.fecha_cierre = datetime.datetime.fromisoformat(data['fecha_cierre'].replace('Z', '+00:00'))
            print(f"Actualizando fecha_cierre a: {incidente.fecha_cierre}")
        except Exception as e:
            print(f"Error al procesar fecha_cierre: {e}")
    
    # Campos enumerados
    if 'severidad' in data:
        incidente.severidad = SeveridadIncidente[data['severidad']]
    if 'prioridad' in data:
        incidente.prioridad = PrioridadIncidente[data['prioridad']]
    
    # Cambio de estado
    estado_anterior = incidente.estado
    if 'estado' in data:
        nuevo_estado = EstadoIncidente[data['estado']]
        incidente.estado = nuevo_estado
        
        # Si se cierra el incidente y no hay fecha de cierre, registrar fecha de cierre
        if nuevo_estado == EstadoIncidente.CERRADO and estado_anterior != EstadoIncidente.CERRADO and not incidente.fecha_cierre:
            incidente.fecha_cierre = datetime.datetime.utcnow()
            print(f"Estableciendo fecha_cierre automática: {incidente.fecha_cierre}")
        
        # Registrar actividad de cambio de estado
        if estado_anterior != nuevo_estado:
            actividad = ActividadIncidente(
                incidente_id=incidente_id,
                descripcion=f"Estado cambiado de {estado_anterior.value} a {nuevo_estado.value}",
                responsable=usuario_id
            )
            db.session.add(actividad)
    
    db.session.commit()
    return jsonify(incidente.to_dict()), 200

@app.route('/incidentes/<int:incidente_id>/actividades', methods=['POST'])
@jwt_required()
def agregar_actividad(incidente_id):
    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({'error': 'Incidente no encontrado'}), 404
    
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    if not data.get('descripcion'):
        return jsonify({'error': 'Descripción de actividad requerida'}), 400
    
    actividad = ActividadIncidente(
        incidente_id=incidente_id,
        descripcion=data['descripcion'],
        responsable=usuario_id
    )
    db.session.add(actividad)
    db.session.commit()
    
    return jsonify(actividad.to_dict()), 201

@app.route('/incidentes/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas():
    total = Incidente.query.count()
    abiertos = Incidente.query.filter_by(estado=EstadoIncidente.ABIERTO).count()
    en_investigacion = Incidente.query.filter_by(estado=EstadoIncidente.EN_INVESTIGACION).count()
    resueltos = Incidente.query.filter_by(estado=EstadoIncidente.RESUELTO).count()
    cerrados = Incidente.query.filter_by(estado=EstadoIncidente.CERRADO).count()
    
    por_severidad = {
        'BAJA': Incidente.query.filter_by(severidad=SeveridadIncidente.BAJA).count(),
        'MEDIA': Incidente.query.filter_by(severidad=SeveridadIncidente.MEDIA).count(),
        'ALTA': Incidente.query.filter_by(severidad=SeveridadIncidente.ALTA).count(),
        'CRITICA': Incidente.query.filter_by(severidad=SeveridadIncidente.CRITICA).count()
    }
    
    por_prioridad = {
        'BAJA': Incidente.query.filter_by(prioridad=PrioridadIncidente.BAJA).count(),
        'MEDIA': Incidente.query.filter_by(prioridad=PrioridadIncidente.MEDIA).count(),
        'ALTA': Incidente.query.filter_by(prioridad=PrioridadIncidente.ALTA).count()
    }
    
    return jsonify({
        'total': total,
        'por_estado': {
            'ABIERTO': abiertos,
            'EN_INVESTIGACION': en_investigacion,
            'RESUELTO': resueltos,
            'CERRADO': cerrados
        },
        'por_severidad': por_severidad,
        'por_prioridad': por_prioridad
    }), 200

@app.route('/incidentes/<int:incidente_id>', methods=['DELETE'])
@jwt_required()
def eliminar_incidente(incidente_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado para eliminar incidentes'}), 403
    
    incidente = Incidente.query.get(incidente_id)
    if not incidente:
        return jsonify({'error': 'Incidente no encontrado'}), 404
    
    db.session.delete(incidente)
    db.session.commit()
    
    return jsonify({'mensaje': 'Incidente eliminado correctamente'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
