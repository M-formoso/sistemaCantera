"""
Servicio de lógica de negocio para Empresas (Clientes y Transportistas)
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional, Literal
from fastapi import HTTPException, status

from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate


def obtener_todos(
    db: Session,
    tipo: Optional[Literal["cliente", "transportista"]] = None,
    solo_activos: bool = True,
    skip: int = 0,
    limit: int = 500
) -> List[Empresa]:
    """Obtiene todas las empresas, opcionalmente filtradas por tipo"""
    query = db.query(Empresa)

    if tipo:
        query = query.filter(Empresa.tipo == tipo)

    if solo_activos:
        query = query.filter(Empresa.activo == True)

    return query.order_by(Empresa.nombre).offset(skip).limit(limit).all()


def obtener_clientes(db: Session, solo_activos: bool = True) -> List[Empresa]:
    """Obtiene solo clientes"""
    return obtener_todos(db, tipo="cliente", solo_activos=solo_activos)


def obtener_transportistas(db: Session, solo_activos: bool = True) -> List[Empresa]:
    """Obtiene solo transportistas"""
    return obtener_todos(db, tipo="transportista", solo_activos=solo_activos)


def obtener_por_id(db: Session, empresa_id: UUID) -> Optional[Empresa]:
    """Obtiene una empresa por ID"""
    return db.query(Empresa).filter(Empresa.id == empresa_id).first()


def buscar_por_nombre(
    db: Session,
    nombre: str,
    tipo: Optional[Literal["cliente", "transportista"]] = None,
    limit: int = 10
) -> List[Empresa]:
    """
    Busca empresas por nombre (para autocompletado)
    Busca coincidencias parciales al inicio del nombre
    """
    query = db.query(Empresa).filter(
        Empresa.activo == True,
        Empresa.nombre.ilike(f"{nombre}%")
    )

    if tipo:
        query = query.filter(Empresa.tipo == tipo)

    return query.order_by(Empresa.nombre).limit(limit).all()


def crear(db: Session, empresa_data: EmpresaCreate) -> Empresa:
    """Crea una nueva empresa"""
    # Verificar si ya existe una con el mismo nombre y tipo
    existente = db.query(Empresa).filter(
        Empresa.nombre.ilike(empresa_data.nombre),
        Empresa.tipo == empresa_data.tipo
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un {empresa_data.tipo} con ese nombre"
        )

    db_empresa = Empresa(**empresa_data.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)

    return db_empresa


def actualizar(db: Session, empresa_id: UUID, empresa_data: EmpresaUpdate) -> Empresa:
    """Actualiza una empresa existente"""
    db_empresa = obtener_por_id(db, empresa_id)

    if not db_empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    update_data = empresa_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_empresa, field, value)

    db.commit()
    db.refresh(db_empresa)

    return db_empresa


def eliminar(db: Session, empresa_id: UUID) -> Empresa:
    """Elimina (soft delete) una empresa"""
    db_empresa = obtener_por_id(db, empresa_id)

    if not db_empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    db_empresa.activo = False
    db.commit()
    db.refresh(db_empresa)

    return db_empresa
