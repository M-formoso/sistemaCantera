"""
Añade módulo de Tesorería

Revision ID: add_tesoreria_001
Revises: (última migración)
Create Date: 2026-03-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = 'add_tesoreria_001'
down_revision = None  # Se ajustará automáticamente
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Verifica si una tabla existe"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
        ),
        {"table_name": table_name}
    )
    return result.scalar()


def column_exists(table_name, column_name):
    """Verifica si una columna existe"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = :table_name AND column_name = :column_name
            )
            """
        ),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar()


def upgrade():
    # ==================== CHEQUES ====================
    if not table_exists('cheques'):
        op.create_table(
            'cheques',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            # Identificación
            sa.Column('numero', sa.String(50), nullable=False, index=True),
            sa.Column('tipo', sa.String(20), nullable=False, default='fisico'),
            sa.Column('origen', sa.String(30), nullable=False, default='recibido_cliente'),
            sa.Column('estado', sa.String(20), nullable=False, default='en_cartera', index=True),

            # Monto y fechas
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('fecha_emision', sa.Date(), nullable=True),
            sa.Column('fecha_vencimiento', sa.Date(), nullable=False, index=True),
            sa.Column('fecha_cobro', sa.Date(), nullable=True),
            sa.Column('fecha_deposito', sa.Date(), nullable=True),
            sa.Column('fecha_entrega', sa.Date(), nullable=True),

            # Bancos
            sa.Column('banco_origen', sa.String(100), nullable=True),
            sa.Column('cuenta_destino_id', UUID(as_uuid=True), sa.ForeignKey('cuentas_bancarias.id'), nullable=True),
            sa.Column('banco_destino', sa.String(100), nullable=True),

            # Relación con empresa (cliente)
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=True, index=True),

            # Información del cheque
            sa.Column('librador', sa.String(200), nullable=True),
            sa.Column('cuit_librador', sa.String(20), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('cobrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
            sa.Column('fecha_registro', sa.DateTime(), nullable=False),

            # Observaciones
            sa.Column('notas', sa.Text(), nullable=True),
            sa.Column('motivo_rechazo', sa.Text(), nullable=True),
            sa.Column('concepto_entrega', sa.String(500), nullable=True),

            # Estado lógico
            sa.Column('activo', sa.Boolean(), nullable=False, default=True),
        )

        # Índices compuestos
        op.create_index('ix_cheques_estado_vencimiento', 'cheques', ['estado', 'fecha_vencimiento'])
        op.create_index('ix_cheques_empresa_estado', 'cheques', ['empresa_id', 'estado'])

    # ==================== CAJAS DE EFECTIVO ====================
    if not table_exists('cajas_efectivo'):
        op.create_table(
            'cajas_efectivo',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            sa.Column('nombre', sa.String(100), nullable=False),
            sa.Column('descripcion', sa.Text(), nullable=True),
            sa.Column('saldo_actual', sa.Numeric(12, 2), nullable=False, default=0),
            sa.Column('saldo_inicial', sa.Numeric(12, 2), nullable=False, default=0),
            sa.Column('moneda', sa.String(10), nullable=False, default='ARS'),
            sa.Column('activo', sa.Boolean(), nullable=False, default=True),
            sa.Column('es_principal', sa.Boolean(), nullable=False, default=False),
            sa.Column('notas', sa.Text(), nullable=True),
        )

    # ==================== MOVIMIENTOS DE TESORERÍA ====================
    if not table_exists('movimientos_tesoreria'):
        op.create_table(
            'movimientos_tesoreria',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            # Tipo y concepto
            sa.Column('tipo', sa.String(30), nullable=False, index=True),
            sa.Column('concepto', sa.String(200), nullable=False),
            sa.Column('descripcion', sa.Text(), nullable=True),

            # Monto
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('es_ingreso', sa.Boolean(), nullable=False),

            # Fechas
            sa.Column('fecha_movimiento', sa.Date(), nullable=False, index=True),
            sa.Column('fecha_valor', sa.Date(), nullable=True),

            # Método de pago
            sa.Column('metodo_pago', sa.String(20), nullable=False),

            # Si es transferencia
            sa.Column('banco_origen', sa.String(100), nullable=True),
            sa.Column('banco_destino', sa.String(100), nullable=True),
            sa.Column('cuenta_destino_id', UUID(as_uuid=True), sa.ForeignKey('cuentas_bancarias.id'), nullable=True),
            sa.Column('numero_transferencia', sa.String(100), nullable=True),

            # Si es cheque
            sa.Column('cheque_id', UUID(as_uuid=True), sa.ForeignKey('cheques.id'), nullable=True),

            # Relaciones
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=True, index=True),
            sa.Column('pesaje_id', UUID(as_uuid=True), sa.ForeignKey('pesajes.id'), nullable=True),
            sa.Column('cobro_id', UUID(as_uuid=True), sa.ForeignKey('cobros_cliente.id'), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('notas', sa.Text(), nullable=True),
            sa.Column('comprobante', sa.String(100), nullable=True),

            # Anulación
            sa.Column('anulado', sa.Boolean(), nullable=False, default=False),
            sa.Column('motivo_anulacion', sa.Text(), nullable=True),
            sa.Column('anulado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
            sa.Column('fecha_anulacion', sa.DateTime(), nullable=True),

            # Estado lógico
            sa.Column('activo', sa.Boolean(), nullable=False, default=True),
        )

        # Índices compuestos
        op.create_index('ix_mov_tesoreria_fecha_tipo', 'movimientos_tesoreria', ['fecha_movimiento', 'tipo'])
        op.create_index('ix_mov_tesoreria_empresa_fecha', 'movimientos_tesoreria', ['empresa_id', 'fecha_movimiento'])

    # ==================== MOVIMIENTOS DE CAJA ====================
    if not table_exists('movimientos_caja'):
        op.create_table(
            'movimientos_caja',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            sa.Column('caja_id', UUID(as_uuid=True), sa.ForeignKey('cajas_efectivo.id'), nullable=False, index=True),

            # Tipo de movimiento
            sa.Column('tipo', sa.String(20), nullable=False),
            sa.Column('concepto', sa.String(200), nullable=False),
            sa.Column('descripcion', sa.Text(), nullable=True),

            # Montos
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('saldo_anterior', sa.Numeric(12, 2), nullable=False),
            sa.Column('saldo_posterior', sa.Numeric(12, 2), nullable=False),

            # Fecha
            sa.Column('fecha', sa.Date(), nullable=False, index=True),

            # Referencias
            sa.Column('movimiento_tesoreria_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_tesoreria.id'), nullable=True),
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('notas', sa.Text(), nullable=True),

            # Anulación
            sa.Column('anulado', sa.Boolean(), nullable=False, default=False),
        )

    # ==================== MOVIMIENTOS BANCARIOS ====================
    if not table_exists('movimientos_bancarios'):
        op.create_table(
            'movimientos_bancarios',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            sa.Column('cuenta_id', UUID(as_uuid=True), sa.ForeignKey('cuentas_bancarias.id'), nullable=False, index=True),

            # Tipo de movimiento
            sa.Column('tipo', sa.String(20), nullable=False),
            sa.Column('concepto', sa.String(200), nullable=False),
            sa.Column('descripcion', sa.Text(), nullable=True),

            # Montos
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),
            sa.Column('saldo_anterior', sa.Numeric(12, 2), nullable=False),
            sa.Column('saldo_posterior', sa.Numeric(12, 2), nullable=False),

            # Fecha
            sa.Column('fecha', sa.Date(), nullable=False, index=True),
            sa.Column('fecha_valor', sa.Date(), nullable=True),

            # Referencias
            sa.Column('numero_operacion', sa.String(100), nullable=True),
            sa.Column('movimiento_tesoreria_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_tesoreria.id'), nullable=True),
            sa.Column('cheque_id', UUID(as_uuid=True), sa.ForeignKey('cheques.id'), nullable=True),
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('notas', sa.Text(), nullable=True),

            # Anulación
            sa.Column('anulado', sa.Boolean(), nullable=False, default=False),
        )

    # ==================== GASTOS ====================
    if not table_exists('gastos'):
        op.create_table(
            'gastos',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            # Datos del gasto
            sa.Column('fecha', sa.Date(), nullable=False, index=True),
            sa.Column('concepto', sa.String(200), nullable=False),
            sa.Column('descripcion', sa.Text(), nullable=True),
            sa.Column('categoria', sa.String(100), nullable=True),

            # Monto
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),

            # Proveedor
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=True),
            sa.Column('proveedor_nombre', sa.String(200), nullable=True),

            # Comprobante
            sa.Column('tipo_comprobante', sa.String(50), nullable=True),
            sa.Column('numero_comprobante', sa.String(100), nullable=True),
            sa.Column('comprobante_url', sa.String(500), nullable=True),

            # Método de pago
            sa.Column('metodo_pago', sa.String(20), nullable=False),
            sa.Column('cuenta_bancaria_id', UUID(as_uuid=True), sa.ForeignKey('cuentas_bancarias.id'), nullable=True),
            sa.Column('caja_id', UUID(as_uuid=True), sa.ForeignKey('cajas_efectivo.id'), nullable=True),
            sa.Column('cheque_id', UUID(as_uuid=True), sa.ForeignKey('cheques.id'), nullable=True),

            # Vinculación con otros módulos
            sa.Column('camion_id', UUID(as_uuid=True), sa.ForeignKey('camiones.id'), nullable=True),
            sa.Column('servicio_id', UUID(as_uuid=True), sa.ForeignKey('servicios.id'), nullable=True),

            # Movimiento de tesorería
            sa.Column('movimiento_tesoreria_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_tesoreria.id'), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('notas', sa.Text(), nullable=True),

            # Estado
            sa.Column('estado', sa.String(20), nullable=False, default='completado'),
            sa.Column('anulado', sa.Boolean(), nullable=False, default=False),
            sa.Column('activo', sa.Boolean(), nullable=False, default=True),
        )

    # ==================== RECIBOS ====================
    if not table_exists('recibos'):
        op.create_table(
            'recibos',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),

            # Numeración
            sa.Column('numero_recibo', sa.String(50), unique=True, nullable=False, index=True),

            # Fecha
            sa.Column('fecha', sa.Date(), nullable=False, index=True),

            # Cliente
            sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False),

            # Monto
            sa.Column('monto', sa.Numeric(12, 2), nullable=False),

            # Concepto
            sa.Column('concepto', sa.String(500), nullable=False),

            # Método de pago
            sa.Column('metodo_pago', sa.String(20), nullable=False),

            # Referencias
            sa.Column('cheque_id', UUID(as_uuid=True), sa.ForeignKey('cheques.id'), nullable=True),
            sa.Column('movimiento_tesoreria_id', UUID(as_uuid=True), sa.ForeignKey('movimientos_tesoreria.id'), nullable=True),
            sa.Column('cobro_id', UUID(as_uuid=True), sa.ForeignKey('cobros_cliente.id'), nullable=True),

            # PDF
            sa.Column('pdf_url', sa.String(500), nullable=True),

            # Auditoría
            sa.Column('registrado_por_id', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('notas', sa.Text(), nullable=True),

            # Estado
            sa.Column('anulado', sa.Boolean(), nullable=False, default=False),
            sa.Column('activo', sa.Boolean(), nullable=False, default=True),
        )

    # ==================== AGREGAR PERMISO DE TESORERÍA A USUARIOS ====================
    if not column_exists('usuarios', 'permiso_tesoreria'):
        op.add_column('usuarios', sa.Column('permiso_tesoreria', sa.Boolean(), nullable=True, default=False))
        # Dar permiso a administradores
        op.execute("UPDATE usuarios SET permiso_tesoreria = TRUE WHERE rol = 'administrador'")


def downgrade():
    # Eliminar en orden inverso por dependencias
    op.drop_table('recibos')
    op.drop_table('gastos')
    op.drop_table('movimientos_bancarios')
    op.drop_table('movimientos_caja')
    op.drop_table('movimientos_tesoreria')
    op.drop_table('cajas_efectivo')
    op.drop_table('cheques')

    # Eliminar columna de permiso
    op.drop_column('usuarios', 'permiso_tesoreria')
