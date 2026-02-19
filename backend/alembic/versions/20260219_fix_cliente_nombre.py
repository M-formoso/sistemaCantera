"""add cliente_nombre to pesajes

Revision ID: fix_cliente_nombre
Revises: add_empresas_01
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_cliente_nombre'
down_revision = 'add_empresas_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar cliente_nombre si no existe
    op.add_column('pesajes', sa.Column('cliente_nombre', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('pesajes', 'cliente_nombre')
