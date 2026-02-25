"""
Schemas Pydantic para Orden de Entrega
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class EstadoOrdenEntrega(str, Enum):
    pendiente = "pendiente"
    en_proceso = "en_proceso"
    completada = "completada"
    cancelada = "cancelada"


class OrdenEntregaBase(BaseModel):
    """Schema base para orden de entrega"""
    fecha_entrega: date
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None
    material: str
    cantidad_cargas: int = Field(..., gt=0)
    peso_estimado_carga: Optional[Decimal] = None
    solicitante: Optional[str] = None
    contacto_cliente: Optional[str] = None
    telefono_contacto: Optional[str] = None
    direccion_entrega: Optional[str] = None
    observaciones: Optional[str] = None

    @field_validator('cliente_id', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convertir strings vacíos a None para UUIDs"""
        if v == '' or v is None:
            return None
        return v


class OrdenEntregaCreate(OrdenEntregaBase):
    """Schema para crear orden de entrega"""
    pass


class OrdenEntregaUpdate(BaseModel):
    """Schema para actualizar orden de entrega"""
    fecha_entrega: Optional[date] = None
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None
    material: Optional[str] = None
    cantidad_cargas: Optional[int] = Field(None, gt=0)
    peso_estimado_carga: Optional[Decimal] = None
    solicitante: Optional[str] = None
    contacto_cliente: Optional[str] = None
    telefono_contacto: Optional[str] = None
    direccion_entrega: Optional[str] = None
    observaciones: Optional[str] = None
    estado: Optional[EstadoOrdenEntrega] = None


class PesajeResumen(BaseModel):
    """Resumen de pesaje para mostrar en orden"""
    id: UUID
    numero_pesaje: int
    fecha: datetime
    peso_neto: Decimal
    material: Optional[str] = None
    chofer: Optional[str] = None
    patente: Optional[str] = None

    class Config:
        from_attributes = True


class OrdenEntregaSchema(OrdenEntregaBase):
    """Schema completo de orden de entrega"""
    id: UUID
    numero_orden: int
    cargas_entregadas: int
    peso_total_estimado: Optional[Decimal] = None
    peso_total_entregado: Optional[Decimal] = None
    estado: EstadoOrdenEntrega
    created_at: datetime
    updated_at: datetime

    # Campos calculados
    cargas_pendientes: Optional[int] = None
    porcentaje_completado: Optional[float] = None

    # Nombre del cliente (cuando viene de relación)
    cliente_nombre_completo: Optional[str] = None

    class Config:
        from_attributes = True


class OrdenEntregaConPesajes(OrdenEntregaSchema):
    """Schema de orden con lista de pesajes asociados"""
    pesajes: List[PesajeResumen] = []


class OrdenEntregaListItem(BaseModel):
    """Schema resumido para listar órdenes"""
    id: UUID
    numero_orden: int
    fecha_entrega: date
    cliente_nombre: Optional[str] = None
    material: str
    cantidad_cargas: int
    cargas_entregadas: int
    cargas_pendientes: int
    estado: EstadoOrdenEntrega
    solicitante: Optional[str] = None

    class Config:
        from_attributes = True
