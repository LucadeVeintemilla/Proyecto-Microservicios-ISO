from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, JWT_SECRET_KEY
from models import db, Documento, VersionDocumento, RevisionDocumento, CategoriaDocumento, DocumentoCategoria, EvidenciaCumplimiento, EstadoDocumento, TipoDocumento

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure CORS to allow requests from frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
jwt = JWTManager(app)
db.init_app(app)

@app.route('/inicializar_db', methods=['POST'])
def inicializar_db():
    db.create_all()
    
    categorias_iniciales = [
        {'nombre': 'Políticas', 'descripcion': 'Políticas de seguridad de la información'},
        {'nombre': 'Procedimientos', 'descripcion': 'Procedimientos operativos de seguridad'},
        {'nombre': 'Formatos', 'descripcion': 'Formatos y plantillas'},
        {'nombre': 'Evidencias', 'descripcion': 'Evidencias de cumplimiento ISO 27001'}
    ]
    
    for cat_data in categorias_iniciales:
        if not CategoriaDocumento.query.filter_by(nombre=cat_data['nombre']).first():
            categoria = CategoriaDocumento(nombre=cat_data['nombre'], descripcion=cat_data['descripcion'])
            db.session.add(categoria)
    
    db.session.commit()
    return jsonify({'mensaje': 'Base de datos de documentación inicializada'}), 201

# --- Documentos ---
@app.route('/documentos', methods=['GET'])
@jwt_required()
def obtener_documentos():
    documentos = Documento.query.all()
    return jsonify([doc.to_dict() for doc in documentos]), 200

@app.route('/documentos', methods=['POST'])
@jwt_required()
def crear_documento():
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    requerido = ['codigo', 'titulo', 'tipo']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Verificar si ya existe un documento con ese código
    if Documento.query.filter_by(codigo=data['codigo']).first():
        return jsonify({'error': 'Ya existe un documento con ese código'}), 400
    
    # Asegurarse de que no se está enviando un ID en los datos
    if 'id' in data:
        del data['id']
    
    documento = Documento(
        codigo=data['codigo'],
        titulo=data['titulo'],
        descripcion=data.get('descripcion', ''),
        tipo=TipoDocumento[data['tipo']],
        estado=EstadoDocumento.BORRADOR,
        creado_por=usuario_id,
        propietario=usuario_id,
        ruta_archivo=data.get('ruta_archivo', ''),
        palabras_clave=data.get('palabras_clave', '')
    )
    db.session.add(documento)
    db.session.flush()  # Obtener el ID generado antes de hacer commit
    
    # Crear primera versión
    version = VersionDocumento(
        documento_id=documento.id,
        numero_version='1.0',
        creado_por=usuario_id,
        ruta_archivo=data.get('ruta_archivo', ''),
        cambios='Versión inicial'
    )
    db.session.add(version)
    
    # Asignar categorías si se proporcionan
    if 'categorias' in data and isinstance(data['categorias'], list):
        for cat_id in data['categorias']:
            doc_cat = DocumentoCategoria(documento_id=documento.id, categoria_id=cat_id)
            db.session.add(doc_cat)
    
    db.session.commit()
    return jsonify(documento.to_dict()), 201

@app.route('/documentos/<int:documento_id>', methods=['GET'])
@jwt_required()
def obtener_documento(documento_id):
    documento = Documento.query.get(documento_id)
    if not documento:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    resultado = documento.to_dict()
    
    # Obtener versiones
    versiones = VersionDocumento.query.filter_by(documento_id=documento_id).all()
    resultado['versiones'] = [v.to_dict() for v in versiones]
    
    # Obtener revisiones
    revisiones = RevisionDocumento.query.filter_by(documento_id=documento_id).all()
    resultado['revisiones'] = [r.to_dict() for r in revisiones]
    
    # Obtener categorías
    doc_cats = DocumentoCategoria.query.filter_by(documento_id=documento_id).all()
    categorias = []
    for dc in doc_cats:
        categoria = CategoriaDocumento.query.get(dc.categoria_id)
        if categoria:
            categorias.append(categoria.to_dict())
    resultado['categorias'] = categorias
    
    return jsonify(resultado), 200

@app.route('/documentos/<int:documento_id>', methods=['PUT'])
@jwt_required()
def actualizar_documento(documento_id):
    documento = Documento.query.get(documento_id)
    if not documento:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    # Actualizar campos básicos
    for campo in ['titulo', 'descripcion', 'palabras_clave', 'ruta_archivo']:
        if campo in data:
            setattr(documento, campo, data[campo])
    
    # Actualizar tipo si se proporciona
    if 'tipo' in data:
        documento.tipo = TipoDocumento[data['tipo']]
    
    # Actualizar estado si se proporciona
    if 'estado' in data:
        documento.estado = EstadoDocumento[data['estado']]
    
    # Actualizar propietario si se proporciona
    if 'propietario' in data:
        documento.propietario = data['propietario']
    
    db.session.commit()
    
    # Actualizar categorías si se proporcionan
    if 'categorias' in data and isinstance(data['categorias'], list):
        DocumentoCategoria.query.filter_by(documento_id=documento_id).delete()
        for cat_id in data['categorias']:
            doc_cat = DocumentoCategoria(documento_id=documento_id, categoria_id=cat_id)
            db.session.add(doc_cat)
        db.session.commit()
    
    return jsonify(documento.to_dict()), 200

@app.route('/documentos/<int:documento_id>', methods=['DELETE'])
@jwt_required()
def eliminar_documento(documento_id):
    documento = Documento.query.get(documento_id)
    if not documento:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    # Las relaciones con cascade="all, delete-orphan" eliminarán automáticamente
    # las versiones y revisiones asociadas
    DocumentoCategoria.query.filter_by(documento_id=documento_id).delete()
    db.session.delete(documento)
    db.session.commit()
    
    return jsonify({'mensaje': 'Documento eliminado correctamente'}), 200

