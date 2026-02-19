"""
Modelos para el módulo de Finanzas
"""
from sqlalchemy import Column, String, Integer, Boolean, Numeric, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoMovimientoEnum(str, enum.Enum):
    """Tipo de movimiento financiero"""
    INGRESO = "ingreso"
    EGRESO = "egreso"


class CategoriaFinanzas(BaseModel):
    """Categorías para movimientos financieros"""

    __tablename__ = "categorias_finanzas"

    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False)  # ingreso o egreso
    descripcion = Column(Text)
    color = Column(String(20), default="#6B7280")  # Color para UI
    icono = Column(String(50))  # Nombre del icono
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    movimientos = relationship("MovimientoFinanciero", back_populates="categoria")

    def __repr__(self):
        return f"<CategoriaFinanzas {self.nombre}>"


class MovimientoFinanciero(BaseModel):
    """Movimientos financieros (ingresos y egresos)"""

    __tablename__ = "movimientos_financieros"

    # Tipo y categoría
    tipo = Column(String(20), nullable=False)  # ingreso o egreso
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_finanzas.id"), nullable=True)

    # Datos del movimiento
    fecha = Column(Date, nullable=False, index=True)
    monto = Column(Numeric(12, 2), nullable=False)
    descripcion = Column(String(500), nullable=False)
    detalle = Column(Text)

    # Referencias opcionales
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)  # Cliente o proveedor

    # Comprobante
    numero_comprobante = Column(String(100))
    tipo_comprobante = Column(String(50))  # factura, recibo, ticket, etc.
    comprobante_url = Column(String(500))  # URL del archivo adjunto

    # Pago
    metodo_pago = Column(String(50))  # efectivo, transferencia, cheque, tarjeta
    referencia_pago = Column(String(100))  # número de transferencia, cheque, etc.
    banco = Column(String(100))
    estado = Column(String(20), default="completado")  # completado, pendiente, anulado

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Relaciones
    categoria = relationship("CategoriaFinanzas", back_populates="movimientos")
    camion = relationship("Camion")
    empresa = relationship("Empresa")
    creador = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoFinanciero {self.tipo} ${self.monto}>"


class CuentaBancaria(BaseModel):
    """Cuentas bancarias de la empresa"""

    __tablename__ = "cuentas_bancarias"

    nombre = Column(String(100), nullable=False)
    banco = Column(String(100), nullable=False)
    tipo_cuenta = Column(String(50))  # corriente, ahorro, etc.
    numero_cuenta = Column(String(50))
    cbu = Column(String(30))
    alias = Column(String(50))
    titular = Column(String(200))
    cuit_titular = Column(String(20))
    saldo_inicial = Column(Numeric(12, 2), default=0)
    saldo_actual = Column(Numeric(12, 2), default=0)
    moneda = Column(String(10), default="ARS")
    activo = Column(Boolean, default=True, nullable=False)
    notas = Column(Text)

    def __repr__(self):
        return f"<CuentaBancaria {self.banco} - {self.nombre}>"
