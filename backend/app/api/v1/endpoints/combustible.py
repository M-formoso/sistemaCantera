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
    CisternaSchema, CisternaConfig, CisternaUpdate, CisternaCreate,
    CargaCisternaSchema, CargaCisternaCreate, CargaCisternaUpdate,
    SuministroCombustibleSchema, SuministroCombustibleCreate,
    TransferenciaCisternaSchema, TransferenciaCisternaCreate
)
from app.services import combustible_service

router = APIRouter()


# ==================== CISTERNAS ====================

@router.get("/cisternas", response_model=List[CisternaSchema])
async def listar_cisternas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las cisternas"""
    return combustible_service.obtener_todas_cisternas(db)


@router.get("/cisternas/{cisterna_id}", response_model=CisternaSchema)
async def obtener_cisterna_por_id(
    cisterna_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una cisterna por ID"""
    from fastapi import HTTPException, status
    cisterna = combustible_service.obtener_cisterna_por_id(db, cisterna_id)

    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no encontrada"
        )

    return cisterna


@router.post("/cisternas", response_model=CisternaSchema, status_code=201)
async def crear_cisterna(
    cisterna: CisternaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Crea una nueva cisterna

    **Requiere rol:** Administrador
    """
    return combustible_service.crear_cisterna(db, cisterna)


@router.put("/cisternas/{cisterna_id}", response_model=CisternaSchema)
async def actualizar_cisterna(
    cisterna_id: UUID,
    update_data: CisternaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza la configuración de una cisterna

    **Requiere rol:** Administrador
    """
    return combustible_service.actualizar_cisterna(db, cisterna_id, update_data)


# ==================== CISTERNA LEGACY (single cisterna) ====================

@router.get("/cisterna", response_model=CisternaSchema)
async def obtener_cisterna(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el estado actual de la cisterna principal (legacy)"""
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
    Configura o crea la cisterna principal (legacy)

    **Requiere rol:** Administrador
    """
    return combustible_service.configurar_cisterna(db, config)


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


@router.put("/cargas/{carga_id}", response_model=CargaCisternaSchema)
async def actualizar_carga(
    carga_id: UUID,
    carga_data: CargaCisternaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza una carga de cisterna

    **Requiere rol:** Administrador

    Si se modifican los litros, se ajusta automáticamente el nivel de la cisterna
    """
    return combustible_service.actualizar_carga(db, carga_id, carga_data)


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


# ==================== TRANSFERENCIAS ENTRE CISTERNAS ====================

@router.get("/transferencias", response_model=List[TransferenciaCisternaSchema])
async def listar_transferencias(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las transferencias entre cisternas"""
    return combustible_service.obtener_todas_transferencias(db, skip, limit)


@router.post("/transferencias", response_model=TransferenciaCisternaSchema, status_code=201)
async def crear_transferencia(
    transferencia: TransferenciaCisternaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Registra una transferencia de combustible entre cisternas

    **Requiere rol:** Administrador u Operador

    - Descuenta litros de la cisterna origen
    - Suma litros a la cisterna destino
    """
    return combustible_service.crear_transferencia(db, transferencia, current_user.id)


@router.delete("/transferencias/{transferencia_id}")
async def eliminar_transferencia(
    transferencia_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina una transferencia

    **Requiere rol:** Administrador

    IMPORTANTE: Revierte los litros (devuelve a origen, quita de destino)
    """
    return combustible_service.eliminar_transferencia(db, transferencia_id)


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
