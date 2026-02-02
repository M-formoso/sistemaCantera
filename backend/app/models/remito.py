from sqlalchemy import Column, String, Date, Numeric, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Remito(BaseModel):
    """Modelo de Remito"""

    __tablename__ = "remitos"

    numero_remito = Column(Integer, unique=True, nullable=False, index=True)
    pesaje_id = Column(UUID(as_uuid=True), ForeignKey("pesajes.id"), nullable=True)
    fecha = Column(Date, nullable=False)
    cliente = Column(String(255), nullable=False)
    producto = Column(String(100), nullable=False)
    peso_neto = Column(Numeric(10, 2), nullable=False)
    camion_patente = Column(String(20))
    chofer = Column(String(100))
    observaciones = Column(Text)
    pdf_url = Column(String(500))
    enviado_email = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    pesaje = relationship("Pesaje", back_populates="remito")
    creador = relationship("Usuario", back_populates="remitos_creados", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Remito #{self.numero_remito} - {self.cliente}>"
