from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user
from app.core.security import get_password_hash
from app.models.usuario import Usuario, RolEnum
from app.schemas.usuario import (
    UsuarioSchema,
    UsuarioCreate,
    UsuarioUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


def check_admin_permission(current_user: Usuario):
    """Verifica que el usuario actual sea administrador"""
    if current_user.rol != RolEnum.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción"
        )


@router.get("", response_model=PaginatedResponse[UsuarioSchema])
async def get_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activo: bool | None = None,
    rol: RolEnum | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de usuarios (solo administradores)

    Parámetros:
    - skip: Cantidad de registros a omitir (paginación)
    - limit: Cantidad máxima de registros a retornar
    - activo: Filtrar por estado activo/inactivo
    - rol: Filtrar por rol
    """
    check_admin_permission(current_user)

    # Query base
    query = db.query(Usuario)

    # Aplicar filtros
    if activo is not None:
        query = query.filter(Usuario.activo == activo)

    if rol is not None:
        query = query.filter(Usuario.rol == rol)

    # Obtener total
    total = query.count()

    # Aplicar paginación y ordenar
    usuarios = query.order_by(Usuario.created_at.desc()).offset(skip).limit(limit).all()

    return PaginatedResponse(
        items=usuarios,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{usuario_id}", response_model=UsuarioSchema)
async def get_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener un usuario por ID (solo administradores)
    """
    check_admin_permission(current_user)

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return usuario


@router.post("", response_model=UsuarioSchema, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear un nuevo usuario (solo administradores)
    """
    check_admin_permission(current_user)

    # Verificar si el email ya existe
    existing_usuario = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existing_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )

    # Crear usuario
    password_hash = get_password_hash(usuario_data.password)

    nuevo_usuario = Usuario(
        email=usuario_data.email,
        nombre=usuario_data.nombre,
        rol=usuario_data.rol,
        password_hash=password_hash,
        activo=True,
        # Permisos por módulo
        permiso_dashboard=usuario_data.permiso_dashboard,
        permiso_camiones=usuario_data.permiso_camiones,
        permiso_empresas=usuario_data.permiso_empresas,
        permiso_repuestos=usuario_data.permiso_repuestos,
        permiso_pesajes=usuario_data.permiso_pesajes,
        permiso_combustible=usuario_data.permiso_combustible,
        permiso_finanzas=usuario_data.permiso_finanzas,
        permiso_usuarios=usuario_data.permiso_usuarios,
        permiso_reportes=usuario_data.permiso_reportes,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


@router.put("/{usuario_id}", response_model=UsuarioSchema)
async def update_usuario(
    usuario_id: UUID,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar un usuario (solo administradores)

    No permite actualizar la contraseña (usar endpoint específico)
    """
    check_admin_permission(current_user)

    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # No permitir que el usuario se desactive a sí mismo
    if usuario.id == current_user.id and usuario_data.activo is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta"
        )

    # No permitir que el usuario cambie su propio rol
    if usuario.id == current_user.id and usuario_data.rol is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede cambiar su propio rol"
        )

    # Si se actualiza el email, verificar que no exista
    if usuario_data.email and usuario_data.email != usuario.email:
        existing_usuario = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
        if existing_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email"
            )

    # Actualizar campos
    update_data = usuario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usuario, field, value)

    db.commit()
    db.refresh(usuario)

    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Desactivar un usuario (solo administradores)

    En lugar de eliminar físicamente, se marca como inactivo para preservar
    la integridad referencial con otros registros del sistema.

    No permite desactivar al propio usuario.
    """
    check_admin_permission(current_user)

    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # No permitir que el usuario se desactive a sí mismo
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta"
        )

    # Desactivar usuario en lugar de eliminarlo
    usuario.activo = False
    db.commit()

    return None


@router.put("/{usuario_id}/reset-password", response_model=dict)
async def reset_usuario_password(
    usuario_id: UUID,
    new_password: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Resetear la contraseña de un usuario (solo administradores)
    """
    check_admin_permission(current_user)

    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar contraseña
    usuario.password_hash = get_password_hash(new_password)
    db.commit()

    return {"message": "Contraseña restablecida correctamente"}
