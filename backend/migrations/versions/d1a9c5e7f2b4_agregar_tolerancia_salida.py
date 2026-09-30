"""agregar tolerancia de salida

Revision ID: d1a9c5e7f2b4
Revises: b7e2d4a1c9f0
Create Date: 2026-09-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d1a9c5e7f2b4"
down_revision = "b7e2d4a1c9f0"
branch_labels = None
depends_on = None


def upgrade():
    """Agrega una tolerancia de salida segura a plantillas y horarios vigentes."""
    op.add_column(
        "plantillas_horario",
        sa.Column("tolerancia_salida", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "horarios_trabajadores",
        sa.Column("tolerancia_salida", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    """Revierte las columnas de tolerancia de salida creadas por esta revision."""
    op.drop_column("horarios_trabajadores", "tolerancia_salida")
    op.drop_column("plantillas_horario", "tolerancia_salida")
