"""
Schemas para Facturación
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# =============================================
# ENUMS
# =============================================

class TipoComprobante(str, Enum):
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


class EstadoFactura(str, Enum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADA = "pagada"
    ANULADA = "anulada"


class FormaPago(str, Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    E_CHEQUE = "e_cheque"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    RETENCION_IIBB = "retencion_iibb"
    RETENCION_GANANCIAS = "retencion_ganancias"
    RETENCION_SUSS = "retencion_suss"
    RETENCION_IVA = "retencion_iva"
    OTRO = "otro"


class TipoRetencion(str, Enum):
    IIBB = "iibb"
    GANANCIAS = "ganancias"
    IVA = "iva"
    SUSS = "suss"


# =============================================
# REMITO (schema simplificado para selección)
# =============================================

class RemitoParaFactura(BaseModel):
    """Remito simplificado para asociar a factura"""
    id: UUID
    numero_remito: int
    fecha: date
    cliente: str
    producto: str
    peso_neto: Decimal
    importe: Optional[Decimal] = Decimal("0")
    saldo_pendiente: Optional[Decimal] = Decimal("0")
    facturado: Optional[bool] = False

    class Config:
        from_attributes = True


# =============================================
# PAGO FACTURA
# =============================================

class PagoFacturaBase(BaseModel):
    fecha: date
    monto: Decimal = Field(gt=0)
    forma_pago: FormaPago

    # Datos cheque (opcional)
    banco: Optional[str] = None
    numero_cheque: Optional[str] = None
    fecha_cheque: Optional[date] = None
    cuit_emisor: Optional[str] = None

    # Retenciones
    es_retencion: bool = False
    tipo_retencion: Optional[TipoRetencion] = None
    numero_certificado: Optional[str] = None

    referencia: Optional[str] = None
    observaciones: Optional[str] = None


class PagoFacturaCreate(PagoFacturaBase):
    factura_id: UUID


class PagoFacturaSchema(PagoFacturaBase):
    id: UUID
    factura_id: UUID
    movimiento_cc_id: Optional[UUID] = None
    anulado: bool = False
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True


# =============================================
# PAGO REMITO (sin factura)
# =============================================

class PagoRemitoBase(BaseModel):
    fecha: date
    monto: Decimal = Field(gt=0)
    forma_pago: FormaPago

    banco: Optional[str] = None
    numero_cheque: Optional[str] = None
    fecha_cheque: Optional[date] = None
    cuit_emisor: Optional[str] = None

    es_retencion: bool = False
    tipo_retencion: Optional[TipoRetencion] = None
    numero_certificado: Optional[str] = None

    referencia: Optional[str] = None
    observaciones: Optional[str] = None


class PagoRemitoCreate(PagoRemitoBase):
    remito_id: UUID


class PagoRemitoSchema(PagoRemitoBase):
    id: UUID
    remito_id: UUID
    movimiento_cc_id: Optional[UUID] = None
    anulado: bool = False
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True


# =============================================
# FACTURA
# =============================================

class FacturaBase(BaseModel):
    tipo_comprobante: TipoComprobante
    punto_venta: int = 1
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None

    # Montos
    subtotal: Decimal = Decimal("0")
    descuento: Decimal = Decimal("0")
    iva_21: Decimal = Decimal("0")
    iva_10_5: Decimal = Decimal("0")
    iva_27: Decimal = Decimal("0")
    percepciones_iibb: Decimal = Decimal("0")
    percepciones_iva: Decimal = Decimal("0")
    otros_impuestos: Decimal = Decimal("0")

    # CAE (opcional)
    cae: Optional[str] = None
    cae_vencimiento: Optional[date] = None

    observaciones: Optional[str] = None


class FacturaCreate(FacturaBase):
    empresa_id: UUID
    remito_ids: List[UUID] = []  # Remitos a asociar
    factura_original_id: Optional[UUID] = None  # Para NC/ND

    # El total se puede calcular automáticamente o enviar
    total: Optional[Decimal] = None


class FacturaUpdate(BaseModel):
    fecha_vencimiento: Optional[date] = None
    cae: Optional[str] = None
    cae_vencimiento: Optional[date] = None
    observaciones: Optional[str] = None


class FacturaSchema(FacturaBase):
    id: UUID
    numero_factura: str
    empresa_id: UUID
    total: Decimal
    saldo_pendiente: Decimal
    estado: EstadoFactura
    factura_original_id: Optional[UUID] = None
    anulada: bool = False
    motivo_anulacion: Optional[str] = None
    created_at: datetime
    created_by: UUID

    # Campos calculados
    porcentaje_pagado: Optional[float] = None
    esta_pagada: Optional[bool] = None

    # Relaciones
    empresa_nombre: Optional[str] = None
    remitos: Optional[List[RemitoParaFactura]] = []
    pagos: Optional[List[PagoFacturaSchema]] = []

    class Config:
        from_attributes = True


class FacturaConDetalles(FacturaSchema):
    """Factura con todos los detalles para vista completa"""
    remitos_detalle: Optional[List[RemitoParaFactura]] = []
    pagos_detalle: Optional[List[PagoFacturaSchema]] = []
    notas_credito: Optional[List["FacturaSchema"]] = []


# =============================================
# REQUESTS ESPECIALES
# =============================================

class AsociarRemitosRequest(BaseModel):
    """Request para asociar remitos a una factura"""
    remito_ids: List[UUID]


class RegistrarPagoMultipleRequest(BaseModel):
    """Request para registrar un pago que cubre múltiples formas"""
    factura_id: UUID
    fecha: date
    pagos: List[PagoFacturaBase]  # Múltiples formas de pago


class BuscarRemitosRequest(BaseModel):
    """Request para buscar remitos pendientes de un cliente"""
    empresa_id: UUID
    solo_sin_facturar: bool = True
    solo_con_saldo: bool = True


# =============================================
# RESÚMENES
# =============================================

class ResumenFacturacionCliente(BaseModel):
    """Resumen de facturación de un cliente"""
    empresa_id: UUID
    empresa_nombre: str
    total_facturado: Decimal
    total_cobrado: Decimal
    saldo_pendiente: Decimal
    cantidad_facturas: int
    cantidad_pendientes: int


class EstadoCuentaItem(BaseModel):
    """Item del estado de cuenta"""
    fecha: date
    tipo: str  # factura, pago, nc, nd
    numero: str
    descripcion: str
    debe: Decimal = Decimal("0")
    haber: Decimal = Decimal("0")
    saldo: Decimal


class EstadoCuentaCliente(BaseModel):
    """Estado de cuenta completo del cliente"""
    empresa_id: UUID
    empresa_nombre: str
    cuit: Optional[str]
    saldo_inicial: Decimal
    movimientos: List[EstadoCuentaItem]
    saldo_final: Decimal
    fecha_desde: date
    fecha_hasta: date
