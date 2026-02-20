"""
Endpoints API para Upload de archivos
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional

from app.core.deps import get_current_active_user
from app.models.usuario import Usuario
from app.services import upload_service

router = APIRouter()


@router.post("/documento")
async def upload_documento(
    file: UploadFile = File(...),
    folder: Optional[str] = Form("documentos"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Sube un documento (PDF, imagen, Word, Excel)

    - **file**: Archivo a subir
    - **folder**: Carpeta destino (opcional, default: documentos)

    Returns: URL del archivo subido y metadatos
    """
    result = await upload_service.upload_file(
        file=file,
        folder=folder,
        allowed_types=upload_service.TIPOS_TODOS,
        max_size_mb=10
    )
    return result


@router.post("/imagen")
async def upload_imagen(
    file: UploadFile = File(...),
    folder: Optional[str] = Form("imagenes"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Sube una imagen (JPEG, PNG, GIF, WebP)

    - **file**: Imagen a subir
    - **folder**: Carpeta destino (opcional, default: imagenes)

    Returns: URL de la imagen subida y metadatos
    """
    result = await upload_service.upload_file(
        file=file,
        folder=folder,
        allowed_types=upload_service.TIPOS_IMAGEN,
        max_size_mb=5
    )
    return result


@router.post("/equipo/{equipo_id}")
async def upload_documento_equipo(
    equipo_id: str,
    tipo_documento: str = Form(...),
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Sube un documento asociado a un equipo (camión/máquina)

    - **equipo_id**: ID del equipo
    - **tipo_documento**: Tipo (tarjeta_verde, seguro, vtv, cedula, otro)
    - **file**: Archivo a subir

    Returns: URL del archivo subido y metadatos
    """
    result = await upload_service.upload_file(
        file=file,
        folder=f"equipos/{equipo_id}/{tipo_documento}",
        allowed_types=upload_service.TIPOS_DOCUMENTO,
        max_size_mb=10
    )
    return {
        **result,
        "equipo_id": equipo_id,
        "tipo_documento": tipo_documento
    }
