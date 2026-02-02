from sqlalchemy import Column, String, Date, Numeric, Enum as SQLEnum, Text, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoServicioEnum(str, enum.Enum):
    """Tipos de servicio"""
    PREVENTIVO = "preventivo"
    CORRECTIVO = "correctivo"
    EMERGENCIA = "emergencia"


class EstadoServicioEnum(str, enum.Enum):
    """Estados de servicio"""
    PROGRAMADO = "programado"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"


class Servicio(BaseModel):
    """Modelo de Servicio/Mantenimiento"""

    __tablename__ = "servicios"

    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    tipo = Column(SQLEnum(TipoServicioEnum), nullable=False)
    descripcion = Column(Text, nullable=False)
    kilometraje_servicio = Column(Integer)
    horometro_servicio = Column(Numeric(10, 2))
    mecanico = Column(String(255))
    costo_mano_obra = Column(Numeric(10, 2), default=0)
    costo_total = Column(Numeric(10, 2), default=0)  # Calculado: mano_obra + repuestos
    estado = Column(SQLEnum(EstadoServicioEnum), default=EstadoServicioEnum.PROGRAMADO, nullable=False)
    observaciones = Column(Text)
    documentos = Column(JSON)  # URLs de fotos/documentos
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="servicios")
    creador = relationship("Usuario", back_populates="servicios_creados", foreign_keys=[created_by])
    servicios_repuestos = relationship("ServicioRepuesto", back_populates="servicio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Servicio {self.tipo} - Camión {self.camion_id}>"


class ServicioRepuesto(BaseModel):
    """Tabla de asociación entre Servicios y Repuestos"""

    __tablename__ = "servicios_repuestos"

    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False, index=True)
    repuesto_id = Column(UUID(as_uuid=True), ForeignKey("repuestos.id"), nullable=False, index=True)
    cantidad = Column(Numeric(10, 2), nullable=False)
    precio_unitario = Column(Numeric(10, 2))
    subtotal = Column(Numeric(10, 2))  # Calculado: cantidad * precio_unitario

    # Relaciones
    servicio = relationship("Servicio", back_populates="servicios_repuestos")
    repuesto = relationship("Repuesto", back_populates="servicios_repuestos")

    def __repr__(self):
        return f"<ServicioRepuesto {self.servicio_id} - {self.repuesto_id}>"
