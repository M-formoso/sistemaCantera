from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal

from app.models.camion import TipoCamionEnum, EstadoCamionEnum
from app.schemas.common import ResponseBase


class CamionBase(BaseModel):
    """Schema base de Camión"""

    patente: str = Field(..., min_length=1, max_length=20)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    año: Optional[int] = Field(None, ge=1900, le=2100)
    tipo: TipoCamionEnum = TipoCamionEnum.VOLCADOR
    estado: EstadoCamionEnum = EstadoCamionEnum.OPERATIVO
    chofer_habitual: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class CamionCreate(CamionBase):
    """Schema para crear Camión"""

    kilometraje_actual: int = Field(default=0, ge=0)
    horometro_actual: Decimal = Field(default=Decimal("0"), ge=0)
    foto: Optional[str] = Field(None, max_length=500)


class CamionUpdate(BaseModel):
    """Schema para actualizar Camión"""

    patente: Optional[str] = Field(None, min_length=1, max_length=20)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    año: Optional[int] = Field(None, ge=1900, le=2100)
    tipo: Optional[TipoCamionEnum] = None
    estado: Optional[EstadoCamionEnum] = None
    kilometraje_actual: Optional[int] = Field(None, ge=0)
    horometro_actual: Optional[Decimal] = Field(None, ge=0)
    chofer_habitual: Optional[str] = Field(None, max_length=100)
    foto: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None
    activo: Optional[bool] = None


class CamionSchema(ResponseBase, CamionBase):
    """Schema de respuesta de Camión"""

    kilometraje_actual: int
    horometro_actual: Decimal
    foto: Optional[str]
    activo: bool


class CamionConsumoStats(BaseModel):
    """Schema para estadísticas de consumo de combustible"""

    camion_id: UUID
    patente: str
    total_litros: Decimal
    total_kilometros: Optional[int]
    promedio_consumo: Optional[Decimal]  # km/litro o horas/litro
    cantidad_suministros: int
