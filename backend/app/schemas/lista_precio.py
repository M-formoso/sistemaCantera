"""
Schemas para Listas de Precios
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from app.schemas.pesaje import MATERIALES_DISPONIBLES


# ============== ITEM DE LISTA ==============

class ItemListaPrecioBase(BaseModel):
    """Schema base para item de lista de precios"""
    material: str = Field(..., max_length=100, description="Material")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio por tonelada (o por m³ si usa conversión)")
    factor_conversion_m3: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Factor de conversión a m³. Ej: 1.66 para 0-20, 1.5 para 6-19"
    )


class ItemListaPrecioCreate(ItemListaPrecioBase):
    """Schema para crear item"""
    pass


class ItemListaPrecioUpdate(BaseModel):
    """Schema para actualizar item"""
    material: Optional[str] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    factor_conversion_m3: Optional[Decimal] = Field(None, ge=0)


class ItemListaPrecioSchema(ItemListaPrecioBase):
    """Schema de respuesta para item"""
    id: UUID
    lista_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== LISTA DE PRECIOS ==============

class ListaPrecioBase(BaseModel):
    """Schema base para lista de precios"""
    nombre: str = Field(..., max_length=100, description="Nombre de la lista")
    descripcion: Optional[str] = Field(None, description="Descripción de la lista")
    activo: bool = Field(True, description="Si la lista está activa")


class ListaPrecioCreate(ListaPrecioBase):
    """Schema para crear lista con items"""
    items: Optional[List[ItemListaPrecioCreate]] = Field(
        default=[],
        description="Items de la lista (materiales con precios)"
    )


class ListaPrecioUpdate(BaseModel):
    """Schema para actualizar lista"""
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class ListaPrecioSchema(ListaPrecioBase):
    """Schema de respuesta para lista"""
    id: UUID
    items: List[ItemListaPrecioSchema] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListaPrecioResumen(BaseModel):
    """Schema resumido para selectores (sin items)"""
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    cantidad_items: int = 0

    class Config:
        from_attributes = True


# ============== OPERACIONES BATCH ==============

class ItemBatchUpdate(BaseModel):
    """Item para actualización batch"""
    material: str
    precio_unitario: Decimal = Field(..., ge=0)
    factor_conversion_m3: Optional[Decimal] = Field(None, ge=0)


class ListaPrecioItemsBatch(BaseModel):
    """Schema para actualizar todos los items de una lista"""
    items: List[ItemBatchUpdate] = Field(
        ...,
        description="Lista de items a crear/actualizar. Los items existentes no incluidos serán eliminados."
    )


# ============== CÁLCULO DE PRECIO ==============

class CalculoPrecioLista(BaseModel):
    """Resultado de calcular precio usando una lista"""
    precio_encontrado: bool
    mensaje: Optional[str] = None
    lista_id: Optional[UUID] = None
    lista_nombre: Optional[str] = None
    material: Optional[str] = None
    peso_toneladas: Optional[float] = None
    cantidad_facturada: Optional[float] = None
    unidad: Optional[str] = None  # 'tn' o 'm3'
    precio_unitario: Optional[float] = None
    factor_conversion: Optional[float] = None
    importe: Optional[float] = None


# ============== OTROS ==============

class MaterialesDisponiblesResponse(BaseModel):
    """Lista de materiales disponibles"""
    materiales: List[str] = MATERIALES_DISPONIBLES
