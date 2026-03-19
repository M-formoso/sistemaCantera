"""
Schemas para el módulo de Reportes
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID


# ============== FILTROS ==============

class FiltroReporte(BaseModel):
    """Filtros base para reportes"""
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    material: Optional[str] = None


# ============== VENTAS POR MATERIAL ==============

class VentaPorMaterial(BaseModel):
    """Venta agrupada por tipo de material"""
    material: str
    cantidad_pesajes: int
    total_kg: Decimal
    total_toneladas: Decimal
    importe_total: Decimal
    precio_promedio: Decimal


class ReporteVentasMaterial(BaseModel):
    """Reporte completo de ventas por material"""
    fecha_desde: date
    fecha_hasta: date
    materiales: List[VentaPorMaterial]
    total_kg: Decimal
    total_toneladas: Decimal
    total_importe: Decimal
    cantidad_pesajes: int


# ============== VENTAS POR SEMANA ==============

class VentaPorSemana(BaseModel):
    """Venta agrupada por semana"""
    semana: int
    anio: int
    fecha_inicio: date
    fecha_fin: date
    cantidad_pesajes: int
    total_kg: Decimal
    total_toneladas: Decimal
    importe_total: Decimal


class ReporteVentasSemanal(BaseModel):
    """Reporte de ventas semanales"""
    fecha_desde: date
    fecha_hasta: date
    material: Optional[str] = None
    semanas: List[VentaPorSemana]
    total_kg: Decimal
    total_toneladas: Decimal
    total_importe: Decimal


# ============== GASTOS ==============

class GastoPorCategoria(BaseModel):
    """Gasto agrupado por categoría"""
    categoria: str
    cantidad: int
    total: Decimal
    porcentaje: Decimal


class ReporteGastos(BaseModel):
    """Reporte de gastos"""
    fecha_desde: date
    fecha_hasta: date
    categorias: List[GastoPorCategoria]
    total_gastos: Decimal
    total_combustible: Decimal
    total_servicios: Decimal
    total_repuestos: Decimal


# ============== MAQUINARIA ==============

class MaquinaActividad(BaseModel):
    """Actividad de una máquina/camión"""
    id: UUID
    identificador: str
    tipo: str
    cantidad_pesajes: int
    total_kg: Decimal
    total_combustible: Decimal
    cantidad_servicios: int
    costo_servicios: Decimal
    dias_activa: int


class ReporteMaquinaria(BaseModel):
    """Reporte de actividad de maquinaria"""
    fecha_desde: date
    fecha_hasta: date
    maquinas: List[MaquinaActividad]
    total_maquinas_activas: int
    total_combustible: Decimal
    total_costo_servicios: Decimal


# ============== TOP CLIENTES ==============

class ClienteTop(BaseModel):
    """Cliente con más compras"""
    id: UUID
    nombre: str
    cantidad_pesajes: int
    total_kg: Decimal
    total_toneladas: Decimal
    importe_total: Decimal
    porcentaje_total: Decimal


class ReporteTopClientes(BaseModel):
    """Reporte de mejores clientes"""
    fecha_desde: date
    fecha_hasta: date
    clientes: List[ClienteTop]
    total_clientes: int
    total_general: Decimal


# ============== REPORTE GENERAL ==============

class ResumenGeneral(BaseModel):
    """Resumen general para el período"""
    fecha_desde: date
    fecha_hasta: date

    # Ventas
    cantidad_pesajes: int
    total_kg: Decimal
    total_toneladas: Decimal
    importe_total_ventas: Decimal

    # Gastos
    total_gastos: Decimal
    gasto_combustible: Decimal
    gasto_servicios: Decimal
    gasto_repuestos: Decimal

    # Maquinaria
    maquinas_activas: int

    # Cliente top
    cliente_top_nombre: Optional[str] = None
    cliente_top_kg: Optional[Decimal] = None

    # Material top
    material_top_nombre: Optional[str] = None
    material_top_kg: Optional[Decimal] = None


# ============== MOVIMIENTOS / DETALLE PESAJES ==============

class MovimientoPesaje(BaseModel):
    """Detalle de un pesaje individual para el reporte de movimientos"""
    id: UUID
    numero_pesaje: int
    fecha: str  # ISO format
    hora: str
    cliente_nombre: Optional[str] = None
    material: Optional[str] = None
    peso_neto: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    flete: Optional[Decimal] = None
    importe_total: Optional[Decimal] = None
    patente: Optional[str] = None
    chofer: Optional[str] = None
    tipo_entrega: Optional[str] = None
    estado: str
    observaciones: Optional[str] = None


class ReporteMovimientos(BaseModel):
    """Reporte de movimientos/pesajes del período"""
    fecha_desde: date
    fecha_hasta: date
    movimientos: List[MovimientoPesaje]
    cantidad_pesajes: int
    total_kg: Decimal
    total_toneladas: Decimal
    total_importe: Decimal
