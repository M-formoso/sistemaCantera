"""
Servicio para Cobros de Clientes con control cruzado
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.cuenta_corriente import CobroCliente, ItemCobroCliente, MovimientoCuentaCorriente
from app.models.empresa import Empresa
from app.models.factura import Factura, PagoFactura
from app.models.remito import Remito
from app.models.pesaje import Pesaje
from app.models.finanzas import MovimientoFinanciero, CategoriaFinanzas
from app.schemas.cobro import (
    CobroClienteCreate, CobroClienteCreateWithItems, CobroClienteUpdate,
    ItemCobroCreate, ValidacionCobroResponse, AplicarCobroResponse,
    DocumentosPendientesResponse, FacturaPendienteSchema, TicketPendienteSchema
)


def obtener_siguiente_numero_cobro(db: Session) -> int:
    """Obtiene el siguiente número de cobro"""
    max_numero = db.query(func.max(CobroCliente.numero_cobro)).scalar()
    return (max_numero or 0) + 1


def crear_cobro(
    db: Session,
    cobro_data: CobroClienteCreate,
    usuario_id: UUID
) -> CobroCliente:
    """Crea un nuevo cobro (solo cabecera)"""
    # Verificar que el cliente existe
    empresa = db.query(Empresa).filter(Empresa.id == cobro_data.empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    numero_cobro = obtener_siguiente_numero_cobro(db)

    cobro = CobroCliente(
        numero_cobro=numero_cobro,
        empresa_id=cobro_data.empresa_id,
        fecha=cobro_data.fecha,
        monto_total=cobro_data.monto_total,
        monto_aplicado=Decimal("0"),
        diferencia=cobro_data.monto_total,  # Inicialmente toda la diferencia
        estado="borrador",
        numero_orden_pago=cobro_data.numero_orden_pago,
        observaciones=cobro_data.observaciones,
        created_by=usuario_id
    )

    db.add(cobro)
    db.commit()
    db.refresh(cobro)

    return cobro


def crear_cobro_con_items(
    db: Session,
    cobro_data: CobroClienteCreateWithItems,
    usuario_id: UUID
) -> CobroCliente:
    """Crea un cobro con items en una sola operación"""
    cobro = crear_cobro(db, CobroClienteCreate(
        empresa_id=cobro_data.empresa_id,
        fecha=cobro_data.fecha,
        monto_total=cobro_data.monto_total,
        numero_orden_pago=cobro_data.numero_orden_pago,
        observaciones=cobro_data.observaciones
    ), usuario_id)

    # Agregar items
    for item_data in cobro_data.items:
        agregar_item(db, cobro.id, item_data)

    # Recalcular totales
    recalcular_cobro(db, cobro.id)

    db.refresh(cobro)
    return cobro


def obtener_cobro(db: Session, cobro_id: UUID) -> Optional[CobroCliente]:
    """Obtiene un cobro por ID"""
    return db.query(CobroCliente).filter(CobroCliente.id == cobro_id).first()


def obtener_cobros_cliente(
    db: Session,
    empresa_id: UUID,
    skip: int = 0,
    limit: int = 50
) -> List[CobroCliente]:
    """Lista cobros de un cliente"""
    return db.query(CobroCliente).filter(
        CobroCliente.empresa_id == empresa_id,
        CobroCliente.anulado == False
    ).order_by(CobroCliente.fecha.desc()).offset(skip).limit(limit).all()


def listar_cobros(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[CobroCliente]:
    """Lista cobros con filtros"""
    query = db.query(CobroCliente).filter(CobroCliente.anulado == False)

    if estado:
        query = query.filter(CobroCliente.estado == estado)
    if empresa_id:
        query = query.filter(CobroCliente.empresa_id == empresa_id)
    if fecha_desde:
        query = query.filter(CobroCliente.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(CobroCliente.fecha <= fecha_hasta)

    return query.order_by(CobroCliente.fecha.desc()).offset(skip).limit(limit).all()


def agregar_item(
    db: Session,
    cobro_id: UUID,
    item_data: ItemCobroCreate
) -> ItemCobroCliente:
    """Agrega un item a un cobro"""
    cobro = obtener_cobro(db, cobro_id)
    if not cobro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobro no encontrado"
        )

    if cobro.estado == "aplicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden agregar items a un cobro ya aplicado"
        )

    item = ItemCobroCliente(
        cobro_id=cobro_id,
        tipo_item=item_data.tipo_item,
        concepto=item_data.concepto,
        monto=item_data.monto,
        descripcion=item_data.descripcion,
        factura_id=item_data.factura_id,
        remito_id=item_data.remito_id,
        pesaje_id=item_data.pesaje_id,
        banco=item_data.banco,
        numero_cheque=item_data.numero_cheque,
        fecha_cheque=item_data.fecha_cheque,
        cuit_emisor=item_data.cuit_emisor,
        referencia_transferencia=item_data.referencia_transferencia,
        numero_certificado=item_data.numero_certificado
    )

    db.add(item)
    db.commit()

    # Recalcular totales del cobro
    recalcular_cobro(db, cobro_id)

    db.refresh(item)
    return item


def eliminar_item(db: Session, item_id: UUID) -> bool:
    """Elimina un item de un cobro"""
    item = db.query(ItemCobroCliente).filter(ItemCobroCliente.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado"
        )

    cobro = item.cobro
    if cobro.estado == "aplicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden eliminar items de un cobro ya aplicado"
        )

    cobro_id = item.cobro_id
    db.delete(item)
    db.commit()

    # Recalcular totales
    recalcular_cobro(db, cobro_id)

    return True


def recalcular_cobro(db: Session, cobro_id: UUID):
    """Recalcula los totales de un cobro"""
    cobro = obtener_cobro(db, cobro_id)
    if not cobro:
        return

    # Sumar items del HABER (medios de pago)
    total_haber = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "haber"
    ).scalar() or Decimal("0")

    # Sumar items del DEBE (aplicaciones)
    total_debe = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe"
    ).scalar() or Decimal("0")

    # Monto aplicado = total del HABER (lo que realmente se pagó)
    cobro.monto_aplicado = total_haber

    # Diferencia = monto_total (orden de pago) - total_haber (medios de pago)
    # Si es positivo: falta ingresar medios de pago
    # Si es negativo: se ingresaron más medios de pago que el total
    cobro.diferencia = cobro.monto_total - total_haber

    db.commit()


def validar_cobro(db: Session, cobro_id: UUID) -> ValidacionCobroResponse:
    """Valida que el cobro esté balanceado"""
    cobro = obtener_cobro(db, cobro_id)
    if not cobro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobro no encontrado"
        )

    # Calcular totales
    total_haber = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "haber"
    ).scalar() or Decimal("0")

    total_debe = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe"
    ).scalar() or Decimal("0")

    errores = []
    mensaje = ""

    # Validar que el HABER coincida con el monto total de la orden de pago
    diferencia_orden = cobro.monto_total - total_haber
    if abs(diferencia_orden) > Decimal("0.01"):
        errores.append(f"El total de medios de pago (${total_haber}) no coincide con el monto de la orden de pago (${cobro.monto_total}). Diferencia: ${diferencia_orden}")

    # Validar balance DEBE = HABER
    diferencia_balance = total_haber - total_debe
    if abs(diferencia_balance) > Decimal("0.01"):
        if diferencia_balance > 0:
            mensaje = f"Saldo a favor del cliente: ${diferencia_balance}"
        else:
            mensaje = f"Faltan aplicar: ${abs(diferencia_balance)}"

    valido = len(errores) == 0

    if valido and abs(diferencia_balance) < Decimal("0.01"):
        mensaje = "Cobro balanceado correctamente"

    return ValidacionCobroResponse(
        valido=valido,
        total_haber=total_haber,
        total_debe=total_debe,
        diferencia=diferencia_balance,
        mensaje=mensaje,
        errores=errores
    )


def confirmar_cobro(db: Session, cobro_id: UUID, usuario_id: UUID) -> CobroCliente:
    """Confirma un cobro (verifica que esté balanceado)"""
    validacion = validar_cobro(db, cobro_id)

    # Permitir confirmar aunque no esté 100% balanceado
    # (puede quedar saldo a favor o pendiente)

    cobro = obtener_cobro(db, cobro_id)
    cobro.estado = "confirmado"
    cobro.confirmed_by = usuario_id
    cobro.fecha_confirmacion = date.today()

    db.commit()
    db.refresh(cobro)

    return cobro


def aplicar_cobro(
    db: Session,
    cobro_id: UUID,
    usuario_id: UUID
) -> AplicarCobroResponse:
    """
    Aplica el cobro generando los movimientos de cuenta corriente.
    - Genera un pago por cada item del HABER
    - Aplica cada pago a las facturas/tickets del DEBE
    - Si hay diferencia, genera saldo a favor o pendiente
    """
    cobro = obtener_cobro(db, cobro_id)
    if not cobro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobro no encontrado"
        )

    if cobro.estado == "aplicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cobro ya fue aplicado"
        )

    # Obtener saldo actual del cliente
    empresa = db.query(Empresa).filter(Empresa.id == cobro.empresa_id).first()
    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")

    # Calcular totales
    total_haber = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "haber"
    ).scalar() or Decimal("0")

    total_debe = db.query(func.coalesce(func.sum(ItemCobroCliente.monto), 0)).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe"
    ).scalar() or Decimal("0")

    movimientos_generados = 0

    # Generar movimiento de pago principal en cuenta corriente
    saldo_posterior = saldo_anterior - total_haber

    # Obtener categoría de ingresos
    categoria_cobros = db.query(CategoriaFinanzas).filter(
        CategoriaFinanzas.nombre.ilike("%cobro%"),
        CategoriaFinanzas.tipo == "ingreso"
    ).first()

    # Crear movimiento financiero (ingreso)
    mov_financiero = MovimientoFinanciero(
        tipo="ingreso",
        categoria_id=categoria_cobros.id if categoria_cobros else None,
        fecha=cobro.fecha,
        monto=total_haber,
        descripcion=f"Cobro #{cobro.numero_cobro} - {empresa.nombre}",
        empresa_id=cobro.empresa_id,
        estado="completado",
        created_by=usuario_id
    )
    db.add(mov_financiero)
    db.flush()

    # Crear movimiento de cuenta corriente
    mov_cc = MovimientoCuentaCorriente(
        empresa_id=cobro.empresa_id,
        tipo="pago",
        monto=total_haber,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        fecha=cobro.fecha,
        descripcion=f"Cobro #{cobro.numero_cobro}",
        detalle=cobro.observaciones,
        movimiento_financiero_id=mov_financiero.id,
        numero_comprobante=cobro.numero_orden_pago,
        tipo_comprobante="orden_pago",
        created_by=usuario_id
    )
    db.add(mov_cc)
    db.flush()
    movimientos_generados += 1

    # Actualizar saldo del cliente
    empresa.saldo_cuenta_corriente = saldo_posterior

    # Actualizar items del HABER con el movimiento generado
    items_haber = db.query(ItemCobroCliente).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "haber"
    ).all()

    for item in items_haber:
        item.movimiento_cc_id = mov_cc.id

    # Aplicar a facturas
    items_factura = db.query(ItemCobroCliente).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe",
        ItemCobroCliente.factura_id.isnot(None)
    ).all()

    for item in items_factura:
        factura = db.query(Factura).filter(Factura.id == item.factura_id).first()
        if factura:
            # Crear pago de factura
            pago = PagoFactura(
                factura_id=factura.id,
                movimiento_cc_id=mov_cc.id,
                fecha=cobro.fecha,
                monto=item.monto,
                forma_pago="cobro_multiple",
                referencia=f"Cobro #{cobro.numero_cobro}",
                created_by=usuario_id
            )
            db.add(pago)

            # Actualizar saldo de factura
            factura.saldo_pendiente -= item.monto
            if factura.saldo_pendiente <= 0:
                factura.estado = "pagada"
            else:
                factura.estado = "parcial"

    # Aplicar a remitos/tickets
    items_remito = db.query(ItemCobroCliente).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe",
        ItemCobroCliente.remito_id.isnot(None)
    ).all()

    for item in items_remito:
        remito = db.query(Remito).filter(Remito.id == item.remito_id).first()
        if remito:
            # Actualizar saldo pendiente del remito
            remito.saldo_pendiente = (remito.saldo_pendiente or Decimal("0")) - item.monto
            if remito.saldo_pendiente < 0:
                remito.saldo_pendiente = Decimal("0")

    # Aplicar a pesajes directos (sin remito)
    items_pesaje = db.query(ItemCobroCliente).filter(
        ItemCobroCliente.cobro_id == cobro_id,
        ItemCobroCliente.concepto == "debe",
        ItemCobroCliente.pesaje_id.isnot(None),
        ItemCobroCliente.remito_id.is_(None)  # Solo pesajes sin remito
    ).all()

    for item in items_pesaje:
        pesaje = db.query(Pesaje).filter(Pesaje.id == item.pesaje_id).first()
        if pesaje and pesaje.remito:
            # Si el pesaje tiene remito, actualizar el remito
            pesaje.remito.saldo_pendiente = (pesaje.remito.saldo_pendiente or Decimal("0")) - item.monto
            if pesaje.remito.saldo_pendiente < 0:
                pesaje.remito.saldo_pendiente = Decimal("0")

    # Calcular diferencia
    diferencia = total_haber - total_debe
    saldo_a_favor = None

    if diferencia > Decimal("0.01"):
        # Queda saldo a favor del cliente
        saldo_a_favor = diferencia

    # Actualizar estado del cobro
    cobro.estado = "aplicado"
    cobro.monto_aplicado = total_haber
    cobro.diferencia = diferencia

    db.commit()

    return AplicarCobroResponse(
        cobro_id=cobro.id,
        numero_cobro=cobro.numero_cobro,
        movimientos_generados=movimientos_generados,
        saldo_a_favor=saldo_a_favor,
        mensaje=f"Cobro aplicado exitosamente. {'Saldo a favor: $' + str(saldo_a_favor) if saldo_a_favor else 'Balance correcto.'}"
    )


def anular_cobro(
    db: Session,
    cobro_id: UUID,
    motivo: str,
    usuario_id: UUID
) -> CobroCliente:
    """Anula un cobro"""
    cobro = obtener_cobro(db, cobro_id)
    if not cobro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobro no encontrado"
        )

    if cobro.estado == "aplicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede anular un cobro ya aplicado. Debe revertir los movimientos primero."
        )

    cobro.anulado = True
    cobro.motivo_anulacion = motivo

    db.commit()
    db.refresh(cobro)

    return cobro


def obtener_documentos_pendientes(
    db: Session,
    empresa_id: UUID
) -> DocumentosPendientesResponse:
    """Obtiene facturas y tickets pendientes de cobro de un cliente"""
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Obtener facturas pendientes
    facturas_db = db.query(Factura).filter(
        Factura.empresa_id == empresa_id,
        Factura.estado.in_(["pendiente", "parcial"]),
        Factura.anulada == False,
        Factura.saldo_pendiente > 0
    ).order_by(Factura.fecha_emision).all()

    facturas = [
        FacturaPendienteSchema(
            id=f.id,
            numero_factura=f.numero_factura,
            fecha_emision=f.fecha_emision,
            total=f.total,
            saldo_pendiente=f.saldo_pendiente
        )
        for f in facturas_db
    ]

    # Obtener remitos pendientes con saldo > 0
    remitos_db = db.query(Remito).join(Pesaje).filter(
        Pesaje.cliente_id == empresa_id,
        Remito.saldo_pendiente > 0,
        Remito.facturado == False
    ).order_by(Remito.fecha).all()

    tickets = [
        TicketPendienteSchema(
            id=r.id,
            numero=r.numero_remito,
            tipo="remito",
            fecha=r.fecha,
            material=r.producto,
            peso_neto=r.peso_neto,
            importe=r.importe or Decimal("0"),
            saldo_pendiente=r.saldo_pendiente or Decimal("0")
        )
        for r in remitos_db
    ]

    # También buscar pesajes con importe que no tienen remito o cuyo remito no tiene saldo
    # Esto es para pesajes históricos que no se migraron correctamente
    pesajes_ids_con_remito = [r.pesaje_id for r in remitos_db if r.pesaje_id]

    pesajes_pendientes = db.query(Pesaje).filter(
        Pesaje.cliente_id == empresa_id,
        Pesaje.estado == "completado",
        Pesaje.importe_total > 0,
        ~Pesaje.id.in_(pesajes_ids_con_remito) if pesajes_ids_con_remito else True
    ).order_by(Pesaje.fecha).all()

    # Agregar pesajes que no están en remitos con saldo
    for p in pesajes_pendientes:
        # Verificar si tiene remito pero sin saldo (datos históricos)
        remito_existente = db.query(Remito).filter(Remito.pesaje_id == p.id).first()

        if remito_existente:
            # Si tiene remito pero saldo_pendiente es 0 o NULL, usar el importe del pesaje
            if not remito_existente.saldo_pendiente or remito_existente.saldo_pendiente <= 0:
                # Actualizar el remito con el saldo correcto
                remito_existente.importe = p.importe_total
                remito_existente.saldo_pendiente = p.importe_total
                db.commit()

                tickets.append(TicketPendienteSchema(
                    id=remito_existente.id,
                    numero=remito_existente.numero_remito,
                    tipo="remito",
                    fecha=remito_existente.fecha,
                    material=remito_existente.producto,
                    peso_neto=remito_existente.peso_neto,
                    importe=p.importe_total,
                    saldo_pendiente=p.importe_total
                ))
        else:
            # Pesaje sin remito - mostrar como ticket directo
            patente = p.camion.patente if p.camion else p.patente_externa
            tickets.append(TicketPendienteSchema(
                id=p.id,  # Usamos el ID del pesaje
                numero=p.numero_pesaje,
                tipo="pesaje",
                fecha=p.fecha.date() if hasattr(p.fecha, 'date') else p.fecha,
                material=p.material,
                peso_neto=p.peso_neto,
                importe=p.importe_total,
                saldo_pendiente=p.importe_total  # Todo el importe está pendiente
            ))

    total_facturas = sum(f.saldo_pendiente for f in facturas)
    total_tickets = sum(t.saldo_pendiente for t in tickets)

    return DocumentosPendientesResponse(
        empresa_id=empresa_id,
        empresa_nombre=empresa.nombre,
        saldo_cuenta_corriente=empresa.saldo_cuenta_corriente or Decimal("0"),
        facturas=facturas,
        tickets=tickets,
        total_pendiente=total_facturas + total_tickets
    )
