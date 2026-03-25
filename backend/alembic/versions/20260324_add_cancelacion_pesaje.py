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
    # Verificar qué columnas ya existen
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pesajes')]

    # Agregar campos de cancelación solo si no existen
    if 'motivo_cancelacion' not in columns:
        op.add_column('pesajes', sa.Column('motivo_cancelacion', sa.Text(), nullable=True))

    if 'fecha_cancelacion' not in columns:
        op.add_column('pesajes', sa.Column('fecha_cancelacion', sa.DateTime(), nullable=True))

    if 'cancelado_por' not in columns:
        op.add_column('pesajes', sa.Column('cancelado_por', postgresql.UUID(as_uuid=True), nullable=True))

        # Crear foreign key para cancelado_por (solo si agregamos la columna)
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
