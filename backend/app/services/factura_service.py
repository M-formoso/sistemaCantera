"""
Servicio de Facturación
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.factura import Factura, PagoFactura, PagoRemito, factura_remito
from app.models.remito import Remito
from app.models.empresa import Empresa
from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.schemas.factura import (
    FacturaCreate, FacturaUpdate, PagoFacturaCreate, PagoRemitoCreate,
    EstadoCuentaItem, EstadoCuentaCliente
)


# =============================================
# FACTURAS
# =============================================

def obtener_siguiente_numero_factura(db: Session, tipo_comprobante: str, punto_venta: int = 1) -> str:
    """Genera el siguiente número de factura"""
    # Obtener el último número para este tipo y punto de venta
    ultima = db.query(Factura).filter(
        Factura.tipo_comprobante == tipo_comprobante,
        Factura.punto_venta == punto_venta
    ).order_by(Factura.created_at.desc()).first()

    if ultima and ultima.numero_factura:
        # Extraer el número secuencial
        partes = ultima.numero_factura.split('-')
        if len(partes) >= 2:
            try:
                ultimo_num = int(partes[-1])
                siguiente = ultimo_num + 1
            except ValueError:
                siguiente = 1
        else:
            siguiente = 1
    else:
        siguiente = 1

    # Formato: A-0001-00000001 (tipo-pv-numero)
    tipo_letra = tipo_comprobante.split('_')[-1].upper()[0] if '_' in tipo_comprobante else tipo_comprobante[0].upper()
    prefijo = tipo_comprobante.replace('_', ' ').title().replace(' ', '')[:2].upper()

    return f"{prefijo}-{punto_venta:04d}-{siguiente:08d}"


def crear_factura(db: Session, factura_data: FacturaCreate, usuario_id: UUID) -> Factura:
    """Crea una nueva factura asociando remitos"""

    # Verificar que el cliente existe
    empresa = db.query(Empresa).filter(Empresa.id == factura_data.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener remitos a asociar
    remitos = []
    subtotal_remitos = Decimal("0")

    if factura_data.remito_ids:
        remitos = db.query(Remito).filter(Remito.id.in_(factura_data.remito_ids)).all()

        if len(remitos) != len(factura_data.remito_ids):
            raise HTTPException(status_code=400, detail="Algunos remitos no fueron encontrados")

        # Verificar que no estén ya facturados
        for remito in remitos:
            if remito.facturado:
                raise HTTPException(
                    status_code=400,
                    detail=f"El remito #{remito.numero_remito} ya está facturado"
                )
            subtotal_remitos += remito.importe or Decimal("0")

    # Usar subtotal de remitos si no se especificó
    subtotal = factura_data.subtotal if factura_data.subtotal > 0 else subtotal_remitos

    # Calcular total
    total = (
        subtotal
        - factura_data.descuento
        + factura_data.iva_21
        + factura_data.iva_10_5
        + factura_data.iva_27
        + factura_data.percepciones_iibb
        + factura_data.percepciones_iva
        + factura_data.otros_impuestos
    )

    if factura_data.total:
        total = factura_data.total

    # Generar número de factura
    numero_factura = obtener_siguiente_numero_factura(
        db, factura_data.tipo_comprobante, factura_data.punto_venta
    )

    # Crear factura
    factura = Factura(
        numero_factura=numero_factura,
        punto_venta=factura_data.punto_venta,
        tipo_comprobante=factura_data.tipo_comprobante,
        empresa_id=factura_data.empresa_id,
        fecha_emision=factura_data.fecha_emision,
        fecha_vencimiento=factura_data.fecha_vencimiento,
        subtotal=subtotal,
        descuento=factura_data.descuento,
        iva_21=factura_data.iva_21,
        iva_10_5=factura_data.iva_10_5,
        iva_27=factura_data.iva_27,
        percepciones_iibb=factura_data.percepciones_iibb,
        percepciones_iva=factura_data.percepciones_iva,
        otros_impuestos=factura_data.otros_impuestos,
        total=total,
        saldo_pendiente=total,
        estado="pendiente",
        cae=factura_data.cae,
        cae_vencimiento=factura_data.cae_vencimiento,
        factura_original_id=factura_data.factura_original_id,
        observaciones=factura_data.observaciones,
        created_by=usuario_id
    )

    db.add(factura)
    db.flush()  # Para obtener el ID

    # Asociar remitos
    for remito in remitos:
        factura.remitos.append(remito)
        remito.facturado = True

    db.commit()
    db.refresh(factura)

    return factura


def obtener_factura_por_id(db: Session, factura_id: UUID) -> Optional[Factura]:
    """Obtiene una factura por ID con relaciones"""
    return db.query(Factura).filter(Factura.id == factura_id).first()


def obtener_facturas(
    db: Session,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_comprobante: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Factura]:
    """Lista facturas con filtros"""
    query = db.query(Factura).filter(Factura.anulada == False)

    if empresa_id:
        query = query.filter(Factura.empresa_id == empresa_id)
    if estado:
        query = query.filter(Factura.estado == estado)
    if tipo_comprobante:
        query = query.filter(Factura.tipo_comprobante == tipo_comprobante)
    if fecha_desde:
        query = query.filter(Factura.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Factura.fecha_emision <= fecha_hasta)

    return query.order_by(Factura.fecha_emision.desc()).offset(skip).limit(limit).all()


def obtener_facturas_pendientes(db: Session, empresa_id: Optional[UUID] = None) -> List[Factura]:
    """Obtiene facturas pendientes de pago"""
    query = db.query(Factura).filter(
        Factura.anulada == False,
        Factura.estado.in_(["pendiente", "parcial"])
    )

    if empresa_id:
        query = query.filter(Factura.empresa_id == empresa_id)

    return query.order_by(Factura.fecha_emision.asc()).all()


def actualizar_factura(db: Session, factura_id: UUID, factura_data: FacturaUpdate) -> Factura:
    """Actualiza datos de una factura"""
    factura = obtener_factura_por_id(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.anulada:
        raise HTTPException(status_code=400, detail="No se puede modificar una factura anulada")

    for field, value in factura_data.model_dump(exclude_unset=True).items():
        setattr(factura, field, value)

    db.commit()
    db.refresh(factura)
    return factura


def anular_factura(db: Session, factura_id: UUID, motivo: str) -> Factura:
    """Anula una factura"""
    factura = obtener_factura_por_id(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.anulada:
        raise HTTPException(status_code=400, detail="La factura ya está anulada")

    # Desasociar remitos
    for remito in factura.remitos:
        remito.facturado = False

    factura.anulada = True
    factura.motivo_anulacion = motivo
    factura.estado = "anulada"

    db.commit()
    db.refresh(factura)
    return factura


# =============================================
# PAGOS DE FACTURA
# =============================================

def registrar_pago_factura(
    db: Session,
    pago_data: PagoFacturaCreate,
    usuario_id: UUID,
    registrar_en_cc: bool = True
) -> PagoFactura:
    """Registra un pago a una factura"""

    factura = obtener_factura_por_id(db, pago_data.factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.anulada:
        raise HTTPException(status_code=400, detail="No se puede pagar una factura anulada")

    if factura.saldo_pendiente <= 0:
        raise HTTPException(status_code=400, detail="La factura ya está pagada")

    if pago_data.monto > factura.saldo_pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"El monto excede el saldo pendiente (${factura.saldo_pendiente})"
        )

    # Crear pago
    pago = PagoFactura(
        factura_id=factura.id,
        fecha=pago_data.fecha,
        monto=pago_data.monto,
        forma_pago=pago_data.forma_pago,
        banco=pago_data.banco,
        numero_cheque=pago_data.numero_cheque,
        fecha_cheque=pago_data.fecha_cheque,
        cuit_emisor=pago_data.cuit_emisor,
        es_retencion=pago_data.es_retencion,
        tipo_retencion=pago_data.tipo_retencion,
        numero_certificado=pago_data.numero_certificado,
        referencia=pago_data.referencia,
        observaciones=pago_data.observaciones,
        created_by=usuario_id
    )

    # Registrar en cuenta corriente si corresponde
    if registrar_en_cc and not pago_data.es_retencion:
        empresa = db.query(Empresa).filter(Empresa.id == factura.empresa_id).first()
        saldo_anterior = empresa.saldo_cuenta_corriente

        movimiento_cc = MovimientoCuentaCorriente(
            empresa_id=factura.empresa_id,
            tipo="pago",
            monto=pago_data.monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_anterior - pago_data.monto,
            fecha=pago_data.fecha,
            descripcion=f"Pago Factura {factura.numero_factura}",
            detalle=f"Forma: {pago_data.forma_pago}",
            numero_comprobante=factura.numero_factura,
            tipo_comprobante="factura",
            metodo_pago=pago_data.forma_pago,
            referencia_pago=pago_data.referencia,
            banco=pago_data.banco,
            created_by=usuario_id
        )
        db.add(movimiento_cc)
        db.flush()

        pago.movimiento_cc_id = movimiento_cc.id
        empresa.saldo_cuenta_corriente = saldo_anterior - pago_data.monto

    db.add(pago)

    # Actualizar saldo de factura
    factura.saldo_pendiente -= pago_data.monto

    # Actualizar estado
    if factura.saldo_pendiente <= 0:
        factura.estado = "pagada"
    else:
        factura.estado = "parcial"

    db.commit()
    db.refresh(pago)

    return pago


def obtener_pagos_factura(db: Session, factura_id: UUID) -> List[PagoFactura]:
    """Obtiene los pagos de una factura"""
    return db.query(PagoFactura).filter(
        PagoFactura.factura_id == factura_id,
        PagoFactura.anulado == False
    ).order_by(PagoFactura.fecha.asc()).all()


def anular_pago_factura(db: Session, pago_id: UUID) -> PagoFactura:
    """Anula un pago de factura"""
    pago = db.query(PagoFactura).filter(PagoFactura.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if pago.anulado:
        raise HTTPException(status_code=400, detail="El pago ya está anulado")

    # Revertir saldo de factura
    factura = pago.factura
    factura.saldo_pendiente += pago.monto

    if factura.saldo_pendiente >= factura.total:
        factura.estado = "pendiente"
    else:
        factura.estado = "parcial"

    # Anular movimiento de CC si existe
    if pago.movimiento_cc_id:
        movimiento = db.query(MovimientoCuentaCorriente).filter(
            MovimientoCuentaCorriente.id == pago.movimiento_cc_id
        ).first()
        if movimiento:
            movimiento.anulado = True
            movimiento.motivo_anulacion = "Pago anulado"

            # Revertir saldo del cliente
            empresa = db.query(Empresa).filter(Empresa.id == factura.empresa_id).first()
            empresa.saldo_cuenta_corriente += pago.monto

    pago.anulado = True

    db.commit()
    db.refresh(pago)
    return pago


# =============================================
# PAGOS DE REMITO (SIN FACTURA)
# =============================================

def registrar_pago_remito(
    db: Session,
    pago_data: PagoRemitoCreate,
    usuario_id: UUID,
    registrar_en_cc: bool = True
) -> PagoRemito:
    """Registra un pago directo a un remito"""

    remito = db.query(Remito).filter(Remito.id == pago_data.remito_id).first()
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")

    if remito.facturado:
        raise HTTPException(
            status_code=400,
            detail="El remito ya está facturado, debe pagar la factura"
        )

    if remito.saldo_pendiente <= 0:
        raise HTTPException(status_code=400, detail="El remito ya está pagado")

    if pago_data.monto > remito.saldo_pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"El monto excede el saldo pendiente (${remito.saldo_pendiente})"
        )

    # Crear pago
    pago = PagoRemito(
        remito_id=remito.id,
        fecha=pago_data.fecha,
        monto=pago_data.monto,
        forma_pago=pago_data.forma_pago,
        banco=pago_data.banco,
        numero_cheque=pago_data.numero_cheque,
        fecha_cheque=pago_data.fecha_cheque,
        cuit_emisor=pago_data.cuit_emisor,
        es_retencion=pago_data.es_retencion,
        tipo_retencion=pago_data.tipo_retencion,
        numero_certificado=pago_data.numero_certificado,
        referencia=pago_data.referencia,
        observaciones=pago_data.observaciones,
        created_by=usuario_id
    )

    # Registrar en cuenta corriente si corresponde
    if registrar_en_cc and not pago_data.es_retencion:
        # Obtener cliente del pesaje asociado al remito
        pesaje = remito.pesaje
        if pesaje and pesaje.cliente_id:
            empresa = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
            if empresa:
                saldo_anterior = empresa.saldo_cuenta_corriente

                movimiento_cc = MovimientoCuentaCorriente(
                    empresa_id=empresa.id,
                    tipo="pago",
                    monto=pago_data.monto,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_anterior - pago_data.monto,
                    fecha=pago_data.fecha,
                    descripcion=f"Pago Remito #{remito.numero_remito}",
                    detalle=f"Forma: {pago_data.forma_pago}",
                    numero_comprobante=str(remito.numero_remito),
                    tipo_comprobante="remito",
                    metodo_pago=pago_data.forma_pago,
                    referencia_pago=pago_data.referencia,
                    banco=pago_data.banco,
                    created_by=usuario_id
                )
                db.add(movimiento_cc)
                db.flush()

                pago.movimiento_cc_id = movimiento_cc.id
                empresa.saldo_cuenta_corriente = saldo_anterior - pago_data.monto

    db.add(pago)

    # Actualizar saldo del remito
    remito.saldo_pendiente -= pago_data.monto

    db.commit()
    db.refresh(pago)

    return pago


# =============================================
# REMITOS PENDIENTES
# =============================================

def obtener_remitos_pendientes_cliente(
    db: Session,
    empresa_id: UUID,
    solo_sin_facturar: bool = True,
    solo_con_saldo: bool = True
) -> List[Remito]:
    """Obtiene remitos pendientes de un cliente"""

    # Obtener pesajes del cliente
    from app.models.pesaje import Pesaje

    query = db.query(Remito).join(Pesaje, Remito.pesaje_id == Pesaje.id).filter(
        Pesaje.cliente_id == empresa_id
    )

    if solo_sin_facturar:
        query = query.filter(or_(Remito.facturado == False, Remito.facturado == None))

    if solo_con_saldo:
        query = query.filter(Remito.saldo_pendiente > 0)

    return query.order_by(Remito.fecha.asc()).all()


# =============================================
# ESTADO DE CUENTA
# =============================================

def obtener_estado_cuenta_cliente(
    db: Session,
    empresa_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> EstadoCuentaCliente:
    """Genera el estado de cuenta completo de un cliente"""

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener todos los movimientos
    query = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.anulado == False
    )

    if fecha_desde:
        query = query.filter(MovimientoCuentaCorriente.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(MovimientoCuentaCorriente.fecha <= fecha_hasta)

    movimientos = query.order_by(MovimientoCuentaCorriente.fecha.asc()).all()

    # Construir items del estado de cuenta
    items = []
    saldo_acumulado = Decimal("0")

    for mov in movimientos:
        debe = Decimal("0")
        haber = Decimal("0")

        if mov.tipo == "cargo":
            debe = mov.monto
            saldo_acumulado += mov.monto
        elif mov.tipo == "pago":
            haber = mov.monto
            saldo_acumulado -= mov.monto
        elif mov.tipo == "ajuste":
            if mov.monto > 0:
                debe = mov.monto
                saldo_acumulado += mov.monto
            else:
                haber = abs(mov.monto)
                saldo_acumulado -= abs(mov.monto)

        items.append(EstadoCuentaItem(
            fecha=mov.fecha,
            tipo=mov.tipo,
            numero=mov.numero_comprobante or "-",
            descripcion=mov.descripcion,
            debe=debe,
            haber=haber,
            saldo=saldo_acumulado
        ))

    return EstadoCuentaCliente(
        empresa_id=empresa.id,
        empresa_nombre=empresa.nombre,
        cuit=empresa.cuit,
        saldo_inicial=Decimal("0"),
        movimientos=items,
        saldo_final=saldo_acumulado,
        fecha_desde=fecha_desde or date.today(),
        fecha_hasta=fecha_hasta or date.today()
    )
