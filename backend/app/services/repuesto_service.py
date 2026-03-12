"""
Servicio de lógica de negocio para Repuestos
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.repuesto import Repuesto, RepuestoEquipo
from app.models.movimiento_stock import MovimientoStock, TipoMovimientoEnum
from app.schemas.repuesto import RepuestoCreate, RepuestoUpdate


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True,
    camion_id: Optional[UUID] = None
) -> List[dict]:
    """Obtiene todos los repuestos con paginación"""
    query = db.query(Repuesto)

    if solo_activos:
        query = query.filter(Repuesto.activo == True)

    if camion_id:
        query = query.filter(Repuesto.camion_id == camion_id)

    repuestos = query.order_by(desc(Repuesto.created_at)).offset(skip).limit(limit).all()

    # Agregar camion_patente a cada repuesto
    return [_repuesto_con_patente(r) for r in repuestos]


def _repuesto_con_patente(repuesto: Repuesto) -> dict:
    """Convierte un repuesto a dict incluyendo la patente del camión"""
    data = {
        "id": repuesto.id,
        "codigo": repuesto.codigo,
        "nombre": repuesto.nombre,
        "categoria": repuesto.categoria,
        "stock_actual": repuesto.stock_actual,
        "stock_minimo": repuesto.stock_minimo,
        "unidad": repuesto.unidad,
        "precio_unitario": repuesto.precio_unitario,
        "proveedor": repuesto.proveedor,
        "ubicacion_deposito": repuesto.ubicacion_deposito,
        "activo": repuesto.activo,
        "camion_id": getattr(repuesto, 'camion_id', None),
        "camion_patente": None,
        "created_at": repuesto.created_at,
        "updated_at": repuesto.updated_at,
    }

    # Intentar obtener la patente del camión de forma segura
    try:
        camion = getattr(repuesto, 'camion', None)
        if camion:
            if getattr(camion, 'categoria', None) == 'maquina':
                data["camion_patente"] = camion.nombre or camion.codigo_interno
            else:
                data["camion_patente"] = camion.patente or camion.codigo_interno
    except Exception:
        pass  # Si falla, dejamos camion_patente como None

    return data


def obtener_por_id(db: Session, repuesto_id: UUID) -> Optional[Repuesto]:
    """Obtiene un repuesto por ID"""
    return db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()


def obtener_por_codigo(db: Session, codigo: str) -> Optional[Repuesto]:
    """Obtiene un repuesto por código"""
    return db.query(Repuesto).filter(Repuesto.codigo == codigo).first()


def obtener_stock_bajo(db: Session) -> List[dict]:
    """
    Obtiene repuestos con stock bajo (stock_actual <= stock_minimo)

    Returns:
        Lista de repuestos con stock bajo
    """
    repuestos = db.query(Repuesto).filter(
        Repuesto.stock_actual <= Repuesto.stock_minimo,
        Repuesto.activo == True
    ).order_by(Repuesto.stock_actual).all()

    return [_repuesto_con_patente(r) for r in repuestos]


def obtener_por_equipo(
    db: Session,
    camion_id: UUID,
    incluir_generales: bool = True
) -> List[dict]:
    """
    Obtiene repuestos asignados a un equipo específico.
    Usa la nueva relación N:N (repuestos_equipos) además de la relación legacy (camion_id).

    Args:
        db: Sesión de base de datos
        camion_id: ID del equipo
        incluir_generales: Si True, incluye también repuestos sin asignación

    Returns:
        Lista de repuestos con campo 'asignado_a_equipo' indicando si está asignado al equipo actual
    """
    from sqlalchemy import or_, exists

    # Subquery para verificar si el repuesto está asignado al equipo en la tabla N:N
    asignado_nn = db.query(RepuestoEquipo.repuesto_id).filter(
        RepuestoEquipo.camion_id == camion_id
    ).subquery()

    query = db.query(Repuesto).filter(Repuesto.activo == True)

    if incluir_generales:
        # Incluir repuestos que:
        # 1. Están en la tabla N:N para este equipo
        # 2. Tienen camion_id = equipo (legacy)
        # 3. No tienen ninguna asignación (generales)
        query = query.filter(
            or_(
                Repuesto.id.in_(db.query(asignado_nn.c.repuesto_id)),
                Repuesto.camion_id == camion_id,
                # Repuestos generales: no tienen asignación legacy NI en tabla N:N
                (Repuesto.camion_id.is_(None) & ~exists(
                    db.query(RepuestoEquipo.id).filter(RepuestoEquipo.repuesto_id == Repuesto.id)
                ))
            )
        )
    else:
        # Solo repuestos asignados al equipo (N:N o legacy)
        query = query.filter(
            or_(
                Repuesto.id.in_(db.query(asignado_nn.c.repuesto_id)),
                Repuesto.camion_id == camion_id
            )
        )

    repuestos = query.order_by(Repuesto.nombre).all()

    # Agregar info de si está asignado a este equipo específico
    resultado = []
    for r in repuestos:
        data = _repuesto_con_patente(r)
        # Verificar si está asignado a este equipo (legacy o N:N)
        asignado_legacy = r.camion_id == camion_id
        asignado_nuevo = any(eq.camion_id == camion_id for eq in r.equipos_asignados)
        data["asignado_a_equipo"] = asignado_legacy or asignado_nuevo
        # Lista de IDs de equipos a los que está asignado (N:N)
        data["equipos_ids"] = [str(eq.camion_id) for eq in r.equipos_asignados]
        resultado.append(data)

    return resultado


def crear(db: Session, repuesto_data: RepuestoCreate) -> Repuesto:
    """
    Crea un nuevo repuesto

    Raises:
        HTTPException: Si el código ya existe
    """
    # Verificar que el código no exista
    if repuesto_data.codigo and obtener_por_codigo(db, repuesto_data.codigo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un repuesto con el código {repuesto_data.codigo}"
        )

    db_repuesto = Repuesto(**repuesto_data.model_dump())
    db.add(db_repuesto)
    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def actualizar(db: Session, repuesto_id: UUID, repuesto_data: RepuestoUpdate) -> Repuesto:
    """Actualiza un repuesto existente"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Si se está actualizando el código, verificar que no exista
    if repuesto_data.codigo and repuesto_data.codigo != db_repuesto.codigo:
        if obtener_por_codigo(db, repuesto_data.codigo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un repuesto con el código {repuesto_data.codigo}"
            )

    update_data = repuesto_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_repuesto, field, value)

    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def eliminar(db: Session, repuesto_id: UUID) -> Repuesto:
    """Elimina (soft delete) un repuesto"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    db_repuesto.activo = False
    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def ajustar_stock(
    db: Session,
    repuesto_id: UUID,
    cantidad: Decimal,
    tipo: TipoMovimientoEnum,
    usuario_id: UUID,
    referencia_tipo: str = "ajuste",
    referencia_id: Optional[UUID] = None,
    observaciones: Optional[str] = None
) -> Repuesto:
    """
    Ajusta el stock de un repuesto y crea un movimiento

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        cantidad: Cantidad a ajustar
        tipo: Tipo de movimiento (ingreso/egreso)
        usuario_id: ID del usuario que realiza el ajuste
        referencia_tipo: Tipo de referencia (ajuste, servicio, etc)
        referencia_id: ID de la referencia (opcional)
        observaciones: Observaciones del movimiento

    Returns:
        Repuesto actualizado

    Raises:
        HTTPException: Si no hay stock suficiente para egreso
    """
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Calcular nuevo stock
    if tipo == TipoMovimientoEnum.INGRESO:
        nuevo_stock = db_repuesto.stock_actual + cantidad
    else:  # EGRESO
        if db_repuesto.stock_actual < cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock actual: {db_repuesto.stock_actual}, requerido: {cantidad}"
            )
        nuevo_stock = db_repuesto.stock_actual - cantidad

    # Actualizar stock
    db_repuesto.stock_actual = nuevo_stock

    # Crear movimiento de stock
    movimiento = MovimientoStock(
        repuesto_id=repuesto_id,
        tipo=tipo,
        cantidad=cantidad,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        observaciones=observaciones,
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(db_repuesto)

    return db_repuesto


def asignar_a_equipo(db: Session, repuesto_id: UUID, camion_id: UUID) -> dict:
    """
    Asigna un repuesto a un equipo (relación N:N).
    Un repuesto puede estar asignado a múltiples equipos.

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        camion_id: ID del equipo

    Returns:
        Diccionario con resultado de la operación
    """
    # Verificar que el repuesto existe
    repuesto = obtener_por_id(db, repuesto_id)
    if not repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Verificar si ya existe la asignación
    existing = db.query(RepuestoEquipo).filter(
        RepuestoEquipo.repuesto_id == repuesto_id,
        RepuestoEquipo.camion_id == camion_id
    ).first()

    if existing:
        return {"message": "El repuesto ya está asignado a este equipo"}

    # Crear la nueva asignación
    nueva_asignacion = RepuestoEquipo(
        repuesto_id=repuesto_id,
        camion_id=camion_id
    )
    db.add(nueva_asignacion)
    db.commit()

    return {"message": "Repuesto asignado exitosamente", "asignacion_id": str(nueva_asignacion.id)}


def desasignar_de_equipo(db: Session, repuesto_id: UUID, camion_id: UUID) -> dict:
    """
    Desasigna un repuesto de un equipo (relación N:N).

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        camion_id: ID del equipo

    Returns:
        Diccionario con resultado de la operación
    """
    asignacion = db.query(RepuestoEquipo).filter(
        RepuestoEquipo.repuesto_id == repuesto_id,
        RepuestoEquipo.camion_id == camion_id
    ).first()

    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe asignación entre este repuesto y equipo"
        )

    db.delete(asignacion)
    db.commit()

    return {"message": "Asignación eliminada exitosamente"}


def obtener_equipos_asignados(db: Session, repuesto_id: UUID) -> List[dict]:
    """
    Obtiene todos los equipos a los que está asignado un repuesto.

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto

    Returns:
        Lista de equipos asignados
    """
    repuesto = obtener_por_id(db, repuesto_id)
    if not repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    equipos = []

    # Incluir equipo legacy si existe
    if repuesto.camion_id and repuesto.camion:
        camion = repuesto.camion
        equipos.append({
            "id": str(camion.id),
            "identificador": camion.patente or camion.nombre or camion.codigo_interno,
            "categoria": camion.categoria,
            "legacy": True
        })

    # Incluir equipos de la tabla N:N
    for asignacion in repuesto.equipos_asignados:
        camion = asignacion.camion
        if camion and str(camion.id) not in [e["id"] for e in equipos]:
            equipos.append({
                "id": str(camion.id),
                "identificador": camion.patente or camion.nombre or camion.codigo_interno,
                "categoria": camion.categoria,
                "legacy": False
            })

    return equipos


def actualizar_equipos_asignados(db: Session, repuesto_id: UUID, equipos_ids: List[UUID]) -> dict:
    """
    Actualiza la lista completa de equipos asignados a un repuesto.
    Reemplaza todas las asignaciones existentes.

    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        equipos_ids: Lista de IDs de equipos a asignar

    Returns:
        Diccionario con resultado de la operación
    """
    repuesto = obtener_por_id(db, repuesto_id)
    if not repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    # Eliminar asignaciones existentes en la tabla N:N
    db.query(RepuestoEquipo).filter(
        RepuestoEquipo.repuesto_id == repuesto_id
    ).delete()

    # Limpiar la asignación legacy
    repuesto.camion_id = None

    # Crear nuevas asignaciones
    for equipo_id in equipos_ids:
        nueva_asignacion = RepuestoEquipo(
            repuesto_id=repuesto_id,
            camion_id=equipo_id
        )
        db.add(nueva_asignacion)

    db.commit()

    return {
        "message": f"Repuesto asignado a {len(equipos_ids)} equipo(s)",
        "equipos_asignados": len(equipos_ids)
    }


def obtener_movimientos(db: Session, repuesto_id: UUID) -> List[dict]:
    """Obtiene el historial de movimientos de un repuesto con info del usuario"""
    db_repuesto = obtener_por_id(db, repuesto_id)

    if not db_repuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repuesto no encontrado"
        )

    movimientos = db.query(MovimientoStock).filter(
        MovimientoStock.repuesto_id == repuesto_id
    ).order_by(desc(MovimientoStock.created_at)).all()

    # Agregar nombre de usuario a cada movimiento
    resultado = []
    for mov in movimientos:
        resultado.append({
            "id": str(mov.id),
            "tipo": mov.tipo.value,
            "cantidad": float(mov.cantidad),
            "observaciones": mov.observaciones,
            "referencia_tipo": mov.referencia_tipo,
            "created_at": mov.created_at.isoformat(),
            "usuario_id": str(mov.usuario_id),
            "usuario_nombre": mov.usuario.nombre if mov.usuario else "Sistema"
        })

    return resultado
