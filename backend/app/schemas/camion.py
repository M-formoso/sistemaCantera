from pydantic import BaseModel, Field, model_validator
from uuid import UUID
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import date, datetime

from app.models.camion import TipoCamionEnum, EstadoCamionEnum
from app.schemas.common import ResponseBase


class CamionBase(BaseModel):
    """Schema base de Camión/Máquina"""

    # Categoría: camion o maquina
    categoria: Literal["camion", "maquina"] = "camion"

    # Identificación
    patente: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    codigo_interno: Optional[str] = Field(None, max_length=50)

    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    año: Optional[int] = Field(None, ge=1900, le=2100)
    numero_serie: Optional[str] = Field(None, max_length=100)

    # Tipo
    tipo: Optional[TipoCamionEnum] = TipoCamionEnum.VOLCADOR
    tipo_maquina: Optional[str] = Field(None, max_length=50)

    estado: EstadoCamionEnum = EstadoCamionEnum.OPERATIVO
    chofer_habitual: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None

    @model_validator(mode='after')
    def validar_identificacion(self):
        """Validar que tenga al menos un identificador"""
        if not self.patente and not self.nombre and not self.codigo_interno:
            raise ValueError('Debe proporcionar al menos patente, nombre o código interno')
        return self


class CamionCreate(CamionBase):
    """Schema para crear Camión/Máquina"""

    kilometraje_actual: int = Field(default=0, ge=0)
    horometro_actual: Decimal = Field(default=Decimal("0"), ge=0)
    horas_promedio_diarias: Decimal = Field(default=Decimal("0"), ge=0)
    foto: Optional[str] = Field(None, max_length=500)
    proximo_servicio_km: Optional[int] = Field(None, ge=0)
    proximo_servicio_horas: Optional[Decimal] = Field(None, ge=0)
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: int = Field(default=10000, ge=100)
    intervalo_servicio_horas: int = Field(default=250, ge=10)

    # Documentación
    tarjeta_verde_url: Optional[str] = Field(None, max_length=500)
    tarjeta_verde_vencimiento: Optional[date] = None
    seguro_url: Optional[str] = Field(None, max_length=500)
    seguro_compania: Optional[str] = Field(None, max_length=100)
    seguro_poliza: Optional[str] = Field(None, max_length=100)
    seguro_vencimiento: Optional[date] = None
    vtv_url: Optional[str] = Field(None, max_length=500)
    vtv_vencimiento: Optional[date] = None
    cedula_url: Optional[str] = Field(None, max_length=500)


class CamionUpdate(BaseModel):
    """Schema para actualizar Camión/Máquina"""

    categoria: Optional[Literal["camion", "maquina"]] = None
    patente: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    codigo_interno: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    año: Optional[int] = Field(None, ge=1900, le=2100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    tipo: Optional[TipoCamionEnum] = None
    tipo_maquina: Optional[str] = Field(None, max_length=50)
    estado: Optional[EstadoCamionEnum] = None
    kilometraje_actual: Optional[int] = Field(None, ge=0)
    horometro_actual: Optional[Decimal] = Field(None, ge=0)
    horas_promedio_diarias: Optional[Decimal] = Field(None, ge=0)
    chofer_habitual: Optional[str] = Field(None, max_length=100)
    foto: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None
    activo: Optional[bool] = None
    proximo_servicio_km: Optional[int] = Field(None, ge=0)
    proximo_servicio_horas: Optional[Decimal] = Field(None, ge=0)
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: Optional[int] = Field(None, ge=100)
    intervalo_servicio_horas: Optional[int] = Field(None, ge=10)

    # Documentación
    tarjeta_verde_url: Optional[str] = Field(None, max_length=500)
    tarjeta_verde_vencimiento: Optional[date] = None
    seguro_url: Optional[str] = Field(None, max_length=500)
    seguro_compania: Optional[str] = Field(None, max_length=100)
    seguro_poliza: Optional[str] = Field(None, max_length=100)
    seguro_vencimiento: Optional[date] = None
    vtv_url: Optional[str] = Field(None, max_length=500)
    vtv_vencimiento: Optional[date] = None
    cedula_url: Optional[str] = Field(None, max_length=500)


class CamionSchema(ResponseBase):
    """Schema de respuesta de Camión/Máquina"""

    # Categoría
    categoria: str = "camion"

    # Identificación
    patente: Optional[str] = None
    nombre: Optional[str] = None
    codigo_interno: Optional[str] = None

    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    numero_serie: Optional[str] = None

    tipo: Optional[TipoCamionEnum] = None
    tipo_maquina: Optional[str] = None
    estado: EstadoCamionEnum

    kilometraje_actual: int
    horometro_actual: Decimal
    horas_promedio_diarias: Optional[Decimal] = Decimal("0")

    chofer_habitual: Optional[str] = None
    foto: Optional[str] = None
    observaciones: Optional[str] = None
    activo: bool

    # Campos de servicio
    ultimo_servicio: Optional[date] = None
    ultimo_servicio_km: Optional[int] = None
    ultimo_servicio_horas: Optional[Decimal] = None
    proximo_servicio_km: Optional[int] = None
    proximo_servicio_horas: Optional[Decimal] = None
    proximo_servicio_fecha: Optional[date] = None
    intervalo_servicio_km: Optional[int] = None
    intervalo_servicio_horas: Optional[int] = None

    # Documentación
    tarjeta_verde_url: Optional[str] = None
    tarjeta_verde_vencimiento: Optional[date] = None
    seguro_url: Optional[str] = None
    seguro_compania: Optional[str] = None
    seguro_poliza: Optional[str] = None
    seguro_vencimiento: Optional[date] = None
    vtv_url: Optional[str] = None
    vtv_vencimiento: Optional[date] = None
    cedula_url: Optional[str] = None

    # Campo calculado para alertas
    km_para_proximo_servicio: Optional[int] = None
    horas_para_proximo_servicio: Optional[Decimal] = None
    requiere_servicio: bool = False

    # Identificador para mostrar en UI
    identificador: Optional[str] = None


class CamionConsumoStats(BaseModel):
    """Schema para estadísticas de consumo de combustible"""

    camion_id: UUID
    identificador: str  # Patente o nombre
    total_litros: Decimal
    total_kilometros: Optional[int]
    total_horas: Optional[Decimal]
    promedio_consumo: Optional[Decimal]  # km/litro o horas/litro
    cantidad_suministros: int


# =============================================
# DOCUMENTOS DE EQUIPO
# =============================================

class DocumentoEquipoBase(BaseModel):
    """Schema base de DocumentoEquipo"""
    tipo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    archivo_url: str = Field(..., max_length=500)
    archivo_nombre: Optional[str] = Field(None, max_length=255)
    archivo_tipo: Optional[str] = Field(None, max_length=50)
    archivo_tamaño: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    notas: Optional[str] = None


class DocumentoEquipoCreate(DocumentoEquipoBase):
    """Schema para crear documento"""
    equipo_id: UUID


class DocumentoEquipoSchema(DocumentoEquipoBase):
    """Schema de respuesta de documento"""
    id: UUID
    equipo_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
