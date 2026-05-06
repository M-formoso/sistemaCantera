"""add saldo_pendiente to pesaje

Revision ID: 20260506_saldo_pesaje
Revises: 20260429_hist_cc
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa


revision = '20260506_saldo_pesaje'
down_revision = '20260429_hist_cc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'pesajes',
        sa.Column('saldo_pendiente', sa.Numeric(12, 2), nullable=True),
    )

    # Inicializar saldo_pendiente para pesajes existentes:
    # saldo_pendiente = importe_total - sum(items_cobro_aplicados.monto)
    # Solo para pesajes con importe (los cargos en cuenta corriente).
    op.execute("""
        UPDATE pesajes p
        SET saldo_pendiente = GREATEST(
            COALESCE(p.importe_total, 0) - COALESCE((
                SELECT SUM(i.monto)
                FROM items_cobro_cliente i
                JOIN cobros_cliente c ON c.id = i.cobro_id
                WHERE i.pesaje_id = p.id
                  AND i.concepto = 'debe'
                  AND c.estado = 'aplicado'
                  AND c.anulado = false
            ), 0),
            0
        )
        WHERE p.importe_total IS NOT NULL AND p.importe_total > 0;
    """)


def downgrade() -> None:
    op.drop_column('pesajes', 'saldo_pendiente')
