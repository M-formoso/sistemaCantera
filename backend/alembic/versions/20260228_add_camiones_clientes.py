"""Add camiones_clientes table for client vehicles

Revision ID: add_camiones_clientes
Revises: add_doble_pesaje
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_camiones_clientes'
down_revision = 'add_doble_pesaje'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear tabla camiones_clientes
    op.create_table(
        'camiones_clientes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patente', sa.String(20), nullable=False),
        sa.Column('descripcion', sa.String(100), nullable=True),
        sa.Column('chofer_habitual', sa.String(100), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cliente_id'], ['empresas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices
    op.create_index('ix_camiones_clientes_cliente_id', 'camiones_clientes', ['cliente_id'])
    op.create_index('ix_camiones_clientes_patente', 'camiones_clientes', ['patente'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_camiones_clientes_patente', table_name='camiones_clientes')
    op.drop_index('ix_camiones_clientes_cliente_id', table_name='camiones_clientes')

    # Eliminar tabla
    op.drop_table('camiones_clientes')
