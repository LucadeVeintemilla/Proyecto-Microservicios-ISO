from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Proveedor, ContactoProveedor, ContratoProveedor, AcuerdoNivelServicio, CriterioEvaluacion, EvaluacionProveedor, CriterioEvaluado, TipoProveedor, EstadoProveedor, NivelRiesgoProveedor

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
    
    # Crear criterios de evaluación iniciales
    criterios_iniciales = [
        {'nombre': 'Calidad del servicio', 'categoria': 'Operacional', 'peso': 0.25, 'descripcion': 'Evalúa la calidad del servicio o producto entregado'},
        {'nombre': 'Cumplimiento de plazos', 'categoria': 'Operacional', 'peso': 0.20, 'descripcion': 'Evalúa el cumplimiento de los plazos acordados'},
        {'nombre': 'Seguridad de la información', 'categoria': 'Seguridad', 'peso': 0.20, 'descripcion': 'Evalúa las medidas de seguridad implementadas'},
        {'nombre': 'Capacidad de respuesta', 'categoria': 'Soporte', 'peso': 0.15, 'descripcion': 'Evalúa la capacidad de respuesta ante incidentes'},
        {'nombre': 'Relación precio-calidad', 'categoria': 'Financiero', 'peso': 0.10, 'descripcion': 'Evalúa la relación entre el precio y la calidad'},
        {'nombre': 'Estabilidad financiera', 'categoria': 'Financiero', 'peso': 0.10, 'descripcion': 'Evalúa la estabilidad financiera del proveedor'}
    ]
    
    for criterio_data in criterios_iniciales:
        if not CriterioEvaluacion.query.filter_by(nombre=criterio_data['nombre']).first():
            criterio = CriterioEvaluacion(
                nombre=criterio_data['nombre'],
                descripcion=criterio_data['descripcion'],
                categoria=criterio_data['categoria'],
                peso=criterio_data['peso']
            )
            db.session.add(criterio)
    
    db.session.commit()
    return jsonify({'mensaje': 'Base de datos de proveedores inicializada'}), 201

# --- Proveedores ---
@app.route('/proveedores', methods=['GET'])
@jwt_required()
def obtener_proveedores():
    proveedores = Proveedor.query.all()
    return jsonify([p.to_dict() for p in proveedores]), 200

@app.route('/proveedores', methods=['POST'])
@jwt_required()
def crear_proveedor():
    data = request.get_json()
    requerido = ['nombre', 'ruc', 'tipo']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if Proveedor.query.filter_by(ruc=data['ruc']).first():
        return jsonify({'error': 'Ya existe un proveedor con ese RUC'}), 400
    
    proveedor = Proveedor(
        nombre=data['nombre'],
        ruc=data['ruc'],
        direccion=data.get('direccion', ''),
        telefono=data.get('telefono', ''),
        email=data.get('email', ''),
        sitio_web=data.get('sitio_web', ''),
        tipo=TipoProveedor[data['tipo']],
        estado=EstadoProveedor.EN_EVALUACION
    )
    db.session.add(proveedor)
    db.session.commit()
    return jsonify(proveedor.to_dict()), 201

@app.route('/proveedores/<int:proveedor_id>', methods=['GET'])
@jwt_required()
def obtener_proveedor(proveedor_id):
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    resultado = proveedor.to_dict()
    
    # Obtener contactos
    contactos = ContactoProveedor.query.filter_by(proveedor_id=proveedor_id).all()
    resultado['contactos'] = [c.to_dict() for c in contactos]
    
    # Obtener contratos
    contratos = ContratoProveedor.query.filter_by(proveedor_id=proveedor_id).all()
    resultado['contratos'] = [c.to_dict() for c in contratos]
    
    # Obtener evaluaciones
    evaluaciones = EvaluacionProveedor.query.filter_by(proveedor_id=proveedor_id).all()
    resultado['evaluaciones'] = [e.to_dict() for e in evaluaciones]
    
    return jsonify(resultado), 200

@app.route('/proveedores/<int:proveedor_id>', methods=['PUT'])
@jwt_required()
def actualizar_proveedor(proveedor_id):
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    data = request.get_json()
    
    # Actualizar campos básicos
    for campo in ['nombre', 'direccion', 'telefono', 'email', 'sitio_web']:
        if campo in data:
            setattr(proveedor, campo, data[campo])
    
    # Actualizar campos enumerados
    if 'tipo' in data:
        proveedor.tipo = TipoProveedor[data['tipo']]
    if 'estado' in data:
        proveedor.estado = EstadoProveedor[data['estado']]
    if 'nivel_riesgo' in data:
        proveedor.nivel_riesgo = NivelRiesgoProveedor[data['nivel_riesgo']] if data['nivel_riesgo'] else None
    
    db.session.commit()
    return jsonify(proveedor.to_dict()), 200

