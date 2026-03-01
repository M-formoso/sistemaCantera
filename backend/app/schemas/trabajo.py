"""
Schemas para Trabajos/Reparaciones
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime


class RepuestoAsignado(BaseModel):
    """Repuesto a usar en el trabajo"""
    repuesto_id: UUID
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)


class TrabajoCreate(BaseModel):
    """Schema para crear un trabajo"""
    camion_id: UUID
    fecha: date
    descripcion: str = Field(..., min_length=3)
    responsable: Optional[str] = Field(None, max_length=100)
    costo_mano_obra: Decimal = Field(default=Decimal("0"), ge=0)
    observaciones: Optional[str] = None
    repuestos: List[RepuestoAsignado] = []


class TrabajoUpdate(BaseModel):
    """Schema para actualizar un trabajo"""
    fecha: Optional[date] = None
    descripcion: Optional[str] = Field(None, min_length=3)
    responsable: Optional[str] = Field(None, max_length=100)
    costo_mano_obra: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class RepuestoUtilizado(BaseModel):
    """Repuesto utilizado en el trabajo"""
    id: UUID
    repuesto_id: UUID
    nombre: str
    codigo: Optional[str]
    cantidad: Decimal
    precio_unitario: Optional[Decimal]
    subtotal: Optional[Decimal]

    class Config:
        from_attributes = True


class TrabajoSchema(BaseModel):
    """Schema de respuesta de trabajo"""
    id: UUID
    camion_id: UUID
    fecha: date
    descripcion: str
    responsable: Optional[str]
    costo_mano_obra: Decimal
    costo_total: Decimal
    observaciones: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    # Datos relacionados
    camion_identificador: Optional[str] = None
    usuario_nombre: Optional[str] = None
    repuestos: List[RepuestoUtilizado] = []

    class Config:
        from_attributes = True
