"""Add transferencias_cisterna table and cisterna_origen_id column

Revision ID: add_transferencias_cisterna
Revises: add_facturacion
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_transferencias_cisterna'
down_revision = 'add_facturacion'
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
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Agregar columna cisterna_origen_id a cisterna_combustible
    if not column_exists('cisterna_combustible', 'cisterna_origen_id'):
        op.add_column('cisterna_combustible', sa.Column(
            'cisterna_origen_id',
            UUID(as_uuid=True),
            sa.ForeignKey('cisterna_combustible.id'),
            nullable=True
        ))

    # Crear tabla transferencias_cisterna
    if not table_exists('transferencias_cisterna'):
        op.create_table(
            'transferencias_cisterna',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('cisterna_origen_id', UUID(as_uuid=True), sa.ForeignKey('cisterna_combustible.id'), nullable=False),
            sa.Column('cisterna_destino_id', UUID(as_uuid=True), sa.ForeignKey('cisterna_combustible.id'), nullable=False),
            sa.Column('fecha', sa.DateTime, nullable=False),
            sa.Column('litros', sa.Numeric(10, 2), nullable=False),
            sa.Column('observaciones', sa.Text, nullable=True),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )


def downgrade():
    # Eliminar tabla transferencias_cisterna
    if table_exists('transferencias_cisterna'):
        op.drop_table('transferencias_cisterna')

    # Eliminar columna cisterna_origen_id
    if column_exists('cisterna_combustible', 'cisterna_origen_id'):
        op.drop_column('cisterna_combustible', 'cisterna_origen_id')
