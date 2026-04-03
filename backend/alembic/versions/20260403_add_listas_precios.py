"""
Añade módulo de Listas de Precios

Revision ID: add_listas_precios_001
Revises: add_tesoreria_001
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = 'add_listas_precios_001'
down_revision = 'add_tesoreria_001'
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
    """Verifica si una columna existe en una tabla"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = :table_name AND column_name = :column_name
            )"""
        ),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar()


def upgrade():
    # Crear tabla listas_precios
    if not table_exists('listas_precios'):
        op.create_table(
            'listas_precios',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('nombre', sa.String(100), nullable=False, unique=True),
            sa.Column('descripcion', sa.Text, nullable=True),
            sa.Column('activo', sa.Boolean, nullable=False, default=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
        )
        op.create_index('ix_listas_precios_nombre', 'listas_precios', ['nombre'])
        op.create_index('ix_listas_precios_activo', 'listas_precios', ['activo'])

    # Crear tabla items_lista_precio
    if not table_exists('items_lista_precio'):
        op.create_table(
            'items_lista_precio',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('lista_id', UUID(as_uuid=True), sa.ForeignKey('listas_precios.id', ondelete='CASCADE'), nullable=False),
            sa.Column('material', sa.String(100), nullable=False),
            sa.Column('precio_unitario', sa.Numeric(12, 2), nullable=False),
            sa.Column('factor_conversion_m3', sa.Numeric(6, 3), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
            sa.UniqueConstraint('lista_id', 'material', name='uq_item_lista_material'),
        )
        op.create_index('ix_items_lista_precio_lista_id', 'items_lista_precio', ['lista_id'])
        op.create_index('ix_items_lista_precio_material', 'items_lista_precio', ['material'])

    # Agregar columna lista_precio_id a pesajes
    if not column_exists('pesajes', 'lista_precio_id'):
        op.add_column(
            'pesajes',
            sa.Column('lista_precio_id', UUID(as_uuid=True), sa.ForeignKey('listas_precios.id'), nullable=True)
        )
        op.create_index('ix_pesajes_lista_precio_id', 'pesajes', ['lista_precio_id'])


def downgrade():
    # Eliminar columna de pesajes
    if column_exists('pesajes', 'lista_precio_id'):
        op.drop_index('ix_pesajes_lista_precio_id', table_name='pesajes')
        op.drop_column('pesajes', 'lista_precio_id')

    # Eliminar tablas
    if table_exists('items_lista_precio'):
        op.drop_table('items_lista_precio')

    if table_exists('listas_precios'):
        op.drop_table('listas_precios')
