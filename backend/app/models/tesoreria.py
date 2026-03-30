"""
Modelos para el módulo de Tesorería
Gestiona cheques, movimientos de caja, cuentas bancarias y flujos de fondos
"""
from sqlalchemy import Column, String, Numeric, Text, Date, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, get_argentina_now


# ==================== ENUMS ====================

class TipoChequeEnum(str, enum.Enum):
    """Tipo de cheque"""
    FISICO = "fisico"
    ECHEQ = "echeq"


class OrigenChequeEnum(str, enum.Enum):
    """Origen del cheque"""
    RECIBIDO_CLIENTE = "recibido_cliente"  # Cheque recibido de un cliente como pago
    RECIBIDO_PROVEEDOR = "recibido_proveedor"  # Cheque recibido de un proveedor (ej: devolución)
    EMITIDO = "emitido"  # Cheque emitido por la empresa


class EstadoChequeEnum(str, enum.Enum):
    """Estado del cheque"""
    EN_CARTERA = "en_cartera"  # Cheque en poder de la empresa
    DEPOSITADO = "depositado"  # Depositado en banco, esperando acreditación
    COBRADO = "cobrado"  # Cobrado/acreditado en cuenta
    ENTREGADO = "entregado"  # Entregado a tercero como forma de pago
    RECHAZADO = "rechazado"  # Rechazado por el banco
    ANULADO = "anulado"  # Anulado del sistema


class TipoMovimientoTesoreriaEnum(str, enum.Enum):
    """Tipo de movimiento de tesorería"""
    INGRESO_EFECTIVO = "ingreso_efectivo"
    INGRESO_TRANSFERENCIA = "ingreso_transferencia"
    INGRESO_CHEQUE = "ingreso_cheque"
    EGRESO_EFECTIVO = "egreso_efectivo"
    EGRESO_TRANSFERENCIA = "egreso_transferencia"
    EGRESO_CHEQUE = "egreso_cheque"
    DEPOSITO_CHEQUE = "deposito_cheque"
    COBRO_CHEQUE = "cobro_cheque"


class MetodoPagoEnum(str, enum.Enum):
    """Método de pago"""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    E_CHEQUE = "e_cheque"


# Lista de bancos de Argentina
BANCOS_ARGENTINA = [
    "Banco Nación",
    "Banco Provincia",
    "Banco Ciudad",
    "Banco Santander",
    "Banco Galicia",
    "Banco BBVA",
    "Banco Macro",
    "Banco HSBC",
    "Banco Credicoop",
    "Banco Patagonia",
    "Banco Supervielle",
    "Banco ICBC",
    "Banco Hipotecario",
    "Otro"
]


# ==================== MODELOS ====================

class Cheque(BaseModel):
    """
    Gestión de cheques (físicos y e-cheqs)
    """

    __tablename__ = "cheques"

    # Identificación del cheque
    numero = Column(String(50), nullable=False, index=True)
    tipo = Column(String(20), default=TipoChequeEnum.FISICO.value, nullable=False)
    origen = Column(String(30), default=OrigenChequeEnum.RECIBIDO_CLIENTE.value, nullable=False)
    estado = Column(String(20), default=EstadoChequeEnum.EN_CARTERA.value, nullable=False, index=True)

    # Monto y fechas
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_emision = Column(Date, nullable=True)
    fecha_vencimiento = Column(Date, nullable=False, index=True)
    fecha_cobro = Column(Date, nullable=True)
    fecha_deposito = Column(Date, nullable=True)
    fecha_entrega = Column(Date, nullable=True)

    # Bancos
    banco_origen = Column(String(100))  # Banco que emite el cheque
    cuenta_destino_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_bancarias.id"), nullable=True)
    banco_destino = Column(String(100))  # Banco donde se deposita

    # Relaciones con entidades
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True, index=True)  # Cliente si es recibido

    # Información del cheque
    librador = Column(String(200))  # Persona/empresa que emite el cheque
    cuit_librador = Column(String(20))

    # Auditoría y control
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    cobrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_registro = Column(DateTime, default=get_argentina_now, nullable=False)

    # Observaciones
    notas = Column(Text)
    motivo_rechazo = Column(Text)
    concepto_entrega = Column(String(500))  # Para qué se entregó el cheque

    # Estado lógico
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    empresa = relationship("Empresa")
    cuenta_destino = relationship("CuentaBancaria")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])
    cobrado_por = relationship("Usuario", foreign_keys=[cobrado_por_id])

    # Índices compuestos
    __table_args__ = (
        Index('ix_cheques_estado_vencimiento', 'estado', 'fecha_vencimiento'),
        Index('ix_cheques_empresa_estado', 'empresa_id', 'estado'),
    )

    def __repr__(self):
        return f"<Cheque #{self.numero} ${self.monto} - {self.estado}>"


