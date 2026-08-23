from app import db
from app.utils.datetime_utils import obtener_hora_actual


class Trabajador(db.Model):
    __tablename__ = "trabajadores"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=obtener_hora_actual,
        onupdate=obtener_hora_actual,
    )

    horarios = db.relationship(
        "HorarioTrabajador",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )
    huellas = db.relationship(
        "Huella",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )
    marcaciones = db.relationship("Marcacion", back_populates="trabajador")

    def __repr__(self):
        return f"<Trabajador {self.codigo}>"
