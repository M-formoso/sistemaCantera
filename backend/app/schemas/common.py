from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Generic, TypeVar, List

T = TypeVar('T')


class BaseSchema(BaseModel):
    """Schema base con configuración común"""

    model_config = ConfigDict(from_attributes=True)


class ResponseBase(BaseSchema):
    """Schema base para respuestas"""

    id: UUID
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Schema para mensajes de respuesta simples"""

    message: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema para respuestas paginadas"""

    items: List[T]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
