"""
Endpoints API para Órdenes de Entrega
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.orden_entrega import (
    OrdenEntregaSchema,
    OrdenEntregaCreate,
    OrdenEntregaUpdate,
    OrdenEntregaListItem,
    OrdenEntregaConPesajes,
    PesajeResumen
)
from app.services import orden_entrega_service

router = APIRouter()


@router.get("/", response_model=List[OrdenEntregaSchema])
async def listar_ordenes(
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las órdenes de entrega con filtros opcionales"""
    ordenes = orden_entrega_service.obtener_todas(
        db, estado, fecha_desde, fecha_hasta, skip, limit
    )

    result = []
    for orden in ordenes:
        data = OrdenEntregaSchema.model_validate(orden)
        data.cliente_nombre_completo = orden.cliente_nombre_completo
        data.cargas_pendientes = orden.cargas_pendientes
        data.porcentaje_completado = orden.porcentaje_completado
        result.append(data)

    return result


@router.get("/pendientes", response_model=List[OrdenEntregaSchema])
async def listar_ordenes_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista órdenes pendientes o en proceso"""
    ordenes = orden_entrega_service.obtener_pendientes(db)

    result = []
    for orden in ordenes:
        data = OrdenEntregaSchema.model_validate(orden)
        data.cliente_nombre_completo = orden.cliente_nombre_completo
        data.cargas_pendientes = orden.cargas_pendientes
        data.porcentaje_completado = orden.porcentaje_completado
        result.append(data)

    return result


@router.get("/{orden_id}", response_model=OrdenEntregaSchema)
async def obtener_orden(
    orden_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una orden de entrega por ID"""
    orden = orden_entrega_service.obtener_por_id(db, orden_id)
    if not orden:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    data = OrdenEntregaSchema.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado
    return data


@router.get("/{orden_id}/detalle", response_model=OrdenEntregaConPesajes)
async def obtener_orden_con_pesajes(
    orden_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una orden con sus pesajes asociados"""
    orden = orden_entrega_service.obtener_con_pesajes(db, orden_id)
    if not orden:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de entrega no encontrada"
        )

    data = OrdenEntregaConPesajes.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado

    # Mapear pesajes
    if hasattr(orden, 'pesajes_lista'):
        data.pesajes = [
            PesajeResumen(
                id=p.id,
                numero_pesaje=p.numero_pesaje,
                fecha=p.fecha,
                peso_neto=p.peso_neto,
                material=p.material,
                chofer=p.chofer,
                patente=p.patente if hasattr(p, 'patente') else None
            )
            for p in orden.pesajes_lista
        ]

    return data


@router.post("/", response_model=OrdenEntregaSchema, status_code=201)
async def crear_orden(
    orden: OrdenEntregaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Crea una nueva orden de entrega"""
    nueva_orden = orden_entrega_service.crear(db, orden, current_user.id)

    data = OrdenEntregaSchema.model_validate(nueva_orden)
    data.cliente_nombre_completo = nueva_orden.cliente_nombre_completo
    data.cargas_pendientes = nueva_orden.cargas_pendientes
    data.porcentaje_completado = nueva_orden.porcentaje_completado
    return data


@router.put("/{orden_id}", response_model=OrdenEntregaSchema)
async def actualizar_orden(
    orden_id: UUID,
    orden: OrdenEntregaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Actualiza una orden de entrega"""
    orden_actualizada = orden_entrega_service.actualizar(db, orden_id, orden)

    data = OrdenEntregaSchema.model_validate(orden_actualizada)
    data.cliente_nombre_completo = orden_actualizada.cliente_nombre_completo
    data.cargas_pendientes = orden_actualizada.cargas_pendientes
    data.porcentaje_completado = orden_actualizada.porcentaje_completado
    return data


@router.post("/{orden_id}/registrar-entrega/{pesaje_id}", response_model=OrdenEntregaSchema)
async def registrar_entrega(
    orden_id: UUID,
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Registra un pesaje como entrega de la orden"""
    orden = orden_entrega_service.registrar_entrega(db, orden_id, pesaje_id)

    data = OrdenEntregaSchema.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado
    return data


@router.delete("/{orden_id}/desasociar-pesaje/{pesaje_id}", response_model=OrdenEntregaSchema)
async def desasociar_pesaje(
    orden_id: UUID,
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Desasocia un pesaje de la orden"""
    orden = orden_entrega_service.desasociar_pesaje(db, orden_id, pesaje_id)

    data = OrdenEntregaSchema.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado
    return data


@router.post("/{orden_id}/cancelar", response_model=OrdenEntregaSchema)
async def cancelar_orden(
    orden_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Cancela una orden de entrega"""
    orden = orden_entrega_service.cancelar(db, orden_id)

    data = OrdenEntregaSchema.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado
    return data


@router.post("/{orden_id}/completar", response_model=OrdenEntregaSchema)
async def completar_orden(
    orden_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Marca una orden como completada manualmente"""
    orden = orden_entrega_service.completar_manualmente(db, orden_id)

    data = OrdenEntregaSchema.model_validate(orden)
    data.cliente_nombre_completo = orden.cliente_nombre_completo
    data.cargas_pendientes = orden.cargas_pendientes
    data.porcentaje_completado = orden.porcentaje_completado
    return data


@router.delete("/{orden_id}")
async def eliminar_orden(
    orden_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Elimina una orden de entrega"""
    return orden_entrega_service.eliminar(db, orden_id)
