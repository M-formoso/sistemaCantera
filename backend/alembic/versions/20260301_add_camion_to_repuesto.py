"""Add camion_id to repuestos for equipment assignment

Revision ID: add_camion_to_repuesto
Revises: add_camiones_clientes
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_camion_to_repuesto'
down_revision = 'add_camiones_clientes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna camion_id a repuestos
    op.add_column(
        'repuestos',
        sa.Column('camion_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Crear FK
    op.create_foreign_key(
        'fk_repuestos_camion_id',
        'repuestos',
        'camiones',
        ['camion_id'],
        ['id']
    )

    # Crear índice
    op.create_index('ix_repuestos_camion_id', 'repuestos', ['camion_id'])


def downgrade() -> None:
    # Eliminar índice
    op.drop_index('ix_repuestos_camion_id', table_name='repuestos')

    # Eliminar FK
    op.drop_constraint('fk_repuestos_camion_id', 'repuestos', type_='foreignkey')

    # Eliminar columna
    op.drop_column('repuestos', 'camion_id')
