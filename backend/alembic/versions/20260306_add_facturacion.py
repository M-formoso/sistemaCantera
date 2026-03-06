"""Add facturacion tables (facturas, pagos_factura, pagos_remito)

Revision ID: add_facturacion
Revises: add_camion_to_repuesto
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_facturacion'
down_revision = 'add_camion_to_repuesto'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Verifica si una tabla existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Verifica si una columna existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # =============================================
    # TABLA: facturas
    # =============================================
    if not table_exists('facturas'):
        op.create_table(
            'facturas',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

            # Numeración
            sa.Column('numero_factura', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('punto_venta', sa.Integer, server_default='1'),

            # Tipo
            sa.Column('tipo_comprobante', sa.String(30), nullable=False),

            # Cliente
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False, index=True),

            # Fechas
            sa.Column('fecha_emision', sa.Date, nullable=False, index=True),
            sa.Column('fecha_vencimiento', sa.Date, nullable=True),

            # Montos
            sa.Column('subtotal', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('descuento', sa.Numeric(12, 2), server_default='0'),
            sa.Column('iva_21', sa.Numeric(12, 2), server_default='0'),
            sa.Column('iva_10_5', sa.Numeric(12, 2), server_default='0'),
            sa.Column('iva_27', sa.Numeric(12, 2), server_default='0'),
            sa.Column('percepciones_iibb', sa.Numeric(12, 2), server_default='0'),
            sa.Column('percepciones_iva', sa.Numeric(12, 2), server_default='0'),
            sa.Column('otros_impuestos', sa.Numeric(12, 2), server_default='0'),
            sa.Column('total', sa.Numeric(12, 2), nullable=False),
            sa.Column('saldo_pendiente', sa.Numeric(12, 2), nullable=False),

            # Estado
            sa.Column('estado', sa.String(20), server_default='pendiente', nullable=False, index=True),

            # CAE
            sa.Column('cae', sa.String(20)),
            sa.Column('cae_vencimiento', sa.Date),

            # Referencia NC/ND
            sa.Column('factura_original_id', UUID(as_uuid=True), sa.ForeignKey('facturas.id'), nullable=True),

            # Observaciones
            sa.Column('observaciones', sa.Text),

            # Auditoría
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('anulada', sa.Boolean, server_default='false', nullable=False),
            sa.Column('motivo_anulacion', sa.Text),
            sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        )

    # =============================================
    # TABLA: factura_remito (relación N:M)
    # =============================================
    if not table_exists('factura_remito'):
        op.create_table(
            'factura_remito',
            sa.Column('factura_id', UUID(as_uuid=True), sa.ForeignKey('facturas.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('remito_id', UUID(as_uuid=True), sa.ForeignKey('remitos.id', ondelete='CASCADE'), primary_key=True),
        )

    # =============================================
    # TABLA: pagos_factura
    # =============================================
    if not table_exists('pagos_factura'):
        op.create_table(
            'pagos_factura',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

            # Factura
            sa.Column('factura_id', UUID(as_uuid=True), sa.ForeignKey('facturas.id'), nullable=False, index=True),
            sa.Column('movimiento_cc_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_cuenta_corriente.id'), nullable=True),

            # Datos del pago
            sa.Column('fecha', sa.Date, nullable=False),
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('forma_pago', sa.String(50), nullable=False),

            # Datos cheque
            sa.Column('banco', sa.String(100)),
            sa.Column('numero_cheque', sa.String(50)),
            sa.Column('fecha_cheque', sa.Date),
            sa.Column('cuit_emisor', sa.String(20)),

            # Retenciones
            sa.Column('es_retencion', sa.Boolean, server_default='false'),
            sa.Column('tipo_retencion', sa.String(50)),
            sa.Column('numero_certificado', sa.String(100)),

            # Referencia
            sa.Column('referencia', sa.String(200)),
            sa.Column('observaciones', sa.Text),

            # Auditoría
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('anulado', sa.Boolean, server_default='false'),
            sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        )

    # =============================================
    # TABLA: pagos_remito
    # =============================================
    if not table_exists('pagos_remito'):
        op.create_table(
            'pagos_remito',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

            # Remito
            sa.Column('remito_id', UUID(as_uuid=True), sa.ForeignKey('remitos.id'), nullable=False, index=True),
            sa.Column('movimiento_cc_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_cuenta_corriente.id'), nullable=True),

            # Datos del pago
            sa.Column('fecha', sa.Date, nullable=False),
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('forma_pago', sa.String(50), nullable=False),

            # Datos cheque
            sa.Column('banco', sa.String(100)),
            sa.Column('numero_cheque', sa.String(50)),
            sa.Column('fecha_cheque', sa.Date),
            sa.Column('cuit_emisor', sa.String(20)),

            # Retenciones
            sa.Column('es_retencion', sa.Boolean, server_default='false'),
            sa.Column('tipo_retencion', sa.String(50)),
            sa.Column('numero_certificado', sa.String(100)),

            # Referencia
            sa.Column('referencia', sa.String(200)),
            sa.Column('observaciones', sa.Text),

            # Auditoría
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('anulado', sa.Boolean, server_default='false'),
            sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        )

    # =============================================
    # AGREGAR COLUMNAS A REMITOS (para saldo)
    # =============================================
    if not column_exists('remitos', 'importe'):
        op.add_column('remitos', sa.Column('importe', sa.Numeric(12, 2), server_default='0'))

    if not column_exists('remitos', 'saldo_pendiente'):
        op.add_column('remitos', sa.Column('saldo_pendiente', sa.Numeric(12, 2), server_default='0'))

    if not column_exists('remitos', 'facturado'):
        op.add_column('remitos', sa.Column('facturado', sa.Boolean, server_default='false'))


def downgrade() -> None:
    # Eliminar columnas de remitos
    if column_exists('remitos', 'facturado'):
        op.drop_column('remitos', 'facturado')
    if column_exists('remitos', 'saldo_pendiente'):
        op.drop_column('remitos', 'saldo_pendiente')
    if column_exists('remitos', 'importe'):
        op.drop_column('remitos', 'importe')

    # Eliminar tablas
    if table_exists('pagos_remito'):
        op.drop_table('pagos_remito')
    if table_exists('pagos_factura'):
        op.drop_table('pagos_factura')
    if table_exists('factura_remito'):
        op.drop_table('factura_remito')
    if table_exists('facturas'):
        op.drop_table('facturas')
