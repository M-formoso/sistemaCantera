"""
Endpoints API para Empresas (Clientes y Transportistas)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.models.empresa import TipoEmpresaEnum
from app.schemas.empresa import EmpresaSchema, EmpresaCreate, EmpresaUpdate
from app.services import empresa_service

router = APIRouter()


@router.get("/", response_model=List[EmpresaSchema])
async def listar_empresas(
    tipo: Optional[TipoEmpresaEnum] = None,
    solo_activos: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todas las empresas (clientes y transportistas)

    Parámetros:
    - tipo: Filtrar por tipo (cliente/transportista)
    - solo_activos: Si es True, solo retorna empresas activas
    """
    return empresa_service.obtener_todos(db, tipo, solo_activos, skip, limit)


@router.get("/clientes", response_model=List[EmpresaSchema])
async def listar_clientes(
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista solo clientes"""
    return empresa_service.obtener_clientes(db, solo_activos)


@router.get("/transportistas", response_model=List[EmpresaSchema])
async def listar_transportistas(
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista solo transportistas"""
    return empresa_service.obtener_transportistas(db, solo_activos)


@router.get("/buscar", response_model=List[EmpresaSchema])
async def buscar_empresas(
    q: str = Query(..., min_length=1, description="Texto a buscar"),
    tipo: Optional[TipoEmpresaEnum] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Busca empresas por nombre (para autocompletado)

    Retorna empresas cuyo nombre comienza con el texto buscado
    """
    return empresa_service.buscar_por_nombre(db, q, tipo, limit)


@router.get("/{empresa_id}", response_model=EmpresaSchema)
async def obtener_empresa(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una empresa por ID"""
    from fastapi import HTTPException, status
    empresa = empresa_service.obtener_por_id(db, empresa_id)

    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    return empresa


@router.post("/", response_model=EmpresaSchema, status_code=201)
async def crear_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crea una nueva empresa (cliente o transportista)
    """
    return empresa_service.crear(db, empresa)


@router.put("/{empresa_id}", response_model=EmpresaSchema)
async def actualizar_empresa(
    empresa_id: UUID,
    empresa_data: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza una empresa existente

    **Requiere rol:** Administrador
    """
    return empresa_service.actualizar(db, empresa_id, empresa_data)


@router.delete("/{empresa_id}", response_model=EmpresaSchema)
async def eliminar_empresa(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina (desactiva) una empresa

    **Requiere rol:** Administrador
    """
    return empresa_service.eliminar(db, empresa_id)
