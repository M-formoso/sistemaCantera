from sqlalchemy import Column, String, Numeric, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoMovimientoEnum(str, enum.Enum):
    """Tipos de movimiento de stock"""
    INGRESO = "ingreso"
    EGRESO = "egreso"


class MovimientoStock(BaseModel):
    """Modelo de Movimiento de Stock"""

    __tablename__ = "movimientos_stock"

    repuesto_id = Column(UUID(as_uuid=True), ForeignKey("repuestos.id"), nullable=False, index=True)
    tipo = Column(SQLEnum(TipoMovimientoEnum), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    referencia_tipo = Column(String(50))  # 'servicio', 'compra', 'ajuste'
    referencia_id = Column(UUID(as_uuid=True), nullable=True)  # ID del servicio, compra, etc
    observaciones = Column(Text)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    repuesto = relationship("Repuesto", back_populates="movimientos")
    usuario = relationship("Usuario", back_populates="movimientos_stock")

    def __repr__(self):
        return f"<MovimientoStock {self.tipo} - {self.repuesto_id}>"
