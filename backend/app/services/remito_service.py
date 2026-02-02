"""
Servicio de lógica de negocio para Remitos
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.remito import Remito
from app.models.pesaje import Pesaje
from app.schemas.remito import RemitoCreate
from app.services import pesaje_service


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Remito]:
    """Obtiene todos los remitos con paginación"""
    return db.query(Remito).order_by(desc(Remito.numero_remito)).offset(skip).limit(limit).all()


def obtener_por_id(db: Session, remito_id: UUID) -> Optional[Remito]:
    """Obtiene un remito por ID"""
    return db.query(Remito).filter(Remito.id == remito_id).first()


def obtener_por_numero(db: Session, numero_remito: int) -> Optional[Remito]:
    """Obtiene un remito por número"""
    return db.query(Remito).filter(Remito.numero_remito == numero_remito).first()


def _obtener_proximo_numero(db: Session) -> int:
    """Obtiene el próximo número de remito"""
    ultimo_remito = db.query(Remito).order_by(desc(Remito.numero_remito)).first()
    return (ultimo_remito.numero_remito + 1) if ultimo_remito else 1


def crear(db: Session, remito_data: RemitoCreate, usuario_id: UUID) -> Remito:
    """
    Crea un remito manualmente

    Args:
        db: Sesión de base de datos
        remito_data: Datos del remito
        usuario_id: ID del usuario

    Returns:
        Remito creado
    """
    # Obtener próximo número
    numero_remito = _obtener_proximo_numero(db)

    # Si tiene pesaje_id, verificar que exista
    if remito_data.pesaje_id:
        pesaje = pesaje_service.obtener_por_id(db, remito_data.pesaje_id)
        if not pesaje:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pesaje no encontrado"
            )
        if pesaje.remito_generado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este pesaje ya tiene un remito generado"
            )

    # Crear remito
    db_remito = Remito(
        **remito_data.model_dump(),
        numero_remito=numero_remito,
        created_by=usuario_id
    )

    db.add(db_remito)

    # Marcar pesaje como procesado si corresponde
    if remito_data.pesaje_id:
        pesaje = db.query(Pesaje).filter(Pesaje.id == remito_data.pesaje_id).first()
        pesaje.remito_generado = True

    db.commit()
    db.refresh(db_remito)

    return db_remito


def generar_desde_pesaje(db: Session, pesaje_id: UUID, usuario_id: UUID) -> Remito:
    """
    Genera un remito automáticamente desde un pesaje

    Este es el flujo principal de generación de remitos:
    1. Verifica que el pesaje exista
    2. Verifica que no tenga remito generado
    3. Crea remito con datos del pesaje
    4. Marca pesaje como procesado
    5. (Opcional) Genera PDF en background con Celery

    Args:
        db: Sesión de base de datos
        pesaje_id: ID del pesaje
        usuario_id: ID del usuario

    Returns:
        Remito generado

    Raises:
        HTTPException: Si el pesaje no existe o ya tiene remito
    """
    # Verificar que el pesaje exista
    pesaje = pesaje_service.obtener_por_id(db, pesaje_id)
    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Verificar que no tenga remito generado
    if pesaje.remito_generado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pesaje ya tiene un remito generado"
        )

    # Obtener próximo número de remito
    numero_remito = _obtener_proximo_numero(db)

    # Crear remito con datos del pesaje
    db_remito = Remito(
        numero_remito=numero_remito,
        pesaje_id=pesaje.id,
        fecha=pesaje.fecha.date(),
        cliente=pesaje.cliente_destino or "Cliente no especificado",
        producto=pesaje.material or "Material no especificado",
        peso_neto=pesaje.peso_neto,
        camion_patente=pesaje.camion.patente,
        chofer=pesaje.chofer,
        observaciones=pesaje.observaciones,
        created_by=usuario_id
    )

    db.add(db_remito)

    # Marcar pesaje como procesado
    pesaje.remito_generado = True

    db.commit()
    db.refresh(db_remito)

    # Generar PDF en background (opcional, con Celery)
    try:
        from app.tasks.reportes import generar_pdf_remito
        generar_pdf_remito.delay(str(db_remito.id))
    except ImportError:
        print(f"⚠️ Celery no disponible. PDF de remito #{numero_remito} no generado")

    return db_remito


def eliminar(db: Session, remito_id: UUID) -> dict:
    """
    Elimina un remito

    Al eliminar, marca el pesaje asociado como no procesado (si existe)
    """
    db_remito = obtener_por_id(db, remito_id)

    if not db_remito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remito no encontrado"
        )

    # Si tiene pesaje asociado, desmarcarlo
    if db_remito.pesaje_id:
        pesaje = db.query(Pesaje).filter(Pesaje.id == db_remito.pesaje_id).first()
        if pesaje:
            pesaje.remito_generado = False

    db.delete(db_remito)
    db.commit()

    return {"message": "Remito eliminado correctamente"}
