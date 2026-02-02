from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.usuario import Usuario

# Security scheme
security = HTTPBearer()


def get_db() -> Generator:
    """
    Dependency para obtener sesión de base de datos

    Yields:
        Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency para obtener usuario autenticado desde el token JWT

    Args:
        credentials: Credenciales HTTP Bearer
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == UUID(user_id)).first()

    if usuario is None:
        raise credentials_exception

    return usuario


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependency para verificar que el usuario esté activo

    Args:
        current_user: Usuario actual

    Returns:
        Usuario activo

    Raises:
        HTTPException: Si el usuario está inactivo
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user


def require_admin(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """
    Dependency para verificar que el usuario sea administrador

    Args:
        current_user: Usuario actual

    Returns:
        Usuario administrador

    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes"
        )
    return current_user


def require_admin_or_operador(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """
    Dependency para verificar que el usuario sea administrador u operador

    Args:
        current_user: Usuario actual

    Returns:
        Usuario con permisos

    Raises:
        HTTPException: Si el usuario no tiene permisos
    """
    if current_user.rol not in ["administrador", "operador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes"
        )
    return current_user
