"""
Endpoints para el módulo de Reportes
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from io import BytesIO

from app.core.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.services import reportes_service
from app.schemas.reportes import (
    ReporteVentasMaterial,
    ReporteVentasSemanal,
    ReporteGastos,
    ReporteMaquinaria,
    ReporteTopClientes,
    ResumenGeneral
)

router = APIRouter()


@router.get("/materiales", response_model=List[str])
def obtener_materiales(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene la lista de materiales disponibles para filtrar"""
    return reportes_service.obtener_materiales_disponibles(db)


@router.get("/resumen", response_model=ResumenGeneral)
def obtener_resumen_general(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un resumen general del período:
    - Total de ventas (kg, toneladas, importe)
    - Total de gastos por categoría
    - Máquinas activas
    - Cliente y material top
    """
    return reportes_service.obtener_resumen_general(db, fecha_desde, fecha_hasta)


@router.get("/ventas-material", response_model=ReporteVentasMaterial)
def obtener_ventas_por_material(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene las ventas agrupadas por tipo de material/árido:
    - Cantidad de pesajes por material
    - Total de kg y toneladas
    - Importe total
    - Precio promedio
    """
    return reportes_service.obtener_ventas_por_material(db, fecha_desde, fecha_hasta)


@router.get("/ventas-semanal", response_model=ReporteVentasSemanal)
def obtener_ventas_semanales(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    material: Optional[str] = Query(None, description="Filtrar por material específico"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene las ventas agrupadas por semana:
    - Total vendido por semana
    - Filtrable por tipo de material
    """
    return reportes_service.obtener_ventas_semanales(db, fecha_desde, fecha_hasta, material)


@router.get("/gastos", response_model=ReporteGastos)
def obtener_reporte_gastos(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el reporte de gastos:
    - Combustible
    - Servicios/Mantenimiento
    - Repuestos
    - Otros gastos
    """
    return reportes_service.obtener_reporte_gastos(db, fecha_desde, fecha_hasta)


@router.get("/maquinaria", response_model=ReporteMaquinaria)
def obtener_reporte_maquinaria(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el reporte de actividad de maquinaria:
    - Cantidad de máquinas que trabajaron
    - Pesajes por máquina
    - Combustible consumido
    - Servicios realizados
    """
    return reportes_service.obtener_reporte_maquinaria(db, fecha_desde, fecha_hasta)


@router.get("/top-clientes", response_model=ReporteTopClientes)
def obtener_top_clientes(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    limite: int = Query(10, description="Cantidad de clientes a mostrar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los clientes con más compras:
    - Ordenados por total de kg
    - Con importe y porcentaje del total
    """
    return reportes_service.obtener_top_clientes(db, fecha_desde, fecha_hasta, limite)


@router.get("/exportar-pdf")
def exportar_reporte_pdf(
    tipo: str = Query(..., description="Tipo de reporte: resumen, ventas-material, ventas-semanal, gastos, maquinaria, top-clientes"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin del período"),
    material: Optional[str] = Query(None, description="Material para filtro (solo ventas-semanal)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Exporta un reporte a PDF
    """
    from app.services.reportes_pdf_service import generar_pdf_reporte

    pdf_buffer = generar_pdf_reporte(
        db=db,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        material=material
    )

    # Nombre del archivo
    fecha_str = date.today().strftime("%Y%m%d")
    filename = f"reporte_{tipo}_{fecha_str}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
