import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'message': 'Token inválido'}), 401
        token = auth.split()[1]
        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
            current_user = Usuario.query.get(data['id'])
            if not current_user:
                raise jwt.InvalidTokenError()
        except Exception:
            return jsonify({'message': 'Token inválido ou expirado'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    
    if Usuario.query.filter_by(email=data.get('email')).first():
        return jsonify({'message':'Email já cadastrado'}), 400

    hashed = generate_password_hash(data.get('senha'))

    user = Usuario(
        nome=data.get('nome'),
        email=data.get('email'),
        senha=hashed,
        telefone=None,  # Ou '' se preferir string vazia
        is_admin=False
    )

    db.session.add(user)
    db.session.commit()
    return jsonify({'message':'Usuário criado'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    user = Usuario.query.filter_by(email=data.get('email')).first()
    if not user or not check_password_hash(user.senha, data.get('senha')):
        return jsonify({'message':'Credenciais inválidas'}), 401

    token = jwt.encode({
        'id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, os.getenv('SECRET_KEY'), algorithm='HS256')

    return jsonify({'token': token, 'user_id': user.id, 'admin': str(user.is_admin).lower()}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'id': current_user.id,
        'nome': current_user.nome,
        'email': current_user.email,
        'is_admin': current_user.is_admin
    }), 200
