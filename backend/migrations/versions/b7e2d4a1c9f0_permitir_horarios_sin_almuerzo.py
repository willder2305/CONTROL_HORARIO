"""permitir horarios sin almuerzo

Revision ID: b7e2d4a1c9f0
Revises: 8066f0fdd060
Create Date: 2026-08-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b7e2d4a1c9f0"
down_revision = "8066f0fdd060"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "plantillas_horario",
        "hora_salida_almuerzo",
        existing_type=sa.Time(),
        nullable=True,
    )
    op.alter_column(
        "plantillas_horario",
        "hora_regreso_almuerzo",
        existing_type=sa.Time(),
        nullable=True,
    )
    op.alter_column(
        "horarios_trabajadores",
        "hora_salida_almuerzo",
        existing_type=sa.Time(),
        nullable=True,
    )
    op.alter_column(
        "horarios_trabajadores",
        "hora_regreso_almuerzo",
        existing_type=sa.Time(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "horarios_trabajadores",
        "hora_regreso_almuerzo",
        existing_type=sa.Time(),
        nullable=False,
    )
    op.alter_column(
        "horarios_trabajadores",
        "hora_salida_almuerzo",
        existing_type=sa.Time(),
        nullable=False,
    )
    op.alter_column(
        "plantillas_horario",
        "hora_regreso_almuerzo",
        existing_type=sa.Time(),
        nullable=False,
    )
    op.alter_column(
        "plantillas_horario",
        "hora_salida_almuerzo",
        existing_type=sa.Time(),
        nullable=False,
    )
