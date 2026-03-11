"""Add flete and precio_fijo fields to pesajes

Revision ID: 20260311_flete
Revises: 20260310_transfer
Create Date: 2026-03-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260311_flete'
down_revision = '20260310_transfer'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campo flete (monto fijo que se suma al total)
    op.add_column('pesajes', sa.Column('flete', sa.Numeric(12, 2), nullable=True))
    # Agregar campo precio_fijo (precio fijo por viaje, ignora precio_unitario)
    op.add_column('pesajes', sa.Column('precio_fijo', sa.Numeric(12, 2), nullable=True))


def downgrade():
    op.drop_column('pesajes', 'precio_fijo')
    op.drop_column('pesajes', 'flete')
