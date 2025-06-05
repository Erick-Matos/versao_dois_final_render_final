import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # força criar uploads em static
    base_dir    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    uploads_dir = os.path.join(base_dir, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    app = Flask(
        __name__,
        static_folder='../static',
        template_folder='../templates',
        static_url_path='/static'
    )
    app.config.from_object('config.Config')

    # CORS
    origins = app.config.get('CORS_ORIGINS','')
    CORS(app, origins=origins.split(',') if origins else ['*'])

    # DB & Migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    from app.auth.routes import auth_bp
    from app.anuncios.routes import anuncios_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(anuncios_bp)

    # Cria tabelas e admin
    with app.app_context():
        db.create_all()  # tabelas criadas automaticamente
        from werkzeug.security import generate_password_hash
        from app.models import Usuario

        admin_email    = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_phone    = os.getenv('ADMIN_PHONE', os.getenv('ADMIN_TELEFONE','0000000000'))
        admin_name     = os.getenv('ADMIN_NAME','admin')

        if admin_email and admin_password:
            if not Usuario.query.filter_by(email=admin_email).first():
                hashed = generate_password_hash(admin_password)
                admin  = Usuario(
                    nome=admin_name,
                    email=admin_email,
                    senha=hashed,
                    telefone=admin_phone,
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()

    # Rotas estáticas
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/health')
    def health():
        return 'OK', 200

    return app
