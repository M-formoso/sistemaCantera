"""add iva fields to cuenta corriente and empresas

Revision ID: 20260604_iva_cc
Revises: 20260506_saldo_pesaje
Create Date: 2026-06-04

"""
from alembic import op


revision = '20260604_iva_cc'
down_revision = '20260506_saldo_pesaje'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columnas: usamos ADD COLUMN IF NOT EXISTS para que la migration sea idempotente
    # (importante si un intento previo aplicó parte y dejó la BD a medias).
    op.execute("""
        ALTER TABLE empresas
            ADD COLUMN IF NOT EXISTS alicuota_iva NUMERIC(5, 2) NOT NULL DEFAULT 21.00;
    """)

    op.execute("""
        ALTER TABLE movimientos_cuenta_corriente
            ADD COLUMN IF NOT EXISTS alicuota_iva NUMERIC(5, 2) NOT NULL DEFAULT 21.00;
    """)
    op.execute("""
        ALTER TABLE movimientos_cuenta_corriente
            ADD COLUMN IF NOT EXISTS monto_neto NUMERIC(12, 2);
    """)
    op.execute("""
        ALTER TABLE movimientos_cuenta_corriente
            ADD COLUMN IF NOT EXISTS monto_iva NUMERIC(12, 2);
    """)

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

    # Recalcular saldo_anterior/saldo_posterior en orden cronológico por cliente.
    # PostgreSQL no permite anidar funciones de ventana (LAG sobre SUM OVER), por eso
    # separamos en tres CTEs: deltas, saldo acumulado y saldo previo via LAG.
    op.execute("""
        WITH ordered AS (
            SELECT id,
                   empresa_id,
                   CASE
                       WHEN tipo = 'cargo' THEN monto
                       WHEN tipo = 'pago' THEN -monto
                       ELSE monto
                   END AS delta,
                   ROW_NUMBER() OVER (
                       PARTITION BY empresa_id
                       ORDER BY fecha ASC, created_at ASC
                   ) AS rn
            FROM movimientos_cuenta_corriente
            WHERE anulado = false
        ),
        with_running AS (
            SELECT id,
                   empresa_id,
                   rn,
                   SUM(delta) OVER (
                       PARTITION BY empresa_id
                       ORDER BY rn
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ) AS saldo_post
            FROM ordered
        ),
        with_pre AS (
            SELECT id,
                   saldo_post,
                   COALESCE(
                       LAG(saldo_post) OVER (PARTITION BY empresa_id ORDER BY rn),
                       0
                   ) AS saldo_pre
            FROM with_running
        )
        UPDATE movimientos_cuenta_corriente m
        SET saldo_anterior = p.saldo_pre,
            saldo_posterior = p.saldo_post
        FROM with_pre p
        WHERE m.id = p.id;
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
    op.execute("ALTER TABLE movimientos_cuenta_corriente DROP COLUMN IF EXISTS monto_iva;")
    op.execute("ALTER TABLE movimientos_cuenta_corriente DROP COLUMN IF EXISTS monto_neto;")
    op.execute("ALTER TABLE movimientos_cuenta_corriente DROP COLUMN IF EXISTS alicuota_iva;")
    op.execute("ALTER TABLE empresas DROP COLUMN IF EXISTS alicuota_iva;")
