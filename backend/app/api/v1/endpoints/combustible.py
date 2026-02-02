"""
Endpoints API para Combustible
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.combustible import (
    CisternaSchema, CisternaConfig, CisternaUpdate,
    CargaCisternaSchema, CargaCisternaCreate,
    SuministroCombustibleSchema, SuministroCombustibleCreate
)
from app.services import combustible_service

router = APIRouter()


# ==================== CISTERNA ====================

@router.get("/cisterna", response_model=CisternaSchema)
async def obtener_cisterna(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el estado actual de la cisterna"""
    cisterna = combustible_service.obtener_cisterna(db)

    if not cisterna:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no configurada"
        )

    return cisterna


@router.post("/cisterna/configurar", response_model=CisternaSchema)
async def configurar_cisterna(
    config: CisternaConfig,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Configura o crea la cisterna

    **Requiere rol:** Administrador
    """
    return combustible_service.configurar_cisterna(db, config)


@router.put("/cisterna", response_model=CisternaSchema)
async def actualizar_cisterna(
    update_data: CisternaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza la configuración de la cisterna

    **Requiere rol:** Administrador
    """
    return combustible_service.actualizar_cisterna(db, update_data)


# ==================== CARGAS DE CISTERNA ====================

@router.get("/cargas", response_model=List[CargaCisternaSchema])
async def listar_cargas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las cargas de cisterna"""
    return combustible_service.obtener_todas_cargas(db, skip, limit)


@router.post("/cargas", response_model=CargaCisternaSchema, status_code=201)
async def crear_carga(
    carga: CargaCisternaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Registra una carga de combustible a la cisterna

    **Requiere rol:** Administrador u Operador

    - Actualiza automáticamente el nivel de la cisterna
    - Calcula costo por litro si se proporciona costo total
    """
    return combustible_service.crear_carga_cisterna(db, carga, current_user.id)


@router.get("/cargas/{carga_id}", response_model=CargaCisternaSchema)
async def obtener_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una carga específica por ID"""
    carga = combustible_service.obtener_carga_por_id(db, carga_id)

    if not carga:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carga no encontrada"
        )

    return carga


@router.delete("/cargas/{carga_id}")
async def eliminar_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina una carga

    **Requiere rol:** Administrador

    IMPORTANTE: Descuenta los litros del nivel actual de la cisterna
    """
    return combustible_service.eliminar_carga(db, carga_id)


# ==================== SUMINISTROS A CAMIONES ====================

@router.get("/suministros", response_model=List[SuministroCombustibleSchema])
async def listar_suministros(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los suministros de combustible"""
    return combustible_service.obtener_todos_suministros(db, skip, limit)


@router.get("/suministros/por-camion/{camion_id}", response_model=List[SuministroCombustibleSchema])
async def listar_suministros_por_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene suministros de un camión específico"""
    return combustible_service.obtener_suministros_por_camion(db, camion_id)


@router.post("/suministros", response_model=SuministroCombustibleSchema, status_code=201)
async def crear_suministro(
    suministro: SuministroCombustibleCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Registra un suministro de combustible a un camión

    **Requiere rol:** Administrador u Operador

    - Descuenta automáticamente del nivel de la cisterna
    - Genera alerta si el nivel queda bajo
    """
    return combustible_service.crear_suministro(db, suministro, current_user.id)


@router.get("/suministros/{suministro_id}", response_model=SuministroCombustibleSchema)
async def obtener_suministro(
    suministro_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un suministro específico por ID"""
    suministro = combustible_service.obtener_suministro_por_id(db, suministro_id)

    if not suministro:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suministro no encontrado"
        )

    return suministro


@router.delete("/suministros/{suministro_id}")
async def eliminar_suministro(
    suministro_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina un suministro

    **Requiere rol:** Administrador

    IMPORTANTE: Devuelve los litros al nivel de la cisterna
    """
    return combustible_service.eliminar_suministro(db, suministro_id)


# ==================== ESTADÍSTICAS ====================

@router.get("/consumo-por-camion/{camion_id}")
async def obtener_consumo_por_camion(
    camion_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene estadísticas de consumo de combustible por camión"""
    return combustible_service.obtener_consumo_por_camion(
        db, camion_id, fecha_desde, fecha_hasta
    )
