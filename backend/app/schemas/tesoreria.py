"""
Schemas Pydantic para el módulo de Tesorería
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ==================== CONSTANTES ====================

TIPOS_CHEQUE = [
    {"value": "fisico", "label": "Cheque Físico"},
    {"value": "echeq", "label": "E-Cheq"},
]

ORIGENES_CHEQUE = [
    {"value": "recibido_cliente", "label": "Recibido de Cliente"},
    {"value": "recibido_proveedor", "label": "Recibido de Proveedor"},
    {"value": "emitido", "label": "Emitido (Propio)"},
]

ESTADOS_CHEQUE = [
    {"value": "en_cartera", "label": "En Cartera", "color": "blue"},
    {"value": "depositado", "label": "Depositado", "color": "yellow"},
    {"value": "cobrado", "label": "Cobrado", "color": "green"},
    {"value": "entregado", "label": "Entregado", "color": "purple"},
    {"value": "rechazado", "label": "Rechazado", "color": "red"},
    {"value": "anulado", "label": "Anulado", "color": "gray"},
]

METODOS_PAGO = [
    {"value": "efectivo", "label": "Efectivo"},
    {"value": "transferencia", "label": "Transferencia"},
    {"value": "cheque", "label": "Cheque"},
]

BANCOS_ARGENTINA = [
    {"value": "banco_nacion", "label": "Banco Nación"},
    {"value": "banco_provincia", "label": "Banco Provincia"},
    {"value": "banco_ciudad", "label": "Banco Ciudad"},
    {"value": "banco_santander", "label": "Banco Santander"},
    {"value": "banco_galicia", "label": "Banco Galicia"},
    {"value": "banco_bbva", "label": "Banco BBVA"},
    {"value": "banco_macro", "label": "Banco Macro"},
    {"value": "banco_hsbc", "label": "Banco HSBC"},
    {"value": "banco_credicoop", "label": "Banco Credicoop"},
    {"value": "banco_patagonia", "label": "Banco Patagonia"},
    {"value": "banco_supervielle", "label": "Banco Supervielle"},
    {"value": "banco_icbc", "label": "Banco ICBC"},
    {"value": "banco_hipotecario", "label": "Banco Hipotecario"},
    {"value": "otro", "label": "Otro"},
]

CATEGORIAS_GASTO = [
    {"value": "combustible", "label": "Combustible"},
    {"value": "repuestos", "label": "Repuestos"},
    {"value": "mantenimiento", "label": "Mantenimiento"},
    {"value": "sueldos", "label": "Sueldos"},
    {"value": "servicios", "label": "Servicios"},
    {"value": "impuestos", "label": "Impuestos"},
    {"value": "alquileres", "label": "Alquileres"},
    {"value": "seguros", "label": "Seguros"},
    {"value": "administrativos", "label": "Gastos Administrativos"},
    {"value": "otros", "label": "Otros"},
]


# ==================== CHEQUE SCHEMAS ====================

class ChequeBase(BaseModel):
    """Base para cheques"""
    numero: str = Field(..., min_length=1, max_length=50)
    tipo: str = Field(default="fisico")
    origen: str = Field(default="recibido_cliente")
    monto: Decimal = Field(..., gt=0)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: date
    banco_origen: Optional[str] = None
    cuenta_destino_id: Optional[UUID] = None
    banco_destino: Optional[str] = None
    empresa_id: Optional[UUID] = None
    librador: Optional[str] = Field(None, max_length=200)
    cuit_librador: Optional[str] = Field(None, max_length=20)
    notas: Optional[str] = None


class ChequeCreate(ChequeBase):
    """Schema para crear cheque"""
    pass


class ChequeUpdate(BaseModel):
    """Schema para actualizar cheque"""
    numero: Optional[str] = Field(None, min_length=1, max_length=50)
    tipo: Optional[str] = None
    origen: Optional[str] = None
    estado: Optional[str] = None
    monto: Optional[Decimal] = Field(None, gt=0)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    banco_origen: Optional[str] = None
    cuenta_destino_id: Optional[UUID] = None
    banco_destino: Optional[str] = None
    empresa_id: Optional[UUID] = None
    librador: Optional[str] = Field(None, max_length=200)
    cuit_librador: Optional[str] = Field(None, max_length=20)
    notas: Optional[str] = None


class ChequeResponse(ChequeBase):
    """Schema de respuesta de cheque"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado: str
    fecha_cobro: Optional[date] = None
    fecha_deposito: Optional[date] = None
    fecha_entrega: Optional[date] = None
    motivo_rechazo: Optional[str] = None
    concepto_entrega: Optional[str] = None
    registrado_por_id: UUID
    cobrado_por_id: Optional[UUID] = None
    fecha_registro: datetime
    activo: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    empresa_nombre: Optional[str] = None
    registrado_por_nombre: Optional[str] = None
    cobrado_por_nombre: Optional[str] = None
    cuenta_destino_nombre: Optional[str] = None
    dias_para_vencimiento: Optional[int] = None


