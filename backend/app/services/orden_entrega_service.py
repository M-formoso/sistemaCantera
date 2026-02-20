"""
Servicio de lógica de negocio para Órdenes de Entrega
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import date
from fastapi import HTTPException, status

from app.models.orden_entrega import OrdenEntrega, EstadoOrdenEntrega
from app.models.pesaje import Pesaje
from app.models.empresa import Empresa
from app.schemas.orden_entrega import OrdenEntregaCreate, OrdenEntregaUpdate


def _obtener_proximo_numero(db: Session) -> int:
    """Obtiene el próximo número de orden"""
    ultima_orden = db.query(OrdenEntrega).order_by(desc(OrdenEntrega.numero_orden)).first()
    return (ultima_orden.numero_orden + 1) if ultima_orden else 1


def obtener_todas(
    db: Session,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[OrdenEntrega]:
    """Obtiene todas las órdenes con filtros opcionales"""
    query = db.query(OrdenEntrega)

    if estado:
        query = query.filter(OrdenEntrega.estado == estado)

    if fecha_desde:
        query = query.filter(OrdenEntrega.fecha_entrega >= fecha_desde)

    if fecha_hasta:
        query = query.filter(OrdenEntrega.fecha_entrega <= fecha_hasta)

    ordenes = query.order_by(desc(OrdenEntrega.fecha_entrega), desc(OrdenEntrega.numero_orden)).offset(skip).limit(limit).all()

    # Enriquecer con nombre del cliente
    for orden in ordenes:
        if orden.cliente_id and orden.cliente:
            orden.cliente_nombre_completo = orden.cliente.nombre
        else:
            orden.cliente_nombre_completo = orden.cliente_nombre

        # Calcular campos
        orden.cargas_pendientes = orden.cantidad_cargas - orden.cargas_entregadas
        orden.porcentaje_completado = (orden.cargas_entregadas / orden.cantidad_cargas * 100) if orden.cantidad_cargas > 0 else 0

    return ordenes


def obtener_pendientes(db: Session) -> List[OrdenEntrega]:
    """Obtiene órdenes pendientes o en proceso"""
    ordenes = db.query(OrdenEntrega).filter(
        OrdenEntrega.estado.in_([
            EstadoOrdenEntrega.pendiente.value,
            EstadoOrdenEntrega.en_proceso.value
        ])
    ).order_by(OrdenEntrega.fecha_entrega, OrdenEntrega.numero_orden).all()

    for orden in ordenes:
        if orden.cliente_id and orden.cliente:
            orden.cliente_nombre_completo = orden.cliente.nombre
        else:
            orden.cliente_nombre_completo = orden.cliente_nombre

        orden.cargas_pendientes = orden.cantidad_cargas - orden.cargas_entregadas
        orden.porcentaje_completado = (orden.cargas_entregadas / orden.cantidad_cargas * 100) if orden.cantidad_cargas > 0 else 0

    return ordenes


def obtener_por_id(db: Session, orden_id: UUID) -> Optional[OrdenEntrega]:
    """Obtiene una orden por ID"""
    orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if orden:
        if orden.cliente_id and orden.cliente:
            orden.cliente_nombre_completo = orden.cliente.nombre
        else:
            orden.cliente_nombre_completo = orden.cliente_nombre

        orden.cargas_pendientes = orden.cantidad_cargas - orden.cargas_entregadas
        orden.porcentaje_completado = (orden.cargas_entregadas / orden.cantidad_cargas * 100) if orden.cantidad_cargas > 0 else 0

    return orden


def obtener_con_pesajes(db: Session, orden_id: UUID) -> Optional[OrdenEntrega]:
    """Obtiene una orden con sus pesajes asociados"""
    orden = obtener_por_id(db, orden_id)

    if orden:
        # Cargar pesajes asociados
        pesajes = db.query(Pesaje).filter(Pesaje.orden_entrega_id == orden_id).order_by(Pesaje.fecha).all()

        # Agregar patente a cada pesaje
        for pesaje in pesajes:
            if pesaje.camion_id and pesaje.camion:
                pesaje.patente = pesaje.camion.patente
            else:
                pesaje.patente = pesaje.patente_externa

        orden.pesajes_lista = pesajes

    return orden


def crear(db: Session, orden_data: OrdenEntregaCreate, usuario_id: UUID) -> OrdenEntrega:
    """Crea una nueva orden de entrega"""
    # Verificar cliente si se proporciona
    cliente_empresa = None
    if orden_data.cliente_id:
        cliente_empresa = db.query(Empresa).filter(Empresa.id == orden_data.cliente_id).first()
        if not cliente_empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )

    # Obtener próximo número
    numero_orden = _obtener_proximo_numero(db)

    # Calcular peso total estimado
    peso_total_estimado = None
    if orden_data.peso_estimado_carga:
        peso_total_estimado = orden_data.peso_estimado_carga * orden_data.cantidad_cargas

    # Crear orden
    db_orden = OrdenEntrega(
        numero_orden=numero_orden,
        fecha_entrega=orden_data.fecha_entrega,
        cliente_id=orden_data.cliente_id,
        cliente_nombre=orden_data.cliente_nombre or (cliente_empresa.nombre if cliente_empresa else None),
        material=orden_data.material,
        cantidad_cargas=orden_data.cantidad_cargas,
        cargas_entregadas=0,
        peso_estimado_carga=orden_data.peso_estimado_carga,
        peso_total_estimado=peso_total_estimado,
        peso_total_entregado=Decimal("0"),
        estado=EstadoOrdenEntrega.pendiente.value,
        solicitante=orden_data.solicitante,
        contacto_cliente=orden_data.contacto_cliente,
        telefono_contacto=orden_data.telefono_contacto,
        direccion_entrega=orden_data.direccion_entrega,
        observaciones=orden_data.observaciones,
        created_by=usuario_id
    )

    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)

    # Agregar campos calculados para respuesta
    db_orden.cargas_pendientes = db_orden.cantidad_cargas
    db_orden.porcentaje_completado = 0
    db_orden.cliente_nombre_completo = db_orden.cliente_nombre

    return db_orden


def actualizar(db: Session, orden_id: UUID, orden_data: OrdenEntregaUpdate) -> OrdenEntrega:
    """Actualiza una orden de entrega"""
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    # No permitir editar órdenes completadas o canceladas
    if db_orden.estado in [EstadoOrdenEntrega.completada.value, EstadoOrdenEntrega.cancelada.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar una orden completada o cancelada"
        )

    update_data = orden_data.model_dump(exclude_unset=True)

    # Si se cambia cantidad de cargas, validar que no sea menor a las ya entregadas
    if 'cantidad_cargas' in update_data:
        if update_data['cantidad_cargas'] < db_orden.cargas_entregadas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La cantidad de cargas no puede ser menor a las ya entregadas ({db_orden.cargas_entregadas})"
            )

    # Aplicar actualizaciones
    for field, value in update_data.items():
        setattr(db_orden, field, value)

    # Recalcular peso total estimado si cambió
    if db_orden.peso_estimado_carga and db_orden.cantidad_cargas:
        db_orden.peso_total_estimado = db_orden.peso_estimado_carga * db_orden.cantidad_cargas

    db.commit()
    db.refresh(db_orden)

    return obtener_por_id(db, orden_id)


def registrar_entrega(db: Session, orden_id: UUID, pesaje_id: UUID) -> OrdenEntrega:
    """
    Registra una entrega (pesaje) en la orden
    Incrementa cargas_entregadas y actualiza peso_total_entregado
    """
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    if db_orden.estado in [EstadoOrdenEntrega.completada.value, EstadoOrdenEntrega.cancelada.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden agregar entregas a una orden completada o cancelada"
        )

    # Obtener pesaje
    pesaje = db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()
    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Asociar pesaje a la orden
    pesaje.orden_entrega_id = orden_id

    # Incrementar cargas entregadas
    db_orden.cargas_entregadas += 1

    # Actualizar peso total entregado
    peso_actual = db_orden.peso_total_entregado or Decimal("0")
    db_orden.peso_total_entregado = peso_actual + (pesaje.peso_neto or Decimal("0"))

    # Actualizar estado
    if db_orden.cargas_entregadas >= db_orden.cantidad_cargas:
        db_orden.estado = EstadoOrdenEntrega.completada.value
    elif db_orden.cargas_entregadas > 0:
        db_orden.estado = EstadoOrdenEntrega.en_proceso.value

    db.commit()
    db.refresh(db_orden)

    return obtener_por_id(db, orden_id)


def desasociar_pesaje(db: Session, orden_id: UUID, pesaje_id: UUID) -> OrdenEntrega:
    """
    Desasocia un pesaje de la orden
    Decrementa cargas_entregadas y actualiza peso_total_entregado
    """
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    pesaje = db.query(Pesaje).filter(
        Pesaje.id == pesaje_id,
        Pesaje.orden_entrega_id == orden_id
    ).first()

    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado o no asociado a esta orden"
        )

    # Desasociar pesaje
    pesaje.orden_entrega_id = None

    # Decrementar cargas entregadas
    if db_orden.cargas_entregadas > 0:
        db_orden.cargas_entregadas -= 1

    # Actualizar peso total entregado
    peso_actual = db_orden.peso_total_entregado or Decimal("0")
    db_orden.peso_total_entregado = max(Decimal("0"), peso_actual - (pesaje.peso_neto or Decimal("0")))

    # Actualizar estado
    if db_orden.cargas_entregadas == 0:
        db_orden.estado = EstadoOrdenEntrega.pendiente.value
    elif db_orden.cargas_entregadas < db_orden.cantidad_cargas:
        db_orden.estado = EstadoOrdenEntrega.en_proceso.value

    db.commit()
    db.refresh(db_orden)

    return obtener_por_id(db, orden_id)


def cancelar(db: Session, orden_id: UUID) -> OrdenEntrega:
    """Cancela una orden de entrega"""
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    if db_orden.estado == EstadoOrdenEntrega.completada.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar una orden ya completada"
        )

    db_orden.estado = EstadoOrdenEntrega.cancelada.value
    db.commit()
    db.refresh(db_orden)

    return obtener_por_id(db, orden_id)


def completar_manualmente(db: Session, orden_id: UUID) -> OrdenEntrega:
    """Marca una orden como completada manualmente"""
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    db_orden.estado = EstadoOrdenEntrega.completada.value
    db.commit()
    db.refresh(db_orden)

    return obtener_por_id(db, orden_id)


def eliminar(db: Session, orden_id: UUID) -> dict:
    """Elimina una orden de entrega"""
    db_orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()

    if not db_orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    # Si tiene pesajes asociados, desasociarlos primero
    db.query(Pesaje).filter(Pesaje.orden_entrega_id == orden_id).update(
        {Pesaje.orden_entrega_id: None}
    )

    db.delete(db_orden)
    db.commit()

    return {"message": "Orden de entrega eliminada correctamente"}
