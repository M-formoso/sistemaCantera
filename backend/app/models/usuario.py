from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class RolEnum(str, enum.Enum):
    """Roles de usuario"""
    ADMINISTRADOR = "administrador"
    OPERADOR = "operador"
    SOLO_LECTURA = "solo_lectura"


class Usuario(BaseModel):
    """Modelo de Usuario"""

    __tablename__ = "usuarios"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(SQLEnum(RolEnum), nullable=False, default=RolEnum.OPERADOR)
    activo = Column(Boolean, default=True, nullable=False)
    ultimo_acceso = Column(DateTime, nullable=True)

    # Relaciones
    servicios_creados = relationship("Servicio", back_populates="creador", foreign_keys="Servicio.created_by")
    pesajes_creados = relationship("Pesaje", back_populates="creador", foreign_keys="Pesaje.created_by")
    remitos_creados = relationship("Remito", back_populates="creador", foreign_keys="Remito.created_by")
    cargas_cisterna = relationship("CargaCisterna", back_populates="creador", foreign_keys="CargaCisterna.created_by")
    suministros = relationship("SuministroCombustible", back_populates="creador", foreign_keys="SuministroCombustible.created_by")
    movimientos_stock = relationship("MovimientoStock", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario {self.email}>"
