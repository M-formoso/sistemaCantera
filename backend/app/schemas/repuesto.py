from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal

from app.schemas.common import ResponseBase


class RepuestoBase(BaseModel):
    """Schema base de Repuesto"""

    codigo: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=255)
    categoria: Optional[str] = Field(None, max_length=100)
    unidad: str = Field(default="unidades", max_length=20)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    proveedor: Optional[str] = Field(None, max_length=255)
    ubicacion_deposito: Optional[str] = Field(None, max_length=100)
    camion_id: Optional[UUID] = Field(None, description="ID del equipo asignado (legacy)")
    equipos_ids: Optional[List[UUID]] = Field(None, description="IDs de equipos asignados (N:N)")


class RepuestoCreate(RepuestoBase):
    """Schema para crear Repuesto"""

    stock_actual: Decimal = Field(default=Decimal("0"), ge=0)
    stock_minimo: Decimal = Field(default=Decimal("0"), ge=0)


class RepuestoUpdate(BaseModel):
    """Schema para actualizar Repuesto"""

    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    categoria: Optional[str] = Field(None, max_length=100)
    stock_actual: Optional[Decimal] = Field(None, ge=0)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    unidad: Optional[str] = Field(None, max_length=20)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    proveedor: Optional[str] = Field(None, max_length=255)
    ubicacion_deposito: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None
    camion_id: Optional[UUID] = Field(None, description="ID del equipo asignado")


class RepuestoSchema(ResponseBase, RepuestoBase):
    """Schema de respuesta de Repuesto"""

    stock_actual: Decimal
    stock_minimo: Decimal
    activo: bool
    camion_patente: Optional[str] = None  # Patente del equipo asignado (legacy)
    asignado_a_equipo: Optional[bool] = None  # Si está asignado al equipo consultado
    equipos_ids: Optional[List[UUID]] = None  # IDs de equipos asignados (N:N)


class EquipoAsignado(BaseModel):
    """Schema para equipo asignado a un repuesto"""

    id: UUID
    identificador: str
    categoria: str
    legacy: bool = False


class RepuestoEquiposUpdate(BaseModel):
    """Schema para actualizar equipos asignados a un repuesto"""

    equipos_ids: List[UUID] = Field(..., description="Lista de IDs de equipos a asignar")


class RepuestoStockBajo(BaseModel):
    """Schema para repuestos con stock bajo"""

    id: UUID
    codigo: Optional[str]
    nombre: str
    stock_actual: Decimal
    stock_minimo: Decimal
    unidad: str
    diferencia: Decimal


class RepuestoMovimiento(BaseModel):
    """Schema para movimiento de stock"""

    repuesto_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    tipo_movimiento: str  # 'ingreso' o 'egreso'
    observaciones: Optional[str] = None
