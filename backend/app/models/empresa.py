from sqlalchemy import Column, String, Boolean, Enum, Numeric
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
    activo = Column(Boolean, default=True, nullable=False)

    # Cuenta corriente
    saldo_cuenta_corriente = Column(Numeric(12, 2), default=0, nullable=False)

    # Relaciones
    movimientos_cuenta_corriente = relationship("MovimientoCuentaCorriente", back_populates="empresa")
    facturas = relationship("Factura", back_populates="empresa")

    def __repr__(self):
        return f"<Empresa {self.nombre} ({self.tipo})>"
