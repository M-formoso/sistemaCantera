"""
Endpoints API para Cobros de Clientes
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.cobro import (
    CobroClienteSchema, CobroClienteListSchema, CobroClienteCreate,
    CobroClienteCreateWithItems, CobroClienteUpdate, ItemCobroCreate,
    ItemCobroSchema, ValidacionCobroResponse, AplicarCobroResponse,
    DocumentosPendientesResponse
)
from app.services import cobro_service

router = APIRouter()


@router.get("/", response_model=List[CobroClienteListSchema])
async def listar_cobros(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    estado: Optional[str] = Query(None, description="Filtrar por estado: borrador, confirmado, aplicado"),
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista cobros con filtros opcionales"""
    cobros = cobro_service.listar_cobros(
        db, skip, limit, estado, empresa_id, fecha_desde, fecha_hasta
    )

    # Agregar nombre de empresa
    result = []
    for cobro in cobros:
        cobro_dict = {
            "id": cobro.id,
            "numero_cobro": cobro.numero_cobro,
            "empresa_id": cobro.empresa_id,
            "empresa_nombre": cobro.empresa.nombre if cobro.empresa else None,
            "fecha": cobro.fecha,
            "monto_total": cobro.monto_total,
            "monto_aplicado": cobro.monto_aplicado,
            "diferencia": cobro.diferencia,
            "estado": cobro.estado,
            "anulado": cobro.anulado
        }
        result.append(CobroClienteListSchema(**cobro_dict))

    return result


