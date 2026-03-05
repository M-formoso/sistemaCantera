"""
Endpoints API para Servicios/Mantenimientos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador, require_admin
from app.models.usuario import Usuario
from app.models.servicio import EstadoServicioEnum
from app.schemas.servicio import ServicioSchema, ServicioCreate, ServicioUpdate
from app.services import servicio_service

router = APIRouter()


@router.get("/", response_model=List[ServicioSchema])
async def listar_servicios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[EstadoServicioEnum] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todos los servicios con paginación

    - **estado**: Filtrar por estado (programado, en_proceso, completado)
    """
    return servicio_service.obtener_todos(db, skip, limit, estado)


@router.get("/programados", response_model=List[ServicioSchema])
async def listar_servicios_programados(
    dias: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene servicios programados en los próximos X días

    - **dias**: Número de días a futuro (1-30)
    """
    return servicio_service.obtener_programados(db, dias)


@router.get("/por-camion/{camion_id}", response_model=List[ServicioSchema])
async def listar_servicios_por_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene servicios de un camión específico"""
    return servicio_service.obtener_por_camion(db, camion_id)


@router.post("/", response_model=ServicioSchema, status_code=201)
async def crear_servicio(
    servicio: ServicioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un nuevo servicio con asignación de repuestos

    **Requiere rol:** Administrador u Operador

    IMPORTANTE:
    - Los repuestos se descontarán automáticamente del stock
    - Se crearán movimientos de stock
    - Se generarán alertas si algún repuesto queda bajo stock mínimo
    - El costo total se calculará automáticamente
    """
    return servicio_service.crear_con_repuestos(db, servicio, current_user.id)


@router.get("/{servicio_id}", response_model=ServicioSchema)
async def obtener_servicio(
    servicio_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un servicio específico por ID"""
    servicio = servicio_service.obtener_por_id(db, servicio_id)

    if not servicio:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )

    return servicio


@router.put("/{servicio_id}", response_model=ServicioSchema)
async def actualizar_servicio(
    servicio_id: UUID,
    servicio_data: ServicioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza un servicio existente

    **Requiere rol:** Administrador u Operador

    NOTA: No permite modificar repuestos asignados
    """
    return servicio_service.actualizar(db, servicio_id, servicio_data)


@router.delete("/{servicio_id}")
async def eliminar_servicio(
    servicio_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina un servicio

    **Requiere rol:** Administrador u Operador

    IMPORTANTE: El stock de repuestos NO se devolverá
    """
    return servicio_service.eliminar(db, servicio_id)
