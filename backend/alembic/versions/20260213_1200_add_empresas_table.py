"""add_empresas_table_and_pesaje_fields

Revision ID: add_empresas_01
Revises: 14d1e2b3fbaf
Create Date: 2026-02-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_empresas_01'
down_revision = '14d1e2b3fbaf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear tabla empresas
    op.create_table('empresas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('tipo', sa.Enum('cliente', 'transportista', name='tipoempresaenum'), nullable=False),
        sa.Column('cuit', sa.String(length=20), nullable=True),
        sa.Column('direccion', sa.String(length=255), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('contacto', sa.String(length=100), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_empresas_nombre'), 'empresas', ['nombre'], unique=False)
    op.create_index(op.f('ix_empresas_tipo'), 'empresas', ['tipo'], unique=False)

    # Agregar campos nuevos a pesajes
    op.add_column('pesajes', sa.Column('tipo_entrega', sa.String(length=20), nullable=True, server_default='propio'))
    op.add_column('pesajes', sa.Column('transportista_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('pesajes', sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('pesajes', sa.Column('cliente_nombre', sa.String(length=255), nullable=True))
    op.add_column('pesajes', sa.Column('patente_externa', sa.String(length=20), nullable=True))

    # Crear foreign keys
    op.create_foreign_key('fk_pesajes_transportista_id', 'pesajes', 'empresas', ['transportista_id'], ['id'])
    op.create_foreign_key('fk_pesajes_cliente_id', 'pesajes', 'empresas', ['cliente_id'], ['id'])

    # Hacer camion_id nullable (ya que ahora puede ser transportista externo)
    op.alter_column('pesajes', 'camion_id',
                    existing_type=postgresql.UUID(),
                    nullable=True)


def downgrade() -> None:
    # Revertir camion_id a not nullable
    op.alter_column('pesajes', 'camion_id',
                    existing_type=postgresql.UUID(),
                    nullable=False)

    # Eliminar foreign keys
    op.drop_constraint('fk_pesajes_cliente_id', 'pesajes', type_='foreignkey')
    op.drop_constraint('fk_pesajes_transportista_id', 'pesajes', type_='foreignkey')

    # Eliminar columnas de pesajes
    op.drop_column('pesajes', 'patente_externa')
    op.drop_column('pesajes', 'cliente_nombre')
    op.drop_column('pesajes', 'cliente_id')
    op.drop_column('pesajes', 'transportista_id')
    op.drop_column('pesajes', 'tipo_entrega')

    # Eliminar tabla empresas
    op.drop_index(op.f('ix_empresas_tipo'), table_name='empresas')
    op.drop_index(op.f('ix_empresas_nombre'), table_name='empresas')
    op.drop_table('empresas')

    # Eliminar enum
    op.execute('DROP TYPE IF EXISTS tipoempresaenum')
