"""Add cuenta corriente tables

Revision ID: add_cuenta_corriente
Revises: 20260220_importe
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'add_cuenta_corriente'
down_revision = '20260220_importe'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla de movimientos de cuenta corriente
    op.create_table(
        'movimientos_cuenta_corriente',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('saldo_anterior', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('saldo_posterior', sa.Numeric(12, 2), nullable=False),
        sa.Column('fecha', sa.Date, nullable=False, index=True),
        sa.Column('descripcion', sa.String(500), nullable=False),
        sa.Column('detalle', sa.Text),
        sa.Column('pesaje_id', UUID(as_uuid=True), sa.ForeignKey('pesajes.id'), nullable=True),
        sa.Column('movimiento_financiero_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_financieros.id'), nullable=True),
        sa.Column('numero_comprobante', sa.String(100)),
        sa.Column('tipo_comprobante', sa.String(50)),
        sa.Column('comprobante_url', sa.String(500)),
        sa.Column('metodo_pago', sa.String(50)),
        sa.Column('referencia_pago', sa.String(100)),
        sa.Column('banco', sa.String(100)),
        sa.Column('anulado', sa.Boolean, default=False, nullable=False, server_default='false'),
        sa.Column('motivo_anulacion', sa.Text),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('notas', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )

    # Agregar campo saldo_cuenta_corriente a empresas
    op.add_column('empresas', sa.Column('saldo_cuenta_corriente', sa.Numeric(12, 2), server_default='0', nullable=False))


def downgrade():
    op.drop_column('empresas', 'saldo_cuenta_corriente')
    op.drop_table('movimientos_cuenta_corriente')
