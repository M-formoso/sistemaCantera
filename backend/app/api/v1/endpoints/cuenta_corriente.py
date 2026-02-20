"""
Endpoints API para Cuenta Corriente
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.cuenta_corriente import (
    MovimientoCCSchema,
    PagoCreate,
    AjusteCreate,
    ResumenCuentaCorriente,
    ClienteConDeuda,
    AnularMovimientoRequest
)
from app.services import cuenta_corriente_service

router = APIRouter()


@router.get("/clientes-con-deuda", response_model=List[ClienteConDeuda])
async def listar_clientes_con_deuda(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los clientes con saldo pendiente"""
    return cuenta_corriente_service.obtener_clientes_con_deuda(db)


@router.get("/cliente/{empresa_id}/resumen", response_model=ResumenCuentaCorriente)
async def obtener_resumen_cliente(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el resumen de cuenta corriente de un cliente"""
    return cuenta_corriente_service.obtener_resumen_cliente(db, empresa_id)


@router.get("/cliente/{empresa_id}/movimientos", response_model=List[MovimientoCCSchema])
async def listar_movimientos_cliente(
    empresa_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista movimientos de cuenta corriente de un cliente"""
    movimientos = cuenta_corriente_service.obtener_movimientos_cliente(
        db, empresa_id, fecha_desde, fecha_hasta, skip, limit
    )

    # Enriquecer con nombre de empresa
    result = []
    for m in movimientos:
        data = MovimientoCCSchema.model_validate(m)
        if m.empresa:
            data.empresa_nombre = m.empresa.nombre
        result.append(data)

    return result


@router.post("/pago", response_model=MovimientoCCSchema, status_code=201)
async def registrar_pago(
    pago: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Registra un pago de un cliente

    - Reduce el saldo de cuenta corriente
    - Opcionalmente crea un ingreso en Finanzas
    """
    movimiento = cuenta_corriente_service.registrar_pago(
        db=db,
        empresa_id=pago.empresa_id,
        monto=pago.monto,
        fecha=pago.fecha,
        descripcion=pago.descripcion,
        usuario_id=current_user.id,
        metodo_pago=pago.metodo_pago,
        numero_comprobante=pago.numero_comprobante,
        referencia_pago=pago.referencia_pago,
        banco=pago.banco,
        notas=pago.notas,
        registrar_ingreso=pago.registrar_ingreso
    )

    result = MovimientoCCSchema.model_validate(movimiento)
    if movimiento.empresa:
        result.empresa_nombre = movimiento.empresa.nombre
    return result


@router.post("/ajuste", response_model=MovimientoCCSchema, status_code=201)
async def registrar_ajuste(
    ajuste: AjusteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Registra un ajuste (nota de crédito o débito)

    - es_credito=true: Nota de crédito (reduce deuda)
    - es_credito=false: Nota de débito (aumenta deuda)
    """
    movimiento = cuenta_corriente_service.registrar_ajuste(
        db=db,
        empresa_id=ajuste.empresa_id,
        monto=ajuste.monto,
        es_credito=ajuste.es_credito,
        fecha=ajuste.fecha,
        descripcion=ajuste.descripcion,
        usuario_id=current_user.id,
        notas=ajuste.notas
    )

    result = MovimientoCCSchema.model_validate(movimiento)
    if movimiento.empresa:
        result.empresa_nombre = movimiento.empresa.nombre
    return result


@router.post("/{movimiento_id}/anular", response_model=MovimientoCCSchema)
async def anular_movimiento(
    movimiento_id: UUID,
    request: AnularMovimientoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """Anula un movimiento de cuenta corriente"""
    movimiento = cuenta_corriente_service.anular_movimiento(
        db=db,
        movimiento_id=movimiento_id,
        motivo=request.motivo,
        usuario_id=current_user.id
    )

    result = MovimientoCCSchema.model_validate(movimiento)
    if movimiento.empresa:
        result.empresa_nombre = movimiento.empresa.nombre
    return result


@router.get("/cliente/{empresa_id}/saldo")
async def obtener_saldo_cliente(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el saldo actual de un cliente"""
    saldo = cuenta_corriente_service.obtener_saldo_cliente(db, empresa_id)
    return {"saldo": float(saldo)}
