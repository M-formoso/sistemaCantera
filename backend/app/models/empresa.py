from sqlalchemy import Column, String, Boolean, Enum, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoEmpresaEnum(str, enum.Enum):
    CLIENTE = "cliente"
    TRANSPORTISTA = "transportista"


class Empresa(BaseModel):
    """Modelo de Empresa (Cliente o Transportista)"""

    __tablename__ = "empresas"

    nombre = Column(String(200), nullable=False, index=True)
    tipo = Column(Enum('cliente', 'transportista', name='tipoempresaenum'), nullable=False, index=True)
    cuit = Column(String(20))
    direccion = Column(String(255))
    telefono = Column(String(50))
    email = Column(String(100))
    contacto = Column(String(100))  # Persona de contacto
    notas = Column(Text)  # Notas internas sobre el cliente
    activo = Column(Boolean, default=True, nullable=False)

    # Cuenta corriente
    saldo_cuenta_corriente = Column(Numeric(12, 2), default=0, nullable=False)

    # Alícuota de IVA por defecto del cliente (21%, 10.5%, etc.). Editable por movimiento.
    alicuota_iva = Column(Numeric(5, 2), default=21, nullable=False)
    # Si True, el IVA se suma al total y al saldo de cuenta corriente.
    # Si False, el IVA queda solo como dato informativo (saldo = neto).
    iva_en_total = Column(Boolean, default=False, nullable=False)

    # Lista de precios asignada
    lista_precio_id = Column(UUID(as_uuid=True), ForeignKey("listas_precios.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    movimientos_cuenta_corriente = relationship("MovimientoCuentaCorriente", back_populates="empresa")
    facturas = relationship("Factura", back_populates="empresa")
    lista_precio = relationship("ListaPrecio", foreign_keys=[lista_precio_id])

    def __repr__(self):
        return f"<Empresa {self.nombre} ({self.tipo})>"
