"""Agregar intervalo_servicio_dias a camiones

Revision ID: 20260313_intervalo_dias
Revises: 20260312_repuestos_nn
Create Date: 2026-03-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260313_intervalo_dias'
down_revision = '20260312_repuestos_nn'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verificar si la columna ya existe
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('camiones')]

    if 'intervalo_servicio_dias' not in columns:
        op.add_column('camiones', sa.Column('intervalo_servicio_dias', sa.Integer(), nullable=True, server_default='90'))


def downgrade() -> None:
    op.drop_column('camiones', 'intervalo_servicio_dias')
