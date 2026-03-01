"""
Modelo de Trabajo/Reparación para equipos
Registro simple de arreglos sin alertas ni programación
"""
from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Trabajo(BaseModel):
    """Registro de trabajos/reparaciones realizados a equipos"""

    __tablename__ = "trabajos"

    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    responsable = Column(String(100))  # Quien hizo el trabajo
    costo_mano_obra = Column(Numeric(12, 2), default=0)
    costo_total = Column(Numeric(12, 2), default=0)
    observaciones = Column(Text)

    # Usuario que registró
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    camion = relationship("Camion", backref="trabajos")
    usuario = relationship("Usuario", foreign_keys=[created_by])
    repuestos_utilizados = relationship("TrabajoRepuesto", back_populates="trabajo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trabajo {self.id} - {self.descripcion[:30]}>"


class TrabajoRepuesto(BaseModel):
    """Repuestos utilizados en un trabajo"""

    __tablename__ = "trabajos_repuestos"

    trabajo_id = Column(UUID(as_uuid=True), ForeignKey("trabajos.id", ondelete="CASCADE"), nullable=False)
    repuesto_id = Column(UUID(as_uuid=True), ForeignKey("repuestos.id"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False, default=1)
    precio_unitario = Column(Numeric(12, 2))  # Precio al momento del trabajo
    subtotal = Column(Numeric(12, 2))

    # Relaciones
    trabajo = relationship("Trabajo", back_populates="repuestos_utilizados")
    repuesto = relationship("Repuesto")

    def __repr__(self):
        return f"<TrabajoRepuesto {self.trabajo_id} - {self.repuesto_id}>"
