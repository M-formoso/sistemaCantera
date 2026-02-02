"""
Endpoints API para Dashboard
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.models.usuario import Usuario
from app.services import dashboard_service

router = APIRouter()


@router.get("/resumen-dia")
async def obtener_resumen_dia(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el resumen de operaciones del día actual

    Este es el endpoint principal del dashboard que incluye:
    - Pesajes del día (cantidad y toneladas)
    - Nivel de combustible en cisterna
    - Estado de camiones (operativos/en servicio)
    - Alertas (repuestos bajo stock, servicios próximos, combustible bajo)
    - Servicios programados próximos 7 días
    - Últimos 10 pesajes
    """
    return dashboard_service.obtener_resumen_dia(db)


@router.get("/estadisticas-mes")
async def obtener_estadisticas_mes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas del mes actual

    Incluye:
    - Total de pesajes del mes
    - Toneladas totales
    - Combustible consumido
    - Servicios realizados
    - Costo total de mantenimiento
    """
    return dashboard_service.obtener_estadisticas_mes(db)
