from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import date

from app.models.servicio import TipoServicioEnum, EstadoServicioEnum
from app.schemas.common import ResponseBase


class RepuestoAsignado(BaseModel):
    """Schema para asignar repuesto a servicio"""

    repuesto_id: UUID
    cantidad: Decimal = Field(..., gt=0)


class ServicioRepuestoSchema(BaseModel):
    """Schema de respuesta para relación servicio-repuesto"""

    id: UUID
    repuesto_id: UUID
    cantidad: Decimal
    precio_unitario: Optional[Decimal]
    subtotal: Optional[Decimal]
    # Información del repuesto (para incluir en respuesta)
    repuesto_nombre: Optional[str] = None
    repuesto_codigo: Optional[str] = None


class ServicioBase(BaseModel):
    """Schema base de Servicio"""

    camion_id: UUID
    fecha: date
    tipo: TipoServicioEnum
    descripcion: str = Field(..., min_length=1)
    kilometraje_servicio: Optional[int] = Field(None, ge=0)
    horometro_servicio: Optional[Decimal] = Field(None, ge=0)
    mecanico: Optional[str] = Field(None, max_length=255)
    costo_mano_obra: Decimal = Field(default=Decimal("0"), ge=0)
    observaciones: Optional[str] = None


class ServicioCreate(ServicioBase):
    """Schema para crear Servicio"""

    estado: EstadoServicioEnum = EstadoServicioEnum.PROGRAMADO
    repuestos: List[RepuestoAsignado] = Field(default_factory=list)


class ServicioUpdate(BaseModel):
    """Schema para actualizar Servicio"""

    fecha: Optional[date] = None
    tipo: Optional[TipoServicioEnum] = None
    descripcion: Optional[str] = Field(None, min_length=1)
    kilometraje_servicio: Optional[int] = Field(None, ge=0)
    horometro_servicio: Optional[Decimal] = Field(None, ge=0)
    mecanico: Optional[str] = Field(None, max_length=255)
    costo_mano_obra: Optional[Decimal] = Field(None, ge=0)
    estado: Optional[EstadoServicioEnum] = None
    observaciones: Optional[str] = None


class ServicioSchema(ResponseBase, ServicioBase):
    """Schema de respuesta de Servicio"""

    costo_total: Decimal
    estado: EstadoServicioEnum
    created_by: UUID
    # Relaciones
    repuestos_utilizados: List[ServicioRepuestoSchema] = Field(default_factory=list)
    # Información del camión (opcional)
    camion_patente: Optional[str] = None


class ServicioConRepuestos(ServicioSchema):
    """Schema extendido con información de repuestos"""

    pass  # Ya tiene repuestos_utilizados en ServicioSchema
