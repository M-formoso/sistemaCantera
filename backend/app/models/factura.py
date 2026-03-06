"""
Modelos para Facturación
"""
from sqlalchemy import Column, String, Numeric, Text, Date, ForeignKey, Boolean, Integer, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class TipoComprobanteEnum(str, enum.Enum):
    """Tipo de comprobante"""
    FACTURA_A = "factura_a"
    FACTURA_B = "factura_b"
    FACTURA_C = "factura_c"
    NOTA_CREDITO_A = "nota_credito_a"
    NOTA_CREDITO_B = "nota_credito_b"
    NOTA_CREDITO_C = "nota_credito_c"
    NOTA_DEBITO_A = "nota_debito_a"
    NOTA_DEBITO_B = "nota_debito_b"
    NOTA_DEBITO_C = "nota_debito_c"
    RECIBO = "recibo"


class EstadoFacturaEnum(str, enum.Enum):
    """Estado de la factura"""
    PENDIENTE = "pendiente"  # Sin pagar
    PARCIAL = "parcial"      # Parcialmente pagada
    PAGADA = "pagada"        # Totalmente pagada
    ANULADA = "anulada"


# Tabla intermedia para relación muchos a muchos entre Factura y Remito
factura_remito = Table(
    'factura_remito',
    BaseModel.metadata,
    Column('factura_id', UUID(as_uuid=True), ForeignKey('facturas.id', ondelete='CASCADE'), primary_key=True),
    Column('remito_id', UUID(as_uuid=True), ForeignKey('remitos.id', ondelete='CASCADE'), primary_key=True),
)


class Factura(BaseModel):
    """Modelo de Factura/Comprobante"""

    __tablename__ = "facturas"

    # Numeración
    numero_factura = Column(String(50), unique=True, nullable=False, index=True)
    punto_venta = Column(Integer, default=1)

    # Tipo de comprobante
    tipo_comprobante = Column(String(30), nullable=False)  # factura_a, nota_credito_b, etc.

    # Cliente
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)

    # Fechas
    fecha_emision = Column(Date, nullable=False, index=True)
    fecha_vencimiento = Column(Date, nullable=True)

    # Montos
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    descuento = Column(Numeric(12, 2), default=0)
    iva_21 = Column(Numeric(12, 2), default=0)
    iva_10_5 = Column(Numeric(12, 2), default=0)
    iva_27 = Column(Numeric(12, 2), default=0)
    percepciones_iibb = Column(Numeric(12, 2), default=0)
    percepciones_iva = Column(Numeric(12, 2), default=0)
    otros_impuestos = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)

    # Saldo pendiente (se actualiza con cada pago)
    saldo_pendiente = Column(Numeric(12, 2), nullable=False)

    # Estado
    estado = Column(String(20), default="pendiente", nullable=False, index=True)

    # CAE (para facturación electrónica, opcional)
    cae = Column(String(20))
    cae_vencimiento = Column(Date)

    # Referencia a comprobante original (para NC/ND)
    factura_original_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=True)

    # Observaciones
    observaciones = Column(Text)

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    anulada = Column(Boolean, default=False, nullable=False)
    motivo_anulacion = Column(Text)

    # Relaciones
    empresa = relationship("Empresa", back_populates="facturas")
    creador = relationship("Usuario")
    remitos = relationship("Remito", secondary=factura_remito, back_populates="facturas")
    factura_original = relationship("Factura", remote_side="Factura.id", backref="notas_credito_debito")
    pagos = relationship("PagoFactura", back_populates="factura")

    def __repr__(self):
        return f"<Factura {self.numero_factura} - {self.empresa_id}>"

    @property
    def esta_pagada(self):
        return self.saldo_pendiente <= 0

    @property
    def porcentaje_pagado(self):
        if self.total == 0:
            return 100
        return round(((self.total - self.saldo_pendiente) / self.total) * 100, 2)


class PagoFactura(BaseModel):
    """Pagos asociados a una factura"""

    __tablename__ = "pagos_factura"

    # Factura a la que se aplica
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=False, index=True)

    # Movimiento de cuenta corriente asociado
    movimiento_cc_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_cuenta_corriente.id"), nullable=True)

    # Datos del pago
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)

    # Forma de pago detallada
    forma_pago = Column(String(50), nullable=False)  # efectivo, cheque, e_cheque, transferencia, etc.

    # Datos específicos según forma de pago
    banco = Column(String(100))
    numero_cheque = Column(String(50))
    fecha_cheque = Column(Date)  # Fecha de cobro del cheque
    cuit_emisor = Column(String(20))  # CUIT del emisor del cheque

    # Retenciones (se registran como pagos negativos o con forma_pago específica)
    es_retencion = Column(Boolean, default=False)
    tipo_retencion = Column(String(50))  # iibb, ganancias, suss, etc.
    numero_certificado = Column(String(100))  # Número del certificado de retención

    # Referencia de pago
    referencia = Column(String(200))  # Número de transferencia, etc.

    observaciones = Column(Text)

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    anulado = Column(Boolean, default=False)

    # Relaciones
    factura = relationship("Factura", back_populates="pagos")
    movimiento_cc = relationship("MovimientoCuentaCorriente")
    creador = relationship("Usuario")

    def __repr__(self):
        return f"<PagoFactura {self.monto} - {self.forma_pago}>"


class PagoRemito(BaseModel):
    """Pagos directos a remitos (sin factura)"""

    __tablename__ = "pagos_remito"

    # Remito al que se aplica
    remito_id = Column(UUID(as_uuid=True), ForeignKey("remitos.id"), nullable=False, index=True)

    # Movimiento de cuenta corriente asociado
    movimiento_cc_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_cuenta_corriente.id"), nullable=True)

    # Datos del pago
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)

    # Forma de pago
    forma_pago = Column(String(50), nullable=False)
    banco = Column(String(100))
    numero_cheque = Column(String(50))
    fecha_cheque = Column(Date)
    cuit_emisor = Column(String(20))

    # Retenciones
    es_retencion = Column(Boolean, default=False)
    tipo_retencion = Column(String(50))
    numero_certificado = Column(String(100))

    referencia = Column(String(200))
    observaciones = Column(Text)

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    anulado = Column(Boolean, default=False)

    # Relaciones
    remito = relationship("Remito", back_populates="pagos")
    movimiento_cc = relationship("MovimientoCuentaCorriente")
    creador = relationship("Usuario")

    def __repr__(self):
        return f"<PagoRemito {self.monto} - {self.remito_id}>"
