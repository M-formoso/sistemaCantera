from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.deps import get_db, get_current_active_user
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, AccessTokenResponse
from app.schemas.usuario import UsuarioSchema, UsuarioChangePassword
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/debug-admin")
async def debug_admin(db: Session = Depends(get_db)):
    """Debug endpoint - REMOVER EN PRODUCCION"""
    usuario = db.query(Usuario).filter(Usuario.email == "admin@canteralarufina.com.ar").first()
    if not usuario:
        return {"error": "Usuario admin no existe"}
    return {
        "email": usuario.email,
        "nombre": usuario.nombre,
        "activo": usuario.activo,
        "rol": usuario.rol,
        "tiene_password": bool(usuario.password_hash),
        "password_hash_prefix": usuario.password_hash[:20] if usuario.password_hash else None
    }


@router.get("/test-password/{password}")
async def test_password(password: str, db: Session = Depends(get_db)):
    """Test password - REMOVER EN PRODUCCION"""
    usuario = db.query(Usuario).filter(Usuario.email == "admin@canteralarufina.com.ar").first()
    if not usuario:
        return {"error": "Usuario no existe"}

    is_valid = verify_password(password, usuario.password_hash)
    return {
        "password_recibido": password,
        "es_valido": is_valid
    }


@router.get("/reset-admin-password")
async def reset_admin_password(db: Session = Depends(get_db)):
    """Reset admin password - REMOVER EN PRODUCCION"""
    usuario = db.query(Usuario).filter(Usuario.email == "admin@canteralarufina.com.ar").first()
    if not usuario:
        return {"error": "Usuario no existe"}

    new_password = "Cantera2024!"
    usuario.password_hash = get_password_hash(new_password)
    db.commit()

    return {
        "mensaje": "Contraseña reseteada",
        "email": "admin@canteralarufina.com.ar",
        "nueva_password": new_password
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login de usuario

    Retorna access token y refresh token
    """
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()

    if not usuario or not verify_password(credentials.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.utcnow()
    db.commit()

    # Crear tokens
    token_data = {"sub": str(usuario.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Renovar access token usando refresh token
    """
    try:
        payload = decode_token(request.refresh_token)
        token_type = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        user_id = payload.get("sub")
        usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

        if not usuario or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo"
            )

        # Crear nuevo access token
        token_data = {"sub": str(usuario.id)}
        access_token = create_access_token(token_data)

        return AccessTokenResponse(access_token=access_token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


@router.get("/me", response_model=UsuarioSchema)
async def get_current_user_info(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener información del usuario autenticado
    """
    return current_user


@router.put("/change-password")
async def change_password(
    password_data: UsuarioChangePassword,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar contraseña del usuario autenticado
    """
    # Verificar contraseña actual
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Contraseña actualizada correctamente"}
