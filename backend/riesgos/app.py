from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Activo, Riesgo, Amenaza, Vulnerabilidad, NivelImpacto, NivelProbabilidad, EstadoRiesgo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure CORS to allow requests from frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"], "supports_credentials": True}})
jwt = JWTManager(app)
db.init_app(app)

# Utilidades
impacto_valores = {
    NivelImpacto.BAJO: 1,
    NivelImpacto.MEDIO: 2,
    NivelImpacto.ALTO: 3,
    NivelImpacto.CRITICO: 4,
}

probabilidad_valores = {
    NivelProbabilidad.IMPROBABLE: 1,
    NivelProbabilidad.POSIBLE: 2,
    NivelProbabilidad.PROBABLE: 3,
    NivelProbabilidad.CASI_SEGURO: 4,
}

def calcular_nivel_riesgo(impacto_enum, probabilidad_enum):
    return impacto_valores[impacto_enum] * probabilidad_valores[probabilidad_enum]

@app.route('/inicializar_db', methods=['POST'])
def inicializar_db():
    db.create_all()
    return jsonify({'mensaje': 'Base de datos de riesgos inicializada'}), 201

# --- Activos ---
@app.route('/activos', methods=['GET'])
@jwt_required()
def obtener_activos():
    activos = Activo.query.all()
    return jsonify([a.to_dict() for a in activos]), 200

# --- Amenazas ---
@app.route('/amenazas', methods=['GET'])
@jwt_required()
def obtener_amenazas():
    amenazas = Amenaza.query.all()
    return jsonify([a.to_dict() for a in amenazas]), 200

# --- Vulnerabilidades ---
@app.route('/vulnerabilidades', methods=['GET'])
@jwt_required()
def obtener_vulnerabilidades():
    vulnerabilidades = Vulnerabilidad.query.all()
    return jsonify([v.to_dict() for v in vulnerabilidades]), 200

@app.route('/activos', methods=['POST'])
@jwt_required()
def crear_activo():
    data = request.get_json()
    requerido = ['nombre', 'tipo', 'valor', 'propietario']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    activo = Activo(
        nombre=data['nombre'],
        descripcion=data.get('descripcion'),
        tipo=data['tipo'],
        valor=int(data['valor']),
        propietario=data['propietario'],
        ubicacion=data.get('ubicacion')
    )
    db.session.add(activo)
    db.session.commit()
    return jsonify(activo.to_dict()), 201

@app.route('/activos/<int:activo_id>', methods=['GET'])
@jwt_required()
def obtener_activo(activo_id):
    activo = Activo.query.get(activo_id)
    if not activo:
        return jsonify({'error': 'Activo no encontrado'}), 404
    return jsonify(activo.to_dict()), 200

@app.route('/activos/<int:activo_id>', methods=['PUT'])
@jwt_required()
def actualizar_activo(activo_id):
    activo = Activo.query.get(activo_id)
    if not activo:
        return jsonify({'error': 'Activo no encontrado'}), 404
    data = request.get_json()
    for campo in ['nombre', 'descripcion', 'tipo', 'valor', 'propietario', 'ubicacion']:
        if campo in data:
            setattr(activo, campo, data[campo])
    db.session.commit()
    return jsonify(activo.to_dict()), 200

@app.route('/activos/<int:activo_id>', methods=['DELETE'])
@jwt_required()
def eliminar_activo(activo_id):
    activo = Activo.query.get(activo_id)
    if not activo:
        return jsonify({'error': 'Activo no encontrado'}), 404
    db.session.delete(activo)
    db.session.commit()
    return jsonify({'mensaje': 'Activo eliminado'}), 200

# --- Riesgos ---
@app.route('/riesgos', methods=['GET'])
@jwt_required()
def obtener_riesgos():
    riesgos = Riesgo.query.all()
    return jsonify([r.to_dict() for r in riesgos]), 200

@app.route('/riesgos', methods=['POST'])
@jwt_required()
def crear_riesgo():
    data = request.get_json()
    requerido = ['nombre', 'descripcion', 'activo_id', 'amenaza_id', 'vulnerabilidad_id', 'impacto', 'probabilidad']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    impacto_enum = NivelImpacto[data['impacto']]
    prob_enum = NivelProbabilidad[data['probabilidad']]
    nivel_riesgo = calcular_nivel_riesgo(impacto_enum, prob_enum)
    
    riesgo = Riesgo(
        nombre=data['nombre'],
        descripcion=data['descripcion'],
        activo_id=data['activo_id'],
        amenaza_id=data['amenaza_id'],
        vulnerabilidad_id=data['vulnerabilidad_id'],
        impacto=impacto_enum,
        probabilidad=prob_enum,
        nivel_riesgo=nivel_riesgo,
        estado=EstadoRiesgo.IDENTIFICADO
    )
    db.session.add(riesgo)
    db.session.commit()
    return jsonify(riesgo.to_dict()), 201

@app.route('/riesgos/<int:riesgo_id>', methods=['GET'])
@jwt_required()
def obtener_riesgo(riesgo_id):
    riesgo = Riesgo.query.get(riesgo_id)
    if not riesgo:
        return jsonify({'error': 'Riesgo no encontrado'}), 404
    return jsonify(riesgo.to_dict()), 200

@app.route('/riesgos/<int:riesgo_id>', methods=['PUT'])
@jwt_required()
def actualizar_riesgo(riesgo_id):
    riesgo = Riesgo.query.get(riesgo_id)
    if not riesgo:
        return jsonify({'error': 'Riesgo no encontrado'}), 404
    data = request.get_json()
    if 'impacto' in data or 'probabilidad' in data:
        impacto_enum = riesgo.impacto if 'impacto' not in data else NivelImpacto[data['impacto']]
        prob_enum = riesgo.probabilidad if 'probabilidad' not in data else NivelProbabilidad[data['probabilidad']]
        riesgo.nivel_riesgo = calcular_nivel_riesgo(impacto_enum, prob_enum)
        riesgo.impacto = impacto_enum
        riesgo.probabilidad = prob_enum
    for campo in ['nombre', 'descripcion', 'estado']:
        if campo in data:
            if campo == 'estado':
                riesgo.estado = EstadoRiesgo[data[campo]]
            else:
                setattr(riesgo, campo, data[campo])
    db.session.commit()
    return jsonify(riesgo.to_dict()), 200

@app.route('/riesgos/<int:riesgo_id>', methods=['DELETE'])
@jwt_required()
def eliminar_riesgo(riesgo_id):
    riesgo = Riesgo.query.get(riesgo_id)
    if not riesgo:
        return jsonify({'error': 'Riesgo no encontrado'}), 404
    db.session.delete(riesgo)
    db.session.commit()
    return jsonify({'mensaje': 'Riesgo eliminado'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