class ChequeList(BaseModel):
    """Schema para listado de cheques"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero: str
    tipo: str
    origen: str
    estado: str
    monto: Decimal
    fecha_vencimiento: date
    fecha_cobro: Optional[date] = None
    banco_origen: Optional[str] = None
    empresa_id: Optional[UUID] = None
    empresa_nombre: Optional[str] = None
    librador: Optional[str] = None
    dias_para_vencimiento: Optional[int] = None
    created_at: datetime


# ==================== ACCIONES DE CHEQUE ====================

class DepositarChequeRequest(BaseModel):
    """Request para depositar un cheque"""
    cuenta_destino_id: UUID
    fecha_deposito: Optional[date] = None
    notas: Optional[str] = None


class CobrarChequeRequest(BaseModel):
    """Request para confirmar cobro de cheque"""
    fecha_cobro: Optional[date] = None
    notas: Optional[str] = None


class RechazarChequeRequest(BaseModel):
    """Request para rechazar un cheque"""
    motivo_rechazo: str = Field(..., min_length=3)
    fecha_rechazo: Optional[date] = None


class EntregarChequeRequest(BaseModel):
    """Request para entregar cheque a tercero"""
    empresa_destino_id: Optional[UUID] = None
    concepto: str = Field(..., min_length=3)
    fecha_entrega: Optional[date] = None
    notas: Optional[str] = None


# ==================== MOVIMIENTO TESORERIA SCHEMAS ====================

class MovimientoTesoreriaBase(BaseModel):
    """Base para movimientos de tesorería"""
    tipo: str
    concepto: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    monto: Decimal = Field(..., gt=0)
    es_ingreso: bool
    fecha_movimiento: date
    fecha_valor: Optional[date] = None
    metodo_pago: str
    banco_origen: Optional[str] = None
    banco_destino: Optional[str] = None
    cuenta_destino_id: Optional[UUID] = None
    numero_transferencia: Optional[str] = None
    cheque_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    pesaje_id: Optional[UUID] = None
    cobro_id: Optional[UUID] = None
    notas: Optional[str] = None
    comprobante: Optional[str] = None


class MovimientoTesoreriaCreate(MovimientoTesoreriaBase):
    """Schema para crear movimiento de tesorería"""
    pass


class MovimientoTesoreriaResponse(MovimientoTesoreriaBase):
    """Schema de respuesta de movimiento de tesorería"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registrado_por_id: UUID
    anulado: bool
    motivo_anulacion: Optional[str] = None
    anulado_por_id: Optional[UUID] = None
    fecha_anulacion: Optional[datetime] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    empresa_nombre: Optional[str] = None
    registrado_por_nombre: Optional[str] = None
    cheque_numero: Optional[str] = None
    pesaje_numero: Optional[int] = None


class MovimientoTesoreriaList(BaseModel):
    """Schema para listado de movimientos"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: str
    concepto: str
    monto: Decimal
    es_ingreso: bool
    fecha_movimiento: date
    metodo_pago: str
    empresa_id: Optional[UUID] = None
    empresa_nombre: Optional[str] = None
    anulado: bool
    created_at: datetime


class AnularMovimientoRequest(BaseModel):
    """Request para anular un movimiento"""
    motivo: str = Field(..., min_length=3)


# ==================== CAJA EFECTIVO SCHEMAS ====================

class CajaEfectivoBase(BaseModel):
    """Base para caja de efectivo"""
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    saldo_inicial: Decimal = Field(default=0)
    moneda: str = Field(default="ARS")
    es_principal: bool = False
    notas: Optional[str] = None


class CajaEfectivoCreate(CajaEfectivoBase):
    """Schema para crear caja de efectivo"""
    pass


class CajaEfectivoUpdate(BaseModel):
    """Schema para actualizar caja de efectivo"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    es_principal: Optional[bool] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class CajaEfectivoResponse(CajaEfectivoBase):
    """Schema de respuesta de caja de efectivo"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saldo_actual: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime


# ==================== MOVIMIENTO CAJA SCHEMAS ====================

class MovimientoCajaBase(BaseModel):
    """Base para movimiento de caja"""
    caja_id: UUID
    tipo: str  # ingreso, egreso
    concepto: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    monto: Decimal = Field(..., gt=0)
    fecha: date
    empresa_id: Optional[UUID] = None
    notas: Optional[str] = None


class MovimientoCajaCreate(MovimientoCajaBase):
    """Schema para crear movimiento de caja"""
    pass


class MovimientoCajaResponse(MovimientoCajaBase):
    """Schema de respuesta de movimiento de caja"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saldo_anterior: Decimal
    saldo_posterior: Decimal
    movimiento_tesoreria_id: Optional[UUID] = None
    registrado_por_id: UUID
    anulado: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    caja_nombre: Optional[str] = None
    empresa_nombre: Optional[str] = None
    registrado_por_nombre: Optional[str] = None


