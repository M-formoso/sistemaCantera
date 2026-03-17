"""
Endpoints API para Repuestos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin, require_permiso_repuestos
from app.models.usuario import Usuario
from app.models.movimiento_stock import TipoMovimientoEnum
from app.schemas.repuesto import RepuestoSchema, RepuestoCreate, RepuestoUpdate, EquipoAsignado, RepuestoEquiposUpdate
from app.services import repuesto_service
from pydantic import BaseModel
from decimal import Decimal


class AjusteStockRequest(BaseModel):
    cantidad: Decimal
    observaciones: str | None = None


class AsignarEquipoRequest(BaseModel):
    camion_id: UUID

router = APIRouter()


@router.get("/", response_model=List[RepuestoSchema])
async def listar_repuestos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    camion_id: UUID | None = Query(None, description="Filtrar por equipo asignado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los repuestos con paginación"""
    return repuesto_service.obtener_todos(db, skip, limit, solo_activos, camion_id)


@router.get("/stock-bajo", response_model=List[RepuestoSchema])
async def listar_stock_bajo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene repuestos con stock bajo (stock_actual <= stock_minimo)"""
    return repuesto_service.obtener_stock_bajo(db)


@router.get("/por-equipo/{camion_id}", response_model=List[RepuestoSchema])
async def listar_repuestos_por_equipo(
    camion_id: UUID,
    incluir_generales: bool = Query(True, description="Incluir repuestos sin asignación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene repuestos asignados a un equipo específico.
    Si incluir_generales=True, también devuelve repuestos sin asignación (camion_id=null).
    """
    return repuesto_service.obtener_por_equipo(db, camion_id, incluir_generales)


@router.post("/", response_model=RepuestoSchema, status_code=201)
async def crear_repuesto(
    repuesto: RepuestoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """Crea un nuevo repuesto. **Requiere rol:** Administrador u Operador"""
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
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """Actualiza un repuesto existente. **Requiere rol:** Administrador u Operador"""
    return repuesto_service.actualizar(db, repuesto_id, repuesto_data)


@router.delete("/{repuesto_id}", response_model=RepuestoSchema)
async def eliminar_repuesto(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """Elimina (soft delete) un repuesto. **Requiere rol:** Administrador u Operador"""
    return repuesto_service.eliminar(db, repuesto_id)


@router.get("/{repuesto_id}/movimientos")
async def obtener_movimientos_repuesto(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el historial de movimientos de un repuesto"""
    return repuesto_service.obtener_movimientos(db, repuesto_id)


@router.post("/{repuesto_id}/entrada")
async def registrar_entrada_stock(
    repuesto_id: UUID,
    data: AjusteStockRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """
    Registra una entrada de stock (ingreso)

    **Requiere rol:** Administrador u Operador
    """
    return repuesto_service.ajustar_stock(
        db=db,
        repuesto_id=repuesto_id,
        cantidad=data.cantidad,
        tipo=TipoMovimientoEnum.INGRESO,
        usuario_id=current_user.id,
        observaciones=data.observaciones
    )


@router.post("/{repuesto_id}/salida")
async def registrar_salida_stock(
    repuesto_id: UUID,
    data: AjusteStockRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """
    Registra una salida de stock (egreso)

    **Requiere rol:** Administrador u Operador
    """
    return repuesto_service.ajustar_stock(
        db=db,
        repuesto_id=repuesto_id,
        cantidad=data.cantidad,
        tipo=TipoMovimientoEnum.EGRESO,
        usuario_id=current_user.id,
        observaciones=data.observaciones
    )


# ============ ENDPOINTS PARA ASIGNACIÓN N:N CON EQUIPOS ============

@router.get("/{repuesto_id}/equipos", response_model=List[EquipoAsignado])
async def obtener_equipos_asignados(
    repuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene todos los equipos a los que está asignado un repuesto.

    Un repuesto puede estar asignado a múltiples equipos (relación N:N).
    """
    return repuesto_service.obtener_equipos_asignados(db, repuesto_id)


@router.put("/{repuesto_id}/equipos")
async def actualizar_equipos_asignados(
    repuesto_id: UUID,
    data: RepuestoEquiposUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """
    Actualiza la lista completa de equipos asignados a un repuesto.

    Reemplaza todas las asignaciones existentes con la nueva lista.
    Un repuesto puede estar asignado a múltiples equipos.

    **Requiere rol:** Administrador u Operador
    """
    return repuesto_service.actualizar_equipos_asignados(db, repuesto_id, data.equipos_ids)


@router.post("/{repuesto_id}/equipos/{camion_id}")
async def asignar_a_equipo(
    repuesto_id: UUID,
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """
    Asigna un repuesto a un equipo específico.

    Un repuesto puede estar asignado a múltiples equipos.

    **Requiere rol:** Administrador u Operador
    """
    return repuesto_service.asignar_a_equipo(db, repuesto_id, camion_id)


@router.delete("/{repuesto_id}/equipos/{camion_id}")
async def desasignar_de_equipo(
    repuesto_id: UUID,
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permiso_repuestos)
):
    """
    Desasigna un repuesto de un equipo específico.

    **Requiere rol:** Administrador u Operador
    """
    return repuesto_service.desasignar_de_equipo(db, repuesto_id, camion_id)
