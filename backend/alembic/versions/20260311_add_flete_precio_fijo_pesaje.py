"""Add flete and precio_fijo fields to pesajes

Revision ID: 20260311_flete
Revises: add_transferencias_cisterna
Create Date: 2026-03-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260311_flete'
down_revision = 'add_transferencias_cisterna'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Verifica si una columna existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Agregar campo flete (monto fijo que se suma al total)
    if not column_exists('pesajes', 'flete'):
        op.add_column('pesajes', sa.Column('flete', sa.Numeric(12, 2), nullable=True))
    # Agregar campo precio_fijo (precio fijo por viaje, ignora precio_unitario)
    if not column_exists('pesajes', 'precio_fijo'):
        op.add_column('pesajes', sa.Column('precio_fijo', sa.Numeric(12, 2), nullable=True))


def downgrade():
    if column_exists('pesajes', 'precio_fijo'):
        op.drop_column('pesajes', 'precio_fijo')
    if column_exists('pesajes', 'flete'):
        op.drop_column('pesajes', 'flete')
