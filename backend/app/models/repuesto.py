from sqlalchemy import Column, String, Numeric, Boolean
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

    # Relaciones
    servicios_repuestos = relationship("ServicioRepuesto", back_populates="repuesto")
    movimientos = relationship("MovimientoStock", back_populates="repuesto")

    def __repr__(self):
        return f"<Repuesto {self.nombre} ({self.codigo})>"
