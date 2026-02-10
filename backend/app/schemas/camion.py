from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import date

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
    proximo_servicio_km: Optional[int] = Field(None, ge=0)
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: int = Field(default=10000, ge=1000)


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
    proximo_servicio_km: Optional[int] = Field(None, ge=0)
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: Optional[int] = Field(None, ge=1000)


class CamionSchema(ResponseBase, CamionBase):
    """Schema de respuesta de Camión"""

    kilometraje_actual: int
    horometro_actual: Decimal
    foto: Optional[str]
    activo: bool
    # Campos de servicio
    ultimo_servicio: Optional[date] = None
    ultimo_servicio_km: Optional[int] = None
    proximo_servicio_km: Optional[int] = None
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: Optional[int] = None
    # Campo calculado para alertas
    km_para_proximo_servicio: Optional[int] = None
    requiere_servicio: bool = False


class CamionConsumoStats(BaseModel):
    """Schema para estadísticas de consumo de combustible"""

    camion_id: UUID
    patente: str
    total_litros: Decimal
    total_kilometros: Optional[int]
    promedio_consumo: Optional[Decimal]  # km/litro o horas/litro
    cantidad_suministros: int
