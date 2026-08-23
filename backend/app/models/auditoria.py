from app import db
from app.utils.datetime_utils import obtener_hora_actual


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)
    administrador_id = db.Column(
        db.Integer,
        db.ForeignKey("administradores.id"),
        nullable=True,
        index=True,
    )
    accion = db.Column(db.String(80), nullable=False, index=True)
    entidad = db.Column(db.String(80), nullable=False, index=True)
    entidad_id = db.Column(db.Integer, nullable=True, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    ip = db.Column(db.String(45), nullable=True)

    administrador = db.relationship("Administrador", back_populates="auditorias")

    def __repr__(self):
        return f"<Auditoria {self.accion} {self.entidad}>"
