"""add iva fields to cuenta corriente and empresas

Revision ID: 20260604_iva_cc
Revises: 20260506_saldo_pesaje
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa


revision = '20260604_iva_cc'
down_revision = '20260506_saldo_pesaje'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empresas: alícuota de IVA por defecto del cliente (editable)
    op.add_column(
        'empresas',
        sa.Column('alicuota_iva', sa.Numeric(5, 2), nullable=False, server_default='21.00'),
    )

    # Movimientos CC: alícuota usada, monto neto, monto IVA.
    # El campo `monto` existente pasa a representar el TOTAL c/IVA.
    op.add_column(
        'movimientos_cuenta_corriente',
        sa.Column('alicuota_iva', sa.Numeric(5, 2), nullable=False, server_default='21.00'),
    )
    op.add_column(
        'movimientos_cuenta_corriente',
        sa.Column('monto_neto', sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        'movimientos_cuenta_corriente',
        sa.Column('monto_iva', sa.Numeric(12, 2), nullable=True),
    )

    # Backfill: para movimientos existentes asumimos que `monto` ya era neto
    # (porque hasta hoy no se discriminaba IVA en el sistema). Recalculamos
    # monto_iva y dejamos `monto` como el TOTAL c/IVA usando la alícuota 21%.
    op.execute("""
        UPDATE movimientos_cuenta_corriente
        SET monto_neto = monto,
            monto_iva = ROUND(monto * 0.21, 2),
            monto = ROUND(monto * 1.21, 2)
        WHERE monto_neto IS NULL;
    """)

    # Recalcular saldo_anterior/saldo_posterior de cada movimiento en orden
    # cronológico por cliente para que la columna SALDO refleje los totales c/IVA.
    op.execute("""
        WITH ordered AS (
            SELECT id,
                   empresa_id,
                   CASE
                       WHEN tipo = 'cargo' THEN monto
                       WHEN tipo = 'pago' THEN -monto
                       ELSE monto  -- ajuste: monto ya viene firmado
                   END AS delta,
                   ROW_NUMBER() OVER (
                       PARTITION BY empresa_id
                       ORDER BY fecha ASC, created_at ASC
                   ) AS rn
            FROM movimientos_cuenta_corriente
            WHERE anulado = false
        ),
        running AS (
            SELECT id,
                   empresa_id,
                   SUM(delta) OVER (
                       PARTITION BY empresa_id
                       ORDER BY rn
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ) AS saldo_post,
                   LAG(SUM(delta) OVER (
                       PARTITION BY empresa_id
                       ORDER BY rn
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ), 1, 0) OVER (
                       PARTITION BY empresa_id
                       ORDER BY rn
                   ) AS saldo_pre
            FROM ordered
        )
        UPDATE movimientos_cuenta_corriente m
        SET saldo_anterior = r.saldo_pre,
            saldo_posterior = r.saldo_post
        FROM running r
        WHERE m.id = r.id;
    """)

    # Actualizar saldo_cuenta_corriente de cada empresa al nuevo total con IVA.
    op.execute("""
        UPDATE empresas e
        SET saldo_cuenta_corriente = COALESCE((
            SELECT
                SUM(CASE
                        WHEN tipo = 'cargo' THEN monto
                        WHEN tipo = 'pago' THEN -monto
                        ELSE monto
                    END)
            FROM movimientos_cuenta_corriente
            WHERE empresa_id = e.id AND anulado = false
        ), 0);
    """)


def downgrade() -> None:
    # Volver `monto` a neto (asumiendo 21%) y eliminar columnas IVA.
    op.execute("""
        UPDATE movimientos_cuenta_corriente
        SET monto = ROUND(monto / 1.21, 2)
        WHERE alicuota_iva = 21;
    """)
    op.drop_column('movimientos_cuenta_corriente', 'monto_iva')
    op.drop_column('movimientos_cuenta_corriente', 'monto_neto')
    op.drop_column('movimientos_cuenta_corriente', 'alicuota_iva')
    op.drop_column('empresas', 'alicuota_iva')
