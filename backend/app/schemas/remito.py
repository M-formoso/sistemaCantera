from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import date

from app.schemas.common import ResponseBase


class RemitoBase(BaseModel):
    """Schema base de Remito"""

    cliente: str = Field(..., min_length=1, max_length=255)
    producto: str = Field(..., min_length=1, max_length=100)
    peso_neto: Decimal = Field(..., gt=0)
    camion_patente: Optional[str] = Field(None, max_length=20)
    chofer: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class RemitoCreate(RemitoBase):
    """Schema para crear Remito manualmente"""

    fecha: date = Field(default_factory=date.today)
    pesaje_id: Optional[UUID] = None


class RemitoFromPesaje(BaseModel):
    """Schema para generar remito desde pesaje"""

    pesaje_id: UUID


class RemitoUpdate(BaseModel):
    """Schema para actualizar Remito"""

    cliente: Optional[str] = Field(None, min_length=1, max_length=255)
    producto: Optional[str] = Field(None, min_length=1, max_length=100)
    peso_neto: Optional[Decimal] = Field(None, gt=0)
    camion_patente: Optional[str] = Field(None, max_length=20)
    chofer: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class RemitoSchema(ResponseBase, RemitoBase):
    """Schema de respuesta de Remito"""

    numero_remito: int
    fecha: date
    pesaje_id: Optional[UUID]
    pdf_url: Optional[str]
    enviado_email: bool
    created_by: UUID


class RemitoEmailRequest(BaseModel):
    """Schema para enviar remito por email"""

    email_destino: str = Field(..., min_length=1)
    mensaje_adicional: Optional[str] = None
