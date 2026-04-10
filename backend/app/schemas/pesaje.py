from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID
from typing import Optional, Union, Literal, List
from decimal import Decimal
from datetime import datetime, date

from app.schemas.common import ResponseBase
from app.models.base import get_argentina_now


# Materiales disponibles
MATERIALES_DISPONIBLES = [
    "10.30",
    "6.19",
    "0.20",
    "6.12",
    "relleno",
    "binder",
    "0.6",
    "piedra partida",
    "suelo arena",
    "retiro"
]

# Estados de pesaje
ESTADOS_PESAJE = ["pendiente", "completado", "cancelado"]


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

    # Importe
    precio_unitario: Optional[Decimal] = Field(None, ge=0, description="Precio por tonelada")
    flete: Optional[Decimal] = Field(None, ge=0, description="Monto fijo de flete")
    precio_fijo: Optional[Decimal] = Field(None, ge=0, description="Precio fijo por viaje (ignora precio por tonelada)")
    importe_total: Optional[Decimal] = Field(None, ge=0, description="Importe total del pesaje")

    # Orden de entrega
    orden_entrega_id: Optional[UUID] = None

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

    fecha: Union[datetime, date, str] = Field(default_factory=get_argentina_now)

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
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    flete: Optional[Decimal] = Field(None, ge=0)
    precio_fijo: Optional[Decimal] = Field(None, ge=0)
    importe_total: Optional[Decimal] = Field(None, ge=0)
    orden_entrega_id: Optional[UUID] = None


class PesajeSchema(ResponseBase):
    """Schema de respuesta de Pesaje"""

    numero_pesaje: int
    fecha: datetime
    estado: str = "completado"
    fecha_completado: Optional[datetime] = None
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
    peso_tara: Optional[Decimal] = None
    peso_bruto: Optional[Decimal] = None
    peso_neto: Optional[Decimal] = None

    # Material
    material: Optional[str] = None

    # Operación
    operario: Optional[str] = None
    observaciones: Optional[str] = None

    # Importe
    precio_unitario: Optional[Decimal] = None
    flete: Optional[Decimal] = None
    precio_fijo: Optional[Decimal] = None
    importe_total: Optional[Decimal] = None
    movimiento_financiero_id: Optional[UUID] = None

    # Orden de entrega
    orden_entrega_id: Optional[UUID] = None
    orden_entrega_numero: Optional[int] = None

    remito_generado: bool
    created_by: UUID

    # Campos de cancelación (si aplica)
    motivo_cancelacion: Optional[str] = None
    fecha_cancelacion: Optional[datetime] = None
    cancelado_por: Optional[UUID] = None
    cancelado_por_nombre: Optional[str] = None


class PesajeStats(BaseModel):
    """Schema para estadísticas de pesajes"""

    total_pesajes: int
    total_toneladas: Decimal
    promedio_peso_neto: Decimal
    material_mas_pesado: Optional[str]


class MaterialesDisponibles(BaseModel):
    """Lista de materiales disponibles"""
    materiales: list[str] = MATERIALES_DISPONIBLES


# ============== SCHEMAS PARA FLUJO DOBLE PESAJE ==============

