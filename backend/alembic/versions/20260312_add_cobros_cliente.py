"""Add cobros cliente tables for cross-control payment system

Revision ID: 20260312_cobros
Revises: 20260311_flete
Create Date: 2026-03-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260312_cobros'
down_revision = '20260311_flete'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Verifica si una tabla existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    # Crear tabla cobros_cliente
    if not table_exists('cobros_cliente'):
        op.create_table(
            'cobros_cliente',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('numero_cobro', sa.Integer(), nullable=False),
            sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('fecha', sa.Date(), nullable=False),
            sa.Column('monto_total', sa.Numeric(12, 2), nullable=False),
            sa.Column('monto_aplicado', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('diferencia', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('estado', sa.String(20), nullable=False, server_default='borrador'),
            sa.Column('numero_orden_pago', sa.String(100), nullable=True),
            sa.Column('observaciones', sa.Text(), nullable=True),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('confirmed_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('fecha_confirmacion', sa.Date(), nullable=True),
            sa.Column('anulado', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('motivo_anulacion', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
            sa.ForeignKeyConstraint(['created_by'], ['usuarios.id']),
            sa.ForeignKeyConstraint(['confirmed_by'], ['usuarios.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_cobros_cliente_numero_cobro', 'cobros_cliente', ['numero_cobro'], unique=True)
        op.create_index('ix_cobros_cliente_empresa_id', 'cobros_cliente', ['empresa_id'])
        op.create_index('ix_cobros_cliente_fecha', 'cobros_cliente', ['fecha'])

    # Crear tabla items_cobro_cliente
    if not table_exists('items_cobro_cliente'):
        op.create_table(
            'items_cobro_cliente',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('cobro_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tipo_item', sa.String(30), nullable=False),
            sa.Column('concepto', sa.String(10), nullable=False),
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('descripcion', sa.String(500), nullable=True),
            sa.Column('factura_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('remito_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('pesaje_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('banco', sa.String(100), nullable=True),
            sa.Column('numero_cheque', sa.String(50), nullable=True),
            sa.Column('fecha_cheque', sa.Date(), nullable=True),
            sa.Column('cuit_emisor', sa.String(20), nullable=True),
            sa.Column('referencia_transferencia', sa.String(100), nullable=True),
            sa.Column('numero_certificado', sa.String(100), nullable=True),
            sa.Column('movimiento_cc_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['cobro_id'], ['cobros_cliente.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['factura_id'], ['facturas.id']),
            sa.ForeignKeyConstraint(['remito_id'], ['remitos.id']),
            sa.ForeignKeyConstraint(['pesaje_id'], ['pesajes.id']),
            sa.ForeignKeyConstraint(['movimiento_cc_id'], ['movimientos_cuenta_corriente.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_items_cobro_cliente_cobro_id', 'items_cobro_cliente', ['cobro_id'])


def downgrade():
    if table_exists('items_cobro_cliente'):
        op.drop_table('items_cobro_cliente')
    if table_exists('cobros_cliente'):
        op.drop_table('cobros_cliente')
