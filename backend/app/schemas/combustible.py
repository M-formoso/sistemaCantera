from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.schemas.common import ResponseBase


# ==================== CISTERNA ====================

class CisternaCreate(BaseModel):
    """Schema para crear cisterna"""

    nombre: str = Field(..., max_length=100)
    capacidad_total: Decimal = Field(..., gt=0)
    nivel_minimo: Decimal = Field(..., gt=0)
    cisterna_origen_id: Optional[UUID] = None  # Si se abastece de otra cisterna


class CisternaConfig(BaseModel):
    """Schema para configuración de cisterna (legacy)"""

    capacidad_total: Decimal = Field(..., gt=0)
    nivel_minimo: Decimal = Field(..., gt=0)


class CisternaSchema(ResponseBase):
    """Schema de respuesta de Cisterna"""

    nombre: str
    capacidad_total: Decimal
    nivel_actual: Decimal
    nivel_minimo: Decimal
    porcentaje_actual: Optional[Decimal] = None
    esta_bajo: bool = False
    cisterna_origen_id: Optional[UUID] = None
    cisterna_origen_nombre: Optional[str] = None  # Nombre de la cisterna de origen


class CisternaUpdate(BaseModel):
    """Schema para actualizar configuración de cisterna"""

    nombre: Optional[str] = Field(None, max_length=100)
    capacidad_total: Optional[Decimal] = Field(None, gt=0)
    nivel_actual: Optional[Decimal] = Field(None, ge=0)
    nivel_minimo: Optional[Decimal] = Field(None, gt=0)
    cisterna_origen_id: Optional[UUID] = None  # Si se abastece de otra cisterna


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

    cisterna_id: UUID
    fecha: str  # Acepta fecha como string, se convierte en el servicio


class CargaCisternaUpdate(BaseModel):
    """Schema para actualizar Carga de Cisterna"""

    litros: Optional[Decimal] = Field(None, gt=0)
    proveedor: Optional[str] = Field(None, max_length=255)
    costo_total: Optional[Decimal] = Field(None, ge=0)
    numero_factura: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class CargaCisternaSchema(ResponseBase, CargaCisternaBase):
    """Schema de respuesta de Carga de Cisterna"""

    cisterna_id: Optional[UUID] = None
    cisterna_nombre: Optional[str] = None
    fecha: datetime
    costo_por_litro: Optional[Decimal]
    created_by: UUID


# ==================== SUMINISTROS A CAMIONES ====================

class SuministroCombustibleBase(BaseModel):
    """Schema base de Suministro de Combustible"""

    camion_id: UUID
    litros: Decimal = Field(..., gt=0)
    chofer: Optional[str] = Field(None, max_length=100)
    kilometraje_actual: Optional[int] = Field(None, ge=0)
    horometro: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class SuministroCombustibleCreate(SuministroCombustibleBase):
    """Schema para crear Suministro de Combustible"""

    cisterna_id: UUID
    fecha: str  # Acepta fecha como string, se convierte en el servicio


class SuministroCombustibleUpdate(BaseModel):
    """Schema para actualizar Suministro de Combustible"""

    litros: Optional[Decimal] = Field(None, gt=0)
    chofer: Optional[str] = Field(None, max_length=100)
    kilometraje: Optional[int] = Field(None, ge=0)
    horometro: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class SuministroCombustibleSchema(ResponseBase):
    """Schema de respuesta de Suministro de Combustible"""

    camion_id: UUID
    litros: Decimal
    chofer: Optional[str] = None
    kilometraje_actual: Optional[int] = Field(None, validation_alias="kilometraje")
    horometro: Optional[Decimal] = None
    observaciones: Optional[str] = None
    cisterna_id: Optional[UUID] = None
    cisterna_nombre: Optional[str] = None
    fecha: datetime
    created_by: UUID
    # Información del camión (opcional)
    camion_patente: Optional[str] = None
    # Información del usuario que creó el suministro
    usuario_nombre: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


# ==================== ESTADÍSTICAS ====================

class ConsumoStats(BaseModel):
    """Schema para estadísticas de consumo"""

    total_litros_suministrados: Decimal
    total_cargas_cisterna: int
    total_suministros: int
    promedio_por_suministro: Decimal
    nivel_actual_cisterna: Decimal


# ==================== TRANSFERENCIAS ENTRE CISTERNAS ====================

class TransferenciaCisternaCreate(BaseModel):
    """Schema para crear transferencia entre cisternas"""

    cisterna_origen_id: UUID
    cisterna_destino_id: UUID
    litros: Decimal = Field(..., gt=0)
    fecha: str  # Acepta fecha como string
    observaciones: Optional[str] = None


class TransferenciaCisternaSchema(ResponseBase):
    """Schema de respuesta de Transferencia entre Cisternas"""

    cisterna_origen_id: UUID
    cisterna_destino_id: UUID
    litros: Decimal
    fecha: datetime
    observaciones: Optional[str] = None
    created_by: UUID
    # Info adicional
    cisterna_origen_nombre: Optional[str] = None
    cisterna_destino_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