# ==================== CUENTA BANCARIA SCHEMAS (extendido) ====================

class CuentaBancariaBase(BaseModel):
    """Base para cuenta bancaria"""
    nombre: str = Field(..., min_length=2, max_length=100)
    banco: str = Field(..., min_length=2, max_length=100)
    tipo_cuenta: Optional[str] = None
    numero_cuenta: Optional[str] = None
    cbu: Optional[str] = Field(None, max_length=30)
    alias: Optional[str] = Field(None, max_length=50)
    titular: Optional[str] = None
    cuit_titular: Optional[str] = None
    saldo_inicial: Decimal = Field(default=0)
    moneda: str = Field(default="ARS")
    notas: Optional[str] = None


class CuentaBancariaCreate(CuentaBancariaBase):
    """Schema para crear cuenta bancaria"""
    pass


class CuentaBancariaUpdate(BaseModel):
    """Schema para actualizar cuenta bancaria"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    numero_cuenta: Optional[str] = None
    cbu: Optional[str] = None
    alias: Optional[str] = None
    titular: Optional[str] = None
    cuit_titular: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class CuentaBancariaResponse(CuentaBancariaBase):
    """Schema de respuesta de cuenta bancaria"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saldo_actual: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime


# ==================== MOVIMIENTO BANCARIO SCHEMAS ====================

class MovimientoBancarioBase(BaseModel):
    """Base para movimiento bancario"""
    cuenta_id: UUID
    tipo: str  # ingreso, egreso
    concepto: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    monto: Decimal = Field(..., gt=0)
    fecha: date
    fecha_valor: Optional[date] = None
    numero_operacion: Optional[str] = None
    empresa_id: Optional[UUID] = None
    notas: Optional[str] = None


class MovimientoBancarioCreate(MovimientoBancarioBase):
    """Schema para crear movimiento bancario"""
    pass


class MovimientoBancarioResponse(MovimientoBancarioBase):
    """Schema de respuesta de movimiento bancario"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saldo_anterior: Decimal
    saldo_posterior: Decimal
    movimiento_tesoreria_id: Optional[UUID] = None
    cheque_id: Optional[UUID] = None
    registrado_por_id: UUID
    anulado: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    cuenta_nombre: Optional[str] = None
    cuenta_banco: Optional[str] = None
    empresa_nombre: Optional[str] = None
    registrado_por_nombre: Optional[str] = None


# ==================== GASTO SCHEMAS ====================

class GastoBase(BaseModel):
    """Base para gasto"""
    fecha: date
    concepto: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    monto: Decimal = Field(..., gt=0)
    empresa_id: Optional[UUID] = None
    proveedor_nombre: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    numero_comprobante: Optional[str] = None
    comprobante_url: Optional[str] = None
    metodo_pago: str
    cuenta_bancaria_id: Optional[UUID] = None
    caja_id: Optional[UUID] = None
    cheque_id: Optional[UUID] = None
    camion_id: Optional[UUID] = None
    servicio_id: Optional[UUID] = None
    notas: Optional[str] = None


class GastoCreate(GastoBase):
    """Schema para crear gasto"""
    pass


class GastoUpdate(BaseModel):
    """Schema para actualizar gasto"""
    fecha: Optional[date] = None
    concepto: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    monto: Optional[Decimal] = Field(None, gt=0)
    empresa_id: Optional[UUID] = None
    proveedor_nombre: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    numero_comprobante: Optional[str] = None
    comprobante_url: Optional[str] = None
    notas: Optional[str] = None


class GastoResponse(GastoBase):
    """Schema de respuesta de gasto"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    movimiento_tesoreria_id: Optional[UUID] = None
    registrado_por_id: UUID
    estado: str
    anulado: bool
    activo: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    empresa_nombre: Optional[str] = None
    cuenta_bancaria_nombre: Optional[str] = None
    caja_nombre: Optional[str] = None
    camion_identificador: Optional[str] = None
    registrado_por_nombre: Optional[str] = None


