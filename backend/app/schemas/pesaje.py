from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, Union
from decimal import Decimal
from datetime import datetime, date

from app.schemas.common import ResponseBase


class PesajeBase(BaseModel):
    """Schema base de Pesaje"""

    camion_id: UUID

    # Datos del transporte
    acoplado: Optional[str] = Field(None, max_length=20)
    transportista: Optional[str] = Field(None, max_length=100)
    remitente: str = Field(default="LA RUFINA", max_length=100)
    chofer: Optional[str] = Field(None, max_length=100)

    # Datos del producto
    producto: Optional[str] = Field(None, max_length=100)
    numero_guia: Optional[str] = Field(None, max_length=50)

    # Pesos
    peso_tara: Decimal = Field(..., gt=0)
    peso_bruto: Decimal = Field(..., gt=0)

    # Destino
    material: Optional[str] = Field(None, max_length=100)
    cliente_destino: Optional[str] = Field(None, max_length=255)

    # Operación
    operario: Optional[str] = Field(None, max_length=100)

    observaciones: Optional[str] = None

    @field_validator('peso_bruto')
    @classmethod
    def validar_peso_bruto(cls, v, info):
        """Validar que peso bruto sea mayor que tara"""
        if 'peso_tara' in info.data and v <= info.data['peso_tara']:
            raise ValueError('El peso bruto debe ser mayor que el peso tara')
        return v


class PesajeCreate(PesajeBase):
    """Schema para crear Pesaje"""

    fecha: Union[datetime, date, str] = Field(default_factory=datetime.utcnow)

    @field_validator('fecha', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        """Convertir string a datetime si es necesario"""
        if isinstance(v, str):
            try:
                # Intentar parsear como datetime completo
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Intentar parsear como fecha simple (YYYY-MM-DD)
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Formato de fecha inválido')
        return v


class PesajeUpdate(BaseModel):
    """Schema para actualizar Pesaje"""

    camion_id: Optional[UUID] = None
    chofer: Optional[str] = Field(None, max_length=100)
    peso_tara: Optional[Decimal] = Field(None, gt=0)
    peso_bruto: Optional[Decimal] = Field(None, gt=0)
    material: Optional[str] = Field(None, max_length=100)
    cliente_destino: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None


class PesajeSchema(ResponseBase):
    """Schema de respuesta de Pesaje"""

    camion_id: UUID
    numero_pesaje: int
    fecha: datetime
    peso_neto: Decimal
    remito_generado: bool
    created_by: UUID

    # Datos del transporte (todos opcionales en respuesta para compatibilidad)
    acoplado: Optional[str] = None
    transportista: Optional[str] = None
    remitente: Optional[str] = "LA RUFINA"
    chofer: Optional[str] = None

    # Datos del producto
    producto: Optional[str] = None
    numero_guia: Optional[str] = None

    # Pesos
    peso_tara: Decimal
    peso_bruto: Decimal

    # Destino
    material: Optional[str] = None
    cliente_destino: Optional[str] = None

    # Operación
    operario: Optional[str] = None
    observaciones: Optional[str] = None

    # Información del camión (opcional)
    camion_patente: Optional[str] = None
    # Información del creador (opcional)
    operario_nombre: Optional[str] = None


class PesajeStats(BaseModel):
    """Schema para estadísticas de pesajes"""

    total_pesajes: int
    total_toneladas: Decimal
    promedio_peso_neto: Decimal
    material_mas_pesado: Optional[str]
