"""fase 2 esquema inicial

Revision ID: 8066f0fdd060
Revises:
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa


revision = "8066f0fdd060"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "administradores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("apellido", sa.String(length=120), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("ultimo_login", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario"),
    )
    op.create_index(
        op.f("ix_administradores_usuario"),
        "administradores",
        ["usuario"],
        unique=False,
    )

    op.create_table(
        "plantillas_horario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("hora_entrada", sa.Time(), nullable=False),
        sa.Column("hora_salida_almuerzo", sa.Time(), nullable=False),
        sa.Column("hora_regreso_almuerzo", sa.Time(), nullable=False),
        sa.Column("hora_salida", sa.Time(), nullable=False),
        sa.Column("tolerancia_entrada", sa.Integer(), nullable=False),
        sa.Column("tolerancia_regreso_almuerzo", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index(
        op.f("ix_plantillas_horario_nombre"),
        "plantillas_horario",
        ["nombre"],
        unique=False,
    )

    op.create_table(
        "trabajadores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("apellido", sa.String(length=120), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_index(op.f("ix_trabajadores_codigo"), "trabajadores", ["codigo"], unique=False)

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("administrador_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=80), nullable=False),
        sa.Column("entidad", sa.String(length=80), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(["administrador_id"], ["administradores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auditoria_accion"), "auditoria", ["accion"], unique=False)
    op.create_index(
        op.f("ix_auditoria_administrador_id"),
        "auditoria",
        ["administrador_id"],
        unique=False,
    )
    op.create_index(op.f("ix_auditoria_entidad"), "auditoria", ["entidad"], unique=False)
    op.create_index(
        op.f("ix_auditoria_entidad_id"),
        "auditoria",
        ["entidad_id"],
        unique=False,
    )

    op.create_table(
        "horarios_trabajadores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trabajador_id", sa.Integer(), nullable=False),
        sa.Column("plantilla_id", sa.Integer(), nullable=True),
        sa.Column("hora_entrada", sa.Time(), nullable=False),
        sa.Column("hora_salida_almuerzo", sa.Time(), nullable=False),
        sa.Column("hora_regreso_almuerzo", sa.Time(), nullable=False),
        sa.Column("hora_salida", sa.Time(), nullable=False),
        sa.Column("tolerancia_entrada", sa.Integer(), nullable=False),
        sa.Column("tolerancia_regreso_almuerzo", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plantilla_id"], ["plantillas_horario.id"]),
        sa.ForeignKeyConstraint(["trabajador_id"], ["trabajadores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_horario_trabajador_rango",
        "horarios_trabajadores",
        ["trabajador_id", "fecha_inicio", "fecha_fin"],
        unique=False,
    )
    op.create_index(
        op.f("ix_horarios_trabajadores_fecha_fin"),
        "horarios_trabajadores",
        ["fecha_fin"],
        unique=False,
    )
    op.create_index(
        op.f("ix_horarios_trabajadores_fecha_inicio"),
        "horarios_trabajadores",
        ["fecha_inicio"],
        unique=False,
    )
    op.create_index(
        op.f("ix_horarios_trabajadores_plantilla_id"),
        "horarios_trabajadores",
        ["plantilla_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_horarios_trabajadores_trabajador_id"),
        "horarios_trabajadores",
        ["trabajador_id"],
        unique=False,
    )

    op.create_table(
        "huellas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trabajador_id", sa.Integer(), nullable=False),
        sa.Column("template_biometrico", sa.LargeBinary(), nullable=False),
        sa.Column("proveedor", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["trabajador_id"], ["trabajadores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_huella_trabajador_activa",
        "huellas",
        ["trabajador_id", "activa"],
        unique=False,
    )
    op.create_index(op.f("ix_huellas_activa"), "huellas", ["activa"], unique=False)
    op.create_index(
        op.f("ix_huellas_trabajador_id"),
        "huellas",
        ["trabajador_id"],
        unique=False,
    )

    op.create_table(
        "marcaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trabajador_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(), nullable=False),
        sa.Column("tipo_marcacion", sa.String(length=30), nullable=False),
        sa.Column("hora_programada", sa.Time(), nullable=False),
        sa.Column("hora_real", sa.Time(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("minutos_diferencia", sa.Integer(), nullable=False),
        sa.Column("horario_trabajador_id", sa.Integer(), nullable=False),
        sa.Column("origen", sa.String(length=30), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horario_trabajador_id"], ["horarios_trabajadores.id"]),
        sa.ForeignKeyConstraint(["trabajador_id"], ["trabajadores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "trabajador_id",
            "fecha",
            "tipo_marcacion",
            name="uq_marcacion_trabajador_fecha_tipo",
        ),
    )
    op.create_index(
        "ix_marcacion_fecha_tipo_estado",
        "marcaciones",
        ["fecha", "tipo_marcacion", "estado"],
        unique=False,
    )
    op.create_index(op.f("ix_marcaciones_estado"), "marcaciones", ["estado"], unique=False)
    op.create_index(op.f("ix_marcaciones_fecha"), "marcaciones", ["fecha"], unique=False)
    op.create_index(
        op.f("ix_marcaciones_horario_trabajador_id"),
        "marcaciones",
        ["horario_trabajador_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marcaciones_tipo_marcacion"),
        "marcaciones",
        ["tipo_marcacion"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marcaciones_trabajador_id"),
        "marcaciones",
        ["trabajador_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_marcaciones_trabajador_id"), table_name="marcaciones")
    op.drop_index(op.f("ix_marcaciones_tipo_marcacion"), table_name="marcaciones")
    op.drop_index(op.f("ix_marcaciones_horario_trabajador_id"), table_name="marcaciones")
    op.drop_index(op.f("ix_marcaciones_fecha"), table_name="marcaciones")
    op.drop_index(op.f("ix_marcaciones_estado"), table_name="marcaciones")
    op.drop_index("ix_marcacion_fecha_tipo_estado", table_name="marcaciones")
    op.drop_table("marcaciones")

    op.drop_index(op.f("ix_huellas_trabajador_id"), table_name="huellas")
    op.drop_index(op.f("ix_huellas_activa"), table_name="huellas")
    op.drop_index("ix_huella_trabajador_activa", table_name="huellas")
    op.drop_table("huellas")

    op.drop_index(op.f("ix_horarios_trabajadores_trabajador_id"), table_name="horarios_trabajadores")
    op.drop_index(op.f("ix_horarios_trabajadores_plantilla_id"), table_name="horarios_trabajadores")
    op.drop_index(op.f("ix_horarios_trabajadores_fecha_inicio"), table_name="horarios_trabajadores")
    op.drop_index(op.f("ix_horarios_trabajadores_fecha_fin"), table_name="horarios_trabajadores")
    op.drop_index("ix_horario_trabajador_rango", table_name="horarios_trabajadores")
    op.drop_table("horarios_trabajadores")

    op.drop_index(op.f("ix_auditoria_entidad_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_entidad"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_administrador_id"), table_name="auditoria")
    op.drop_index(op.f("ix_auditoria_accion"), table_name="auditoria")
    op.drop_table("auditoria")

    op.drop_index(op.f("ix_trabajadores_codigo"), table_name="trabajadores")
    op.drop_table("trabajadores")

    op.drop_index(op.f("ix_plantillas_horario_nombre"), table_name="plantillas_horario")
    op.drop_table("plantillas_horario")

    op.drop_index(op.f("ix_administradores_usuario"), table_name="administradores")
    op.drop_table("administradores")
