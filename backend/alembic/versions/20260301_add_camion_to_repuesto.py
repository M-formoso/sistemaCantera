"""Add camion_id to repuestos for equipment assignment

Revision ID: add_camion_to_repuesto
Revises: add_camiones_clientes
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_camion_to_repuesto'
down_revision = 'add_camiones_clientes'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Verifica si una columna existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name, index_name):
    """Verifica si un índice existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def fk_exists(table_name, fk_name):
    """Verifica si una FK existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    fks = inspector.get_foreign_keys(table_name)
    return any(fk['name'] == fk_name for fk in fks)


def upgrade() -> None:
    # Agregar columna camion_id a repuestos (si no existe)
    if not column_exists('repuestos', 'camion_id'):
        op.add_column(
            'repuestos',
            sa.Column('camion_id', postgresql.UUID(as_uuid=True), nullable=True)
        )

    # Crear FK (si no existe)
    if not fk_exists('repuestos', 'fk_repuestos_camion_id'):
        try:
            op.create_foreign_key(
                'fk_repuestos_camion_id',
                'repuestos',
                'camiones',
                ['camion_id'],
                ['id']
            )
        except Exception:
            pass

    # Crear índice (si no existe)
    if not index_exists('repuestos', 'ix_repuestos_camion_id'):
        op.create_index('ix_repuestos_camion_id', 'repuestos', ['camion_id'])


def downgrade() -> None:
    # Eliminar índice
    if index_exists('repuestos', 'ix_repuestos_camion_id'):
        op.drop_index('ix_repuestos_camion_id', table_name='repuestos')

    # Eliminar FK
    if fk_exists('repuestos', 'fk_repuestos_camion_id'):
        op.drop_constraint('fk_repuestos_camion_id', 'repuestos', type_='foreignkey')

    # Eliminar columna
    if column_exists('repuestos', 'camion_id'):
        op.drop_column('repuestos', 'camion_id')
