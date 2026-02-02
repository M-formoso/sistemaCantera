from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.models.usuario import RolEnum
from app.schemas.common import ResponseBase


class UsuarioBase(BaseModel):
    """Schema base de Usuario"""

    email: EmailStr
    nombre: str = Field(..., min_length=1, max_length=100)
    rol: RolEnum


class UsuarioCreate(UsuarioBase):
    """Schema para crear Usuario"""

    password: str = Field(..., min_length=8, max_length=100)


class UsuarioUpdate(BaseModel):
    """Schema para actualizar Usuario"""

    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    rol: Optional[RolEnum] = None
    activo: Optional[bool] = None


class UsuarioChangePassword(BaseModel):
    """Schema para cambiar contraseña"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UsuarioSchema(ResponseBase, UsuarioBase):
    """Schema de respuesta de Usuario"""

    activo: bool
    ultimo_acceso: Optional[datetime] = None


class UsuarioInDB(UsuarioSchema):
    """Schema de Usuario con password hash (solo interno)"""

    password_hash: str
