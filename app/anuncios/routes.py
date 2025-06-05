import os
import uuid
from flask import Blueprint, request, jsonify, url_for, current_app
import cloudinary.uploader
from config_cloudinary import cloudinary
from werkzeug.utils import secure_filename
from app import db
from app.auth.routes import token_required
from app.models import Anuncio

anuncios_bp = Blueprint('anuncios', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload de imagem
@anuncios_bp.route('/upload-imagem', methods=['POST'])
@token_required
def upload_imagem(current_user):
    file = request.files.get('imagem')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Arquivo inválido'}), 400

    # Gera nome único e salva em static/uploads
    safe_name   = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    upload_dir  = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)
    file.save(file_path)

    # Retorna URL completa para o front
    img_url = url_for('static', filename=f'uploads/{unique_name}', _external=True)
    return jsonify({'image_url': img_url}), 200

# Lista todos os anúncios
@anuncios_bp.route('/anuncios', methods=['GET'])
@token_required
def list_anuncios(current_user):
    anuncios = Anuncio.query.all()
    resultado = []
    for a in anuncios:
        d = a.to_dict()
        # Se tiver nome de arquivo em d['imagem'], converte em URL
        if d.get('imagem'):
            d['imagem'] = url_for(
                'static',
                filename=f'uploads/{d["imagem"]}',
                _external=True
            )
        resultado.append(d)
    return jsonify(resultado), 200

# Cria novo anúncio
@anuncios_bp.route('/anuncios', methods=['POST'])
@token_required
def create_anuncio(current_user):
    data      = request.get_json() or {}
    titulo    = data.get('titulo') or data.get('nome_pet')
    descricao = data.get('descricao', '')
    idade     = int(data.get('idade', 0))
    sexo      = data.get('sexo')
    tel_raw   = data.get('telefone_responsavel') or data.get('telefone', '')
    img_url   = data.get('imagem_url', '')
    filename  = os.path.basename(img_url) if img_url else None

    a = Anuncio(
        titulo      = titulo,
        descricao   = descricao,
        idade       = idade,
        sexo        = sexo,
        telefone    = tel_raw and f'+55{tel_raw}',
        imagem      = filename,
        usuario_id  = current_user.id
    )
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201

# Atualiza anúncio existente
@anuncios_bp.route('/anuncios/<int:id>', methods=['PUT'])
@token_required
def update_anuncio(current_user, id):
    a = Anuncio.query.get_or_404(id)
    if a.usuario_id != current_user.id and not current_user.is_admin:
        return jsonify({'message': 'Sem permissão'}), 403

    data    = request.get_json() or {}
    a.titulo    = data.get('titulo', a.titulo)
    a.descricao = data.get('descricao', a.descricao)
    a.idade     = int(data.get('idade', a.idade))
    a.sexo      = data.get('sexo', a.sexo)

    tel_raw = data.get('telefone_responsavel') or data.get('telefone')
    if tel_raw:
        a.telefone = f'+55{tel_raw}'

    img_url = data.get('imagem_url', '')
    if img_url:
        a.imagem = os.path.basename(img_url)

    db.session.commit()
    return jsonify(a.to_dict()), 200

# Remove anúncio
@anuncios_bp.route('/anuncios/<int:id>', methods=['DELETE'])
@token_required
def delete_anuncio(current_user, id):
    a = Anuncio.query.get_or_404(id)
    if a.usuario_id != current_user.id and not current_user.is_admin:
        return jsonify({'message': 'Sem permissão'}), 403

    db.session.delete(a)
    db.session.commit()
    return jsonify({'message': 'Anúncio removido'}), 200
