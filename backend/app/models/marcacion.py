from app import db
from app.utils.datetime_utils import obtener_hora_actual


class Marcacion(db.Model):
    __tablename__ = "marcaciones"

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(
        db.Integer,
        db.ForeignKey("trabajadores.id"),
        nullable=False,
        index=True,
    )
    fecha = db.Column(db.Date, nullable=False, index=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    tipo_marcacion = db.Column(db.String(30), nullable=False, index=True)
    hora_programada = db.Column(db.Time, nullable=False)
    hora_real = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(30), nullable=False, index=True)
    minutos_diferencia = db.Column(db.Integer, nullable=False, default=0)
    horario_trabajador_id = db.Column(
        db.Integer,
        db.ForeignKey("horarios_trabajadores.id"),
        nullable=False,
        index=True,
    )
    origen = db.Column(db.String(30), nullable=False, default="BIOMETRIA")
    observacion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)

    trabajador = db.relationship("Trabajador", back_populates="marcaciones")
    horario_trabajador = db.relationship(
        "HorarioTrabajador",
        back_populates="marcaciones",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "trabajador_id",
            "fecha",
            "tipo_marcacion",
            name="uq_marcacion_trabajador_fecha_tipo",
        ),
        db.Index("ix_marcacion_fecha_tipo_estado", "fecha", "tipo_marcacion", "estado"),
    )

    def __repr__(self):
        return f"<Marcacion trabajador_id={self.trabajador_id} tipo={self.tipo_marcacion}>"
