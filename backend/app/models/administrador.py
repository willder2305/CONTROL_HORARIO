from datetime import datetime

from app import db
from app.utils.datetime_utils import obtener_hora_actual


class Administrador(db.Model):
    __tablename__ = "administradores"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    ultimo_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=obtener_hora_actual,
        onupdate=obtener_hora_actual,
    )

    auditorias = db.relationship("Auditoria", back_populates="administrador")

    def __repr__(self):
        return f"<Administrador {self.usuario}>"