class MovimientoTesoreria(BaseModel):
    """
    Movimientos de tesorería (ingresos y egresos de caja)
    Registra efectivo, transferencias y cheques
    """

    __tablename__ = "movimientos_tesoreria"

    # Tipo y concepto
    tipo = Column(String(30), nullable=False, index=True)
    concepto = Column(String(200), nullable=False)
    descripcion = Column(Text)

    # Monto
    monto = Column(Numeric(12, 2), nullable=False)
    es_ingreso = Column(Boolean, nullable=False)

    # Fechas
    fecha_movimiento = Column(Date, nullable=False, index=True)
    fecha_valor = Column(Date, nullable=True)  # Para cheques diferidos

    # Método de pago
    metodo_pago = Column(String(20), nullable=False)

    # Si es transferencia
    banco_origen = Column(String(100))
    banco_destino = Column(String(100))
    cuenta_destino_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_bancarias.id"), nullable=True)
    numero_transferencia = Column(String(100))

    # Si es cheque
    cheque_id = Column(UUID(as_uuid=True), ForeignKey("cheques.id"), nullable=True)

    # Relaciones con entidades
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True, index=True)  # Cliente o proveedor

    # Vinculación con pesajes (para cobranzas)
    pesaje_id = Column(UUID(as_uuid=True), ForeignKey("pesajes.id"), nullable=True)
    cobro_id = Column(UUID(as_uuid=True), ForeignKey("cobros_cliente.id"), nullable=True)

    # Auditoría
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)
    comprobante = Column(String(100))  # Referencia de comprobante

    # Anulación
    anulado = Column(Boolean, default=False, nullable=False)
    motivo_anulacion = Column(Text)
    anulado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_anulacion = Column(DateTime, nullable=True)

    # Estado lógico
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    empresa = relationship("Empresa")
    cuenta_destino = relationship("CuentaBancaria")
    cheque = relationship("Cheque")
    pesaje = relationship("Pesaje")
    cobro = relationship("CobroCliente")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])
    anulado_por = relationship("Usuario", foreign_keys=[anulado_por_id])

    # Índices compuestos
    __table_args__ = (
        Index('ix_mov_tesoreria_fecha_tipo', 'fecha_movimiento', 'tipo'),
        Index('ix_mov_tesoreria_empresa_fecha', 'empresa_id', 'fecha_movimiento'),
    )

    def __repr__(self):
        return f"<MovimientoTesoreria {self.tipo} ${self.monto}>"


