"""
Endpoints API para Trabajos/Reparaciones
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.trabajo import TrabajoSchema, TrabajoCreate, TrabajoUpdate
from app.services import trabajo_service

router = APIRouter()


@router.get("/", response_model=List[TrabajoSchema])
async def listar_trabajos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    camion_id: UUID = Query(None, description="Filtrar por equipo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los trabajos con paginación"""
    return trabajo_service.obtener_todos(db, skip, limit, camion_id)


@router.get("/por-equipo/{camion_id}", response_model=List[TrabajoSchema])
async def listar_trabajos_por_equipo(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene trabajos de un equipo específico"""
    return trabajo_service.obtener_por_camion(db, camion_id)


@router.get("/{trabajo_id}", response_model=TrabajoSchema)
async def obtener_trabajo(
    trabajo_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un trabajo por ID"""
    from fastapi import HTTPException, status
    trabajo = trabajo_service.obtener_por_id(db, trabajo_id)
    if not trabajo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajo no encontrado"
        )
    return trabajo


@router.post("/", response_model=TrabajoSchema, status_code=201)
async def crear_trabajo(
    trabajo: TrabajoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un nuevo trabajo con repuestos.
    Descuenta automáticamente el stock de los repuestos utilizados.

    **Requiere rol:** Administrador u Operador
    """
    return trabajo_service.crear_con_repuestos(db, trabajo, current_user.id)


@router.put("/{trabajo_id}", response_model=TrabajoSchema)
async def actualizar_trabajo(
    trabajo_id: UUID,
    trabajo_data: TrabajoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Actualiza un trabajo existente.
    No permite modificar repuestos para evitar inconsistencias de stock.

    **Requiere rol:** Administrador u Operador
    """
    return trabajo_service.actualizar(db, trabajo_id, trabajo_data)


@router.delete("/{trabajo_id}")
async def eliminar_trabajo(
    trabajo_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Elimina un trabajo.
    NOTA: El stock de los repuestos NO es devuelto.

    **Requiere rol:** Administrador u Operador
    """
    return trabajo_service.eliminar(db, trabajo_id)
