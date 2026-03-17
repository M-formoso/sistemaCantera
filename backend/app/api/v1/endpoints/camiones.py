"""
Endpoints API para Camiones
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin, require_permiso_camiones
from app.models.usuario import Usuario
from app.schemas.camion import CamionSchema, CamionCreate, CamionUpdate
from app.schemas.servicio import ServicioSchema
from app.services import camion_service

router = APIRouter()


@router.get("/", response_model=List[CamionSchema])
async def listar_camiones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todos los camiones con paginación

    - **skip**: Número de registros a saltar
    - **limit**: Límite de registros a retornar (máx 500)
    - **solo_activos**: Si es True, solo retorna camiones activos
    """
    camiones = camion_service.obtener_todos(
        db,
        skip=skip,
        limit=limit,
        solo_activos=solo_activos
    )
    # Enriquecer cada camión con campos calculados
    return [camion_service.enriquecer_camion(c) for c in camiones]


@router.post("/", response_model=CamionSchema, status_code=201)
async def crear_camion(
    camion: CamionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_camiones)
):
    """
    Crea un nuevo camión

    **Requiere:** Permiso de Camiones/Equipos

    Campos requeridos:
    - **patente**: Identificación única del camión
    """
    return camion_service.crear(db, camion)


@router.get("/{camion_id}", response_model=CamionSchema)
async def obtener_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un camión específico por ID"""
    camion = camion_service.obtener_por_id(db, camion_id)

    if not camion:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    return camion_service.enriquecer_camion(camion)


@router.put("/{camion_id}", response_model=CamionSchema)
async def actualizar_camion(
    camion_id: UUID,
    camion_data: CamionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_camiones)
):
    """
    Actualiza un camión existente

    **Requiere:** Permiso de Camiones/Equipos
    """
    return camion_service.actualizar(db, camion_id, camion_data)


@router.delete("/{camion_id}", response_model=CamionSchema)
async def eliminar_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina (soft delete) un camión

    **Requiere rol:** Administrador (eliminar sigue siendo solo admin)

    Nota: El camión no se elimina físicamente, solo se marca como inactivo
    """
    return camion_service.eliminar(db, camion_id)


@router.get("/{camion_id}/servicios", response_model=List[ServicioSchema])
async def obtener_servicios_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el historial de servicios de un camión"""
    return camion_service.obtener_servicios(db, camion_id)
