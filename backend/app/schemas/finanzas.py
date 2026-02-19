"""
Schemas para el módulo de Finanzas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


# =============================================
# CATEGORÍAS
# =============================================

class CategoriaFinanzasBase(BaseModel):
    """Schema base de CategoríaFinanzas"""
    nombre: str = Field(..., max_length=100)
    tipo: Literal["ingreso", "egreso"]
    descripcion: Optional[str] = None
    color: Optional[str] = Field("#6B7280", max_length=20)
    icono: Optional[str] = Field(None, max_length=50)


class CategoriaFinanzasCreate(CategoriaFinanzasBase):
    """Schema para crear categoría"""
    pass


class CategoriaFinanzasUpdate(BaseModel):
    """Schema para actualizar categoría"""
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icono: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = None


class CategoriaFinanzasSchema(CategoriaFinanzasBase):
    """Schema de respuesta de categoría"""
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================
# MOVIMIENTOS FINANCIEROS
# =============================================

class MovimientoFinancieroBase(BaseModel):
    """Schema base de MovimientoFinanciero"""
    tipo: Literal["ingreso", "egreso"]
    categoria_id: Optional[UUID] = None
    fecha: date
    monto: Decimal = Field(..., gt=0)
    descripcion: str = Field(..., max_length=500)
    detalle: Optional[str] = None
    camion_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    numero_comprobante: Optional[str] = Field(None, max_length=100)
    tipo_comprobante: Optional[str] = Field(None, max_length=50)
    comprobante_url: Optional[str] = Field(None, max_length=500)
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    estado: Optional[Literal["completado", "pendiente", "anulado"]] = "completado"
    notas: Optional[str] = None


class MovimientoFinancieroCreate(MovimientoFinancieroBase):
    """Schema para crear movimiento"""
    pass


class MovimientoFinancieroUpdate(BaseModel):
    """Schema para actualizar movimiento"""
    categoria_id: Optional[UUID] = None
    fecha: Optional[date] = None
    monto: Optional[Decimal] = Field(None, gt=0)
    descripcion: Optional[str] = Field(None, max_length=500)
    detalle: Optional[str] = None
    camion_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    numero_comprobante: Optional[str] = Field(None, max_length=100)
    tipo_comprobante: Optional[str] = Field(None, max_length=50)
    comprobante_url: Optional[str] = Field(None, max_length=500)
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    estado: Optional[Literal["completado", "pendiente", "anulado"]] = None
    notas: Optional[str] = None


class MovimientoFinancieroSchema(MovimientoFinancieroBase):
    """Schema de respuesta de movimiento"""
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    # Datos relacionados
    categoria_nombre: Optional[str] = None
    camion_identificador: Optional[str] = None
    empresa_nombre: Optional[str] = None
    creador_nombre: Optional[str] = None

    model_config = {"from_attributes": True}


# =============================================
# CUENTAS BANCARIAS
# =============================================

class CuentaBancariaBase(BaseModel):
    """Schema base de CuentaBancaria"""
    nombre: str = Field(..., max_length=100)
    banco: str = Field(..., max_length=100)
    tipo_cuenta: Optional[str] = Field(None, max_length=50)
    numero_cuenta: Optional[str] = Field(None, max_length=50)
    cbu: Optional[str] = Field(None, max_length=30)
    alias: Optional[str] = Field(None, max_length=50)
    titular: Optional[str] = Field(None, max_length=200)
    cuit_titular: Optional[str] = Field(None, max_length=20)
    saldo_inicial: Optional[Decimal] = 0
    moneda: Optional[str] = Field("ARS", max_length=10)
    notas: Optional[str] = None


class CuentaBancariaCreate(CuentaBancariaBase):
    """Schema para crear cuenta"""
    pass


class CuentaBancariaUpdate(BaseModel):
    """Schema para actualizar cuenta"""
    nombre: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = Field(None, max_length=50)
    numero_cuenta: Optional[str] = Field(None, max_length=50)
    cbu: Optional[str] = Field(None, max_length=30)
    alias: Optional[str] = Field(None, max_length=50)
    titular: Optional[str] = Field(None, max_length=200)
    cuit_titular: Optional[str] = Field(None, max_length=20)
    saldo_inicial: Optional[Decimal] = None
    moneda: Optional[str] = Field(None, max_length=10)
    activo: Optional[bool] = None
    notas: Optional[str] = None


class CuentaBancariaSchema(CuentaBancariaBase):
    """Schema de respuesta de cuenta"""
    id: UUID
    saldo_actual: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================
# RESUMEN Y ESTADÍSTICAS
# =============================================

class ResumenFinanciero(BaseModel):
    """Resumen financiero para dashboard"""
    total_ingresos: Decimal
    total_egresos: Decimal
    balance: Decimal
    cantidad_ingresos: int
    cantidad_egresos: int


class ResumenPorCategoria(BaseModel):
    """Resumen agrupado por categoría"""
    categoria_id: UUID
    categoria_nombre: str
    tipo: str
    total: Decimal
    cantidad: int
    color: Optional[str] = None
