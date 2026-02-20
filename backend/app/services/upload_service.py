"""
Servicio de upload de archivos a Cloudinary
"""
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from typing import Optional
import uuid

from app.core.config import settings


def _configure_cloudinary():
    """Configura Cloudinary con las credenciales"""
    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary no está configurado. Contacte al administrador."
        )

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )


async def upload_file(
    file: UploadFile,
    folder: str = "documentos",
    allowed_types: Optional[list] = None,
    max_size_mb: int = 10
) -> dict:
    """
    Sube un archivo a Cloudinary

    Args:
        file: Archivo a subir
        folder: Carpeta en Cloudinary (ej: "documentos", "equipos")
        allowed_types: Tipos MIME permitidos (None = todos)
        max_size_mb: Tamaño máximo en MB

    Returns:
        dict con url, public_id, formato, tamaño
    """
    _configure_cloudinary()

    # Validar tipo de archivo
    if allowed_types and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Tipos válidos: {', '.join(allowed_types)}"
        )

    # Leer contenido del archivo
    content = await file.read()

    # Validar tamaño
    size_mb = len(content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo excede el tamaño máximo de {max_size_mb}MB"
        )

    # Generar nombre único
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_name = f"{uuid.uuid4().hex[:12]}"
    if file_extension:
        unique_name += f".{file_extension}"

    try:
        # Determinar resource_type basado en content_type
        if file.content_type and file.content_type.startswith('image/'):
            resource_type = "image"
        elif file.content_type == 'application/pdf':
            resource_type = "raw"
        else:
            resource_type = "auto"

        # Subir a Cloudinary
        result = cloudinary.uploader.upload(
            content,
            folder=f"cantera/{folder}",
            public_id=unique_name,
            resource_type=resource_type,
            overwrite=True
        )

        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "formato": result.get("format", file_extension),
            "tamaño": len(content),
            "nombre_original": file.filename,
            "content_type": file.content_type
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )


async def delete_file(public_id: str) -> bool:
    """
    Elimina un archivo de Cloudinary

    Args:
        public_id: ID público del archivo en Cloudinary

    Returns:
        True si se eliminó correctamente
    """
    _configure_cloudinary()

    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False


# Tipos de archivo permitidos por categoría
TIPOS_IMAGEN = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
]

TIPOS_DOCUMENTO = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

TIPOS_TODOS = TIPOS_IMAGEN + TIPOS_DOCUMENTO + [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]
