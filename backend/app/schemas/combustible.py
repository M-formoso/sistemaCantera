from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.schemas.common import ResponseBase


# ==================== CISTERNA ====================

class CisternaConfig(BaseModel):
    """Schema para configuración de cisterna"""

    capacidad_total: Decimal = Field(..., gt=0)
    nivel_alerta: Decimal = Field(..., gt=0)


class CisternaSchema(ResponseBase):
    """Schema de respuesta de Cisterna"""

    capacidad_total: Decimal
    nivel_actual: Decimal
    nivel_alerta: Decimal
    porcentaje_actual: Optional[Decimal] = None
    esta_bajo: bool = False


class CisternaUpdate(BaseModel):
    """Schema para actualizar configuración de cisterna"""

    capacidad_total: Optional[Decimal] = Field(None, gt=0)
    nivel_actual: Optional[Decimal] = Field(None, ge=0)
    nivel_alerta: Optional[Decimal] = Field(None, gt=0)


# ==================== CARGAS DE CISTERNA ====================

class CargaCisternaBase(BaseModel):
    """Schema base de Carga de Cisterna"""

    litros: Decimal = Field(..., gt=0)
    proveedor: Optional[str] = Field(None, max_length=255)
    costo_total: Optional[Decimal] = Field(None, ge=0)
    numero_factura: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class CargaCisternaCreate(CargaCisternaBase):
    """Schema para crear Carga de Cisterna"""

    fecha: datetime = Field(default_factory=datetime.utcnow)


class CargaCisternaUpdate(BaseModel):
    """Schema para actualizar Carga de Cisterna"""

    litros: Optional[Decimal] = Field(None, gt=0)
    proveedor: Optional[str] = Field(None, max_length=255)
    costo_total: Optional[Decimal] = Field(None, ge=0)
    numero_factura: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class CargaCisternaSchema(ResponseBase, CargaCisternaBase):
    """Schema de respuesta de Carga de Cisterna"""

    fecha: datetime
    costo_por_litro: Optional[Decimal]
    created_by: UUID


# ==================== SUMINISTROS A CAMIONES ====================

class SuministroCombustibleBase(BaseModel):
    """Schema base de Suministro de Combustible"""

    camion_id: UUID
    litros: Decimal = Field(..., gt=0)
    chofer: Optional[str] = Field(None, max_length=100)
    kilometraje: Optional[int] = Field(None, ge=0)
    horometro: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class SuministroCombustibleCreate(SuministroCombustibleBase):
    """Schema para crear Suministro de Combustible"""

    fecha: datetime = Field(default_factory=datetime.utcnow)


class SuministroCombustibleUpdate(BaseModel):
    """Schema para actualizar Suministro de Combustible"""

    litros: Optional[Decimal] = Field(None, gt=0)
    chofer: Optional[str] = Field(None, max_length=100)
    kilometraje: Optional[int] = Field(None, ge=0)
    horometro: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class SuministroCombustibleSchema(ResponseBase, SuministroCombustibleBase):
    """Schema de respuesta de Suministro de Combustible"""

    fecha: datetime
    created_by: UUID
    # Información del camión (opcional)
    camion_patente: Optional[str] = None


# ==================== ESTADÍSTICAS ====================

class ConsumoStats(BaseModel):
    """Schema para estadísticas de consumo"""

    total_litros_suministrados: Decimal
    total_cargas_cisterna: int
    total_suministros: int
    promedio_por_suministro: Decimal
    nivel_actual_cisterna: Decimal
