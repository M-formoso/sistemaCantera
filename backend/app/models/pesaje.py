from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Pesaje(BaseModel):
    """Modelo de Pesaje"""

    __tablename__ = "pesajes"

    numero_pesaje = Column(Integer, unique=True, nullable=False, index=True)
    fecha = Column(DateTime, nullable=False)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)

    # Datos del transporte
    acoplado = Column(String(20))  # Patente del acoplado
    transportista = Column(String(100))  # Nombre del transportista
    remitente = Column(String(100), default="LA RUFINA")  # Empresa remitente
    chofer = Column(String(100))

    # Datos del producto
    producto = Column(String(100))  # Código o nombre del producto
    numero_guia = Column(String(50))  # Número de guía

    # Pesos
    peso_tara = Column(Numeric(10, 2), nullable=False)  # kg
    peso_bruto = Column(Numeric(10, 2), nullable=False)  # kg
    peso_neto = Column(Numeric(10, 2))  # Calculado: bruto - tara

    # Destino
    material = Column(String(100))
    cliente_destino = Column(String(255))  # Destinatario

    # Operación
    operario = Column(String(100))  # Nombre del operario

    observaciones = Column(Text)
    remito_generado = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="pesajes")
    creador = relationship("Usuario", back_populates="pesajes_creados", foreign_keys=[created_by])
    remito = relationship("Remito", back_populates="pesaje", uselist=False)

    def __repr__(self):
        return f"<Pesaje #{self.numero_pesaje} - {self.material}>"
