"""add cancelacion fields to pesaje

Revision ID: add_cancelacion_pesaje
Revises: add_precios_cliente
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_cancelacion_pesaje'
down_revision = 'add_precios_cliente'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos de cancelación a pesajes
    op.add_column('pesajes', sa.Column('motivo_cancelacion', sa.Text(), nullable=True))
    op.add_column('pesajes', sa.Column('fecha_cancelacion', sa.DateTime(), nullable=True))
    op.add_column('pesajes', sa.Column('cancelado_por', postgresql.UUID(as_uuid=True), nullable=True))

    # Crear foreign key para cancelado_por
    op.create_foreign_key(
        'fk_pesajes_cancelado_por',
        'pesajes',
        'usuarios',
        ['cancelado_por'],
        ['id']
    )


def downgrade():
    op.drop_constraint('fk_pesajes_cancelado_por', 'pesajes', type_='foreignkey')
    op.drop_column('pesajes', 'cancelado_por')
    op.drop_column('pesajes', 'fecha_cancelacion')
    op.drop_column('pesajes', 'motivo_cancelacion')