@router.get("/cliente/{empresa_id}", response_model=List[CobroClienteListSchema])
async def listar_cobros_cliente(
    empresa_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista cobros de un cliente específico"""
    cobros = cobro_service.obtener_cobros_cliente(db, empresa_id, skip, limit)

    result = []
    for cobro in cobros:
        cobro_dict = {
            "id": cobro.id,
            "numero_cobro": cobro.numero_cobro,
            "empresa_id": cobro.empresa_id,
            "empresa_nombre": cobro.empresa.nombre if cobro.empresa else None,
            "fecha": cobro.fecha,
            "monto_total": cobro.monto_total,
            "monto_aplicado": cobro.monto_aplicado,
            "diferencia": cobro.diferencia,
            "estado": cobro.estado,
            "anulado": cobro.anulado
        }
        result.append(CobroClienteListSchema(**cobro_dict))

    return result


@router.get("/documentos-pendientes/{empresa_id}", response_model=DocumentosPendientesResponse)
async def obtener_documentos_pendientes(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene facturas y tickets pendientes de cobro de un cliente"""
    return cobro_service.obtener_documentos_pendientes(db, empresa_id)


@router.get("/{cobro_id}", response_model=CobroClienteSchema)
async def obtener_cobro(
    cobro_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un cobro por ID con sus items"""
    cobro = cobro_service.obtener_cobro(db, cobro_id)
    if not cobro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobro no encontrado"
        )

    # Calcular totales
    total_haber = sum(item.monto for item in cobro.items if item.concepto == "haber")
    total_debe = sum(item.monto for item in cobro.items if item.concepto == "debe")

    return CobroClienteSchema(
        id=cobro.id,
        numero_cobro=cobro.numero_cobro,
        empresa_id=cobro.empresa_id,
        fecha=cobro.fecha,
        monto_total=cobro.monto_total,
        monto_aplicado=cobro.monto_aplicado,
        diferencia=cobro.diferencia,
        estado=cobro.estado,
        numero_orden_pago=cobro.numero_orden_pago,
        observaciones=cobro.observaciones,
        created_by=cobro.created_by,
        confirmed_by=cobro.confirmed_by,
        fecha_confirmacion=cobro.fecha_confirmacion,
        anulado=cobro.anulado,
        motivo_anulacion=cobro.motivo_anulacion,
        items=[ItemCobroSchema.model_validate(item) for item in cobro.items],
        total_haber=total_haber,
        total_debe=total_debe,
        esta_balanceado=abs(total_haber - total_debe) < 0.01,
        empresa_nombre=cobro.empresa.nombre if cobro.empresa else None,
        creador_nombre=cobro.creador.nombre if cobro.creador else None
    )


@router.post("/", response_model=CobroClienteSchema, status_code=201)
async def crear_cobro(
    cobro_data: CobroClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un nuevo cobro (solo cabecera).
    El cobro se crea en estado 'borrador' y luego se agregan items.
    """
    cobro = cobro_service.crear_cobro(db, cobro_data, current_user.id)
    return CobroClienteSchema(
        id=cobro.id,
        numero_cobro=cobro.numero_cobro,
        empresa_id=cobro.empresa_id,
        fecha=cobro.fecha,
        monto_total=cobro.monto_total,
        monto_aplicado=cobro.monto_aplicado,
        diferencia=cobro.diferencia,
        estado=cobro.estado,
        numero_orden_pago=cobro.numero_orden_pago,
        observaciones=cobro.observaciones,
        created_by=cobro.created_by,
        confirmed_by=cobro.confirmed_by,
        fecha_confirmacion=cobro.fecha_confirmacion,
        anulado=cobro.anulado,
        motivo_anulacion=cobro.motivo_anulacion,
        items=[],
        empresa_nombre=cobro.empresa.nombre if cobro.empresa else None
    )


@router.post("/con-items", response_model=CobroClienteSchema, status_code=201)
async def crear_cobro_con_items(
    cobro_data: CobroClienteCreateWithItems,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un cobro con items en una sola operación.
    """
    cobro = cobro_service.crear_cobro_con_items(db, cobro_data, current_user.id)

    total_haber = sum(item.monto for item in cobro.items if item.concepto == "haber")
    total_debe = sum(item.monto for item in cobro.items if item.concepto == "debe")

    return CobroClienteSchema(
        id=cobro.id,
        numero_cobro=cobro.numero_cobro,
        empresa_id=cobro.empresa_id,
        fecha=cobro.fecha,
        monto_total=cobro.monto_total,
        monto_aplicado=cobro.monto_aplicado,
        diferencia=cobro.diferencia,
        estado=cobro.estado,
        numero_orden_pago=cobro.numero_orden_pago,
        observaciones=cobro.observaciones,
        created_by=cobro.created_by,
        confirmed_by=cobro.confirmed_by,
        fecha_confirmacion=cobro.fecha_confirmacion,
        anulado=cobro.anulado,
        motivo_anulacion=cobro.motivo_anulacion,
        items=[ItemCobroSchema.model_validate(item) for item in cobro.items],
        total_haber=total_haber,
        total_debe=total_debe,
        esta_balanceado=abs(total_haber - total_debe) < 0.01,
        empresa_nombre=cobro.empresa.nombre if cobro.empresa else None
    )


@router.post("/{cobro_id}/items", response_model=ItemCobroSchema, status_code=201)
async def agregar_item(
    cobro_id: UUID,
    item_data: ItemCobroCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Agrega un item a un cobro existente"""
    item = cobro_service.agregar_item(db, cobro_id, item_data)
    return ItemCobroSchema.model_validate(item)


@router.delete("/{cobro_id}/items/{item_id}")
async def eliminar_item(
    cobro_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Elimina un item de un cobro"""
    cobro_service.eliminar_item(db, item_id)
    return {"mensaje": "Item eliminado correctamente"}


@router.get("/{cobro_id}/validar", response_model=ValidacionCobroResponse)
async def validar_cobro(
    cobro_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Valida que el cobro esté balanceado (debe = haber)"""
    return cobro_service.validar_cobro(db, cobro_id)


@router.post("/{cobro_id}/confirmar", response_model=CobroClienteSchema)
async def confirmar_cobro(
    cobro_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Confirma un cobro (cambia estado a confirmado)"""
    cobro = cobro_service.confirmar_cobro(db, cobro_id, current_user.id)

    total_haber = sum(item.monto for item in cobro.items if item.concepto == "haber")
    total_debe = sum(item.monto for item in cobro.items if item.concepto == "debe")

    return CobroClienteSchema(
        id=cobro.id,
        numero_cobro=cobro.numero_cobro,
        empresa_id=cobro.empresa_id,
        fecha=cobro.fecha,
        monto_total=cobro.monto_total,
        monto_aplicado=cobro.monto_aplicado,
        diferencia=cobro.diferencia,
        estado=cobro.estado,
        numero_orden_pago=cobro.numero_orden_pago,
        observaciones=cobro.observaciones,
        created_by=cobro.created_by,
        confirmed_by=cobro.confirmed_by,
        fecha_confirmacion=cobro.fecha_confirmacion,
        anulado=cobro.anulado,
        motivo_anulacion=cobro.motivo_anulacion,
        items=[ItemCobroSchema.model_validate(item) for item in cobro.items],
        total_haber=total_haber,
        total_debe=total_debe,
        esta_balanceado=abs(total_haber - total_debe) < 0.01,
        empresa_nombre=cobro.empresa.nombre if cobro.empresa else None
    )


@router.post("/{cobro_id}/aplicar", response_model=AplicarCobroResponse)
async def aplicar_cobro(
    cobro_id: UUID,
    caja_efectivo_id: Optional[UUID] = Query(None, description="ID de la caja para ingresar efectivo"),
    cuenta_bancaria_id: Optional[UUID] = Query(None, description="ID de la cuenta bancaria para transferencias"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Aplica el cobro generando los movimientos de cuenta corriente y tesorería.
    - Genera un pago por cada medio de pago (HABER)
    - Aplica a las facturas/tickets seleccionados (DEBE)
    - Si hay diferencia, queda como saldo a favor o pendiente
    - Crea cheques en tesorería si hay pagos con cheque
    - Actualiza saldos de cajas/bancos según corresponda
    """
    return cobro_service.aplicar_cobro(
        db,
        cobro_id,
        current_user.id,
        caja_efectivo_id=caja_efectivo_id,
        cuenta_bancaria_id=cuenta_bancaria_id
    )


@router.post("/{cobro_id}/anular")
async def anular_cobro(
    cobro_id: UUID,
    motivo: str = Query(..., min_length=5),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Anula un cobro (solo si no está aplicado)"""
    cobro = cobro_service.anular_cobro(db, cobro_id, motivo, current_user.id)
    return {"mensaje": f"Cobro #{cobro.numero_cobro} anulado correctamente"}
