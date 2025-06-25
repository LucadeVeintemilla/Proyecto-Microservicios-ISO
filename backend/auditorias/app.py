from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Auditoria, Hallazgo, PlanAccion, ListaVerificacion, CriterioVerificacion, EstadoAuditoria, TipoAuditoria, EstadoHallazgo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure CORS to allow requests from frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
jwt = JWTManager(app)
db.init_app(app)

# Utilidad de verificación de rol administrador

def es_admin(identity):
    return 'Administrador' in identity.get('roles', [])

@app.route('/inicializar_db', methods=['POST'])
@jwt_required()
def inicializar_db():
    if not es_admin(get_jwt_identity()):
        return jsonify({'error': 'No autorizado'}), 403
    db.create_all()
    return jsonify({'mensaje': 'Base de datos de auditorías inicializada'}), 201

# -------- Auditorías --------
@app.route('/auditorias', methods=['GET'])
@jwt_required()
def obtener_auditorias():
    auditorias = Auditoria.query.all()
    return jsonify([a.to_dict() for a in auditorias]), 200

@app.route('/auditorias', methods=['POST'])
@jwt_required()
def crear_auditoria():
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        # Verificar campos requeridos (sin incluir código que lo generamos automáticamente)
        requerido = ['titulo', 'fecha_inicio', 'fecha_fin']
        missing_fields = [field for field in requerido if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Datos incompletos. Faltan campos: {", ".join(missing_fields)}'
            }), 400
            
        # Generar código único si no se proporciona
        if 'codigo' not in data or not data['codigo']:
            # Formato: AUD-YYMMDD-XXX donde XXX es un número secuencial
            fecha_actual = datetime.datetime.now().strftime("%y%m%d")
            ultimo_codigo = Auditoria.query.filter(Auditoria.codigo.like(f'AUD-{fecha_actual}-%')).order_by(Auditoria.codigo.desc()).first()
            
            if ultimo_codigo:
                try:
                    # Extraer el número secuencial y aumentarlo en 1
                    ultimo_numero = int(ultimo_codigo.codigo.split('-')[-1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
                
            data['codigo'] = f'AUD-{fecha_actual}-{nuevo_numero:03d}'
            
        # Verificar si ya existe una auditoría con ese código
        if Auditoria.query.filter_by(codigo=data['codigo']).first():
            return jsonify({'error': 'Ya existe una auditoría con ese código'}), 400
        
        # Establecer valores por defecto para campos opcionales
        if 'tipo' not in data:
            data['tipo'] = 'INTERNA'
        
        if 'auditor_lider' not in data:
            data['auditor_lider'] = identity.get('usuario_id', 1)
        
        # Crear la auditoría
        auditoria = Auditoria(
            codigo=data['codigo'],
            titulo=data['titulo'],
            descripcion=data.get('descripcion', ''),
            tipo=TipoAuditoria[data['tipo']],
            estado=EstadoAuditoria.PLANIFICADA,
            fecha_inicio=datetime.datetime.fromisoformat(data['fecha_inicio']),
            fecha_fin=datetime.datetime.fromisoformat(data['fecha_fin']),
            auditor_lider=data['auditor_lider'],
            equipo_auditores=data.get('equipo_auditores', ''),
            alcance=data.get('alcance', ''),
            objetivos=data.get('objetivos', ''),
            criterios=data.get('criterios', '')
        )
        
        db.session.add(auditoria)
        db.session.commit()
        return jsonify(auditoria.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al crear auditoría: {str(e)}")
        return jsonify({'error': f'Error al crear auditoría: {str(e)}'}), 500

@app.route('/auditorias/<int:auditoria_id>', methods=['GET'])
@jwt_required()
def obtener_auditoria(auditoria_id):
    try:
        auditoria = Auditoria.query.get(auditoria_id)
        if not auditoria:
            return jsonify({'error': 'Auditoría no encontrada'}), 404
        resultado = auditoria.to_dict()
        # Obtener hallazgos de forma segura
        try:
            hallazgos = Hallazgo.query.filter_by(auditoria_id=auditoria_id).all()
            resultado['hallazgos'] = [h.to_dict() for h in hallazgos]
        except Exception as e:
            # Si hay error al obtener hallazgos, simplemente devolver lista vacía
            resultado['hallazgos'] = []
            app.logger.error(f"Error al obtener hallazgos: {str(e)}")
        return jsonify(resultado), 200
    except Exception as e:
        app.logger.error(f"Error al obtener auditoría {auditoria_id}: {str(e)}")
        return jsonify({'error': 'Error interno al obtener la auditoría'}), 500

@app.route('/auditorias/<int:auditoria_id>', methods=['PUT'])
@jwt_required()
def actualizar_auditoria(auditoria_id):
    try:
        auditoria = Auditoria.query.get(auditoria_id)
        if not auditoria:
            return jsonify({'error': 'Auditoría no encontrada'}), 404
            
        data = request.get_json()
        app.logger.info(f"Actualizando auditoría {auditoria_id} con datos: {data}")
        
        # Actualizar campos simples
        for campo in ['titulo', 'descripcion', 'equipo_auditores', 'alcance', 'objetivos', 'criterios']:
            if campo in data:
                setattr(auditoria, campo, data[campo])
        
        # Actualizar tipo si se proporciona
        if 'tipo' in data:
            try:
                auditoria.tipo = TipoAuditoria[data['tipo']]
            except KeyError:
                return jsonify({'error': f"Tipo de auditoría inválido: {data['tipo']}"}), 400
        
        # Actualizar estado si se proporciona
        if 'estado' in data:
            # Convertir estados antiguos a nuevos valores
            estado_map = {
                'PROGRAMADA': 'PLANIFICADA',
                'EN_PROCESO': 'EN_EJECUCION'
            }
            estado = estado_map.get(data['estado'], data['estado'])
            
            try:
                auditoria.estado = EstadoAuditoria[estado]
            except KeyError:
                return jsonify({'error': f'Estado de auditoría inválido: {data["estado"]}. Estados válidos: {[e.name for e in EstadoAuditoria]}'}), 400
        
        # Actualizar fechas si se proporcionan
        if 'fecha_inicio' in data:
            try:
                auditoria.fecha_inicio = datetime.datetime.fromisoformat(data['fecha_inicio'])
            except ValueError:
                return jsonify({'error': f"Formato de fecha inválido para fecha_inicio: {data['fecha_inicio']}"}), 400
                
        if 'fecha_fin' in data:
            try:
                auditoria.fecha_fin = datetime.datetime.fromisoformat(data['fecha_fin'])
            except ValueError:
                return jsonify({'error': f"Formato de fecha inválido para fecha_fin: {data['fecha_fin']}"}), 400
        
        db.session.commit()
        return jsonify(auditoria.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al actualizar auditoría {auditoria_id}: {str(e)}")
        return jsonify({'error': f"Error al actualizar auditoría: {str(e)}"}), 500

@app.route('/auditorias/<int:auditoria_id>', methods=['DELETE'])
@jwt_required()
def eliminar_auditoria(auditoria_id):
    auditoria = Auditoria.query.get(auditoria_id)
    if not auditoria:
        return jsonify({'error': 'Auditoría no encontrada'}), 404
    db.session.delete(auditoria)
    db.session.commit()
    return jsonify({'mensaje': 'Auditoría eliminada'}), 200

# -------- Hallazgos --------
@app.route('/hallazgos', methods=['GET'])
@jwt_required()
def obtener_hallazgos():
    hallazgos = Hallazgo.query.all()
    return jsonify([h.to_dict() for h in hallazgos]), 200

@app.route('/auditorias/<int:auditoria_id>/hallazgos', methods=['POST'])
@jwt_required()
def crear_hallazgo(auditoria_id):
    auditoria = Auditoria.query.get(auditoria_id)
    if not auditoria:
        return jsonify({'error': 'Auditoría no encontrada'}), 404
    data = request.get_json()
    requerido = ['codigo', 'tipo', 'descripcion']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    hallazgo = Hallazgo(
        auditoria_id=auditoria_id,
        codigo=data['codigo'],
        tipo=data['tipo'],
        descripcion=data['descripcion'],
        criterio_incumplido=data.get('criterio_incumplido', ''),
        evidencia=data.get('evidencia', ''),
        area_responsable=data.get('area_responsable', ''),
        estado=EstadoHallazgo.IDENTIFICADO
    )
    db.session.add(hallazgo)
    db.session.commit()
    return jsonify(hallazgo.to_dict()), 201

@app.route('/hallazgos/<int:hallazgo_id>', methods=['PUT'])
@jwt_required()
def actualizar_hallazgo(hallazgo_id):
    hallazgo = Hallazgo.query.get(hallazgo_id)
    if not hallazgo:
        return jsonify({'error': 'Hallazgo no encontrado'}), 404
    data = request.get_json()
    for campo in ['tipo', 'descripcion', 'criterio_incumplido', 'evidencia', 'area_responsable']:
        if campo in data:
            setattr(hallazgo, campo, data[campo])
    if 'estado' in data:
        hallazgo.estado = EstadoHallazgo[data['estado']]
    db.session.commit()
    return jsonify(hallazgo.to_dict()), 200

@app.route('/hallazgos/<int:hallazgo_id>', methods=['DELETE'])
@jwt_required()
def eliminar_hallazgo(hallazgo_id):
    hallazgo = Hallazgo.query.get(hallazgo_id)
    if not hallazgo:
        return jsonify({'error': 'Hallazgo no encontrado'}), 404
    db.session.delete(hallazgo)
    db.session.commit()
    return jsonify({'mensaje': 'Hallazgo eliminado'}), 200

# -------- Planes de acción --------
@app.route('/planes', methods=['GET', 'POST'])
@jwt_required()
def obtener_planes():
    if request.method == 'GET':
        planes = PlanAccion.query.all()
        return jsonify([p.to_dict() for p in planes]), 200
    else:  # POST
        data = request.get_json()
        requerido = ['descripcion', 'tipo_accion', 'responsable', 'fecha_inicio', 'fecha_fin_planificada', 'hallazgo_id']
        if not all(k in data for k in requerido):
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Verificar que el hallazgo existe
        hallazgo_id = data['hallazgo_id']
        hallazgo = Hallazgo.query.get(hallazgo_id)
        if not hallazgo:
            return jsonify({'error': 'Hallazgo no encontrado'}), 404
            
        plan = PlanAccion(
            hallazgo_id=hallazgo_id,
            descripcion=data['descripcion'],
            tipo_accion=data['tipo_accion'],
            responsable=data['responsable'],
            fecha_inicio=datetime.datetime.fromisoformat(data['fecha_inicio']),
            fecha_fin_planificada=datetime.datetime.fromisoformat(data['fecha_fin_planificada']),
            estado='PENDIENTE'
        )
        db.session.add(plan)
        db.session.commit()
        return jsonify(plan.to_dict()), 201

@app.route('/acciones', methods=['GET'])
@jwt_required()
def obtener_acciones():
    # This endpoint is an alias for /planes to match frontend expectations
    planes = PlanAccion.query.all()
    return jsonify([p.to_dict() for p in planes]), 200

@app.route('/hallazgos/<int:hallazgo_id>/planes_accion', methods=['POST'])
@jwt_required()
def crear_plan_accion(hallazgo_id):
    hallazgo = Hallazgo.query.get(hallazgo_id)
    if not hallazgo:
        return jsonify({'error': 'Hallazgo no encontrado'}), 404
    data = request.get_json()
    requerido = ['descripcion', 'tipo_accion', 'responsable', 'fecha_inicio', 'fecha_fin_planificada']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    plan = PlanAccion(
        hallazgo_id=hallazgo_id,
        descripcion=data['descripcion'],
        tipo_accion=data['tipo_accion'],
        responsable=data['responsable'],
        fecha_inicio=datetime.datetime.fromisoformat(data['fecha_inicio']),
        fecha_fin_planificada=datetime.datetime.fromisoformat(data['fecha_fin_planificada']),
        estado='PENDIENTE'
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify(plan.to_dict()), 201

@app.route('/planes_accion/<int:plan_id>', methods=['PUT'])
@jwt_required()
def actualizar_plan_accion(plan_id):
    plan = PlanAccion.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan de acción no encontrado'}), 404
    data = request.get_json()
    for campo in ['descripcion', 'tipo_accion', 'responsable', 'estado', 'resultado', 'eficacia']:
        if campo in data:
            setattr(plan, campo, data[campo])
    if 'fecha_fin_real' in data:
        plan.fecha_fin_real = datetime.datetime.fromisoformat(data['fecha_fin_real'])
    db.session.commit()
    return jsonify(plan.to_dict()), 200

@app.route('/planes_accion/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def eliminar_plan_accion(plan_id):
    plan = PlanAccion.query.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan de acción no encontrado'}), 404
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'mensaje': 'Plan de acción eliminado'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
