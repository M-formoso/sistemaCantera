from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID
from typing import Optional, Union, Literal
from decimal import Decimal
from datetime import datetime, date

from app.schemas.common import ResponseBase


# Materiales disponibles
MATERIALES_DISPONIBLES = [
    "10.30",
    "6.19",
    "0.20",
    "6.12",
    "relleno",
    "binder",
    "0.6"
]


class PesajeBase(BaseModel):
    """Schema base de Pesaje"""

    # Tipo de entrega
    tipo_entrega: Literal["propio", "transportista"] = "propio"

    # Camión propio (requerido si tipo_entrega = "propio")
    camion_id: Optional[UUID] = None

    # Transportista externo (requerido si tipo_entrega = "transportista")
    transportista_id: Optional[UUID] = None
    patente_externa: Optional[str] = Field(None, max_length=20)
    transportista: Optional[str] = Field(None, max_length=100)  # Nombre libre si no está en el sistema

    # Cliente destino
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = Field(None, max_length=255)  # Nombre libre si no está en el sistema

    # Datos del transporte
    acoplado: Optional[str] = Field(None, max_length=20)
    chofer: Optional[str] = Field(None, max_length=100)

    # Pesos
    peso_tara: Decimal = Field(..., gt=0)
    peso_bruto: Decimal = Field(..., gt=0)

    # Material
    material: Optional[str] = Field(None, max_length=100)

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

    @model_validator(mode='after')
    def validar_tipo_entrega(self):
        """Validar que se proporcionen los datos según el tipo de entrega"""
        if self.tipo_entrega == "propio" and not self.camion_id:
            raise ValueError('Debe seleccionar un camión propio')
        if self.tipo_entrega == "transportista":
            if not self.transportista_id and not self.transportista:
                raise ValueError('Debe seleccionar o ingresar un transportista')
            if not self.patente_externa:
                raise ValueError('Debe ingresar la patente del camión externo')
        return self


class PesajeCreate(PesajeBase):
    """Schema para crear Pesaje"""

    fecha: Union[datetime, date, str] = Field(default_factory=datetime.utcnow)

    @field_validator('fecha', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        """Convertir string a datetime si es necesario"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Formato de fecha inválido')
        return v


class PesajeUpdate(BaseModel):
    """Schema para actualizar Pesaje"""

    tipo_entrega: Optional[Literal["propio", "transportista"]] = None
    camion_id: Optional[UUID] = None
    transportista_id: Optional[UUID] = None
    patente_externa: Optional[str] = Field(None, max_length=20)
    transportista: Optional[str] = Field(None, max_length=100)
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = Field(None, max_length=255)
    chofer: Optional[str] = Field(None, max_length=100)
    peso_tara: Optional[Decimal] = Field(None, gt=0)
    peso_bruto: Optional[Decimal] = Field(None, gt=0)
    material: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None


class PesajeSchema(ResponseBase):
    """Schema de respuesta de Pesaje"""

    numero_pesaje: int
    fecha: datetime
    tipo_entrega: str = "propio"

    # Camión propio
    camion_id: Optional[UUID] = None
    camion_patente: Optional[str] = None

    # Transportista externo
    transportista_id: Optional[UUID] = None
    transportista_nombre: Optional[str] = None
    patente_externa: Optional[str] = None
    transportista: Optional[str] = None

    # Cliente
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None

    # Datos del transporte
    acoplado: Optional[str] = None
    chofer: Optional[str] = None

    # Pesos
    peso_tara: Decimal
    peso_bruto: Decimal
    peso_neto: Decimal

    # Material
    material: Optional[str] = None

    # Operación
    operario: Optional[str] = None
    observaciones: Optional[str] = None

    remito_generado: bool
    created_by: UUID


class PesajeStats(BaseModel):
    """Schema para estadísticas de pesajes"""

    total_pesajes: int
    total_toneladas: Decimal
    promedio_peso_neto: Decimal
    material_mas_pesado: Optional[str]


class MaterialesDisponibles(BaseModel):
    """Lista de materiales disponibles"""
    materiales: list[str] = MATERIALES_DISPONIBLES
