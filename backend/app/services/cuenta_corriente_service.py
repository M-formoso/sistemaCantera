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

from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.models.empresa import Empresa
from app.models.pesaje import Pesaje
from app.models.finanzas import MovimientoFinanciero, CategoriaFinanzas


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

    db.add(movimiento)
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
    db.commit()
    db.refresh(movimiento)

    return movimiento


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

    # Revertir el saldo
    empresa = db.query(Empresa).filter(Empresa.id == movimiento.empresa_id).first()
    if movimiento.tipo == "cargo":
        empresa.saldo_cuenta_corriente -= movimiento.monto
    elif movimiento.tipo == "pago":
        empresa.saldo_cuenta_corriente += movimiento.monto
    elif movimiento.tipo == "ajuste":
        empresa.saldo_cuenta_corriente -= movimiento.monto  # Revertir ajuste

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

    db.commit()
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
