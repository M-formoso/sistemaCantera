"""add historial_pesajes table

Revision ID: 20260410_historial
Revises: 20260403_add_listas_precios
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260410_historial'
down_revision = '20260403_add_listas_precios'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'historial_pesajes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pesaje_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pesaje_id'], ['pesajes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_historial_pesajes_pesaje_id', 'historial_pesajes', ['pesaje_id'])


def downgrade() -> None:
    op.drop_index('ix_historial_pesajes_pesaje_id')
    op.drop_table('historial_pesajes')
