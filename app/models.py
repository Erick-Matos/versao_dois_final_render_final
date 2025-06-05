from app import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    anuncios = db.relationship('Anuncio', backref='usuario', cascade='all, delete-orphan')

class Anuncio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    imagem = db.Column(db.String(200))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'idade': self.idade,
            'sexo': self.sexo,
            'telefone': self.telefone,
            'imagem': self.imagem,
            'data_criacao': self.data_criacao.isoformat(),
            'usuario_id': self.usuario_id
        }
