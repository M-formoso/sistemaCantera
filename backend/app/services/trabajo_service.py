"""
Servicio de lógica de negocio para Trabajos/Reparaciones
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.trabajo import Trabajo, TrabajoRepuesto
from app.models.repuesto import Repuesto
from app.models.movimiento_stock import TipoMovimientoEnum
from app.schemas.trabajo import TrabajoCreate, TrabajoUpdate
from app.services import repuesto_service, camion_service


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    camion_id: Optional[UUID] = None
) -> List[dict]:
    """Obtiene todos los trabajos con paginación"""
    query = db.query(Trabajo)

    if camion_id:
        query = query.filter(Trabajo.camion_id == camion_id)

    trabajos = query.order_by(desc(Trabajo.fecha)).offset(skip).limit(limit).all()

    return [_trabajo_con_detalles(t) for t in trabajos]


def obtener_por_id(db: Session, trabajo_id: UUID) -> Optional[dict]:
    """Obtiene un trabajo por ID con detalles"""
    trabajo = db.query(Trabajo).filter(Trabajo.id == trabajo_id).first()
    if trabajo:
        return _trabajo_con_detalles(trabajo)
    return None


def obtener_por_camion(db: Session, camion_id: UUID) -> List[dict]:
    """Obtiene trabajos de un equipo específico"""
    trabajos = db.query(Trabajo).filter(
        Trabajo.camion_id == camion_id
    ).order_by(desc(Trabajo.fecha)).all()

    return [_trabajo_con_detalles(t) for t in trabajos]


def crear_con_repuestos(
    db: Session,
    trabajo_data: TrabajoCreate,
    usuario_id: UUID
) -> dict:
    """
    Crea un trabajo y descuenta repuestos del stock
    """
    # 1. Verificar que el equipo exista
    camion = camion_service.obtener_por_id(db, trabajo_data.camion_id)
    if not camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado"
        )

    # 2. Crear trabajo
    repuestos_data = trabajo_data.repuestos
    trabajo_dict = trabajo_data.model_dump(exclude={'repuestos'})

    db_trabajo = Trabajo(
        **trabajo_dict,
        created_by=usuario_id,
        costo_total=trabajo_data.costo_mano_obra
    )
    db.add(db_trabajo)
    db.flush()

    costo_repuestos = Decimal("0")

    # 3. Procesar repuestos
    for rep_asignado in repuestos_data:
        repuesto = repuesto_service.obtener_por_id(db, rep_asignado.repuesto_id)

        if not repuesto:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repuesto con ID {rep_asignado.repuesto_id} no encontrado"
            )

        # Verificar stock
        if repuesto.stock_actual < rep_asignado.cantidad:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente de '{repuesto.nombre}'. Stock: {repuesto.stock_actual}, requerido: {rep_asignado.cantidad}"
            )

        precio = repuesto.precio_unitario or Decimal("0")
        subtotal = rep_asignado.cantidad * precio

        # Crear relación trabajo-repuesto
        trabajo_repuesto = TrabajoRepuesto(
            trabajo_id=db_trabajo.id,
            repuesto_id=repuesto.id,
            cantidad=rep_asignado.cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )
        db.add(trabajo_repuesto)

        # Descontar stock
        equipo_identificador = camion.nombre or camion.codigo_interno if camion.categoria == 'maquina' else camion.patente
        equipo_label = "Máquina" if camion.categoria == 'maquina' else "Camión"

        repuesto_service.ajustar_stock(
            db=db,
            repuesto_id=repuesto.id,
            cantidad=rep_asignado.cantidad,
            tipo=TipoMovimientoEnum.EGRESO,
            usuario_id=usuario_id,
            referencia_tipo="trabajo",
            referencia_id=db_trabajo.id,
            observaciones=f"Trabajo/Reparación - {equipo_label} {equipo_identificador}"
        )

        costo_repuestos += subtotal

    # 4. Actualizar costo total
    db_trabajo.costo_total = trabajo_data.costo_mano_obra + costo_repuestos

    db.commit()
    db.refresh(db_trabajo)

    return _trabajo_con_detalles(db_trabajo)


def actualizar(db: Session, trabajo_id: UUID, trabajo_data: TrabajoUpdate) -> dict:
    """Actualiza un trabajo (no permite modificar repuestos)"""
    db_trabajo = db.query(Trabajo).filter(Trabajo.id == trabajo_id).first()

    if not db_trabajo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajo no encontrado"
        )

    update_data = trabajo_data.model_dump(exclude_unset=True)

    # Si se actualiza costo_mano_obra, recalcular total
    if 'costo_mano_obra' in update_data:
        costo_repuestos = sum(
            tr.subtotal or Decimal("0")
            for tr in db_trabajo.repuestos_utilizados
        )
        db_trabajo.costo_total = update_data['costo_mano_obra'] + costo_repuestos

    for field, value in update_data.items():
        if field != 'costo_total':
            setattr(db_trabajo, field, value)

    db.commit()
    db.refresh(db_trabajo)

    return _trabajo_con_detalles(db_trabajo)


def eliminar(db: Session, trabajo_id: UUID) -> dict:
    """Elimina un trabajo (NO devuelve stock)"""
    db_trabajo = db.query(Trabajo).filter(Trabajo.id == trabajo_id).first()

    if not db_trabajo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajo no encontrado"
        )

    # Eliminar relaciones
    db.query(TrabajoRepuesto).filter(
        TrabajoRepuesto.trabajo_id == trabajo_id
    ).delete()

    db.delete(db_trabajo)
    db.commit()

    return {"message": "Trabajo eliminado", "detail": "El stock NO fue devuelto."}


def _trabajo_con_detalles(trabajo: Trabajo) -> dict:
    """Convierte trabajo a dict con detalles"""
    # Identificador del equipo
    camion_identificador = None
    if trabajo.camion:
        if trabajo.camion.categoria == 'maquina':
            camion_identificador = trabajo.camion.nombre or trabajo.camion.codigo_interno
        else:
            camion_identificador = trabajo.camion.patente

    # Repuestos
    repuestos = []
    for tr in trabajo.repuestos_utilizados:
        repuestos.append({
            "id": tr.id,
            "repuesto_id": tr.repuesto_id,
            "nombre": tr.repuesto.nombre if tr.repuesto else "Desconocido",
            "codigo": tr.repuesto.codigo if tr.repuesto else None,
            "cantidad": tr.cantidad,
            "precio_unitario": tr.precio_unitario,
            "subtotal": tr.subtotal,
        })

    return {
        "id": trabajo.id,
        "camion_id": trabajo.camion_id,
        "fecha": trabajo.fecha,
        "descripcion": trabajo.descripcion,
        "responsable": trabajo.responsable,
        "costo_mano_obra": trabajo.costo_mano_obra,
        "costo_total": trabajo.costo_total,
        "observaciones": trabajo.observaciones,
        "created_by": trabajo.created_by,
        "created_at": trabajo.created_at,
        "updated_at": trabajo.updated_at,
        "camion_identificador": camion_identificador,
        "usuario_nombre": trabajo.usuario.nombre if trabajo.usuario else None,
        "repuestos": repuestos,
    }
