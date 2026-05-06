"""
Servicio de lógica de negocio para Cuenta Corriente
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import date
from fastapi import HTTPException, status

from app.models.cuenta_corriente import MovimientoCuentaCorriente, HistorialMovimientoCC
from app.models.empresa import Empresa
from app.models.pesaje import Pesaje
from app.models.usuario import Usuario
from app.models.finanzas import MovimientoFinanciero, CategoriaFinanzas


def _registrar_historial(
    db: Session,
    movimiento_id: UUID,
    usuario_id: UUID,
    accion: str,
    detalle: Optional[str] = None,
) -> None:
    """Registra una entrada en el historial de un movimiento de cuenta corriente"""
    historial = HistorialMovimientoCC(
        movimiento_id=movimiento_id,
        usuario_id=usuario_id,
        accion=accion,
        detalle=detalle,
    )
    db.add(historial)


def obtener_historial_movimiento(db: Session, movimiento_id: UUID) -> List[dict]:
    """Obtiene el historial de un movimiento de cuenta corriente.

    Si el movimiento no tiene entradas registradas (movimientos previos a la
    implementación del historial), genera al menos un registro de creación
    a partir de los datos del propio movimiento.
    """
    movimiento = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.id == movimiento_id
    ).first()

    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )

    entradas = db.query(HistorialMovimientoCC).filter(
        HistorialMovimientoCC.movimiento_id == movimiento_id
    ).order_by(desc(HistorialMovimientoCC.created_at)).all()

    resultado = []
    for h in entradas:
        usuario = db.query(Usuario).filter(Usuario.id == h.usuario_id).first()
        resultado.append({
            "id": h.id,
            "fecha": h.created_at,
            "usuario_nombre": usuario.nombre if usuario else "Usuario desconocido",
            "accion": h.accion,
            "detalle": h.detalle,
        })

    if not resultado:
        creador = db.query(Usuario).filter(Usuario.id == movimiento.created_by).first()
        resultado.append({
            "id": None,
            "fecha": movimiento.created_at,
            "usuario_nombre": creador.nombre if creador else "Usuario desconocido",
            "accion": "CREACION",
            "detalle": None,
        })
        if movimiento.anulado:
            resultado.insert(0, {
                "id": None,
                "fecha": movimiento.updated_at,
                "usuario_nombre": creador.nombre if creador else "Usuario desconocido",
                "accion": "ANULACION",
                "detalle": movimiento.motivo_anulacion,
            })

    return resultado


def obtener_saldo_cliente(db: Session, empresa_id: UUID) -> Decimal:
    """Obtiene el saldo actual de un cliente"""
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return empresa.saldo_cuenta_corriente or Decimal("0")


def obtener_movimientos_cliente(
    db: Session,
    empresa_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[MovimientoCuentaCorriente]:
    """Obtiene movimientos de cuenta corriente de un cliente"""
    query = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.anulado == False
    )

    if fecha_desde:
        query = query.filter(MovimientoCuentaCorriente.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(MovimientoCuentaCorriente.fecha <= fecha_hasta)

    return query.order_by(desc(MovimientoCuentaCorriente.created_at)).offset(skip).limit(limit).all()


def obtener_resumen_cliente(db: Session, empresa_id: UUID) -> dict:
    """Obtiene resumen de cuenta corriente de un cliente"""
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Totales
    total_cargos = db.query(func.coalesce(func.sum(MovimientoCuentaCorriente.monto), Decimal("0"))).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.tipo == "cargo",
        MovimientoCuentaCorriente.anulado == False
    ).scalar()

    total_pagos = db.query(func.coalesce(func.sum(MovimientoCuentaCorriente.monto), Decimal("0"))).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.tipo == "pago",
        MovimientoCuentaCorriente.anulado == False
    ).scalar()

    cantidad_movimientos = db.query(func.count(MovimientoCuentaCorriente.id)).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.anulado == False
    ).scalar()

    return {
        "empresa_id": str(empresa_id),
        "empresa_nombre": empresa.nombre,
        "saldo_actual": float(empresa.saldo_cuenta_corriente or 0),
        "total_cargos": float(total_cargos),
        "total_pagos": float(total_pagos),
        "cantidad_movimientos": cantidad_movimientos
    }


def registrar_cargo_pesaje(
    db: Session,
    pesaje: Pesaje,
    usuario_id: UUID
) -> MovimientoCuentaCorriente:
    """
    Registra un cargo en cuenta corriente por un pesaje
    """
    if not pesaje.cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pesaje no tiene cliente asignado"
        )

    if not pesaje.importe_total or pesaje.importe_total <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pesaje no tiene importe"
        )

    # Obtener empresa y saldo actual
    empresa = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")
    saldo_posterior = saldo_anterior + pesaje.importe_total

    # Crear descripción
    peso_tn = pesaje.peso_neto / Decimal("1000")
    descripcion = f"Pesaje #{pesaje.numero_pesaje}"
    if pesaje.material:
        descripcion += f" - {pesaje.material}"
    descripcion += f" ({peso_tn:.2f} tn)"

    # Crear movimiento
    movimiento = MovimientoCuentaCorriente(
        empresa_id=pesaje.cliente_id,
        tipo="cargo",
        monto=pesaje.importe_total,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        fecha=pesaje.fecha.date() if hasattr(pesaje.fecha, 'date') else pesaje.fecha,
        descripcion=descripcion,
        detalle=f"Precio/tn: ${pesaje.precio_unitario:,.2f}" if pesaje.precio_unitario else None,
        pesaje_id=pesaje.id,
        created_by=usuario_id
    )

    # Actualizar saldo de empresa
    empresa.saldo_cuenta_corriente = saldo_posterior

    # Inicializar saldo_pendiente del pesaje (para que aparezca correctamente
    # en la lista de "documentos pendientes" al hacer un cobro).
    pesaje.saldo_pendiente = pesaje.importe_total

    db.add(movimiento)
    db.flush()
    _registrar_historial(
        db,
        movimiento.id,
        usuario_id,
        "CREACION",
        f"Cargo automático por pesaje #{pesaje.numero_pesaje}",
    )
    db.commit()
    db.refresh(movimiento)

    return movimiento


def registrar_pago(
    db: Session,
    empresa_id: UUID,
    monto: Decimal,
    fecha: date,
    descripcion: str,
    usuario_id: UUID,
    metodo_pago: Optional[str] = None,
    numero_comprobante: Optional[str] = None,
    referencia_pago: Optional[str] = None,
    banco: Optional[str] = None,
    notas: Optional[str] = None,
    registrar_ingreso: bool = True
) -> MovimientoCuentaCorriente:
    """
    Registra un pago de un cliente

    Args:
        registrar_ingreso: Si True, crea también un movimiento financiero de ingreso
    """
    # Obtener empresa y saldo actual
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")
    saldo_posterior = saldo_anterior - monto  # Pago reduce el saldo (deuda)

    # Crear movimiento de cuenta corriente
    movimiento = MovimientoCuentaCorriente(
        empresa_id=empresa_id,
        tipo="pago",
        monto=monto,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        fecha=fecha,
        descripcion=descripcion,
        metodo_pago=metodo_pago,
        numero_comprobante=numero_comprobante,
        referencia_pago=referencia_pago,
        banco=banco,
        notas=notas,
        created_by=usuario_id
    )

    # Actualizar saldo de empresa
    empresa.saldo_cuenta_corriente = saldo_posterior

    db.add(movimiento)
    db.flush()

    # Registrar ingreso en finanzas si se solicita
    if registrar_ingreso:
        # Buscar categoría de cobros a clientes
        categoria = db.query(CategoriaFinanzas).filter(
            CategoriaFinanzas.nombre == "Cobros a clientes",
            CategoriaFinanzas.tipo == "ingreso"
        ).first()

        # Si no existe, buscar venta de materiales
        if not categoria:
            categoria = db.query(CategoriaFinanzas).filter(
                CategoriaFinanzas.nombre == "Venta de materiales",
                CategoriaFinanzas.tipo == "ingreso"
            ).first()

        ingreso = MovimientoFinanciero(
            tipo="ingreso",
            categoria_id=categoria.id if categoria else None,
            fecha=fecha,
            monto=monto,
            descripcion=f"Pago de {empresa.nombre}",
            detalle=descripcion,
            empresa_id=empresa_id,
            numero_comprobante=numero_comprobante,
            tipo_comprobante="recibo",
            metodo_pago=metodo_pago,
            referencia_pago=referencia_pago,
            banco=banco,
            estado="completado",
            created_by=usuario_id,
            notas=f"Pago registrado desde cuenta corriente"
        )

        db.add(ingreso)
        db.flush()

        # Vincular movimiento CC con ingreso
        movimiento.movimiento_financiero_id = ingreso.id

    _registrar_historial(
        db,
        movimiento.id,
        usuario_id,
        "CREACION",
        f"Pago registrado{f' ({metodo_pago})' if metodo_pago else ''}",
    )
    db.commit()
    db.refresh(movimiento)

    return movimiento


def registrar_ajuste(
    db: Session,
    empresa_id: UUID,
    monto: Decimal,
    es_credito: bool,
    fecha: date,
    descripcion: str,
    usuario_id: UUID,
    notas: Optional[str] = None
) -> MovimientoCuentaCorriente:
    """
    Registra un ajuste (nota de crédito o débito)

    Args:
        es_credito: True = reduce deuda, False = aumenta deuda
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")

    if es_credito:
        saldo_posterior = saldo_anterior - monto  # Crédito reduce deuda
        tipo_ajuste = "Nota de crédito"
    else:
        saldo_posterior = saldo_anterior + monto  # Débito aumenta deuda
        tipo_ajuste = "Nota de débito"

    movimiento = MovimientoCuentaCorriente(
        empresa_id=empresa_id,
        tipo="ajuste",
        monto=monto if not es_credito else -monto,  # Negativo si es crédito
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        fecha=fecha,
        descripcion=f"{tipo_ajuste}: {descripcion}",
        notas=notas,
        created_by=usuario_id
    )

    empresa.saldo_cuenta_corriente = saldo_posterior

    db.add(movimiento)
    db.flush()
    _registrar_historial(
        db,
        movimiento.id,
        usuario_id,
        "CREACION",
        f"{tipo_ajuste}",
    )
    db.commit()
    db.refresh(movimiento)

    return movimiento


