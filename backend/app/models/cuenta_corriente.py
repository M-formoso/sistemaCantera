"""
Modelos para Cuenta Corriente de Clientes
"""
from sqlalchemy import Column, String, Numeric, Text, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoMovimientoCCEnum(str, enum.Enum):
    """Tipo de movimiento en cuenta corriente"""
    CARGO = "cargo"  # Deuda (pesaje, servicio, etc.)
    PAGO = "pago"    # Pago del cliente
    AJUSTE = "ajuste"  # Ajuste manual (nota de crédito/débito)


class MovimientoCuentaCorriente(BaseModel):
    """Movimientos de cuenta corriente de clientes"""

    __tablename__ = "movimientos_cuenta_corriente"

    # Cliente
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)

    # Tipo de movimiento
    tipo = Column(String(20), nullable=False)  # cargo, pago, ajuste

    # Montos
    monto = Column(Numeric(12, 2), nullable=False)
    saldo_anterior = Column(Numeric(12, 2), nullable=False, default=0)
    saldo_posterior = Column(Numeric(12, 2), nullable=False)

    # Datos del movimiento
    fecha = Column(Date, nullable=False, index=True)
    descripcion = Column(String(500), nullable=False)
    detalle = Column(Text)

    # Referencias opcionales
    pesaje_id = Column(UUID(as_uuid=True), ForeignKey("pesajes.id"), nullable=True)
    movimiento_financiero_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_financieros.id"), nullable=True)

    # Comprobante de pago
    numero_comprobante = Column(String(100))
    tipo_comprobante = Column(String(50))  # recibo, transferencia, cheque
    comprobante_url = Column(String(500))

    # Método de pago (solo para pagos)
    metodo_pago = Column(String(50))  # efectivo, transferencia, cheque
    referencia_pago = Column(String(100))
    banco = Column(String(100))

    # Estado
    anulado = Column(Boolean, default=False, nullable=False)
    motivo_anulacion = Column(Text)

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Relaciones
    empresa = relationship("Empresa")
    pesaje = relationship("Pesaje")
    movimiento_financiero = relationship("MovimientoFinanciero")
    creador = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoCC {self.tipo} ${self.monto} - {self.empresa_id}>"
