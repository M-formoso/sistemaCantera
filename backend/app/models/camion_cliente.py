"""
Modelo para Camiones/Patentes asociados a Clientes
"""
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CamionCliente(BaseModel):
    """
    Modelo de Camión asociado a un Cliente.
    Permite que cada cliente tenga sus propias patentes registradas.
    """

    __tablename__ = "camiones_clientes"

    # Cliente al que pertenece
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)

    # Datos del camión
    patente = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(100))  # Ej: "Camión blanco", "Mercedes Benz", etc.
    chofer_habitual = Column(String(100))  # Nombre del chofer habitual

    # Estado
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    cliente = relationship("Empresa", backref="camiones")

    def __repr__(self):
        return f"<CamionCliente {self.patente} - Cliente {self.cliente_id}>"
