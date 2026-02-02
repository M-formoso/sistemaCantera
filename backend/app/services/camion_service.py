"""
Servicio de lógica de negocio para Camiones
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.camion import Camion
from app.schemas.camion import CamionCreate, CamionUpdate


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True
) -> List[Camion]:
    """
    Obtiene todos los camiones con paginación

    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar
        limit: Límite de registros a retornar
        solo_activos: Si es True, solo retorna camiones activos

    Returns:
        Lista de camiones
    """
    query = db.query(Camion)

    if solo_activos:
        query = query.filter(Camion.activo == True)

    return query.order_by(desc(Camion.created_at)).offset(skip).limit(limit).all()


def obtener_por_id(db: Session, camion_id: UUID) -> Optional[Camion]:
    """
    Obtiene un camión por ID

    Args:
        db: Sesión de base de datos
        camion_id: ID del camión

    Returns:
        Camión o None si no existe
    """
    return db.query(Camion).filter(Camion.id == camion_id).first()


def obtener_por_patente(db: Session, patente: str) -> Optional[Camion]:
    """
    Obtiene un camión por patente

    Args:
        db: Sesión de base de datos
        patente: Patente del camión

    Returns:
        Camión o None si no existe
    """
    return db.query(Camion).filter(Camion.patente == patente).first()


def crear(db: Session, camion_data: CamionCreate) -> Camion:
    """
    Crea un nuevo camión

    Args:
        db: Sesión de base de datos
        camion_data: Datos del camión a crear

    Returns:
        Camión creado

    Raises:
        HTTPException: Si la patente ya existe
    """
    # Verificar que la patente no exista
    if obtener_por_patente(db, camion_data.patente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un camión con la patente {camion_data.patente}"
        )

    db_camion = Camion(**camion_data.model_dump())
    db.add(db_camion)
    db.commit()
    db.refresh(db_camion)

    return db_camion


def actualizar(db: Session, camion_id: UUID, camion_data: CamionUpdate) -> Camion:
    """
    Actualiza un camión existente

    Args:
        db: Sesión de base de datos
        camion_id: ID del camión
        camion_data: Datos a actualizar

    Returns:
        Camión actualizado

    Raises:
        HTTPException: Si el camión no existe o la patente ya existe
    """
    db_camion = obtener_por_id(db, camion_id)

    if not db_camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    # Si se está actualizando la patente, verificar que no exista
    if camion_data.patente and camion_data.patente != db_camion.patente:
        if obtener_por_patente(db, camion_data.patente):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un camión con la patente {camion_data.patente}"
            )

    # Actualizar solo los campos proporcionados
    update_data = camion_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camion, field, value)

    db.commit()
    db.refresh(db_camion)

    return db_camion


def eliminar(db: Session, camion_id: UUID) -> Camion:
    """
    Elimina (soft delete) un camión

    Args:
        db: Sesión de base de datos
        camion_id: ID del camión

    Returns:
        Camión eliminado

    Raises:
        HTTPException: Si el camión no existe
    """
    db_camion = obtener_por_id(db, camion_id)

    if not db_camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    db_camion.activo = False
    db.commit()
    db.refresh(db_camion)

    return db_camion


def obtener_servicios(db: Session, camion_id: UUID):
    """
    Obtiene el historial de servicios de un camión

    Args:
        db: Sesión de base de datos
        camion_id: ID del camión

    Returns:
        Lista de servicios del camión

    Raises:
        HTTPException: Si el camión no existe
    """
    db_camion = obtener_por_id(db, camion_id)

    if not db_camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    return db_camion.servicios
