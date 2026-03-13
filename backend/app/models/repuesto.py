from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.models.base import BaseModel, Base


# Tabla intermedia para relación N:N entre Repuestos y Equipos (Camiones/Máquinas)
# No hereda de BaseModel porque la tabla solo tiene id y created_at (sin updated_at)
class RepuestoEquipo(Base):
    """Tabla de asociación entre Repuestos y Equipos (relación muchos a muchos)"""

    __tablename__ = "repuestos_equipos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    repuesto_id = Column(UUID(as_uuid=True), ForeignKey("repuestos.id", ondelete="CASCADE"), nullable=False, index=True)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    # Relaciones
    repuesto = relationship("Repuesto", back_populates="equipos_asignados")
    camion = relationship("Camion", back_populates="repuestos_compatibles")

    def __repr__(self):
        return f"<RepuestoEquipo {self.repuesto_id} - {self.camion_id}>"


class Repuesto(BaseModel):
    """Modelo de Repuesto"""

    __tablename__ = "repuestos"

    codigo = Column(String(50), unique=True, index=True)
    nombre = Column(String(255), nullable=False)
    categoria = Column(String(100))
    stock_actual = Column(Numeric(10, 2), nullable=False, default=0)
    stock_minimo = Column(Numeric(10, 2), default=0)
    unidad = Column(String(20), default="unidades")  # unidades, litros, kg, etc
    precio_unitario = Column(Numeric(10, 2))
    proveedor = Column(String(255))
    ubicacion_deposito = Column(String(100))
    activo = Column(Boolean, default=True, nullable=False)

    # Asignación a equipo específico (opcional) - LEGACY, se mantiene por compatibilidad
    # Usar la relación equipos_asignados para la nueva funcionalidad N:N
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=True, index=True)

    # Relaciones
    servicios_repuestos = relationship("ServicioRepuesto", back_populates="repuesto")
    movimientos = relationship("MovimientoStock", back_populates="repuesto")
    camion = relationship("Camion", backref="repuestos_asignados", foreign_keys=[camion_id])

    # Nueva relación N:N con equipos
    equipos_asignados = relationship("RepuestoEquipo", back_populates="repuesto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repuesto {self.nombre} ({self.codigo})>"
