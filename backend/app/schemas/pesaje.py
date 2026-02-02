from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.schemas.common import ResponseBase


class PesajeBase(BaseModel):
    """Schema base de Pesaje"""

    camion_id: UUID
    chofer: Optional[str] = Field(None, max_length=100)
    peso_tara: Decimal = Field(..., gt=0)
    peso_bruto: Decimal = Field(..., gt=0)
    material: Optional[str] = Field(None, max_length=100)
    cliente_destino: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None

    @field_validator('peso_bruto')
    @classmethod
    def validar_peso_bruto(cls, v, info):
        """Validar que peso bruto sea mayor que tara"""
        if 'peso_tara' in info.data and v <= info.data['peso_tara']:
            raise ValueError('El peso bruto debe ser mayor que el peso tara')
        return v


class PesajeCreate(PesajeBase):
    """Schema para crear Pesaje"""

    fecha: datetime = Field(default_factory=datetime.utcnow)


class PesajeUpdate(BaseModel):
    """Schema para actualizar Pesaje"""

    camion_id: Optional[UUID] = None
    chofer: Optional[str] = Field(None, max_length=100)
    peso_tara: Optional[Decimal] = Field(None, gt=0)
    peso_bruto: Optional[Decimal] = Field(None, gt=0)
    material: Optional[str] = Field(None, max_length=100)
    cliente_destino: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None


class PesajeSchema(ResponseBase, PesajeBase):
    """Schema de respuesta de Pesaje"""

    numero_pesaje: int
    fecha: datetime
    peso_neto: Decimal
    remito_generado: bool
    created_by: UUID
    # Información del camión (opcional)
    camion_patente: Optional[str] = None


class PesajeStats(BaseModel):
    """Schema para estadísticas de pesajes"""

    total_pesajes: int
    total_toneladas: Decimal
    promedio_peso_neto: Decimal
    material_mas_pesado: Optional[str]
