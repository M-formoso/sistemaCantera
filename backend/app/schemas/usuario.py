from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.models.usuario import RolEnum
from app.schemas.common import ResponseBase


class PermisosModulos(BaseModel):
    """Permisos por módulo"""
    permiso_dashboard: bool = True
    permiso_camiones: bool = True
    permiso_empresas: bool = True
    permiso_repuestos: bool = True
    permiso_pesajes: bool = True
    permiso_combustible: bool = True
    permiso_finanzas: bool = True
    permiso_usuarios: bool = False
    permiso_reportes: bool = True


class UsuarioBase(BaseModel):
    """Schema base de Usuario"""

    email: EmailStr
    nombre: str = Field(..., min_length=1, max_length=100)
    rol: RolEnum


class UsuarioCreate(UsuarioBase):
    """Schema para crear Usuario"""

    password: str = Field(..., min_length=8, max_length=100)
    # Permisos por módulo
    permiso_dashboard: bool = True
    permiso_camiones: bool = True
    permiso_empresas: bool = True
    permiso_repuestos: bool = True
    permiso_pesajes: bool = True
    permiso_combustible: bool = True
    permiso_finanzas: bool = True
    permiso_usuarios: bool = False
    permiso_reportes: bool = True


class UsuarioUpdate(BaseModel):
    """Schema para actualizar Usuario"""

    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    rol: Optional[RolEnum] = None
    activo: Optional[bool] = None
    # Permisos por módulo
    permiso_dashboard: Optional[bool] = None
    permiso_camiones: Optional[bool] = None
    permiso_empresas: Optional[bool] = None
    permiso_repuestos: Optional[bool] = None
    permiso_pesajes: Optional[bool] = None
    permiso_combustible: Optional[bool] = None
    permiso_finanzas: Optional[bool] = None
    permiso_usuarios: Optional[bool] = None
    permiso_reportes: Optional[bool] = None


class UsuarioChangePassword(BaseModel):
    """Schema para cambiar contraseña"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UsuarioSchema(ResponseBase, UsuarioBase):
    """Schema de respuesta de Usuario"""

    activo: bool
    ultimo_acceso: Optional[datetime] = None
    # Permisos por módulo - Optional para retrocompatibilidad con BD sin columnas
    permiso_dashboard: Optional[bool] = True
    permiso_camiones: Optional[bool] = True
    permiso_empresas: Optional[bool] = True
    permiso_repuestos: Optional[bool] = True
    permiso_pesajes: Optional[bool] = True
    permiso_combustible: Optional[bool] = True
    permiso_finanzas: Optional[bool] = True
    permiso_usuarios: Optional[bool] = True  # True por defecto para admins existentes
    permiso_reportes: Optional[bool] = True


class UsuarioInDB(UsuarioSchema):
    """Schema de Usuario con password hash (solo interno)"""

    password_hash: str
