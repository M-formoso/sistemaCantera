"""Add permisos por modulo a usuarios

Revision ID: add_permisos_usuario
Revises: add_ordenes_entrega
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_permisos_usuario'
down_revision = 'add_ordenes_entrega'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columnas de permisos por módulo
    op.add_column('usuarios', sa.Column('permiso_dashboard', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_camiones', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_empresas', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_repuestos', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_pesajes', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_combustible', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_finanzas', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('usuarios', sa.Column('permiso_usuarios', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('usuarios', sa.Column('permiso_reportes', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('usuarios', 'permiso_reportes')
    op.drop_column('usuarios', 'permiso_usuarios')
    op.drop_column('usuarios', 'permiso_finanzas')
    op.drop_column('usuarios', 'permiso_combustible')
    op.drop_column('usuarios', 'permiso_pesajes')
    op.drop_column('usuarios', 'permiso_repuestos')
    op.drop_column('usuarios', 'permiso_empresas')
    op.drop_column('usuarios', 'permiso_camiones')
    op.drop_column('usuarios', 'permiso_dashboard')