@app.route('/proveedores/<int:proveedor_id>', methods=['DELETE'])
@jwt_required()
def eliminar_proveedor(proveedor_id):
    identity = get_jwt_identity()
    roles = identity.get('roles', [])
    if 'Administrador' not in roles:
        return jsonify({'error': 'No autorizado'}), 403
    
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    db.session.delete(proveedor)
    db.session.commit()
    return jsonify({'mensaje': 'Proveedor eliminado correctamente'}), 200

# --- Contactos ---
@app.route('/proveedores/<int:proveedor_id>/contactos', methods=['POST'])
@jwt_required()
def crear_contacto(proveedor_id):
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    data = request.get_json()
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre de contacto requerido'}), 400
    
    contacto = ContactoProveedor(
        proveedor_id=proveedor_id,
        nombre=data['nombre'],
        cargo=data.get('cargo', ''),
        telefono=data.get('telefono', ''),
        email=data.get('email', ''),
        es_principal=data.get('es_principal', False)
    )
    
    # Si este contacto es principal, desmarcar otros contactos principales
    if contacto.es_principal:
        ContactoProveedor.query.filter_by(proveedor_id=proveedor_id, es_principal=True).update({'es_principal': False})
    
    db.session.add(contacto)
    db.session.commit()
    return jsonify(contacto.to_dict()), 201

@app.route('/contactos/<int:contacto_id>', methods=['PUT'])
@jwt_required()
def actualizar_contacto(contacto_id):
    contacto = ContactoProveedor.query.get(contacto_id)
    if not contacto:
        return jsonify({'error': 'Contacto no encontrado'}), 404
    
    data = request.get_json()
    for campo in ['nombre', 'cargo', 'telefono', 'email']:
        if campo in data:
            setattr(contacto, campo, data[campo])
    
    if 'es_principal' in data and data['es_principal'] and not contacto.es_principal:
        ContactoProveedor.query.filter_by(proveedor_id=contacto.proveedor_id, es_principal=True).update({'es_principal': False})
        contacto.es_principal = True
    elif 'es_principal' in data:
        contacto.es_principal = data['es_principal']
    
    db.session.commit()
    return jsonify(contacto.to_dict()), 200

@app.route('/contactos/<int:contacto_id>', methods=['DELETE'])
@jwt_required()
def eliminar_contacto(contacto_id):
    contacto = ContactoProveedor.query.get(contacto_id)
    if not contacto:
        return jsonify({'error': 'Contacto no encontrado'}), 404
    
    db.session.delete(contacto)
    db.session.commit()
    return jsonify({'mensaje': 'Contacto eliminado correctamente'}), 200

# --- Contratos ---
@app.route('/proveedores/<int:proveedor_id>/contratos', methods=['POST'])
@jwt_required()
def crear_contrato(proveedor_id):
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    data = request.get_json()
    requerido = ['codigo', 'servicio', 'fecha_inicio', 'fecha_fin']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if ContratoProveedor.query.filter_by(codigo=data['codigo']).first():
        return jsonify({'error': 'Ya existe un contrato con ese código'}), 400
    
    contrato = ContratoProveedor(
        proveedor_id=proveedor_id,
        codigo=data['codigo'],
        descripcion=data.get('descripcion', ''),
        servicio=data['servicio'],
        fecha_inicio=datetime.datetime.fromisoformat(data['fecha_inicio']),
        fecha_fin=datetime.datetime.fromisoformat(data['fecha_fin']),
        valor=data.get('valor'),
        moneda=data.get('moneda', 'USD'),
        incluye_acuerdo_confidencialidad=data.get('incluye_acuerdo_confidencialidad', False),
        incluye_acuerdo_nivel_servicio=data.get('incluye_acuerdo_nivel_servicio', False),
        ruta_documento=data.get('ruta_documento', '')
    )
    db.session.add(contrato)
    db.session.commit()
    return jsonify(contrato.to_dict()), 201

@app.route('/contratos/<int:contrato_id>', methods=['PUT'])
@jwt_required()
def actualizar_contrato(contrato_id):
    contrato = ContratoProveedor.query.get(contrato_id)
    if not contrato:
        return jsonify({'error': 'Contrato no encontrado'}), 404
    
    data = request.get_json()
    
    for campo in ['descripcion', 'servicio', 'valor', 'moneda', 'incluye_acuerdo_confidencialidad', 
                 'incluye_acuerdo_nivel_servicio', 'ruta_documento']:
        if campo in data:
            setattr(contrato, campo, data[campo])
    
    if 'fecha_inicio' in data:
        contrato.fecha_inicio = datetime.datetime.fromisoformat(data['fecha_inicio'])
    if 'fecha_fin' in data:
        contrato.fecha_fin = datetime.datetime.fromisoformat(data['fecha_fin'])
    
    db.session.commit()
    return jsonify(contrato.to_dict()), 200

