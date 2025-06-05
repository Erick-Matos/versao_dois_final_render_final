import os
from flask import Blueprint, request, jsonify
import cloudinary.uploader
from config_cloudinary import cloudinary
from app import db
from app.auth.routes import token_required
from app.models import Anuncio

anuncios_bp = Blueprint('anuncios', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload de imagem via Cloudinary
@anuncios_bp.route('/upload-imagem', methods=['POST'])
@token_required
def upload_imagem(current_user):
    file = request.files.get('imagem')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Arquivo inválido'}), 400

    try:
        upload_result = cloudinary.uploader.upload(file)
        img_url = upload_result['secure_url']
        return jsonify({'image_url': img_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lista todos os anúncios
@anuncios_bp.route('/anuncios', methods=['GET'])
@token_required
def list_anuncios(current_user):
    anuncios = Anuncio.query.all()
    resultado = []
    for a in anuncios:
        d = a.to_dict()
        resultado.append(d)
    return jsonify(resultado), 200

# Cria novo anúncio
@anuncios_bp.route('/anuncios', methods=['POST'])
@token_required
def create_anuncio(current_user):
    data = request.get_json() or {}
    titulo    = data.get('titulo') or data.get('nome_pet')
    descricao = data.get('descricao', '')
    idade     = int(data.get('idade', 0))
    sexo      = data.get('sexo')
    telefone  = data.get('telefone', '')
    imagem    = data.get('imagem_url', '')

    a = Anuncio(
        titulo     = titulo,
        descricao  = descricao,
        idade      = idade,
        sexo       = sexo,
        telefone   = telefone,
        imagem     = imagem,
        usuario_id = current_user.id
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

    data = request.get_json() or {}
    a.titulo    = data.get('titulo', a.titulo)
    a.descricao = data.get('descricao', a.descricao)
    a.idade     = int(data.get('idade', a.idade))
    a.sexo      = data.get('sexo', a.sexo)

    telefone = data.get('telefone')
    if telefone:
        a.telefone = telefone

    imagem_url = data.get('imagem_url', '')
    if imagem_url:
        a.imagem = imagem_url

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
