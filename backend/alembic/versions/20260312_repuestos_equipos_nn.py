"""Cambiar relación repuestos-equipos de 1:N a N:N (muchos a muchos)

Revision ID: 20260312_repuestos_nn
Revises: 20260312_cobros
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260312_repuestos_nn'
down_revision = '20260312_cobros'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verificar si la tabla ya existe
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'repuestos_equipos' not in existing_tables:
        # Crear tabla intermedia para relación N:N
        op.create_table(
            'repuestos_equipos',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('repuesto_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('camion_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['repuesto_id'], ['repuestos.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['camion_id'], ['camiones.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('repuesto_id', 'camion_id', name='uq_repuesto_equipo')
        )
        op.create_index('ix_repuestos_equipos_repuesto_id', 'repuestos_equipos', ['repuesto_id'])
        op.create_index('ix_repuestos_equipos_camion_id', 'repuestos_equipos', ['camion_id'])

    # Migrar datos existentes de la columna camion_id a la nueva tabla
    # Solo si hay repuestos con camion_id asignado
    conn.execute(sa.text("""
        INSERT INTO repuestos_equipos (repuesto_id, camion_id)
        SELECT id, camion_id FROM repuestos
        WHERE camion_id IS NOT NULL
        ON CONFLICT (repuesto_id, camion_id) DO NOTHING
    """))

    # NO eliminamos la columna camion_id por ahora para mantener compatibilidad
    # Se puede eliminar en una migración futura


def downgrade() -> None:
    op.drop_index('ix_repuestos_equipos_camion_id', table_name='repuestos_equipos')
    op.drop_index('ix_repuestos_equipos_repuesto_id', table_name='repuestos_equipos')
    op.drop_table('repuestos_equipos')
