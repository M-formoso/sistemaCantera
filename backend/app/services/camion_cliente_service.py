"""
Servicio de lógica de negocio para Camiones de Clientes
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.camion_cliente import CamionCliente
from app.models.empresa import Empresa
from app.schemas.empresa import CamionClienteCreate, CamionClienteUpdate


def obtener_por_cliente(
    db: Session,
    cliente_id: UUID,
    solo_activos: bool = True
) -> List[CamionCliente]:
    """Obtiene todos los camiones de un cliente"""
    query = db.query(CamionCliente).filter(CamionCliente.cliente_id == cliente_id)

    if solo_activos:
        query = query.filter(CamionCliente.activo == True)

    return query.order_by(CamionCliente.patente).all()


def obtener_por_id(db: Session, camion_id: UUID) -> Optional[CamionCliente]:
    """Obtiene un camión por ID"""
    return db.query(CamionCliente).filter(CamionCliente.id == camion_id).first()


def buscar_por_patente(db: Session, patente: str) -> Optional[CamionCliente]:
    """
    Busca un camión de cliente por patente exacta.
    Retorna el camión con su cliente asociado.
    """
    patente = patente.upper().strip()

    return db.query(CamionCliente).filter(
        func.upper(CamionCliente.patente) == patente,
        CamionCliente.activo == True
    ).first()


def buscar_patentes(
    db: Session,
    patente: str,
    limit: int = 10
) -> List[CamionCliente]:
    """
    Busca camiones de clientes por patente parcial (para autocompletado).
    """
    patente = patente.upper().strip()

    return db.query(CamionCliente).filter(
        func.upper(CamionCliente.patente).like(f"{patente}%"),
        CamionCliente.activo == True
    ).limit(limit).all()


def crear(
    db: Session,
    cliente_id: UUID,
    camion_data: CamionClienteCreate
) -> CamionCliente:
    """Crea un nuevo camión para un cliente"""

    # Verificar que el cliente exista
    cliente = db.query(Empresa).filter(Empresa.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Verificar que el cliente sea de tipo 'cliente'
    if cliente.tipo != "cliente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden agregar camiones a clientes"
        )

    # Verificar que no exista la patente para este cliente
    patente_upper = camion_data.patente.upper().strip()
    existente = db.query(CamionCliente).filter(
        CamionCliente.cliente_id == cliente_id,
        func.upper(CamionCliente.patente) == patente_upper
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este cliente ya tiene registrada esa patente"
        )

    # Crear el camión
    db_camion = CamionCliente(
        cliente_id=cliente_id,
        patente=patente_upper,
        descripcion=camion_data.descripcion,
        chofer_habitual=camion_data.chofer_habitual
    )

    db.add(db_camion)
    db.commit()
    db.refresh(db_camion)

    return db_camion


def actualizar(
    db: Session,
    camion_id: UUID,
    camion_data: CamionClienteUpdate
) -> CamionCliente:
    """Actualiza un camión de cliente"""

    db_camion = obtener_por_id(db, camion_id)

    if not db_camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    update_data = camion_data.model_dump(exclude_unset=True)

    # Si se actualiza la patente, verificar que no exista para el mismo cliente
    if 'patente' in update_data:
        patente_upper = update_data['patente'].upper().strip()
        existente = db.query(CamionCliente).filter(
            CamionCliente.cliente_id == db_camion.cliente_id,
            func.upper(CamionCliente.patente) == patente_upper,
            CamionCliente.id != camion_id
        ).first()

        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este cliente ya tiene registrada esa patente"
            )

        update_data['patente'] = patente_upper

    for field, value in update_data.items():
        setattr(db_camion, field, value)

    db.commit()
    db.refresh(db_camion)

    return db_camion


def eliminar(db: Session, camion_id: UUID) -> dict:
    """Elimina (soft delete) un camión de cliente"""

    db_camion = obtener_por_id(db, camion_id)

    if not db_camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    db_camion.activo = False
    db.commit()

    return {"message": "Camión eliminado correctamente"}


def obtener_cliente_por_patente(db: Session, patente: str) -> Optional[dict]:
    """
    Busca un cliente por la patente de uno de sus camiones.
    Retorna un diccionario con los datos del cliente y del camión.
    """
    patente = patente.upper().strip()

    camion = db.query(CamionCliente).filter(
        func.upper(CamionCliente.patente) == patente,
        CamionCliente.activo == True
    ).first()

    if not camion:
        return None

    cliente = db.query(Empresa).filter(Empresa.id == camion.cliente_id).first()

    if not cliente:
        return None

    return {
        "cliente_id": cliente.id,
        "cliente_nombre": cliente.nombre,
        "cliente_cuit": cliente.cuit,
        "cliente_direccion": cliente.direccion,
        "cliente_telefono": cliente.telefono,
        "camion_id": camion.id,
        "camion_patente": camion.patente,
        "camion_descripcion": camion.descripcion,
        "chofer_habitual": camion.chofer_habitual,
    }
