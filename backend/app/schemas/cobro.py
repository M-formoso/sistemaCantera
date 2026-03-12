"""
Schemas para Cobros de Clientes con control cruzado
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from enum import Enum


class ConceptoItem(str, Enum):
    """Concepto del item: debe o haber"""
    DEBE = "debe"
    HABER = "haber"


class TipoItemHaber(str, Enum):
    """Tipos de item del HABER (medios de pago)"""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    E_CHEQUE = "e_cheque"
    RETENCION_IIBB = "retencion_iibb"
    RETENCION_GANANCIAS = "retencion_ganancias"
    RETENCION_SUSS = "retencion_suss"


class TipoItemDebe(str, Enum):
    """Tipos de item del DEBE (aplicaciones)"""
    FACTURA = "factura"
    TICKET = "ticket"  # Pesaje/Remito individual
    SALDO_FAVOR = "saldo_favor"  # Saldo a favor del cliente


class EstadoCobro(str, Enum):
    """Estados del cobro"""
    BORRADOR = "borrador"
    CONFIRMADO = "confirmado"
    APLICADO = "aplicado"


# ============== ITEM SCHEMAS ==============

class ItemCobroBase(BaseModel):
    """Base para items de cobro"""
    tipo_item: str
    concepto: ConceptoItem
    monto: Decimal = Field(..., ge=0)
    descripcion: Optional[str] = None


class ItemCobroHaberCreate(ItemCobroBase):
    """Item del HABER (medio de pago)"""
    # Para cheques
    banco: Optional[str] = None
    numero_cheque: Optional[str] = None
    fecha_cheque: Optional[date] = None
    cuit_emisor: Optional[str] = None
    # Para transferencias
    referencia_transferencia: Optional[str] = None
    # Para retenciones
    numero_certificado: Optional[str] = None

    @field_validator('concepto')
    @classmethod
    def validar_concepto_haber(cls, v):
        if v != ConceptoItem.HABER:
            raise ValueError('El concepto debe ser HABER para medios de pago')
        return v


class ItemCobroDebeCreate(ItemCobroBase):
    """Item del DEBE (aplicación a factura/ticket)"""
    factura_id: Optional[UUID] = None
    remito_id: Optional[UUID] = None
    pesaje_id: Optional[UUID] = None

    @field_validator('concepto')
    @classmethod
    def validar_concepto_debe(cls, v):
        if v != ConceptoItem.DEBE:
            raise ValueError('El concepto debe ser DEBE para aplicaciones')
        return v


class ItemCobroCreate(BaseModel):
    """Item genérico de cobro"""
    tipo_item: str
    concepto: ConceptoItem
    monto: Decimal = Field(..., ge=0)
    descripcion: Optional[str] = None
    # Referencias
    factura_id: Optional[UUID] = None
    remito_id: Optional[UUID] = None
    pesaje_id: Optional[UUID] = None
    # Para cheques
    banco: Optional[str] = None
    numero_cheque: Optional[str] = None
    fecha_cheque: Optional[date] = None
    cuit_emisor: Optional[str] = None
    # Para transferencias
    referencia_transferencia: Optional[str] = None
    # Para retenciones
    numero_certificado: Optional[str] = None


class ItemCobroSchema(ItemCobroCreate):
    """Schema completo de item"""
    id: UUID
    cobro_id: UUID
    movimiento_cc_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============== COBRO SCHEMAS ==============

class CobroClienteBase(BaseModel):
    """Base para cobro"""
    empresa_id: UUID
    fecha: date
    monto_total: Decimal = Field(..., gt=0)
    numero_orden_pago: Optional[str] = None
    observaciones: Optional[str] = None


class CobroClienteCreate(CobroClienteBase):
    """Crear cobro (solo cabecera)"""
    pass


class CobroClienteCreateWithItems(CobroClienteBase):
    """Crear cobro con items"""
    items: List[ItemCobroCreate] = []


class CobroClienteUpdate(BaseModel):
    """Actualizar cobro"""
    monto_total: Optional[Decimal] = None
    numero_orden_pago: Optional[str] = None
    observaciones: Optional[str] = None


class CobroClienteSchema(CobroClienteBase):
    """Schema completo de cobro"""
    id: UUID
    numero_cobro: int
    monto_aplicado: Decimal
    diferencia: Decimal
    estado: str
    created_by: UUID
    confirmed_by: Optional[UUID] = None
    fecha_confirmacion: Optional[date] = None
    anulado: bool
    motivo_anulacion: Optional[str] = None
    items: List[ItemCobroSchema] = []

    # Datos calculados
    total_haber: Optional[Decimal] = None
    total_debe: Optional[Decimal] = None
    esta_balanceado: Optional[bool] = None

    # Datos relacionados
    empresa_nombre: Optional[str] = None
    creador_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class CobroClienteListSchema(BaseModel):
    """Schema para listado de cobros"""
    id: UUID
    numero_cobro: int
    empresa_id: UUID
    empresa_nombre: Optional[str] = None
    fecha: date
    monto_total: Decimal
    monto_aplicado: Decimal
    diferencia: Decimal
    estado: str
    anulado: bool

    class Config:
        from_attributes = True


# ============== VALIDACION SCHEMAS ==============

class ValidacionCobroResponse(BaseModel):
    """Respuesta de validación de cobro"""
    valido: bool
    total_haber: Decimal
    total_debe: Decimal
    diferencia: Decimal
    mensaje: str
    errores: List[str] = []


class AplicarCobroResponse(BaseModel):
    """Respuesta al aplicar cobro"""
    cobro_id: UUID
    numero_cobro: int
    movimientos_generados: int
    saldo_a_favor: Optional[Decimal] = None
    mensaje: str


# ============== BUSQUEDA SCHEMAS ==============

class TicketPendienteSchema(BaseModel):
    """Ticket/Pesaje pendiente de cobro"""
    id: UUID
    numero: int  # numero_pesaje o numero_remito
    tipo: str  # "pesaje" o "remito"
    fecha: date
    material: Optional[str] = None
    peso_neto: Optional[Decimal] = None
    importe: Decimal
    saldo_pendiente: Decimal

    class Config:
        from_attributes = True


class FacturaPendienteSchema(BaseModel):
    """Factura pendiente de cobro"""
    id: UUID
    numero_factura: str
    fecha_emision: date
    total: Decimal
    saldo_pendiente: Decimal

    class Config:
        from_attributes = True


class DocumentosPendientesResponse(BaseModel):
    """Documentos pendientes de cobro de un cliente"""
    empresa_id: UUID
    empresa_nombre: str
    saldo_cuenta_corriente: Decimal
    facturas: List[FacturaPendienteSchema] = []
    tickets: List[TicketPendienteSchema] = []
    total_pendiente: Decimal
