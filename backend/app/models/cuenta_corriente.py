"""
Modelos para Cuenta Corriente de Clientes
"""
from sqlalchemy import Column, String, Numeric, Text, Date, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class HistorialMovimientoCC(BaseModel):
    """Historial de acciones sobre movimientos de cuenta corriente"""

    __tablename__ = "historial_movimientos_cc"

    movimiento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("movimientos_cuenta_corriente.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String(50), nullable=False)  # CREACION, MODIFICACION, ANULACION
    detalle = Column(Text)

    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<HistorialMovimientoCC {self.accion} - {self.created_at}>"


class TipoMovimientoCCEnum(str, enum.Enum):
    """Tipo de movimiento en cuenta corriente"""
    CARGO = "cargo"  # Deuda (pesaje, servicio, etc.)
    PAGO = "pago"    # Pago del cliente
    AJUSTE = "ajuste"  # Ajuste manual (nota de crédito/débito)


class FormaPagoEnum(str, enum.Enum):
    """Formas de pago disponibles"""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    E_CHEQUE = "e_cheque"
    RETENCION_IIBB = "retencion_iibb"
    RETENCION_GANANCIAS = "retencion_ganancias"
    RETENCION_SUSS = "retencion_suss"


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
    historial = relationship(
        "HistorialMovimientoCC",
        backref="movimiento",
        cascade="all, delete-orphan",
        order_by="desc(HistorialMovimientoCC.created_at)",
    )

    def __repr__(self):
        return f"<MovimientoCC {self.tipo} ${self.monto} - {self.empresa_id}>"


class CobroCliente(BaseModel):
    """
    Cobro de cliente con control cruzado.
    Registra el monto total de una orden de pago y permite desglosarlo en items.
    El sistema verifica que la suma de items coincida con el monto total.
    """

    __tablename__ = "cobros_cliente"

    # Numeración
    numero_cobro = Column(Integer, unique=True, nullable=False, index=True)

    # Cliente
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)

    # Fecha de reconocimiento (por defecto fecha actual)
    fecha = Column(Date, nullable=False, index=True)

    # Monto total de la orden de pago del cliente
    monto_total = Column(Numeric(12, 2), nullable=False)

    # Suma de los items de detalle
    monto_aplicado = Column(Numeric(12, 2), nullable=False, default=0)

    # Diferencia (positivo = saldo a favor cliente, negativo = saldo pendiente)
    # diferencia = monto_total - monto_aplicado
    diferencia = Column(Numeric(12, 2), nullable=False, default=0)

    # Estado
    # - borrador: en proceso de carga de items
    # - confirmado: items cargados y verificados
    # - aplicado: ya generó movimientos en cuenta corriente
    estado = Column(String(20), default="borrador", nullable=False)

    # Referencia a la orden de pago
    numero_orden_pago = Column(String(100))  # Número de orden de pago del cliente
    observaciones = Column(Text)

    # Auditoría
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_confirmacion = Column(Date, nullable=True)
    anulado = Column(Boolean, default=False, nullable=False)
    motivo_anulacion = Column(Text)

    # Relaciones
    empresa = relationship("Empresa")
    creador = relationship("Usuario", foreign_keys=[created_by])
    confirmador = relationship("Usuario", foreign_keys=[confirmed_by])
    items = relationship("ItemCobroCliente", back_populates="cobro", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CobroCliente #{self.numero_cobro} ${self.monto_total} - {self.empresa_id}>"

    @property
    def esta_balanceado(self):
        """Verifica si el cobro está balanceado (debe = haber)"""
        return abs(self.diferencia) < 0.01


class ItemCobroCliente(BaseModel):
    """
    Item de detalle de un cobro.
    Puede ser:
    - Un medio de pago (efectivo, cheque, transferencia, retención)
    - Una aplicación a factura o ticket
    """

    __tablename__ = "items_cobro_cliente"

    # Cobro padre
    cobro_id = Column(UUID(as_uuid=True), ForeignKey("cobros_cliente.id", ondelete="CASCADE"), nullable=False, index=True)

    # Tipo de item
    # HABER (ingresos del cobro):
    #   - efectivo, transferencia, cheque, e_cheque
    #   - retencion_iibb, retencion_ganancias, retencion_suss
    # DEBE (aplicaciones):
    #   - factura, ticket, saldo_favor
    tipo_item = Column(String(30), nullable=False)

    # Concepto (DEBE o HABER)
    concepto = Column(String(10), nullable=False)  # "debe" o "haber"

    # Monto del item
    monto = Column(Numeric(12, 2), nullable=False)

    # Descripción
    descripcion = Column(String(500))

    # Referencias opcionales según tipo
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=True)
    remito_id = Column(UUID(as_uuid=True), ForeignKey("remitos.id"), nullable=True)
    pesaje_id = Column(UUID(as_uuid=True), ForeignKey("pesajes.id"), nullable=True)

    # Datos para cheques
    banco = Column(String(100))
    numero_cheque = Column(String(50))
    fecha_cheque = Column(Date)
    cuit_emisor = Column(String(20))

    # Datos para transferencias
    referencia_transferencia = Column(String(100))

    # Datos para retenciones
    numero_certificado = Column(String(100))

    # Movimiento de cuenta corriente generado (cuando se aplica)
    movimiento_cc_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_cuenta_corriente.id"), nullable=True)

    # Relaciones
    cobro = relationship("CobroCliente", back_populates="items")
    factura = relationship("Factura")
    remito = relationship("Remito")
    pesaje = relationship("Pesaje")
    movimiento_cc = relationship("MovimientoCuentaCorriente")

    def __repr__(self):
        return f"<ItemCobro {self.tipo_item} {self.concepto} ${self.monto}>"