class GastoList(BaseModel):
    """Schema para listado de gastos"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fecha: date
    concepto: str
    categoria: Optional[str] = None
    monto: Decimal
    metodo_pago: str
    empresa_nombre: Optional[str] = None
    proveedor_nombre: Optional[str] = None
    estado: str
    anulado: bool
    created_at: datetime


# ==================== RECIBO SCHEMAS ====================

class ReciboBase(BaseModel):
    """Base para recibo"""
    fecha: date
    empresa_id: UUID
    monto: Decimal = Field(..., gt=0)
    concepto: str = Field(..., min_length=3, max_length=500)
    metodo_pago: str
    cheque_id: Optional[UUID] = None
    cobro_id: Optional[UUID] = None
    notas: Optional[str] = None


class ReciboCreate(ReciboBase):
    """Schema para crear recibo"""
    pass


class ReciboResponse(ReciboBase):
    """Schema de respuesta de recibo"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero_recibo: str
    movimiento_tesoreria_id: Optional[UUID] = None
    pdf_url: Optional[str] = None
    registrado_por_id: UUID
    anulado: bool
    activo: bool
    created_at: datetime
    updated_at: datetime

    # Campos enriquecidos
    empresa_nombre: Optional[str] = None
    registrado_por_nombre: Optional[str] = None


# ==================== RESUMEN TESORERIA ====================

class ResumenTesoreria(BaseModel):
    """Resumen de tesorería"""
    # Cheques en cartera
    cheques_en_cartera: int = 0
    total_cheques_cartera: Decimal = Decimal("0")

    # Cheques próximos a vencer
    cheques_proximos_vencer: int = 0
    total_proximos_vencer: Decimal = Decimal("0")

    # Cheques vencidos
    cheques_vencidos: int = 0
    total_vencidos: Decimal = Decimal("0")

    # Ingresos del período
    total_ingresos_efectivo: Decimal = Decimal("0")
    total_ingresos_transferencia: Decimal = Decimal("0")
    total_ingresos_cheque: Decimal = Decimal("0")
    total_ingresos: Decimal = Decimal("0")

    # Egresos del período
    total_egresos_efectivo: Decimal = Decimal("0")
    total_egresos_transferencia: Decimal = Decimal("0")
    total_egresos_cheque: Decimal = Decimal("0")
    total_egresos: Decimal = Decimal("0")

    # Saldos
    saldo_periodo: Decimal = Decimal("0")

    # Cajas
    saldo_cajas: Decimal = Decimal("0")

    # Bancos
    saldo_bancos: Decimal = Decimal("0")

    # Total disponible
    total_disponible: Decimal = Decimal("0")


# ==================== MOVIMIENTOS CONSOLIDADOS ====================

class MovimientoConsolidado(BaseModel):
    """Movimiento consolidado (unifica cheques, caja, banco)"""
    id: str
    fecha: date
    tipo: str
    origen: str  # 'cheque', 'movimiento_tesoreria', 'movimiento_caja', 'movimiento_bancario'
    concepto: str
    monto: Decimal
    es_ingreso: bool
    metodo_pago: str
    empresa_nombre: Optional[str] = None
    numero_referencia: Optional[str] = None
    banco: Optional[str] = None
    estado: Optional[str] = None
    created_at: datetime


class MovimientosConsolidadosResponse(BaseModel):
    """Respuesta de movimientos consolidados"""
    items: List[MovimientoConsolidado]
    total: int
    total_ingresos: Decimal
    total_egresos: Decimal
    skip: int
    limit: int


# ==================== PAGINACIÓN ====================

class PaginatedCheques(BaseModel):
    """Respuesta paginada de cheques"""
    items: List[ChequeList]
    total: int
    skip: int
    limit: int


class PaginatedMovimientos(BaseModel):
    """Respuesta paginada de movimientos"""
    items: List[MovimientoTesoreriaList]
    total: int
    skip: int
    limit: int


class PaginatedGastos(BaseModel):
    """Respuesta paginada de gastos"""
    items: List[GastoList]
    total: int
    skip: int
    limit: int
