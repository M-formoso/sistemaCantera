"""
Schemas para precios por cliente y material
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from app.schemas.common import ResponseBase
from app.schemas.pesaje import MATERIALES_DISPONIBLES


class PrecioClienteBase(BaseModel):
    """Schema base para precio de cliente"""
    material: str = Field(..., max_length=100, description="Material (debe estar en MATERIALES_DISPONIBLES)")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio por tonelada (o por m³ si usa conversión)")
    factor_conversion_m3: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Factor de conversión a m³. Ej: 1.66 para 0-20, 1.5 para 6-19. Si está definido, el precio es por m³"
    )


class PrecioClienteCreate(PrecioClienteBase):
    """Schema para crear precio de cliente"""
    cliente_id: UUID


class PrecioClienteUpdate(BaseModel):
    """Schema para actualizar precio de cliente"""
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    factor_conversion_m3: Optional[Decimal] = Field(None, ge=0)


class PrecioClienteSchema(ResponseBase, PrecioClienteBase):
    """Schema de respuesta de precio de cliente"""
    cliente_id: UUID
    cliente_nombre: Optional[str] = None


class PrecioClienteConCalculo(PrecioClienteSchema):
    """Schema con cálculo de ejemplo para mostrar al usuario"""
    ejemplo_1000kg: Optional[dict] = None  # Cálculo ejemplo con 1000kg


class PreciosClienteResumen(BaseModel):
    """Resumen de precios de un cliente"""
    cliente_id: UUID
    cliente_nombre: str
    precios: List[PrecioClienteSchema]
    usa_conversion_m3: bool = False  # True si algún precio tiene factor_conversion_m3


class CalculoPrecio(BaseModel):
    """Resultado de calcular precio para un peso dado"""
    peso_neto_kg: float
    peso_toneladas: float
    material: str
    precio_unitario: float
    factor_conversion_m3: Optional[float] = None
    cantidad_facturada: float  # Toneladas o m³
    unidad: str  # "tn" o "m3"
    importe: float


class MaterialesDisponiblesResponse(BaseModel):
    """Lista de materiales disponibles"""
    materiales: List[str] = MATERIALES_DISPONIBLES