@app.route('/contratos/<int:contrato_id>/sla', methods=['POST'])
@jwt_required()
def crear_sla(contrato_id):
    contrato = ContratoProveedor.query.get(contrato_id)
    if not contrato:
        return jsonify({'error': 'Contrato no encontrado'}), 404
    
    data = request.get_json()
    requerido = ['nombre', 'metrica', 'valor_objetivo']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    sla = AcuerdoNivelServicio(
        contrato_id=contrato_id,
        nombre=data['nombre'],
        descripcion=data.get('descripcion', ''),
        metrica=data['metrica'],
        valor_objetivo=float(data['valor_objetivo']),
        unidad=data.get('unidad', ''),
        frecuencia_medicion=data.get('frecuencia_medicion', ''),
        penalizacion=data.get('penalizacion', '')
    )
    db.session.add(sla)
    
    # Actualizar contrato para indicar que incluye SLA
    contrato.incluye_acuerdo_nivel_servicio = True
    
    db.session.commit()
    return jsonify(sla.to_dict()), 201

# --- Evaluaciones ---
@app.route('/criterios-evaluacion', methods=['GET'])
@jwt_required()
def obtener_criterios():
    criterios = CriterioEvaluacion.query.all()
    return jsonify([c.to_dict() for c in criterios]), 200

@app.route('/proveedores/<int:proveedor_id>/evaluaciones', methods=['POST'])
@jwt_required()
def crear_evaluacion(proveedor_id):
    proveedor = Proveedor.query.get(proveedor_id)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    data = request.get_json()
    if 'criterios' not in data or not isinstance(data['criterios'], list):
        return jsonify({'error': 'Se requieren criterios de evaluación'}), 400
    
    # Calcular puntuación total
    puntuacion_total = 0
    criterios_evaluados = []
    
    for criterio_data in data['criterios']:
        if 'criterio_id' not in criterio_data or 'puntuacion' not in criterio_data:
            return jsonify({'error': 'Datos de criterio incompletos'}), 400
        
        criterio = CriterioEvaluacion.query.get(criterio_data['criterio_id'])
        if not criterio:
            return jsonify({'error': f'Criterio {criterio_data["criterio_id"]} no encontrado'}), 404
        
        puntuacion = float(criterio_data['puntuacion'])
        if puntuacion < 0 or puntuacion > 5:
            return jsonify({'error': 'La puntuación debe estar entre 0 y 5'}), 400
        
        puntuacion_total += puntuacion * criterio.peso
        criterios_evaluados.append({
            'criterio_id': criterio.id,
            'puntuacion': puntuacion,
            'comentario': criterio_data.get('comentario', '')
        })
    
    # Crear evaluación
    evaluacion = EvaluacionProveedor(
        proveedor_id=proveedor_id,
        evaluador=usuario_id,
        puntuacion_total=round(puntuacion_total, 2),
        observaciones=data.get('observaciones', '')
    )
    db.session.add(evaluacion)
    db.session.flush()  # Para obtener el ID de la evaluación
    
    # Crear criterios evaluados
    for criterio_data in criterios_evaluados:
        criterio_evaluado = CriterioEvaluado(
            evaluacion_id=evaluacion.id,
            criterio_id=criterio_data['criterio_id'],
            puntuacion=criterio_data['puntuacion'],
            comentario=criterio_data['comentario']
        )
        db.session.add(criterio_evaluado)
    
    # Actualizar nivel de riesgo del proveedor basado en la puntuación
    if puntuacion_total >= 4:
        proveedor.nivel_riesgo = NivelRiesgoProveedor.BAJO
    elif puntuacion_total >= 3:
        proveedor.nivel_riesgo = NivelRiesgoProveedor.MEDIO
    elif puntuacion_total >= 2:
        proveedor.nivel_riesgo = NivelRiesgoProveedor.ALTO
    else:
        proveedor.nivel_riesgo = NivelRiesgoProveedor.CRITICO
    
    # Si es la primera evaluación, cambiar estado de proveedor a ACTIVO
    if proveedor.estado == EstadoProveedor.EN_EVALUACION:
        proveedor.estado = EstadoProveedor.ACTIVO
    
    db.session.commit()
    
    return jsonify(evaluacion.to_dict()), 201

@app.route('/evaluaciones/<int:evaluacion_id>', methods=['GET'])
@jwt_required()
def obtener_evaluacion(evaluacion_id):
    evaluacion = EvaluacionProveedor.query.get(evaluacion_id)
    if not evaluacion:
        return jsonify({'error': 'Evaluación no encontrada'}), 404
    
    resultado = evaluacion.to_dict()
    
    # Obtener criterios evaluados con detalles
    criterios_evaluados = []
    for ce in CriterioEvaluado.query.filter_by(evaluacion_id=evaluacion_id).all():
        criterio = CriterioEvaluacion.query.get(ce.criterio_id)
        criterios_evaluados.append({
            'id': ce.id,
            'criterio_id': ce.criterio_id,
            'nombre_criterio': criterio.nombre,
            'categoria': criterio.categoria,
            'peso': criterio.peso,
            'puntuacion': ce.puntuacion,
            'comentario': ce.comentario
        })
    
    resultado['criterios_evaluados'] = criterios_evaluados
    
    return jsonify(resultado), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)
