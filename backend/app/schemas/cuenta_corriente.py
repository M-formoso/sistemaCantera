"""
Schemas para Cuenta Corriente
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime


class MovimientoCCBase(BaseModel):
    """Schema base de movimiento de cuenta corriente"""
    fecha: date
    descripcion: str = Field(..., max_length=500)
    notas: Optional[str] = None


class CargoCreate(MovimientoCCBase):
    """Schema para crear un cargo manual"""
    empresa_id: UUID
    monto: Decimal = Field(..., gt=0, description="Monto NETO (sin IVA)")
    alicuota_iva: Optional[Decimal] = Field(None, ge=0, le=100)


class PagoCreate(BaseModel):
    """Schema para registrar un pago.

    monto = total c/IVA. El sistema lo descompone en neto + IVA usando alicuota_iva
    (si no viene, toma la del cliente).
    """
    empresa_id: UUID
    monto: Decimal = Field(..., gt=0, description="Monto TOTAL c/IVA recibido")
    alicuota_iva: Optional[Decimal] = Field(None, ge=0, le=100)
    fecha: date
    descripcion: str = Field(..., max_length=500)
    metodo_pago: Optional[str] = Field(None, max_length=50)
    numero_comprobante: Optional[str] = Field(None, max_length=100)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    banco: Optional[str] = Field(None, max_length=100)
    notas: Optional[str] = None
    registrar_ingreso: bool = True  # Si registrar en finanzas


class AjusteCreate(BaseModel):
    """Schema para crear un ajuste"""
    empresa_id: UUID
    monto: Decimal = Field(..., gt=0)
    es_credito: bool  # True = nota de crédito, False = nota de débito
    fecha: date
    descripcion: str = Field(..., max_length=500)
    notas: Optional[str] = None
    alicuota_iva: Optional[Decimal] = Field(None, ge=0, le=100)


class MovimientoCCSchema(BaseModel):
    """Schema de respuesta de movimiento"""
    id: UUID
    empresa_id: UUID
    tipo: str
    monto: Decimal  # TOTAL c/IVA
    monto_neto: Optional[Decimal] = None
    monto_iva: Optional[Decimal] = None
    alicuota_iva: Optional[Decimal] = None
    saldo_anterior: Decimal
    saldo_posterior: Decimal
    fecha: date
    descripcion: str
    detalle: Optional[str] = None
    pesaje_id: Optional[UUID] = None
    movimiento_financiero_id: Optional[UUID] = None
    numero_comprobante: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    banco: Optional[str] = None
    anulado: bool
    created_at: datetime
    notas: Optional[str] = None

    # Datos relacionados
    empresa_nombre: Optional[str] = None

    # Cantidades del pesaje asociado (solo para cargos generados por pesajes)
    material: Optional[str] = None
    toneladas: Optional[float] = None
    metros_cubicos: Optional[float] = None
    factor_conversion_m3: Optional[float] = None

    class Config:
        from_attributes = True


class ResumenCuentaCorriente(BaseModel):
    """Resumen de cuenta corriente de un cliente"""
    empresa_id: str
    empresa_nombre: str
    saldo_actual: float
    total_cargos: float
    total_pagos: float
    cantidad_movimientos: int


class ClienteConDeuda(BaseModel):
    """Cliente con saldo pendiente"""
    id: str
    nombre: str
    cuit: Optional[str] = None
    saldo: float


class AnularMovimientoRequest(BaseModel):
    """Request para anular un movimiento"""
    motivo: str = Field(..., min_length=5, max_length=500)


class ActualizarMontoRequest(BaseModel):
    """Request para actualizar el monto NETO de un cargo y/o su alícuota de IVA.

    Si se pasa alicuota_iva, recalcula monto_iva y monto total c/IVA.
    """
    monto: Decimal = Field(..., ge=0, description="Monto NETO (sin IVA)")
    precio_unitario: Optional[Decimal] = Field(None, ge=0)  # Precio por tonelada
    alicuota_iva: Optional[Decimal] = Field(None, ge=0, le=100)


class HistorialMovimientoCCSchema(BaseModel):
    """Schema de respuesta del historial de un movimiento"""
    id: Optional[UUID] = None
    fecha: datetime
    usuario_nombre: str
    accion: str
    detalle: Optional[str] = None

    class Config:
        from_attributes = True
