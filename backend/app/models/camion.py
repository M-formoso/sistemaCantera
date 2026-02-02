from sqlalchemy import Column, String, Integer, Boolean, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoCamionEnum(str, enum.Enum):
    """Tipos de camión"""
    VOLCADOR = "volcador"
    ACOPLADO = "acoplado"
    MIXER = "mixer"
    OTRO = "otro"


class EstadoCamionEnum(str, enum.Enum):
    """Estados de camión"""
    OPERATIVO = "operativo"
    EN_SERVICIO = "en_servicio"
    FUERA_SERVICIO = "fuera_servicio"


class Camion(BaseModel):
    """Modelo de Camión"""

    __tablename__ = "camiones"

    patente = Column(String(20), unique=True, nullable=False, index=True)
    marca = Column(String(100))
    modelo = Column(String(100))
    año = Column(Integer)
    tipo = Column(SQLEnum(TipoCamionEnum), default=TipoCamionEnum.VOLCADOR)
    estado = Column(SQLEnum(EstadoCamionEnum), default=EstadoCamionEnum.OPERATIVO, nullable=False)
    kilometraje_actual = Column(Integer, default=0)
    horometro_actual = Column(Numeric(10, 2), default=0)
    chofer_habitual = Column(String(100))
    foto = Column(String(500))  # URL de Cloudinary
    observaciones = Column(Text)
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    servicios = relationship("Servicio", back_populates="camion")
    pesajes = relationship("Pesaje", back_populates="camion")
    suministros_combustible = relationship("SuministroCombustible", back_populates="camion")

    def __repr__(self):
        return f"<Camion {self.patente}>"
