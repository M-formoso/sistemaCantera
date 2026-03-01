"""Add estado and fecha_completado to pesajes for double weighing flow

Revision ID: add_doble_pesaje
Revises: add_permisos_usuario
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_doble_pesaje'
down_revision = 'add_permisos_usuario'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar campo estado a pesajes
    op.add_column('pesajes', sa.Column('estado', sa.String(20), nullable=True))

    # Agregar campo fecha_completado a pesajes
    op.add_column('pesajes', sa.Column('fecha_completado', sa.DateTime(), nullable=True))

    # Actualizar pesajes existentes a estado 'completado'
    op.execute("UPDATE pesajes SET estado = 'completado' WHERE estado IS NULL")

    # Hacer el campo estado NOT NULL después de actualizar
    op.alter_column('pesajes', 'estado', nullable=False, server_default='completado')

    # Crear índice en estado para búsquedas rápidas
    op.create_index('ix_pesajes_estado', 'pesajes', ['estado'])

    # Modificar peso_bruto y peso_tara para permitir NULL (para pesajes pendientes)
    op.alter_column('pesajes', 'peso_bruto', nullable=True)
    op.alter_column('pesajes', 'peso_tara', nullable=True)
    op.alter_column('pesajes', 'peso_neto', nullable=True)


def downgrade() -> None:
    # Eliminar índice
    op.drop_index('ix_pesajes_estado', table_name='pesajes')

    # Eliminar columnas
    op.drop_column('pesajes', 'fecha_completado')
    op.drop_column('pesajes', 'estado')

    # Revertir nullable en pesos
    op.alter_column('pesajes', 'peso_bruto', nullable=False)
    op.alter_column('pesajes', 'peso_tara', nullable=False)
