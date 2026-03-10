from sqlalchemy import Column, String, DateTime, Numeric, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CisternaCombustible(BaseModel):
    """Modelo de Cisterna de Combustible"""

    __tablename__ = "cisterna_combustible"

    nombre = Column(String(100), nullable=False, default="Cisterna Principal")
    capacidad_total = Column(Numeric(10, 2), nullable=False)  # litros
    nivel_actual = Column(Numeric(10, 2), nullable=False, default=0)  # litros
    nivel_minimo = Column(Numeric(10, 2), default=1000)  # litros para alertar (antes nivel_alerta)

    # Cisterna de origen (para cisternas que se abastecen de otra)
    cisterna_origen_id = Column(UUID(as_uuid=True), ForeignKey("cisterna_combustible.id"), nullable=True)

    # Relaciones
    cargas = relationship("CargaCisterna", back_populates="cisterna")
    suministros = relationship("SuministroCombustible", back_populates="cisterna")
    cisterna_origen = relationship("CisternaCombustible", remote_side="CisternaCombustible.id", foreign_keys=[cisterna_origen_id])
    transferencias_salida = relationship("TransferenciaCisterna", back_populates="cisterna_origen", foreign_keys="TransferenciaCisterna.cisterna_origen_id")
    transferencias_entrada = relationship("TransferenciaCisterna", back_populates="cisterna_destino", foreign_keys="TransferenciaCisterna.cisterna_destino_id")

    def __repr__(self):
        return f"<Cisterna {self.nombre}: {self.nivel_actual}/{self.capacidad_total}L>"


class CargaCisterna(BaseModel):
    """Modelo de Carga de Cisterna"""

    __tablename__ = "cargas_cisterna"

    cisterna_id = Column(UUID(as_uuid=True), ForeignKey("cisterna_combustible.id"), nullable=True)
    fecha = Column(DateTime, nullable=False)
    litros = Column(Numeric(10, 2), nullable=False)
    proveedor = Column(String(255))
    costo_total = Column(Numeric(10, 2))
    costo_por_litro = Column(Numeric(6, 2))  # Calculado
    numero_factura = Column(String(100))
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    cisterna = relationship("CisternaCombustible", back_populates="cargas")
    creador = relationship("Usuario", back_populates="cargas_cisterna", foreign_keys=[created_by])

    def __repr__(self):
        return f"<CargaCisterna {self.litros}L - {self.fecha}>"


class SuministroCombustible(BaseModel):
    """Modelo de Suministro de Combustible a Camiones"""

    __tablename__ = "suministros_combustible"

    cisterna_id = Column(UUID(as_uuid=True), ForeignKey("cisterna_combustible.id"), nullable=True)
    fecha = Column(DateTime, nullable=False)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)
    litros = Column(Numeric(10, 2), nullable=False)
    chofer = Column(String(100))
    kilometraje = Column(Integer)
    horometro = Column(Numeric(10, 2))
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    cisterna = relationship("CisternaCombustible", back_populates="suministros")
    camion = relationship("Camion", back_populates="suministros_combustible")
    creador = relationship("Usuario", back_populates="suministros", foreign_keys=[created_by])

    def __repr__(self):
        return f"<SuministroCombustible {self.litros}L - Camión {self.camion_id}>"


class TransferenciaCisterna(BaseModel):
    """Modelo de Transferencia entre Cisternas"""

    __tablename__ = "transferencias_cisterna"

    cisterna_origen_id = Column(UUID(as_uuid=True), ForeignKey("cisterna_combustible.id"), nullable=False)
    cisterna_destino_id = Column(UUID(as_uuid=True), ForeignKey("cisterna_combustible.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    litros = Column(Numeric(10, 2), nullable=False)
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    cisterna_origen = relationship("CisternaCombustible", back_populates="transferencias_salida", foreign_keys=[cisterna_origen_id])
    cisterna_destino = relationship("CisternaCombustible", back_populates="transferencias_entrada", foreign_keys=[cisterna_destino_id])
    creador = relationship("Usuario", back_populates="transferencias_cisterna", foreign_keys=[created_by])
