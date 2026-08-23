from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config
from app.security import register_security

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    db.init_app(app)
    migrate.init_app(app, db)
    register_security(app)

    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.biometria import biometria_bp
    from app.routes.horarios import horarios_bp
    from app.routes.marcaciones import admin_marcaciones_bp, marcaciones_bp
    from app.routes.reportes import reportes_bp
    from app.routes.trabajadores import trabajadores_bp
    from app import models
    from app.commands import register_commands

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(biometria_bp, url_prefix="/api/biometria")
    app.register_blueprint(horarios_bp, url_prefix="/api/admin/horarios")
    app.register_blueprint(admin_marcaciones_bp, url_prefix="/api/admin/marcaciones")
    app.register_blueprint(reportes_bp, url_prefix="/api/admin/reportes")
    app.register_blueprint(marcaciones_bp, url_prefix="/api/marcaciones")
    app.register_blueprint(trabajadores_bp, url_prefix="/api/admin/trabajadores")
    register_commands(app)

    return app
