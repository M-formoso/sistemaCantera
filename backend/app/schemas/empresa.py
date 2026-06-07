from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from uuid import UUID
from datetime import datetime


# ============== CAMION CLIENTE ==============

class CamionClienteBase(BaseModel):
    """Schema base para camión de cliente"""
    patente: str = Field(..., max_length=20)
    descripcion: Optional[str] = Field(None, max_length=100)
    chofer_habitual: Optional[str] = Field(None, max_length=100)


class CamionClienteCreate(CamionClienteBase):
    """Schema para crear camión de cliente"""
    pass


class CamionClienteUpdate(BaseModel):
    """Schema para actualizar camión de cliente"""
    patente: Optional[str] = Field(None, max_length=20)
    descripcion: Optional[str] = Field(None, max_length=100)
    chofer_habitual: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None


class CamionClienteSchema(CamionClienteBase):
    """Schema de respuesta de camión de cliente"""
    id: UUID
    cliente_id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============== EMPRESA ==============

class EmpresaBase(BaseModel):
    """Schema base de Empresa"""
    nombre: str = Field(..., max_length=200)
    tipo: Literal["cliente", "transportista"]
    cuit: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    contacto: Optional[str] = Field(None, max_length=100)


class EmpresaCreate(EmpresaBase):
    """Schema para crear Empresa"""
    lista_precio_id: Optional[UUID] = None
    alicuota_iva: Optional[float] = Field(21, ge=0, le=100)
    iva_en_total: Optional[bool] = False


class EmpresaUpdate(BaseModel):
    """Schema para actualizar Empresa"""
    nombre: Optional[str] = Field(None, max_length=200)
    cuit: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    contacto: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None
    lista_precio_id: Optional[UUID] = None
    alicuota_iva: Optional[float] = Field(None, ge=0, le=100)
    iva_en_total: Optional[bool] = None


class EmpresaSchema(EmpresaBase):
    """Schema de respuesta de Empresa"""
    id: UUID
    activo: bool
    saldo_cuenta_corriente: Optional[float] = 0
    alicuota_iva: Optional[float] = 21
    iva_en_total: Optional[bool] = False
    lista_precio_id: Optional[UUID] = None
    lista_precio_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmpresaConCamionesSchema(EmpresaSchema):
    """Schema de empresa con sus camiones"""
    camiones: List[CamionClienteSchema] = []
