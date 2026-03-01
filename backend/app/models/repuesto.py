from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


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

    # Asignación a equipo específico (opcional)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=True, index=True)

    # Relaciones
    servicios_repuestos = relationship("ServicioRepuesto", back_populates="repuesto")
    movimientos = relationship("MovimientoStock", back_populates="repuesto")
    camion = relationship("Camion", backref="repuestos_asignados")

    def __repr__(self):
        return f"<Repuesto {self.nombre} ({self.codigo})>"
