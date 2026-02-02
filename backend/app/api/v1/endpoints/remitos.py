"""
Endpoints API para Remitos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.remito import RemitoSchema, RemitoCreate, RemitoFromPesaje
from app.services import remito_service

router = APIRouter()


@router.get("/", response_model=List[RemitoSchema])
async def listar_remitos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los remitos con paginación"""
    return remito_service.obtener_todos(db, skip, limit)


@router.post("/", response_model=RemitoSchema, status_code=201)
async def crear_remito(
    remito: RemitoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un remito manualmente

    **Requiere rol:** Administrador u Operador

    - El número de remito se asigna automáticamente
    """
    return remito_service.crear(db, remito, current_user.id)


@router.post("/generar-desde-pesaje", response_model=RemitoSchema, status_code=201)
async def generar_remito_desde_pesaje(
    data: RemitoFromPesaje,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Genera un remito automáticamente desde un pesaje

    **Requiere rol:** Administrador u Operador

    Este es el flujo principal de generación de remitos:
    - Toma los datos del pesaje
    - Crea el remito con número autoincremental
    - Marca el pesaje como procesado
    - Genera PDF en background (Celery)
    """
    return remito_service.generar_desde_pesaje(db, data.pesaje_id, current_user.id)


@router.get("/{remito_id}", response_model=RemitoSchema)
async def obtener_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un remito específico por ID"""
    remito = remito_service.obtener_por_id(db, remito_id)

    if not remito:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remito no encontrado"
        )

    return remito


@router.delete("/{remito_id}")
async def eliminar_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Elimina un remito

    **Requiere rol:** Administrador u Operador

    Al eliminar, desmarca el pesaje asociado como no procesado
    """
    return remito_service.eliminar(db, remito_id)
