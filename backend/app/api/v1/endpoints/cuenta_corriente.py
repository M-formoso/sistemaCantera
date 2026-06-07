"""
Endpoints API para Cuenta Corriente
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.models.empresa import Empresa
from app.schemas.cuenta_corriente import (
    MovimientoCCSchema,
    PagoCreate,
    AjusteCreate,
    ResumenCuentaCorriente,
    ClienteConDeuda,
    AnularMovimientoRequest,
    ActualizarMontoRequest,
    HistorialMovimientoCCSchema,
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

    # Resolver factor_conversion_m3 por material a partir de la lista de precios del cliente.
    factores_por_material = {}
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa and empresa.lista_precio_id and empresa.lista_precio:
        for item in empresa.lista_precio.items:
            if item.factor_conversion_m3:
                factores_por_material[item.material.lower()] = float(item.factor_conversion_m3)

    # Enriquecer con nombre de empresa + cantidades en tn / m³
    result = []
    for m in movimientos:
        data = MovimientoCCSchema.model_validate(m)
        if m.empresa:
            data.empresa_nombre = m.empresa.nombre

        # Si el movimiento corresponde a un pesaje, derivar material/tn/m³.
        if m.pesaje:
            pesaje = m.pesaje
            if pesaje.material:
                data.material = pesaje.material
            if pesaje.peso_neto:
                tn = float(pesaje.peso_neto) / 1000.0
                data.toneladas = round(tn, 3)
                factor = factores_por_material.get((pesaje.material or "").lower())
                if factor and factor > 0:
                    data.factor_conversion_m3 = factor
                    data.metros_cubicos = round(tn / factor, 3)
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
        registrar_ingreso=pago.registrar_ingreso,
        alicuota_iva=pago.alicuota_iva,
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


@router.post("/cliente/{empresa_id}/recalcular")
async def recalcular_saldos_cliente(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador),
):
    """Reconcilia los saldos acumulados de un cliente.

    Recorre todos los movimientos no anulados en orden cronológico y reescribe
    saldo_anterior/saldo_posterior. También sincroniza el saldo total de la empresa.
    """
    return cuenta_corriente_service.recalcular_saldos_movimientos(db, empresa_id)


@router.post("/cliente/{empresa_id}/aplicar-iva")
async def aplicar_iva_cliente(
    empresa_id: UUID,
    iva_en_total: bool = Query(..., description="True para sumar IVA al total y saldo, False para dejarlos en neto"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador),
):
    """Activa o desactiva el cobro con IVA en el total/saldo del cliente.

    Cambia el flag `iva_en_total` del cliente y recalcula todos sus movimientos
    no anulados:
    - True: monto = monto_neto + IVA (saldo crece con total c/IVA).
    - False: monto = monto_neto (IVA solo informativo).
    """
    return cuenta_corriente_service.aplicar_iva_en_total_cliente(
        db=db,
        empresa_id=empresa_id,
        iva_en_total=iva_en_total,
        usuario_id=current_user.id,
    )


@router.put("/{movimiento_id}/monto", response_model=MovimientoCCSchema)
async def actualizar_monto_cargo(
    movimiento_id: UUID,
    request: ActualizarMontoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Actualiza el monto de un cargo en cuenta corriente.

    Útil para agregar precio a pesajes que se registraron sin importe.
    También actualiza el pesaje asociado si existe.
    """
    movimiento = cuenta_corriente_service.actualizar_monto_cargo(
        db=db,
        movimiento_id=movimiento_id,
        nuevo_monto=request.monto,
        precio_unitario=request.precio_unitario,
        usuario_id=current_user.id,
        alicuota_iva=request.alicuota_iva,
    )

    result = MovimientoCCSchema.model_validate(movimiento)
    if movimiento.empresa:
        result.empresa_nombre = movimiento.empresa.nombre
    return result


@router.get("/movimientos/{movimiento_id}/historial", response_model=List[HistorialMovimientoCCSchema])
async def obtener_historial_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Obtiene el historial de un movimiento de cuenta corriente."""
    return cuenta_corriente_service.obtener_historial_movimiento(db, movimiento_id)


@router.get("/movimientos/{movimiento_id}/comprobante-pdf")
async def descargar_comprobante_pdf(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Genera y descarga un PDF tipo comprobante para un movimiento."""
    movimiento = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.id == movimiento_id
    ).first()

    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )

    empresa = db.query(Empresa).filter(Empresa.id == movimiento.empresa_id).first()

    # Si el movimiento proviene de un cobro multi-aplicación, recolectar
    # los items DEBE para mostrarlos en el recibo.
    aplicaciones = []
    if movimiento.tipo == "pago":
        from app.models.cuenta_corriente import ItemCobroCliente
        from app.models.factura import Factura
        from app.models.remito import Remito
        from app.models.pesaje import Pesaje as PesajeModel

        items_debe = db.query(ItemCobroCliente).filter(
            ItemCobroCliente.movimiento_cc_id == movimiento.id,
            ItemCobroCliente.concepto == "debe",
        ).all()

        for it in items_debe:
            label = it.descripcion or ""
            if it.factura_id:
                f = db.query(Factura).filter(Factura.id == it.factura_id).first()
                if f:
                    label = f"Factura #{f.numero_factura}"
            elif it.remito_id:
                r = db.query(Remito).filter(Remito.id == it.remito_id).first()
                if r:
                    numero = r.pesaje.numero_pesaje if r.pesaje else r.numero_remito
                    label = f"Remito/Pesaje #{numero}"
            elif it.pesaje_id:
                p = db.query(PesajeModel).filter(PesajeModel.id == it.pesaje_id).first()
                if p:
                    label = f"Pesaje #{p.numero_pesaje}"

            aplicaciones.append({
                "descripcion": label or "Aplicación",
                "monto": float(it.monto) if it.monto is not None else 0,
            })

    data = {
        "tipo": movimiento.tipo,
        "fecha": movimiento.fecha,
        "descripcion": movimiento.descripcion,
        "detalle": movimiento.detalle,
        "monto": float(movimiento.monto) if movimiento.monto is not None else 0,
        "saldo_anterior": float(movimiento.saldo_anterior) if movimiento.saldo_anterior is not None else 0,
        "saldo_posterior": float(movimiento.saldo_posterior) if movimiento.saldo_posterior is not None else 0,
        "metodo_pago": movimiento.metodo_pago,
        "numero_comprobante": movimiento.numero_comprobante,
        "banco": movimiento.banco,
        "referencia_pago": movimiento.referencia_pago,
        "anulado": movimiento.anulado,
        "motivo_anulacion": movimiento.motivo_anulacion,
        "notas": movimiento.notas,
        "cliente_nombre": empresa.nombre if empresa else None,
        "cliente_cuit": empresa.cuit if empresa else None,
        "aplicaciones": aplicaciones,
    }

    from app.tasks.reportes import generar_comprobante_movimiento_cc_pdf
    pdf_buffer = generar_comprobante_movimiento_cc_pdf(data)

    fecha_str = movimiento.fecha.strftime("%Y%m%d") if movimiento.fecha else "sin_fecha"
    filename = f"comprobante_{movimiento.tipo}_{fecha_str}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
