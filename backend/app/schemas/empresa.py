from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime


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
    pass


class EmpresaUpdate(BaseModel):
    """Schema para actualizar Empresa"""
    nombre: Optional[str] = Field(None, max_length=200)
    cuit: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    contacto: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None


class EmpresaSchema(EmpresaBase):
    """Schema de respuesta de Empresa"""
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
