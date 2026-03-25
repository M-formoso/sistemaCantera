"""add precios_cliente table

Revision ID: add_precios_cliente
Revises: 20260313_intervalo_servicio_dias
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_precios_cliente'
down_revision = '20260313_intervalo_servicio_dias'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla precios_cliente
    op.create_table(
        'precios_cliente',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        sa.Column('material', sa.String(100), nullable=False, index=True),
        sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
        sa.Column('factor_conversion_m3', sa.Numeric(6, 3), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint('cliente_id', 'material', name='uq_precio_cliente_material'),
    )


def downgrade():
    op.drop_table('precios_cliente')