def actualizar_monto_cargo(
    db: Session,
    movimiento_id: UUID,
    nuevo_monto: Decimal,
    precio_unitario: Optional[Decimal] = None,
    usuario_id: UUID = None
) -> MovimientoCuentaCorriente:
    """
    Actualiza el monto de un cargo en cuenta corriente.
    Útil para agregar precio a pesajes que se registraron sin importe.

    También actualiza el pesaje asociado si existe.
    """
    movimiento = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.id == movimiento_id
    ).first()

    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    if movimiento.anulado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar un movimiento anulado"
        )

    if movimiento.tipo != "cargo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden editar montos de cargos"
        )

    # Obtener empresa
    empresa = db.query(Empresa).filter(Empresa.id == movimiento.empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Calcular diferencia y actualizar saldo
    diferencia = nuevo_monto - movimiento.monto
    empresa.saldo_cuenta_corriente = (empresa.saldo_cuenta_corriente or Decimal("0")) + diferencia

    # Actualizar monto del movimiento
    monto_anterior = movimiento.monto
    movimiento.monto = nuevo_monto
    movimiento.saldo_posterior = movimiento.saldo_anterior + nuevo_monto

    # Actualizar detalle
    if precio_unitario:
        movimiento.detalle = f"Precio/tn: ${precio_unitario:,.2f}"
    elif nuevo_monto > 0:
        movimiento.detalle = f"Monto actualizado (anterior: ${monto_anterior:,.2f})"

    # Si tiene pesaje asociado, actualizarlo también
    if movimiento.pesaje_id:
        pesaje = db.query(Pesaje).filter(Pesaje.id == movimiento.pesaje_id).first()
        if pesaje:
            pesaje.importe_total = nuevo_monto
            if precio_unitario:
                pesaje.precio_unitario = precio_unitario

            # Ajustar saldo_pendiente del pesaje por la diferencia, sin bajar de 0.
            saldo_actual = pesaje.saldo_pendiente or Decimal("0")
            nuevo_saldo = saldo_actual + diferencia
            pesaje.saldo_pendiente = nuevo_saldo if nuevo_saldo > 0 else Decimal("0")

            # Si tiene remito vinculado, sincronizar su importe y saldo_pendiente.
            from app.models.remito import Remito
            remito = db.query(Remito).filter(Remito.pesaje_id == pesaje.id).first()
            if remito:
                remito.importe = nuevo_monto
                saldo_remito = remito.saldo_pendiente or Decimal("0")
                nuevo_saldo_remito = saldo_remito + diferencia
                remito.saldo_pendiente = nuevo_saldo_remito if nuevo_saldo_remito > 0 else Decimal("0")

    if usuario_id:
        detalle_hist = f"Monto: ${monto_anterior:,.2f} → ${nuevo_monto:,.2f}"
        if precio_unitario:
            detalle_hist += f" (precio/tn: ${precio_unitario:,.2f})"
        _registrar_historial(db, movimiento.id, usuario_id, "MODIFICACION", detalle_hist)

    db.commit()
    db.refresh(movimiento)

    return movimiento


def recalcular_saldos_movimientos(db: Session, empresa_id: UUID) -> dict:
    """Recalcula saldo_anterior/saldo_posterior de todos los movimientos no anulados
    de un cliente en orden cronológico, y sincroniza empresa.saldo_cuenta_corriente.

    Útil después de anular movimientos viejos para que el running balance de cada
    fila vuelva a ser coherente.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    movimientos = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.empresa_id == empresa_id,
        MovimientoCuentaCorriente.anulado == False,
    ).order_by(
        MovimientoCuentaCorriente.fecha.asc(),
        MovimientoCuentaCorriente.created_at.asc(),
    ).all()

    saldo = Decimal("0")
    actualizados = 0
    for mov in movimientos:
        nuevo_anterior = saldo
        if mov.tipo == "cargo":
            nuevo_posterior = saldo + mov.monto
        elif mov.tipo == "pago":
            nuevo_posterior = saldo - mov.monto
        else:  # ajuste: monto ya viene firmado (negativo si es crédito)
            nuevo_posterior = saldo + mov.monto

        if mov.saldo_anterior != nuevo_anterior or mov.saldo_posterior != nuevo_posterior:
            mov.saldo_anterior = nuevo_anterior
            mov.saldo_posterior = nuevo_posterior
            actualizados += 1

        saldo = nuevo_posterior

    saldo_previo = empresa.saldo_cuenta_corriente or Decimal("0")
    empresa.saldo_cuenta_corriente = saldo
    db.commit()

    return {
        "empresa_id": str(empresa_id),
        "movimientos_procesados": len(movimientos),
        "movimientos_actualizados": actualizados,
        "saldo_anterior_empresa": float(saldo_previo),
        "saldo_recalculado": float(saldo),
    }


def anular_movimiento(
    db: Session,
    movimiento_id: UUID,
    motivo: str,
    usuario_id: UUID
) -> MovimientoCuentaCorriente:
    """Anula un movimiento de cuenta corriente"""
    movimiento = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.id == movimiento_id
    ).first()

    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    if movimiento.anulado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El movimiento ya está anulado"
        )

    empresa_id = movimiento.empresa_id

    # Marcar como anulado
    movimiento.anulado = True
    movimiento.motivo_anulacion = motivo

    # Si tiene movimiento financiero asociado, anularlo también
    if movimiento.movimiento_financiero_id:
        ingreso = db.query(MovimientoFinanciero).filter(
            MovimientoFinanciero.id == movimiento.movimiento_financiero_id
        ).first()
        if ingreso:
            ingreso.estado = "anulado"

    _registrar_historial(db, movimiento.id, usuario_id, "ANULACION", motivo)
    db.flush()

    # Recalcular saldos de todos los movimientos posteriores y el saldo de la empresa
    recalcular_saldos_movimientos(db, empresa_id)

    db.refresh(movimiento)
    return movimiento


def obtener_clientes_con_deuda(db: Session) -> List[dict]:
    """Obtiene lista de clientes con saldo pendiente"""
    empresas = db.query(Empresa).filter(
        Empresa.tipo == "cliente",
        Empresa.activo == True,
        Empresa.saldo_cuenta_corriente > 0
    ).order_by(desc(Empresa.saldo_cuenta_corriente)).all()

    return [
        {
            "id": str(e.id),
            "nombre": e.nombre,
            "cuit": e.cuit,
            "saldo": float(e.saldo_cuenta_corriente)
        }
        for e in empresas
    ]
