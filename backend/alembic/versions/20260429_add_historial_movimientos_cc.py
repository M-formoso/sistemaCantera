"""add historial_movimientos_cc table

Revision ID: 20260429_hist_cc
Revises: 20260410_historial
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260429_hist_cc'
down_revision = '20260410_historial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'historial_movimientos_cc',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('movimiento_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['movimiento_id'], ['movimientos_cuenta_corriente.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_historial_movimientos_cc_movimiento_id',
        'historial_movimientos_cc',
        ['movimiento_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_historial_movimientos_cc_movimiento_id')
    op.drop_table('historial_movimientos_cc')
