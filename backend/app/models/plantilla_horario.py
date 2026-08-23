from app import db
from app.utils.datetime_utils import obtener_hora_actual


class PlantillaHorario(db.Model):
    __tablename__ = "plantillas_horario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True, index=True)
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida_almuerzo = db.Column(db.Time, nullable=True)
    hora_regreso_almuerzo = db.Column(db.Time, nullable=True)
    hora_salida = db.Column(db.Time, nullable=False)
    tolerancia_entrada = db.Column(db.Integer, nullable=False, default=0)
    tolerancia_regreso_almuerzo = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=obtener_hora_actual,
        onupdate=obtener_hora_actual,
    )

    horarios_trabajadores = db.relationship(
        "HorarioTrabajador",
        back_populates="plantilla",
    )

    def __repr__(self):
        return f"<PlantillaHorario {self.nombre}>"