# --- Versiones de documentos ---
@app.route('/documentos/<int:documento_id>/versiones', methods=['GET'])
@jwt_required()
def obtener_versiones(documento_id):
    versiones = VersionDocumento.query.filter_by(documento_id=documento_id).all()
    return jsonify([v.to_dict() for v in versiones]), 200

@app.route('/documentos/<int:documento_id>/versiones', methods=['POST'])
@jwt_required()
def crear_version(documento_id):
    documento = Documento.query.get(documento_id)
    if not documento:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    if not data.get('numero_version'):
        return jsonify({'error': 'Número de versión requerido'}), 400
    
    version = VersionDocumento(
        documento_id=documento_id,
        numero_version=data['numero_version'],
        creado_por=usuario_id,
        ruta_archivo=data.get('ruta_archivo', documento.ruta_archivo),
        cambios=data.get('cambios', '')
    )
    db.session.add(version)
    
    # Actualizar ruta de archivo en el documento principal si se proporciona
    if data.get('ruta_archivo'):
        documento.ruta_archivo = data['ruta_archivo']
    
    db.session.commit()
    return jsonify(version.to_dict()), 201

# --- Revisiones de documentos ---
@app.route('/documentos/<int:documento_id>/revisiones', methods=['GET'])
@jwt_required()
def obtener_revisiones(documento_id):
    revisiones = RevisionDocumento.query.filter_by(documento_id=documento_id).all()
    return jsonify([r.to_dict() for r in revisiones]), 200

@app.route('/documentos/<int:documento_id>/revisiones', methods=['POST'])
@jwt_required()
def crear_revision(documento_id):
    documento = Documento.query.get(documento_id)
    if not documento:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    data = request.get_json()
    if not data.get('revisor_id'):
        return jsonify({'error': 'ID del revisor requerido'}), 400
    
    revision = RevisionDocumento(
        documento_id=documento_id,
        revisor_id=data['revisor_id'],
        estado='PENDIENTE',
        comentarios=data.get('comentarios', '')
    )
    db.session.add(revision)
    
    # Actualizar estado del documento a EN_REVISION
    documento.estado = EstadoDocumento.EN_REVISION
    
    db.session.commit()
    return jsonify(revision.to_dict()), 201

@app.route('/revisiones/<int:revision_id>', methods=['PUT'])
@jwt_required()
def actualizar_revision(revision_id):
    revision = RevisionDocumento.query.get(revision_id)
    if not revision:
        return jsonify({'error': 'Revisión no encontrada'}), 404
    
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    # Verificar que el usuario sea el revisor asignado
    if revision.revisor_id != usuario_id:
        return jsonify({'error': 'No autorizado para actualizar esta revisión'}), 403
    
    if 'estado' in data:
        revision.estado = data['estado']
        revision.fecha_revision = datetime.datetime.utcnow()
    
    if 'comentarios' in data:
        revision.comentarios = data['comentarios']
    
    # Si todas las revisiones están aprobadas, actualizar estado del documento
    if revision.estado == 'APROBADO':
        documento = Documento.query.get(revision.documento_id)
        revisiones_pendientes = RevisionDocumento.query.filter_by(
            documento_id=revision.documento_id, 
            estado='PENDIENTE'
        ).count()
        
        if revisiones_pendientes == 0:
            documento.estado = EstadoDocumento.APROBADO
    
    db.session.commit()
    return jsonify(revision.to_dict()), 200

# --- Categorías de documentos ---
@app.route('/categorias', methods=['GET'])
@jwt_required()
def obtener_categorias():
    categorias = CategoriaDocumento.query.all()
    return jsonify([c.to_dict() for c in categorias]), 200

@app.route('/categorias', methods=['POST'])
@jwt_required()
def crear_categoria():
    data = request.get_json()
    
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre de categoría requerido'}), 400
    
    if CategoriaDocumento.query.filter_by(nombre=data['nombre']).first():
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 400
    
    categoria = CategoriaDocumento(
        nombre=data['nombre'],
        descripcion=data.get('descripcion', '')
    )
    db.session.add(categoria)
    db.session.commit()
    
    return jsonify(categoria.to_dict()), 201

# --- Evidencias de cumplimiento ---
@app.route('/evidencias', methods=['GET'])
@jwt_required()
def obtener_evidencias():
    evidencias = EvidenciaCumplimiento.query.all()
    return jsonify([e.to_dict() for e in evidencias]), 200

@app.route('/evidencias', methods=['POST'])
@jwt_required()
def crear_evidencia():
    data = request.get_json()
    identity = get_jwt_identity()
    usuario_id = identity.get('usuario_id')
    
    requerido = ['titulo', 'requisito']
    if not all(k in data for k in requerido):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    evidencia = EvidenciaCumplimiento(
        titulo=data['titulo'],
        descripcion=data.get('descripcion', ''),
        requisito=data['requisito'],
        registrado_por=usuario_id,
        ruta_archivo=data.get('ruta_archivo', '')
    )
    db.session.add(evidencia)
    db.session.commit()
    
    return jsonify(evidencia.to_dict()), 201

@app.route('/evidencias/<int:evidencia_id>', methods=['GET'])
@jwt_required()
def obtener_evidencia(evidencia_id):
    evidencia = EvidenciaCumplimiento.query.get(evidencia_id)
    if not evidencia:
        return jsonify({'error': 'Evidencia no encontrada'}), 404
    return jsonify(evidencia.to_dict()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
