"""
Endpoints API para Empresas (Clientes y Transportistas)
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.empresa import (
    EmpresaSchema, EmpresaCreate, EmpresaUpdate,
    EmpresaConCamionesSchema,
    CamionClienteSchema, CamionClienteCreate, CamionClienteUpdate
)
from app.services import empresa_service, camion_cliente_service

router = APIRouter()


@router.get("/", response_model=List[EmpresaSchema])
async def listar_empresas(
    tipo: Optional[Literal["cliente", "transportista"]] = None,
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
    empresas = empresa_service.obtener_todos(db, tipo, solo_activos, skip, limit)

    # Agregar nombre de lista de precios
    result = []
    for empresa in empresas:
        empresa_dict = {
            "id": empresa.id,
            "nombre": empresa.nombre,
            "tipo": empresa.tipo,
            "cuit": empresa.cuit,
            "direccion": empresa.direccion,
            "telefono": empresa.telefono,
            "email": empresa.email,
            "contacto": empresa.contacto,
            "activo": empresa.activo,
            "saldo_cuenta_corriente": float(empresa.saldo_cuenta_corriente) if empresa.saldo_cuenta_corriente else 0,
            "lista_precio_id": empresa.lista_precio_id,
            "lista_precio_nombre": empresa.lista_precio.nombre if empresa.lista_precio else None,
            "created_at": empresa.created_at,
            "updated_at": empresa.updated_at,
        }
        result.append(empresa_dict)

    return result


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
    tipo: Optional[Literal["cliente", "transportista"]] = None,
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


@router.put("/{empresa_id}/lista-precio")
async def asignar_lista_precio(
    empresa_id: UUID,
    lista_precio_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Asigna una lista de precios a un cliente.
    Si lista_precio_id es None, quita la lista asignada.
    """
    from app.models.empresa import Empresa
    from app.models.lista_precio import ListaPrecio

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    if empresa.tipo != 'cliente':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede asignar lista de precios a clientes"
        )

    # Verificar que la lista existe
    if lista_precio_id:
        lista = db.query(ListaPrecio).filter(ListaPrecio.id == lista_precio_id).first()
        if not lista:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lista de precios no encontrada"
            )
        empresa.lista_precio_id = lista_precio_id
        lista_nombre = lista.nombre
    else:
        empresa.lista_precio_id = None
        lista_nombre = None

    db.commit()
    db.refresh(empresa)

    return {
        "message": "Lista de precios asignada correctamente" if lista_precio_id else "Lista de precios removida",
        "empresa_id": str(empresa.id),
        "empresa_nombre": empresa.nombre,
        "lista_precio_id": str(empresa.lista_precio_id) if empresa.lista_precio_id else None,
        "lista_precio_nombre": lista_nombre
    }


# ============== ENDPOINTS PARA CAMIONES DE CLIENTES ==============

@router.get("/{empresa_id}/camiones", response_model=List[CamionClienteSchema])
async def listar_camiones_cliente(
    empresa_id: UUID,
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todos los camiones/patentes de un cliente
    """
    return camion_cliente_service.obtener_por_cliente(db, empresa_id, solo_activos)


@router.post("/{empresa_id}/camiones", response_model=CamionClienteSchema, status_code=201)
async def crear_camion_cliente(
    empresa_id: UUID,
    camion: CamionClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Agrega un nuevo camión/patente a un cliente

    **Requiere rol:** Administrador u Operador
    """
    return camion_cliente_service.crear(db, empresa_id, camion)


@router.put("/camiones/{camion_id}", response_model=CamionClienteSchema)
async def actualizar_camion_cliente(
    camion_id: UUID,
    camion_data: CamionClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza un camión de cliente

    **Requiere rol:** Administrador u Operador
    """
    return camion_cliente_service.actualizar(db, camion_id, camion_data)


@router.delete("/camiones/{camion_id}")
async def eliminar_camion_cliente(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina (desactiva) un camión de cliente

    **Requiere rol:** Administrador u Operador
    """
    return camion_cliente_service.eliminar(db, camion_id)


@router.get("/camiones/buscar-patente/{patente}")
async def buscar_cliente_por_patente(
    patente: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Busca un cliente por la patente de uno de sus camiones.
    Retorna datos del cliente y del camión si se encuentra.
    """
    resultado = camion_cliente_service.obtener_cliente_por_patente(db, patente)

    if not resultado:
        return {"encontrado": False}

    return {
        "encontrado": True,
        **resultado
    }
