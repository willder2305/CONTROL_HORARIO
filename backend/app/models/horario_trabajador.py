from app import db
from app.utils.datetime_utils import obtener_hora_actual


class HorarioTrabajador(db.Model):
    __tablename__ = "horarios_trabajadores"

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(
        db.Integer,
        db.ForeignKey("trabajadores.id"),
        nullable=False,
        index=True,
    )
    plantilla_id = db.Column(
        db.Integer,
        db.ForeignKey("plantillas_horario.id"),
        nullable=True,
        index=True,
    )
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida_almuerzo = db.Column(db.Time, nullable=True)
    hora_regreso_almuerzo = db.Column(db.Time, nullable=True)
    hora_salida = db.Column(db.Time, nullable=False)
    tolerancia_entrada = db.Column(db.Integer, nullable=False, default=0)
    tolerancia_regreso_almuerzo = db.Column(db.Integer, nullable=False, default=0)
    fecha_inicio = db.Column(db.Date, nullable=False, index=True)
    fecha_fin = db.Column(db.Date, nullable=True, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=obtener_hora_actual,
        onupdate=obtener_hora_actual,
    )

    trabajador = db.relationship("Trabajador", back_populates="horarios")
    plantilla = db.relationship(
        "PlantillaHorario",
        back_populates="horarios_trabajadores",
    )
    marcaciones = db.relationship("Marcacion", back_populates="horario_trabajador")

    __table_args__ = (
        db.Index(
            "ix_horario_trabajador_rango",
            "trabajador_id",
            "fecha_inicio",
            "fecha_fin",
        ),
    )

    def __repr__(self):
        return f"<HorarioTrabajador trabajador_id={self.trabajador_id}>"
