from sqlalchemy import Column, String, DateTime, Numeric, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CisternaCombustible(BaseModel):
    """Modelo de Cisterna de Combustible"""

    __tablename__ = "cisterna_combustible"

    capacidad_total = Column(Numeric(10, 2), nullable=False)  # litros
    nivel_actual = Column(Numeric(10, 2), nullable=False, default=0)  # litros
    nivel_alerta = Column(Numeric(10, 2), default=1000)  # litros para alertar

    def __repr__(self):
        return f"<Cisterna {self.nivel_actual}/{self.capacidad_total}L>"


class CargaCisterna(BaseModel):
    """Modelo de Carga de Cisterna"""

    __tablename__ = "cargas_cisterna"

    fecha = Column(DateTime, nullable=False)
    litros = Column(Numeric(10, 2), nullable=False)
    proveedor = Column(String(255))
    costo_total = Column(Numeric(10, 2))
    costo_por_litro = Column(Numeric(6, 2))  # Calculado
    numero_factura = Column(String(100))
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    creador = relationship("Usuario", back_populates="cargas_cisterna", foreign_keys=[created_by])

    def __repr__(self):
        return f"<CargaCisterna {self.litros}L - {self.fecha}>"


class SuministroCombustible(BaseModel):
    """Modelo de Suministro de Combustible a Camiones"""

    __tablename__ = "suministros_combustible"

    fecha = Column(DateTime, nullable=False)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)
    litros = Column(Numeric(10, 2), nullable=False)
    chofer = Column(String(100))
    kilometraje = Column(Integer)
    horometro = Column(Numeric(10, 2))
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="suministros_combustible")
    creador = relationship("Usuario", back_populates="suministros", foreign_keys=[created_by])

    def __repr__(self):
        return f"<SuministroCombustible {self.litros}L - Camión {self.camion_id}>"