class CajaEfectivo(BaseModel):
    """
    Representa una caja de efectivo (ej: Caja Principal, Caja Chica)
    Permite tener múltiples cajas de efectivo
    """

    __tablename__ = "cajas_efectivo"

    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    saldo_actual = Column(Numeric(12, 2), default=0, nullable=False)
    saldo_inicial = Column(Numeric(12, 2), default=0, nullable=False)
    moneda = Column(String(10), default="ARS", nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    es_principal = Column(Boolean, default=False, nullable=False)
    notas = Column(Text)

    def __repr__(self):
        return f"<CajaEfectivo {self.nombre} ${self.saldo_actual}>"


class MovimientoCaja(BaseModel):
    """
    Movimientos de una caja de efectivo específica
    """

    __tablename__ = "movimientos_caja"

    caja_id = Column(UUID(as_uuid=True), ForeignKey("cajas_efectivo.id"), nullable=False, index=True)

    # Tipo de movimiento
    tipo = Column(String(20), nullable=False)  # ingreso, egreso
    concepto = Column(String(200), nullable=False)
    descripcion = Column(Text)

    # Montos
    monto = Column(Numeric(12, 2), nullable=False)
    saldo_anterior = Column(Numeric(12, 2), nullable=False)
    saldo_posterior = Column(Numeric(12, 2), nullable=False)

    # Fecha
    fecha = Column(Date, nullable=False, index=True)

    # Referencias
    movimiento_tesoreria_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_tesoreria.id"), nullable=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)

    # Auditoría
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Anulación
    anulado = Column(Boolean, default=False, nullable=False)

    # Relaciones
    caja = relationship("CajaEfectivo")
    movimiento_tesoreria = relationship("MovimientoTesoreria")
    empresa = relationship("Empresa")
    registrado_por = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoCaja {self.tipo} ${self.monto}>"


class MovimientoBancario(BaseModel):
    """
    Movimientos de una cuenta bancaria específica
    """

    __tablename__ = "movimientos_bancarios"

    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_bancarias.id"), nullable=False, index=True)

    # Tipo de movimiento
    tipo = Column(String(20), nullable=False)  # ingreso, egreso
    concepto = Column(String(200), nullable=False)
    descripcion = Column(Text)

    # Montos
    monto = Column(Numeric(12, 2), nullable=False)
    saldo_anterior = Column(Numeric(12, 2), nullable=False)
    saldo_posterior = Column(Numeric(12, 2), nullable=False)

    # Fecha
    fecha = Column(Date, nullable=False, index=True)
    fecha_valor = Column(Date, nullable=True)  # Fecha de acreditación

    # Referencias
    numero_operacion = Column(String(100))
    movimiento_tesoreria_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_tesoreria.id"), nullable=True)
    cheque_id = Column(UUID(as_uuid=True), ForeignKey("cheques.id"), nullable=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)

    # Auditoría
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Anulación
    anulado = Column(Boolean, default=False, nullable=False)

    # Relaciones
    cuenta = relationship("CuentaBancaria")
    movimiento_tesoreria = relationship("MovimientoTesoreria")
    cheque = relationship("Cheque")
    empresa = relationship("Empresa")
    registrado_por = relationship("Usuario")

    def __repr__(self):
        return f"<MovimientoBancario {self.tipo} ${self.monto}>"


class Gasto(BaseModel):
    """
    Registro de gastos de la empresa
    """

    __tablename__ = "gastos"

    # Datos del gasto
    fecha = Column(Date, nullable=False, index=True)
    concepto = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(100))

    # Monto
    monto = Column(Numeric(12, 2), nullable=False)

    # Proveedor (opcional)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True)
    proveedor_nombre = Column(String(200))  # Si no está en el sistema

    # Comprobante
    tipo_comprobante = Column(String(50))  # factura, ticket, recibo
    numero_comprobante = Column(String(100))
    comprobante_url = Column(String(500))

    # Método de pago
    metodo_pago = Column(String(20), nullable=False)
    cuenta_bancaria_id = Column(UUID(as_uuid=True), ForeignKey("cuentas_bancarias.id"), nullable=True)
    caja_id = Column(UUID(as_uuid=True), ForeignKey("cajas_efectivo.id"), nullable=True)
    cheque_id = Column(UUID(as_uuid=True), ForeignKey("cheques.id"), nullable=True)

    # Vinculación con otros módulos
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=True)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=True)

    # Movimiento de tesorería generado
    movimiento_tesoreria_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_tesoreria.id"), nullable=True)

    # Auditoría
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Estado
    estado = Column(String(20), default="completado")  # completado, pendiente, anulado
    anulado = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    empresa = relationship("Empresa")
    cuenta_bancaria = relationship("CuentaBancaria")
    caja = relationship("CajaEfectivo")
    cheque = relationship("Cheque")
    camion = relationship("Camion")
    movimiento_tesoreria = relationship("MovimientoTesoreria")
    registrado_por = relationship("Usuario")

    def __repr__(self):
        return f"<Gasto {self.concepto} ${self.monto}>"


class Recibo(BaseModel):
    """
    Recibos generados por pagos de clientes
    """

    __tablename__ = "recibos"

    # Numeración
    numero_recibo = Column(String(50), unique=True, nullable=False, index=True)

    # Fecha
    fecha = Column(Date, nullable=False, index=True)

    # Cliente
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # Monto
    monto = Column(Numeric(12, 2), nullable=False)

    # Concepto
    concepto = Column(String(500), nullable=False)

    # Método de pago
    metodo_pago = Column(String(20), nullable=False)

    # Referencias
    cheque_id = Column(UUID(as_uuid=True), ForeignKey("cheques.id"), nullable=True)
    movimiento_tesoreria_id = Column(UUID(as_uuid=True), ForeignKey("movimientos_tesoreria.id"), nullable=True)
    cobro_id = Column(UUID(as_uuid=True), ForeignKey("cobros_cliente.id"), nullable=True)

    # PDF
    pdf_url = Column(String(500))

    # Auditoría
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notas = Column(Text)

    # Estado
    anulado = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    empresa = relationship("Empresa")
    cheque = relationship("Cheque")
    movimiento_tesoreria = relationship("MovimientoTesoreria")
    cobro = relationship("CobroCliente")
    registrado_por = relationship("Usuario")

    def __repr__(self):
        return f"<Recibo #{self.numero_recibo} ${self.monto}>"
