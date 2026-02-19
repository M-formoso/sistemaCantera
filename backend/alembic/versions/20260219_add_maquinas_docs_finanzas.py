"""add maquinas, documentos y finanzas

Revision ID: add_maquinas_finanzas
Revises: fix_cliente_nombre
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_maquinas_finanzas'
down_revision = 'fix_cliente_nombre'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =============================================
    # CAMIONES: Agregar campos para máquinas y documentos
    # =============================================

    # Campos de categoría y identificación
    op.add_column('camiones', sa.Column('categoria', sa.String(length=20), nullable=True, server_default='camion'))
    op.add_column('camiones', sa.Column('nombre', sa.String(length=100), nullable=True))
    op.add_column('camiones', sa.Column('codigo_interno', sa.String(length=50), nullable=True))
    op.add_column('camiones', sa.Column('numero_serie', sa.String(length=100), nullable=True))
    op.add_column('camiones', sa.Column('tipo_maquina', sa.String(length=50), nullable=True))

    # Métricas para máquinas
    op.add_column('camiones', sa.Column('horas_promedio_diarias', sa.Numeric(5, 2), nullable=True, server_default='0'))
    op.add_column('camiones', sa.Column('ultimo_servicio_horas', sa.Numeric(10, 2), nullable=True))
    op.add_column('camiones', sa.Column('proximo_servicio_horas', sa.Numeric(10, 2), nullable=True))
    op.add_column('camiones', sa.Column('intervalo_servicio_horas', sa.Integer(), nullable=True, server_default='250'))

    # Documentación inline
    op.add_column('camiones', sa.Column('tarjeta_verde_url', sa.String(length=500), nullable=True))
    op.add_column('camiones', sa.Column('tarjeta_verde_vencimiento', sa.Date(), nullable=True))
    op.add_column('camiones', sa.Column('seguro_url', sa.String(length=500), nullable=True))
    op.add_column('camiones', sa.Column('seguro_compania', sa.String(length=100), nullable=True))
    op.add_column('camiones', sa.Column('seguro_poliza', sa.String(length=100), nullable=True))
    op.add_column('camiones', sa.Column('seguro_vencimiento', sa.Date(), nullable=True))
    op.add_column('camiones', sa.Column('vtv_url', sa.String(length=500), nullable=True))
    op.add_column('camiones', sa.Column('vtv_vencimiento', sa.Date(), nullable=True))
    op.add_column('camiones', sa.Column('cedula_url', sa.String(length=500), nullable=True))

    # Hacer patente nullable (máquinas pueden no tener patente)
    op.alter_column('camiones', 'patente', existing_type=sa.String(length=20), nullable=True)

    # =============================================
    # TABLA: documentos_equipo
    # =============================================
    op.create_table('documentos_equipo',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('equipo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('archivo_url', sa.String(length=500), nullable=False),
        sa.Column('archivo_nombre', sa.String(length=255), nullable=True),
        sa.Column('archivo_tipo', sa.String(length=50), nullable=True),
        sa.Column('archivo_tamaño', sa.Integer(), nullable=True),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['equipo_id'], ['camiones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documentos_equipo_equipo_id', 'documentos_equipo', ['equipo_id'])

    # =============================================
    # TABLA: categorias_finanzas
    # =============================================
    op.create_table('categorias_finanzas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True, server_default='#6B7280'),
        sa.Column('icono', sa.String(length=50), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # =============================================
    # TABLA: movimientos_financieros
    # =============================================
    op.create_table('movimientos_financieros',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('categoria_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=False),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.Column('camion_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('numero_comprobante', sa.String(length=100), nullable=True),
        sa.Column('tipo_comprobante', sa.String(length=50), nullable=True),
        sa.Column('comprobante_url', sa.String(length=500), nullable=True),
        sa.Column('metodo_pago', sa.String(length=50), nullable=True),
        sa.Column('referencia_pago', sa.String(length=100), nullable=True),
        sa.Column('banco', sa.String(length=100), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=True, server_default='completado'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias_finanzas.id'], ),
        sa.ForeignKeyConstraint(['camion_id'], ['camiones.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_movimientos_financieros_fecha', 'movimientos_financieros', ['fecha'])
    op.create_index('ix_movimientos_financieros_tipo', 'movimientos_financieros', ['tipo'])

    # =============================================
    # TABLA: cuentas_bancarias
    # =============================================
    op.create_table('cuentas_bancarias',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('banco', sa.String(length=100), nullable=False),
        sa.Column('tipo_cuenta', sa.String(length=50), nullable=True),
        sa.Column('numero_cuenta', sa.String(length=50), nullable=True),
        sa.Column('cbu', sa.String(length=30), nullable=True),
        sa.Column('alias', sa.String(length=50), nullable=True),
        sa.Column('titular', sa.String(length=200), nullable=True),
        sa.Column('cuit_titular', sa.String(length=20), nullable=True),
        sa.Column('saldo_inicial', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('saldo_actual', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('moneda', sa.String(length=10), nullable=True, server_default='ARS'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # =============================================
    # INSERTAR CATEGORÍAS POR DEFECTO
    # =============================================
    op.execute("""
        INSERT INTO categorias_finanzas (id, nombre, tipo, descripcion, color, activo, created_at, updated_at) VALUES
        (gen_random_uuid(), 'Venta de materiales', 'ingreso', 'Ingresos por venta de áridos, piedra, arena, etc.', '#10B981', true, now(), now()),
        (gen_random_uuid(), 'Servicios de transporte', 'ingreso', 'Ingresos por flete y transporte', '#3B82F6', true, now(), now()),
        (gen_random_uuid(), 'Alquiler de maquinaria', 'ingreso', 'Ingresos por alquiler de equipos', '#8B5CF6', true, now(), now()),
        (gen_random_uuid(), 'Otros ingresos', 'ingreso', 'Otros ingresos varios', '#6B7280', true, now(), now()),
        (gen_random_uuid(), 'Combustible', 'egreso', 'Gastos en combustible', '#EF4444', true, now(), now()),
        (gen_random_uuid(), 'Mantenimiento y repuestos', 'egreso', 'Gastos de mantenimiento y repuestos', '#F59E0B', true, now(), now()),
        (gen_random_uuid(), 'Sueldos y jornales', 'egreso', 'Gastos en personal', '#EC4899', true, now(), now()),
        (gen_random_uuid(), 'Seguros', 'egreso', 'Gastos en seguros de vehículos y equipos', '#6366F1', true, now(), now()),
        (gen_random_uuid(), 'Impuestos y tasas', 'egreso', 'Impuestos, patentes, tasas municipales', '#14B8A6', true, now(), now()),
        (gen_random_uuid(), 'Servicios (luz, agua, etc)', 'egreso', 'Servicios básicos', '#84CC16', true, now(), now()),
        (gen_random_uuid(), 'Otros egresos', 'egreso', 'Otros gastos varios', '#6B7280', true, now(), now())
    """)


def downgrade() -> None:
    # Eliminar tablas
    op.drop_table('cuentas_bancarias')
    op.drop_index('ix_movimientos_financieros_tipo', table_name='movimientos_financieros')
    op.drop_index('ix_movimientos_financieros_fecha', table_name='movimientos_financieros')
    op.drop_table('movimientos_financieros')
    op.drop_table('categorias_finanzas')
    op.drop_index('ix_documentos_equipo_equipo_id', table_name='documentos_equipo')
    op.drop_table('documentos_equipo')

    # Revertir cambios en camiones
    op.alter_column('camiones', 'patente', existing_type=sa.String(length=20), nullable=False)

    op.drop_column('camiones', 'cedula_url')
    op.drop_column('camiones', 'vtv_vencimiento')
    op.drop_column('camiones', 'vtv_url')
    op.drop_column('camiones', 'seguro_vencimiento')
    op.drop_column('camiones', 'seguro_poliza')
    op.drop_column('camiones', 'seguro_compania')
    op.drop_column('camiones', 'seguro_url')
    op.drop_column('camiones', 'tarjeta_verde_vencimiento')
    op.drop_column('camiones', 'tarjeta_verde_url')
    op.drop_column('camiones', 'intervalo_servicio_horas')
    op.drop_column('camiones', 'proximo_servicio_horas')
    op.drop_column('camiones', 'ultimo_servicio_horas')
    op.drop_column('camiones', 'horas_promedio_diarias')
    op.drop_column('camiones', 'tipo_maquina')
    op.drop_column('camiones', 'numero_serie')
    op.drop_column('camiones', 'codigo_interno')
    op.drop_column('camiones', 'nombre')
    op.drop_column('camiones', 'categoria')
