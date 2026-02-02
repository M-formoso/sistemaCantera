from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import date


class ResumenPesajesHoy(BaseModel):
    """Schema para resumen de pesajes del día"""

    cantidad: int
    toneladas: Decimal


class NivelCombustible(BaseModel):
    """Schema para nivel de combustible"""

    nivel_actual: Decimal
    capacidad_total: Decimal
    porcentaje: Decimal
    esta_bajo: bool


class EstadoCamiones(BaseModel):
    """Schema para estado de camiones"""

    operativos: int
    en_servicio: int
    fuera_servicio: int
    total: int


class AlertaResumen(BaseModel):
    """Schema para alertas"""

    repuestos_bajo_stock: int
    servicios_proximos: int
    nivel_combustible_bajo: bool


class ServicioProximo(BaseModel):
    """Schema para servicio próximo"""

    id: str
    camion_patente: str
    fecha: date
    tipo: str
    descripcion: str


class UltimoPesaje(BaseModel):
    """Schema para últimos pesajes"""

    id: str
    numero_pesaje: int
    fecha: str
    camion_patente: str
    material: str
    peso_neto: Decimal
    cliente_destino: str


class DashboardResumen(BaseModel):
    """Schema principal del dashboard"""

    pesajes: ResumenPesajesHoy
    combustible: NivelCombustible
    camiones: EstadoCamiones
    alertas: AlertaResumen
    servicios_proximos: List[ServicioProximo]
    ultimos_pesajes: List[UltimoPesaje]


class EstadisticasMes(BaseModel):
    """Schema para estadísticas del mes"""

    total_pesajes_mes: int
    total_toneladas_mes: Decimal
    total_combustible_mes: Decimal
    total_servicios_mes: int
    costo_total_servicios: Decimal