class PesajeIniciarCreate(BaseModel):
    """Schema para iniciar un pesaje (solo tara - camión vacío)"""

    # Tipo de entrega
    tipo_entrega: Literal["propio", "transportista"] = "propio"

    # Camión propio (requerido si tipo_entrega = "propio")
    camion_id: Optional[UUID] = None

    # Transportista externo (requerido si tipo_entrega = "transportista")
    transportista_id: Optional[UUID] = None
    patente_externa: Optional[str] = Field(None, max_length=20)
    transportista: Optional[str] = Field(None, max_length=100)

    # Cliente destino
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = Field(None, max_length=255)

    # Datos del transporte
    acoplado: Optional[str] = Field(None, max_length=20)
    chofer: Optional[str] = Field(None, max_length=100)

    # Peso tara (camión vacío)
    peso_tara: Decimal = Field(..., gt=0, description="Peso del camión vacío en kg")

    # Material (opcional al iniciar)
    material: Optional[str] = Field(None, max_length=100)

    # Operación
    operario: Optional[str] = Field(None, max_length=100)

    observaciones: Optional[str] = None

    # Orden de entrega
    orden_entrega_id: Optional[UUID] = None

    fecha: Union[datetime, date, str] = Field(default_factory=get_argentina_now)

    @field_validator('fecha', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Formato de fecha inválido')
        return v

    @model_validator(mode='after')
    def validar_tipo_entrega(self):
        if self.tipo_entrega == "propio" and not self.camion_id:
            raise ValueError('Debe seleccionar un camión propio')
        if self.tipo_entrega == "transportista":
            # Para transportista solo es obligatoria la patente
            if not self.patente_externa:
                raise ValueError('Debe ingresar la patente del camión externo')
        return self


class PesajeCompletarCreate(BaseModel):
    """Schema para completar un pesaje (peso bruto - camión cargado)

    IMPORTANTE: Al completar el pesaje es OBLIGATORIO tener:
    - cliente_id: Se puede haber cargado al iniciar, o se puede agregar aquí
    - material: Se puede haber cargado al iniciar, o se debe especificar aquí
    """

    peso_bruto: Decimal = Field(..., gt=0, description="Peso del camión cargado en kg")

    # Cliente (opcional aquí si ya se cargó al iniciar, pero DEBE existir al completar)
    cliente_id: Optional[UUID] = Field(None, description="ID del cliente - obligatorio si no se cargó al iniciar")

    # Datos opcionales que se pueden actualizar al completar
    material: Optional[str] = Field(None, max_length=100, description="Material - obligatorio si no se cargó al iniciar")
    chofer: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None

    # Importe (opcional)
    precio_unitario: Optional[Decimal] = Field(None, ge=0, description="Precio por tonelada")
    flete: Optional[Decimal] = Field(None, ge=0, description="Monto fijo de flete")
    precio_fijo: Optional[Decimal] = Field(None, ge=0, description="Precio fijo por viaje")
    importe_total: Optional[Decimal] = Field(None, ge=0, description="Importe total")

    # Orden de entrega
    orden_entrega_id: Optional[UUID] = None


class PesajePendienteSchema(ResponseBase):
    """Schema para listar pesajes pendientes (solo tara registrada)"""

    numero_pesaje: int
    fecha: datetime
    estado: str = "pendiente"

    # Identificación del camión
    tipo_entrega: str
    camion_id: Optional[UUID] = None
    camion_patente: Optional[str] = None
    patente_externa: Optional[str] = None

    # Cliente
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None

    # Transportista
    transportista_id: Optional[UUID] = None
    transportista_nombre: Optional[str] = None

    # Datos
    peso_tara: Decimal
    material: Optional[str] = None
    chofer: Optional[str] = None
    acoplado: Optional[str] = None

    # Tiempo esperando
    minutos_esperando: Optional[int] = None


class BusquedaPatenteResult(BaseModel):
    """Resultado de búsqueda por patente"""

    encontrado: bool
    # Tipo: 'propio' (cantera), 'cliente' (camión de cliente), 'transportista' (externo)
    tipo: Optional[Literal["propio", "cliente", "transportista"]] = None

    # Datos del camión
    camion_id: Optional[str] = None
    camion_patente: Optional[str] = None
    camion_marca: Optional[str] = None
    camion_modelo: Optional[str] = None
    camion_descripcion: Optional[str] = None  # Para camiones de clientes
    camion_tipo: Optional[str] = None  # volcador, acoplado, etc.
    camion_año: Optional[int] = None

    # Cliente asociado (si existe)
    cliente_id: Optional[str] = None
    cliente_nombre: Optional[str] = None

    # Chofer habitual (si está registrado)
    chofer_habitual: Optional[str] = None

    # Acoplado (si tiene)
    acoplado: Optional[str] = None

    # Pesaje pendiente (si existe)
    pesaje_pendiente_id: Optional[str] = None
    pesaje_pendiente_numero: Optional[int] = None
    pesaje_pendiente_tara: Optional[float] = None
    pesaje_pendiente_fecha: Optional[str] = None


class PesajeCancelarCreate(BaseModel):
    """Schema para cancelar un pesaje pendiente (soft-delete con auditoría)"""

    motivo: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Motivo de la cancelación (mínimo 10 caracteres)"
    )


class PesajeCanceladoSchema(ResponseBase):
    """Schema de respuesta de pesaje cancelado"""

    numero_pesaje: int
    fecha: datetime  # Fecha de la tara
    fecha_cancelacion: datetime
    estado: str = "cancelado"

    # Identificación
    tipo_entrega: str
    patente: Optional[str] = None  # patente externa o del camión propio

    # Cliente
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None

    # Datos
    peso_tara: Optional[Decimal] = None
    material: Optional[str] = None

    # Auditoría
    motivo_cancelacion: str
    cancelado_por: Optional[UUID] = None
    cancelado_por_nombre: Optional[str] = None


# ============== SCHEMAS PARA HISTORIAL ==============

class HistorialPesajeSchema(BaseModel):
    """Schema de respuesta de historial de pesaje"""

    id: UUID
    fecha: datetime
    usuario_nombre: str
    accion: str

    class Config:
        from_attributes = True
