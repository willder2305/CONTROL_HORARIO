from app import db
from app.utils.datetime_utils import obtener_hora_actual


class Huella(db.Model):
    __tablename__ = "huellas"

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(
        db.Integer,
        db.ForeignKey("trabajadores.id"),
        nullable=False,
        index=True,
    )
    template_biometrico = db.Column(db.LargeBinary, nullable=False)
    proveedor = db.Column(db.String(80), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=obtener_hora_actual)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=obtener_hora_actual,
        onupdate=obtener_hora_actual,
    )

    trabajador = db.relationship("Trabajador", back_populates="huellas")

    __table_args__ = (
        db.Index("ix_huella_trabajador_activa", "trabajador_id", "activa"),
    )

    def __repr__(self):
        return f"<Huella trabajador_id={self.trabajador_id} activa={self.activa}>"
