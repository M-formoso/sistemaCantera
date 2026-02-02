"""
Endpoints API para Repuestos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.schemas.repuesto import RepuestoSchema, RepuestoCreate, RepuestoUpdate
from app.services import repuesto_service

router = APIRouter()


@router.get("/", response_model=List[RepuestoSchema])
async def listar_repuestos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los repuestos con paginación"""
    return repuesto_service.obtener_todos(db, skip, limit, solo_activos)


@router.get("/stock-bajo", response_model=List[RepuestoSchema])
async def listar_stock_bajo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene repuestos con stock bajo (stock_actual <= stock_minimo)"""
    return repuesto_service.obtener_stock_bajo(db)


@router.post("/", response_model=RepuestoSchema, status_code=201)
async def crear_repuesto(
    repuesto: RepuestoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo repuesto. **Requiere rol:** Administrador"""
    return repuesto_service.crear(db, repuesto)


@router.get("/{repuesto_id}", response_model=RepuestoSchema)
async def obtener_repuesto(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un repuesto específico por ID"""
    repuesto = repuesto_service.obtener_por_id(db, repuesto_id)

    if not repuesto:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    return repuesto


@router.put("/{repuesto_id}", response_model=RepuestoSchema)
async def actualizar_repuesto(
    repuesto_id: UUID,
    repuesto_data: RepuestoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un repuesto existente. **Requiere rol:** Administrador"""
    return repuesto_service.actualizar(db, repuesto_id, repuesto_data)


@router.delete("/{repuesto_id}", response_model=RepuestoSchema)
async def eliminar_repuesto(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Elimina (soft delete) un repuesto. **Requiere rol:** Administrador"""
    return repuesto_service.eliminar(db, repuesto_id)


@router.get("/{repuesto_id}/movimientos")
async def obtener_movimientos_repuesto(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el historial de movimientos de un repuesto"""
    return repuesto_service.obtener_movimientos(db, repuesto_id)
