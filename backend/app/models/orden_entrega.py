"""
Modelo de Orden de Entrega
"""
from sqlalchemy import Column, String, Date, Numeric, Integer, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class EstadoOrdenEntrega(str, enum.Enum):
    """Estados posibles de una orden de entrega"""
    pendiente = "pendiente"
    en_proceso = "en_proceso"
    completada = "completada"
    cancelada = "cancelada"


class OrdenEntrega(BaseModel):
    """
    Modelo de Orden de Entrega

    Representa una orden de entrega programada (ej: 6 cargas de 0-20 para el lunes)
    Los pesajes/remitos se asocian a esta orden y se descuentan del total.
    """
    __tablename__ = "ordenes_entrega"

    # Número de orden (autoincremental)
    numero_orden = Column(Integer, unique=True, nullable=False, index=True)

    # Fecha programada de entrega
    fecha_entrega = Column(Date, nullable=False, index=True)

    # Cliente
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)
    cliente_nombre = Column(String(255))  # Texto libre si no hay cliente registrado

    # Material a entregar
    material = Column(String(100), nullable=False)

    # Cantidad de cargas/viajes solicitados
    cantidad_cargas = Column(Integer, nullable=False)
    cargas_entregadas = Column(Integer, default=0, nullable=False)

    # Peso estimado por carga (opcional)
    peso_estimado_carga = Column(Numeric(10, 2))  # kg

    # Totales de peso
    peso_total_estimado = Column(Numeric(12, 2))  # kg total estimado
    peso_total_entregado = Column(Numeric(12, 2), default=0)  # kg total real entregado

    # Estado
    estado = Column(
        String(20),
        default=EstadoOrdenEntrega.pendiente.value,
        nullable=False,
        index=True
    )

    # Solicitante (quien pidió la orden)
    solicitante = Column(String(100))  # Ej: "Martín", "Vero"

    # Contacto del cliente
    contacto_cliente = Column(String(100))
    telefono_contacto = Column(String(50))

    # Dirección de entrega
    direccion_entrega = Column(Text)

    # Observaciones
    observaciones = Column(Text)

    # Usuario que creó la orden
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    cliente = relationship("Empresa", foreign_keys=[cliente_id])
    creador = relationship("Usuario", foreign_keys=[created_by])
    pesajes = relationship("Pesaje", back_populates="orden_entrega")

    @property
    def cargas_pendientes(self) -> int:
        """Retorna la cantidad de cargas pendientes"""
        return self.cantidad_cargas - self.cargas_entregadas

    @property
    def porcentaje_completado(self) -> float:
        """Retorna el porcentaje de completado"""
        if self.cantidad_cargas == 0:
            return 0
        return (self.cargas_entregadas / self.cantidad_cargas) * 100

    def __repr__(self):
        return f"<OrdenEntrega #{self.numero_orden} - {self.material} ({self.cargas_entregadas}/{self.cantidad_cargas})>"
