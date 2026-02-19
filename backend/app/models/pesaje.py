from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Pesaje(BaseModel):
    """Modelo de Pesaje"""

    __tablename__ = "pesajes"

    numero_pesaje = Column(Integer, unique=True, nullable=False, index=True)
    fecha = Column(DateTime, nullable=False)

    # Tipo de entrega: 'propio' (camión de la cantera) o 'transportista' (externo)
    tipo_entrega = Column(String(20), default="propio")

    # Camión propio (opcional si es transportista externo)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=True, index=True)

    # Transportista externo (cuando no es camión propio)
    transportista_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)
    patente_externa = Column(String(20))  # Patente del camión externo

    # Cliente destino
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)
    cliente_nombre = Column(String(255))  # Nombre del cliente (texto libre/legacy)

    # Datos del transporte
    acoplado = Column(String(20))  # Patente del acoplado
    transportista = Column(String(100))  # Nombre del transportista (legacy/texto libre)
    chofer = Column(String(100))

    # Pesos
    peso_tara = Column(Numeric(10, 2), nullable=False)  # kg
    peso_bruto = Column(Numeric(10, 2), nullable=False)  # kg
    peso_neto = Column(Numeric(10, 2))  # Calculado: bruto - tara

    # Material
    material = Column(String(100))

    # Operación
    operario = Column(String(100))  # Nombre del operario

    observaciones = Column(Text)
    remito_generado = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="pesajes")
    transportista_empresa = relationship("Empresa", foreign_keys=[transportista_id])
    cliente = relationship("Empresa", foreign_keys=[cliente_id])
    creador = relationship("Usuario", back_populates="pesajes_creados", foreign_keys=[created_by])
    remito = relationship("Remito", back_populates="pesaje", uselist=False)

    def __repr__(self):
        return f"<Pesaje #{self.numero_pesaje} - {self.material}>"
