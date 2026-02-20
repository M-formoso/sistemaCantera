"""Add importe field to pesajes and link with finanzas

Revision ID: 20260220_importe
Revises: 20260219_add_maquinas_docs_finanzas
Create Date: 2026-02-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20260220_importe'
down_revision = '20260219_add_maquinas_docs_finanzas'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos de importe al pesaje
    op.add_column('pesajes', sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=True))
    op.add_column('pesajes', sa.Column('importe_total', sa.Numeric(12, 2), nullable=True))
    op.add_column('pesajes', sa.Column('movimiento_financiero_id', UUID(as_uuid=True), nullable=True))

    # Crear foreign key al movimiento financiero
    op.create_foreign_key(
        'fk_pesajes_movimiento_financiero',
        'pesajes', 'movimientos_financieros',
        ['movimiento_financiero_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_pesajes_movimiento_financiero', 'pesajes', type_='foreignkey')
    op.drop_column('pesajes', 'movimiento_financiero_id')
    op.drop_column('pesajes', 'importe_total')
    op.drop_column('pesajes', 'precio_unitario')
