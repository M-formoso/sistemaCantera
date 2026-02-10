"""
Servicio de lógica de negocio para Repuestos
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.repuesto import Repuesto
from app.models.movimiento_stock import MovimientoStock, TipoMovimientoEnum
from app.schemas.repuesto import RepuestoCreate, RepuestoUpdate


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True
) -> List[Repuesto]:
    """Obtiene todos los repuestos con paginación"""
    query = db.query(Repuesto)

    if solo_activos:
        query = query.filter(Repuesto.activo == True)

    return query.order_by(desc(Repuesto.created_at)).offset(skip).limit(limit).all()


def obtener_por_id(db: Session, repuesto_id: UUID) -> Optional[Repuesto]:
    """Obtiene un repuesto por ID"""
    return db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()


def obtener_por_codigo(db: Session, codigo: str) -> Optional[Repuesto]:
    """Obtiene un repuesto por código"""
    return db.query(Repuesto).filter(Repuesto.codigo == codigo).first()


def obtener_stock_bajo(db: Session) -> List[Repuesto]:
    """
    Obtiene repuestos con stock bajo (stock_actual <= stock_minimo)

    Returns:
        Lista de repuestos con stock bajo
    """
    return db.query(Repuesto).filter(
        Repuesto.stock_actual <= Repuesto.stock_minimo,
        Repuesto.activo == True
    ).order_by(Repuesto.stock_actual).all()


def crear(db: Session, repuesto_data: RepuestoCreate) -> Repuesto:
    """
    Crea un nuevo repuesto

    Raises:
        HTTPException: Si el código ya existe
    """
    # Verificar que el código no exista
    if repuesto_data.codigo and obtener_por_codigo(db, repuesto_data.codigo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un repuesto con el código {repuesto_data.codigo}"
        )

    db_repuesto = Repuesto(**repuesto_data.model_dump())
    db.add(db_repuesto)
    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def actualizar(db: Session, repuesto_id: UUID, repuesto_data: RepuestoUpdate) -> Repuesto:
    """Actualiza un repuesto existente"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Si se está actualizando el código, verificar que no exista
    if repuesto_data.codigo and repuesto_data.codigo != db_repuesto.codigo:
        if obtener_por_codigo(db, repuesto_data.codigo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un repuesto con el código {repuesto_data.codigo}"
            )

    update_data = repuesto_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_repuesto, field, value)

    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def eliminar(db: Session, repuesto_id: UUID) -> Repuesto:
    """Elimina (soft delete) un repuesto"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    db_repuesto.activo = False
    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def ajustar_stock(
    db: Session,
    repuesto_id: UUID,
    cantidad: Decimal,
    tipo: TipoMovimientoEnum,
    usuario_id: UUID,
    referencia_tipo: str = "ajuste",
    referencia_id: Optional[UUID] = None,
    observaciones: Optional[str] = None
) -> Repuesto:
    """
    Ajusta el stock de un repuesto y crea un movimiento

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        cantidad: Cantidad a ajustar
        tipo: Tipo de movimiento (ingreso/egreso)
        usuario_id: ID del usuario que realiza el ajuste
        referencia_tipo: Tipo de referencia (ajuste, servicio, etc)
        referencia_id: ID de la referencia (opcional)
        observaciones: Observaciones del movimiento

    Returns:
        Repuesto actualizado

    Raises:
        HTTPException: Si no hay stock suficiente para egreso
    """
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Calcular nuevo stock
    if tipo == TipoMovimientoEnum.INGRESO:
        nuevo_stock = db_repuesto.stock_actual + cantidad
    else:  # EGRESO
        if db_repuesto.stock_actual < cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock actual: {db_repuesto.stock_actual}, requerido: {cantidad}"
            )
        nuevo_stock = db_repuesto.stock_actual - cantidad

    # Actualizar stock
    db_repuesto.stock_actual = nuevo_stock

    # Crear movimiento de stock
    movimiento = MovimientoStock(
        repuesto_id=repuesto_id,
        tipo=tipo,
        cantidad=cantidad,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        observaciones=observaciones,
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def obtener_movimientos(db: Session, repuesto_id: UUID) -> List[dict]:
    """Obtiene el historial de movimientos de un repuesto con info del usuario"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    movimientos = db.query(MovimientoStock).filter(
        MovimientoStock.repuesto_id == repuesto_id
    ).order_by(desc(MovimientoStock.created_at)).all()

    # Agregar nombre de usuario a cada movimiento
    resultado = []
    for mov in movimientos:
        resultado.append({
            "id": str(mov.id),
            "tipo": mov.tipo.value,
            "cantidad": float(mov.cantidad),
            "observaciones": mov.observaciones,
            "referencia_tipo": mov.referencia_tipo,
            "created_at": mov.created_at.isoformat(),
            "usuario_id": str(mov.usuario_id),
            "usuario_nombre": mov.usuario.nombre if mov.usuario else "Sistema"
        })

    return resultado
