"""
Servicio de lógica de negocio para Finanzas
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from uuid import UUID
from typing import List, Optional, Literal
from decimal import Decimal
from datetime import date, datetime, timedelta
from fastapi import HTTPException, status

from app.models.finanzas import CategoriaFinanzas, MovimientoFinanciero, CuentaBancaria
from app.models.camion import Camion
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.finanzas import (
    CategoriaFinanzasCreate, CategoriaFinanzasUpdate,
    MovimientoFinancieroCreate, MovimientoFinancieroUpdate,
    CuentaBancariaCreate, CuentaBancariaUpdate,
    ResumenFinanciero, ResumenPorCategoria
)


# =============================================
# CATEGORÍAS
# =============================================

def obtener_categorias(
    db: Session,
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    solo_activos: bool = True
) -> List[CategoriaFinanzas]:
    """Obtiene todas las categorías"""
    query = db.query(CategoriaFinanzas)

    if tipo:
        query = query.filter(CategoriaFinanzas.tipo == tipo)

    if solo_activos:
        query = query.filter(CategoriaFinanzas.activo == True)

    return query.order_by(CategoriaFinanzas.tipo, CategoriaFinanzas.nombre).all()


def obtener_categoria_por_id(db: Session, categoria_id: UUID) -> Optional[CategoriaFinanzas]:
    """Obtiene una categoría por ID"""
    return db.query(CategoriaFinanzas).filter(CategoriaFinanzas.id == categoria_id).first()


def crear_categoria(db: Session, data: CategoriaFinanzasCreate) -> CategoriaFinanzas:
    """Crea una nueva categoría"""
    db_categoria = CategoriaFinanzas(**data.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


def actualizar_categoria(db: Session, categoria_id: UUID, data: CategoriaFinanzasUpdate) -> CategoriaFinanzas:
    """Actualiza una categoría"""
    db_categoria = obtener_categoria_por_id(db, categoria_id)

    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_categoria, field, value)

    db.commit()
    db.refresh(db_categoria)
    return db_categoria


# =============================================
# MOVIMIENTOS FINANCIEROS
# =============================================

def obtener_movimientos(
    db: Session,
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    categoria_id: Optional[UUID] = None,
    camion_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[MovimientoFinanciero]:
    """Obtiene movimientos con filtros"""
    query = db.query(MovimientoFinanciero)

    if tipo:
        query = query.filter(MovimientoFinanciero.tipo == tipo)

    if categoria_id:
        query = query.filter(MovimientoFinanciero.categoria_id == categoria_id)

    if camion_id:
        query = query.filter(MovimientoFinanciero.camion_id == camion_id)

    if empresa_id:
        query = query.filter(MovimientoFinanciero.empresa_id == empresa_id)

    if fecha_desde:
        query = query.filter(MovimientoFinanciero.fecha >= fecha_desde)

    if fecha_hasta:
        query = query.filter(MovimientoFinanciero.fecha <= fecha_hasta)

    if estado:
        query = query.filter(MovimientoFinanciero.estado == estado)

    return query.order_by(desc(MovimientoFinanciero.fecha), desc(MovimientoFinanciero.created_at)).offset(skip).limit(limit).all()


def obtener_movimiento_por_id(db: Session, movimiento_id: UUID) -> Optional[MovimientoFinanciero]:
    """Obtiene un movimiento por ID"""
    return db.query(MovimientoFinanciero).filter(MovimientoFinanciero.id == movimiento_id).first()


def crear_movimiento(db: Session, data: MovimientoFinancieroCreate, usuario_id: UUID) -> MovimientoFinanciero:
    """Crea un nuevo movimiento"""
    db_movimiento = MovimientoFinanciero(
        **data.model_dump(),
        created_by=usuario_id
    )
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    return db_movimiento


def actualizar_movimiento(db: Session, movimiento_id: UUID, data: MovimientoFinancieroUpdate) -> MovimientoFinanciero:
    """Actualiza un movimiento"""
    db_movimiento = obtener_movimiento_por_id(db, movimiento_id)

    if not db_movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movimiento, field, value)

    db.commit()
    db.refresh(db_movimiento)
    return db_movimiento


def eliminar_movimiento(db: Session, movimiento_id: UUID) -> MovimientoFinanciero:
    """Elimina un movimiento (anulación)"""
    db_movimiento = obtener_movimiento_por_id(db, movimiento_id)

    if not db_movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    db_movimiento.estado = "anulado"
    db.commit()
    db.refresh(db_movimiento)
    return db_movimiento


def obtener_movimiento_con_relaciones(db: Session, movimiento: MovimientoFinanciero) -> dict:
    """Obtiene un movimiento con datos de relaciones para el schema"""
    data = {
        "id": movimiento.id,
        "tipo": movimiento.tipo,
        "categoria_id": movimiento.categoria_id,
        "fecha": movimiento.fecha,
        "monto": movimiento.monto,
        "descripcion": movimiento.descripcion,
        "detalle": movimiento.detalle,
        "camion_id": movimiento.camion_id,
        "empresa_id": movimiento.empresa_id,
        "numero_comprobante": movimiento.numero_comprobante,
        "tipo_comprobante": movimiento.tipo_comprobante,
        "comprobante_url": movimiento.comprobante_url,
        "metodo_pago": movimiento.metodo_pago,
        "referencia_pago": movimiento.referencia_pago,
        "banco": movimiento.banco,
        "estado": movimiento.estado,
        "created_by": movimiento.created_by,
        "notas": movimiento.notas,
        "created_at": movimiento.created_at,
        "updated_at": movimiento.updated_at,
        "categoria_nombre": None,
        "camion_identificador": None,
        "empresa_nombre": None,
        "creador_nombre": None
    }

    # Cargar relaciones
    if movimiento.categoria:
        data["categoria_nombre"] = movimiento.categoria.nombre

    if movimiento.camion:
        data["camion_identificador"] = movimiento.camion.patente or movimiento.camion.nombre or movimiento.camion.codigo_interno

    if movimiento.empresa:
        data["empresa_nombre"] = movimiento.empresa.nombre

    if movimiento.creador:
        data["creador_nombre"] = movimiento.creador.nombre

    return data


# =============================================
# RESÚMENES Y ESTADÍSTICAS
# =============================================

def obtener_resumen(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> ResumenFinanciero:
    """Obtiene resumen financiero del período"""
    query_ingresos = db.query(
        func.coalesce(func.sum(MovimientoFinanciero.monto), Decimal("0")).label("total"),
        func.count(MovimientoFinanciero.id).label("cantidad")
    ).filter(
        MovimientoFinanciero.tipo == "ingreso",
        MovimientoFinanciero.estado != "anulado"
    )

    query_egresos = db.query(
        func.coalesce(func.sum(MovimientoFinanciero.monto), Decimal("0")).label("total"),
        func.count(MovimientoFinanciero.id).label("cantidad")
    ).filter(
        MovimientoFinanciero.tipo == "egreso",
        MovimientoFinanciero.estado != "anulado"
    )

    if fecha_desde:
        query_ingresos = query_ingresos.filter(MovimientoFinanciero.fecha >= fecha_desde)
        query_egresos = query_egresos.filter(MovimientoFinanciero.fecha >= fecha_desde)

    if fecha_hasta:
        query_ingresos = query_ingresos.filter(MovimientoFinanciero.fecha <= fecha_hasta)
        query_egresos = query_egresos.filter(MovimientoFinanciero.fecha <= fecha_hasta)

    resultado_ingresos = query_ingresos.first()
    resultado_egresos = query_egresos.first()

    total_ingresos = resultado_ingresos.total or Decimal("0")
    total_egresos = resultado_egresos.total or Decimal("0")

    return ResumenFinanciero(
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        balance=total_ingresos - total_egresos,
        cantidad_ingresos=resultado_ingresos.cantidad or 0,
        cantidad_egresos=resultado_egresos.cantidad or 0
    )


def obtener_resumen_por_categoria(
    db: Session,
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[ResumenPorCategoria]:
    """Obtiene resumen agrupado por categoría"""
    query = db.query(
        CategoriaFinanzas.id.label("categoria_id"),
        CategoriaFinanzas.nombre.label("categoria_nombre"),
        CategoriaFinanzas.tipo.label("tipo"),
        CategoriaFinanzas.color.label("color"),
        func.coalesce(func.sum(MovimientoFinanciero.monto), Decimal("0")).label("total"),
        func.count(MovimientoFinanciero.id).label("cantidad")
    ).outerjoin(
        MovimientoFinanciero,
        and_(
            MovimientoFinanciero.categoria_id == CategoriaFinanzas.id,
            MovimientoFinanciero.estado != "anulado"
        )
    ).filter(
        CategoriaFinanzas.activo == True
    ).group_by(
        CategoriaFinanzas.id,
        CategoriaFinanzas.nombre,
        CategoriaFinanzas.tipo,
        CategoriaFinanzas.color
    )

    if tipo:
        query = query.filter(CategoriaFinanzas.tipo == tipo)

    if fecha_desde:
        query = query.filter(
            (MovimientoFinanciero.fecha >= fecha_desde) | (MovimientoFinanciero.fecha.is_(None))
        )

    if fecha_hasta:
        query = query.filter(
            (MovimientoFinanciero.fecha <= fecha_hasta) | (MovimientoFinanciero.fecha.is_(None))
        )

    resultados = query.order_by(CategoriaFinanzas.tipo, desc("total")).all()

    return [
        ResumenPorCategoria(
            categoria_id=r.categoria_id,
            categoria_nombre=r.categoria_nombre,
            tipo=r.tipo,
            total=r.total,
            cantidad=r.cantidad,
            color=r.color
        )
        for r in resultados
    ]


def obtener_resumen_diario(
    db: Session,
    dias: int = 30
) -> List[dict]:
    """Obtiene resumen de los últimos N días"""
    fecha_inicio = date.today() - timedelta(days=dias)

    resultados = db.query(
        MovimientoFinanciero.fecha,
        MovimientoFinanciero.tipo,
        func.sum(MovimientoFinanciero.monto).label("total")
    ).filter(
        MovimientoFinanciero.fecha >= fecha_inicio,
        MovimientoFinanciero.estado != "anulado"
    ).group_by(
        MovimientoFinanciero.fecha,
        MovimientoFinanciero.tipo
    ).order_by(
        MovimientoFinanciero.fecha
    ).all()

    # Agrupar por fecha
    por_fecha = {}
    for r in resultados:
        fecha_str = r.fecha.isoformat()
        if fecha_str not in por_fecha:
            por_fecha[fecha_str] = {"fecha": fecha_str, "ingresos": Decimal("0"), "egresos": Decimal("0")}
        if r.tipo == "ingreso":
            por_fecha[fecha_str]["ingresos"] = r.total
        else:
            por_fecha[fecha_str]["egresos"] = r.total

    return list(por_fecha.values())


# =============================================
# CUENTAS BANCARIAS
# =============================================

def obtener_cuentas(db: Session, solo_activas: bool = True) -> List[CuentaBancaria]:
    """Obtiene todas las cuentas bancarias"""
    query = db.query(CuentaBancaria)

    if solo_activas:
        query = query.filter(CuentaBancaria.activo == True)

    return query.order_by(CuentaBancaria.nombre).all()


def obtener_cuenta_por_id(db: Session, cuenta_id: UUID) -> Optional[CuentaBancaria]:
    """Obtiene una cuenta por ID"""
    return db.query(CuentaBancaria).filter(CuentaBancaria.id == cuenta_id).first()


def crear_cuenta(db: Session, data: CuentaBancariaCreate) -> CuentaBancaria:
    """Crea una nueva cuenta"""
    db_cuenta = CuentaBancaria(
        **data.model_dump(),
        saldo_actual=data.saldo_inicial or Decimal("0")
    )
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def actualizar_cuenta(db: Session, cuenta_id: UUID, data: CuentaBancariaUpdate) -> CuentaBancaria:
    """Actualiza una cuenta"""
    db_cuenta = obtener_cuenta_por_id(db, cuenta_id)

    if not db_cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cuenta, field, value)

    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta
