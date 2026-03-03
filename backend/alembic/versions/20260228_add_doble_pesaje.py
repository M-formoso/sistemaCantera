"""Add estado and fecha_completado to pesajes for double weighing flow

Revision ID: add_doble_pesaje
Revises: add_permisos_usuario
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_doble_pesaje'
down_revision = 'add_permisos_usuario'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name):
    """Verifica si un índice existe"""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes('pesajes')
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    # Agregar campo estado a pesajes (si no existe)
    if not column_exists('pesajes', 'estado'):
        op.add_column('pesajes', sa.Column('estado', sa.String(20), nullable=True))

    # Agregar campo fecha_completado a pesajes (si no existe)
    if not column_exists('pesajes', 'fecha_completado'):
        op.add_column('pesajes', sa.Column('fecha_completado', sa.DateTime(), nullable=True))

    # Actualizar pesajes existentes a estado 'completado'
    op.execute("UPDATE pesajes SET estado = 'completado' WHERE estado IS NULL")

    # Hacer el campo estado NOT NULL después de actualizar
    try:
        op.alter_column('pesajes', 'estado', nullable=False, server_default='completado')
    except Exception:
        pass  # Ya puede tener la constraint

    # Crear índice en estado para búsquedas rápidas (si no existe)
    if not index_exists('ix_pesajes_estado'):
        op.create_index('ix_pesajes_estado', 'pesajes', ['estado'])

    # Modificar peso_bruto y peso_tara para permitir NULL (para pesajes pendientes)
    try:
        op.alter_column('pesajes', 'peso_bruto', nullable=True)
    except Exception:
        pass
    try:
        op.alter_column('pesajes', 'peso_tara', nullable=True)
    except Exception:
        pass
    try:
        op.alter_column('pesajes', 'peso_neto', nullable=True)
    except Exception:
        pass


def downgrade() -> None:
    # Eliminar índice
    if index_exists('ix_pesajes_estado'):
        op.drop_index('ix_pesajes_estado', table_name='pesajes')

    # Eliminar columnas
    if column_exists('pesajes', 'fecha_completado'):
        op.drop_column('pesajes', 'fecha_completado')
    if column_exists('pesajes', 'estado'):
        op.drop_column('pesajes', 'estado')

    # Revertir nullable en pesos
    try:
        op.alter_column('pesajes', 'peso_bruto', nullable=False)
        op.alter_column('pesajes', 'peso_tara', nullable=False)
    except Exception:
        pass
