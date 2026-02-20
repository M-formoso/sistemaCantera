"""Add ordenes_entrega table

Revision ID: add_ordenes_entrega
Revises: add_cuenta_corriente
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ordenes_entrega'
down_revision = 'add_cuenta_corriente'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear tabla ordenes_entrega
    op.create_table(
        'ordenes_entrega',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('numero_orden', sa.Integer(), nullable=False),
        sa.Column('fecha_entrega', sa.Date(), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cliente_nombre', sa.String(255), nullable=True),
        sa.Column('material', sa.String(100), nullable=False),
        sa.Column('cantidad_cargas', sa.Integer(), nullable=False),
        sa.Column('cargas_entregadas', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('peso_estimado_carga', sa.Numeric(10, 2), nullable=True),
        sa.Column('peso_total_estimado', sa.Numeric(12, 2), nullable=True),
        sa.Column('peso_total_entregado', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('estado', sa.String(20), nullable=False, server_default='pendiente'),
        sa.Column('solicitante', sa.String(100), nullable=True),
        sa.Column('contacto_cliente', sa.String(100), nullable=True),
        sa.Column('telefono_contacto', sa.String(50), nullable=True),
        sa.Column('direccion_entrega', sa.Text(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cliente_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices
    op.create_index('ix_ordenes_entrega_numero_orden', 'ordenes_entrega', ['numero_orden'], unique=True)
    op.create_index('ix_ordenes_entrega_fecha_entrega', 'ordenes_entrega', ['fecha_entrega'])
    op.create_index('ix_ordenes_entrega_estado', 'ordenes_entrega', ['estado'])

    # Agregar columna orden_entrega_id a pesajes
    op.add_column('pesajes', sa.Column('orden_entrega_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_pesajes_orden_entrega',
        'pesajes', 'ordenes_entrega',
        ['orden_entrega_id'], ['id']
    )
    op.create_index('ix_pesajes_orden_entrega_id', 'pesajes', ['orden_entrega_id'])


def downgrade() -> None:
    # Eliminar columna de pesajes
    op.drop_index('ix_pesajes_orden_entrega_id', table_name='pesajes')
    op.drop_constraint('fk_pesajes_orden_entrega', 'pesajes', type_='foreignkey')
    op.drop_column('pesajes', 'orden_entrega_id')

    # Eliminar índices
    op.drop_index('ix_ordenes_entrega_estado', table_name='ordenes_entrega')
    op.drop_index('ix_ordenes_entrega_fecha_entrega', table_name='ordenes_entrega')
    op.drop_index('ix_ordenes_entrega_numero_orden', table_name='ordenes_entrega')

    # Eliminar tabla
    op.drop_table('ordenes_entrega')
