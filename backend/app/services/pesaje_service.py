"""
Servicio de lógica de negocio para Pesajes
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
from fastapi import HTTPException, status

from app.models.pesaje import Pesaje
from app.models.remito import Remito
from app.models.empresa import Empresa
from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.models.orden_entrega import OrdenEntrega, EstadoOrdenEntrega
from app.schemas.pesaje import PesajeCreate, PesajeUpdate
from app.services import camion_service


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Pesaje]:
    """Obtiene todos los pesajes con paginación, enriquecidos con datos relacionados"""
    from app.models.camion import Camion

    pesajes = db.query(Pesaje).order_by(desc(Pesaje.fecha)).offset(skip).limit(limit).all()

    # Enriquecer con datos
    for p in pesajes:
        # Patente del camión propio
        if p.camion_id:
            camion = db.query(Camion).filter(Camion.id == p.camion_id).first()
            if camion:
                p.camion_patente = camion.patente

        # Nombre del transportista
        if p.transportista_id:
            transportista = db.query(Empresa).filter(Empresa.id == p.transportista_id).first()
            if transportista:
                p.transportista_nombre = transportista.nombre

        # Nombre del cliente
        if p.cliente_id:
            cliente = db.query(Empresa).filter(Empresa.id == p.cliente_id).first()
            if cliente:
                p.cliente_nombre = cliente.nombre

    return pesajes


def obtener_por_id(db: Session, pesaje_id: UUID) -> Optional[Pesaje]:
    """Obtiene un pesaje por ID"""
    return db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()


def obtener_por_camion(db: Session, camion_id: UUID) -> List[Pesaje]:
    """Obtiene pesajes de un camión específico"""
    return db.query(Pesaje).filter(
        Pesaje.camion_id == camion_id
    ).order_by(desc(Pesaje.fecha)).all()


def obtener_por_fecha(
    db: Session,
    fecha_desde: date,
    fecha_hasta: Optional[date] = None
) -> List[Pesaje]:
    """
    Obtiene pesajes por rango de fechas

    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final (opcional, si no se provee usa fecha_desde)

    Returns:
        Lista de pesajes en el rango
    """
    if not fecha_hasta:
        fecha_hasta = fecha_desde

    return db.query(Pesaje).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta
    ).order_by(Pesaje.fecha).all()


def obtener_del_dia(db: Session, fecha: Optional[date] = None) -> List[Pesaje]:
    """
    Obtiene pesajes del día

    Args:
        db: Sesión de base de datos
        fecha: Fecha (opcional, por defecto hoy)

    Returns:
        Lista de pesajes del día
    """
    if not fecha:
        fecha = date.today()

    return obtener_por_fecha(db, fecha, fecha)


def _obtener_proximo_numero(db: Session) -> int:
    """
    Obtiene el próximo número de pesaje

    Returns:
        Próximo número de pesaje
    """
    ultimo_pesaje = db.query(Pesaje).order_by(desc(Pesaje.numero_pesaje)).first()
    return (ultimo_pesaje.numero_pesaje + 1) if ultimo_pesaje else 1


def crear(db: Session, pesaje_data: PesajeCreate, usuario_id: UUID) -> Pesaje:
    """
    Crea un nuevo pesaje

    Calcula automáticamente:
    - Número de pesaje (autoincremental)
    - Peso neto (bruto - tara)

    Soporta dos tipos de entrega:
    - propio: Camión de la cantera
    - transportista: Camión externo

    Returns:
        Pesaje creado
    """
    camion = None
    transportista_empresa = None
    cliente_empresa = None

    # Validar según tipo de entrega
    if pesaje_data.tipo_entrega == "propio":
        if not pesaje_data.camion_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe seleccionar un camión propio"
            )
        camion = camion_service.obtener_por_id(db, pesaje_data.camion_id)
        if not camion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camión no encontrado"
            )
    else:  # transportista
        if pesaje_data.transportista_id:
            transportista_empresa = db.query(Empresa).filter(Empresa.id == pesaje_data.transportista_id).first()
            if not transportista_empresa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transportista no encontrado"
                )

    # Verificar cliente si se proporciona
    if pesaje_data.cliente_id:
        cliente_empresa = db.query(Empresa).filter(Empresa.id == pesaje_data.cliente_id).first()
        if not cliente_empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )

    # Validar pesos
    if pesaje_data.peso_bruto <= pesaje_data.peso_tara:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El peso bruto debe ser mayor que el peso tara"
        )

    # Calcular peso neto
    peso_neto = pesaje_data.peso_bruto - pesaje_data.peso_tara

    # Obtener próximo número de pesaje
    numero_pesaje = _obtener_proximo_numero(db)

    # Preparar datos (excluir cliente_nombre que no es campo del modelo)
    pesaje_dict = pesaje_data.model_dump(exclude={'cliente_nombre'})

    # Crear pesaje
    db_pesaje = Pesaje(
        **pesaje_dict,
        numero_pesaje=numero_pesaje,
        peso_neto=peso_neto,
        created_by=usuario_id
    )

    db.add(db_pesaje)
    db.commit()
    db.refresh(db_pesaje)

    # Generar remito automáticamente
    _generar_remito_automatico(db, db_pesaje, usuario_id)

    # Si hay importe y cliente, registrar en cuenta corriente
    if db_pesaje.importe_total and db_pesaje.importe_total > 0 and db_pesaje.cliente_id:
        _registrar_en_cuenta_corriente(db, db_pesaje, usuario_id)

    # Si está asociado a una orden de entrega, actualizar la orden
    if db_pesaje.orden_entrega_id:
        _actualizar_orden_entrega(db, db_pesaje.orden_entrega_id, db_pesaje.peso_neto)

    # Agregar info para respuesta
    if camion:
        db_pesaje.camion_patente = camion.patente
    if transportista_empresa:
        db_pesaje.transportista_nombre = transportista_empresa.nombre
    if cliente_empresa:
        db_pesaje.cliente_nombre = cliente_empresa.nombre

    return db_pesaje


def _obtener_proximo_numero_remito(db: Session) -> int:
    """Obtiene el próximo número de remito"""
    from sqlalchemy import desc
    ultimo_remito = db.query(Remito).order_by(desc(Remito.numero_remito)).first()
    return (ultimo_remito.numero_remito + 1) if ultimo_remito else 1


def _actualizar_orden_entrega(db: Session, orden_id: UUID, peso_neto: Decimal) -> None:
    """
    Actualiza una orden de entrega al crear un pesaje asociado
    Incrementa cargas_entregadas y peso_total_entregado
    """
    orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == orden_id).first()
    if not orden:
        return

    # Incrementar cargas entregadas
    orden.cargas_entregadas = (orden.cargas_entregadas or 0) + 1

    # Actualizar peso total entregado
    peso_actual = orden.peso_total_entregado or Decimal("0")
    orden.peso_total_entregado = peso_actual + (peso_neto or Decimal("0"))

    # Actualizar estado
    if orden.cargas_entregadas >= orden.cantidad_cargas:
        orden.estado = EstadoOrdenEntrega.completada.value
    elif orden.cargas_entregadas > 0:
        orden.estado = EstadoOrdenEntrega.en_proceso.value

    db.commit()


def _registrar_en_cuenta_corriente(db: Session, pesaje: Pesaje, usuario_id: UUID) -> MovimientoCuentaCorriente:
    """
    Registra un cargo en la cuenta corriente del cliente al crear un pesaje con importe
    """
    # Obtener empresa y saldo actual
    empresa = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
    if not empresa:
        return None

    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")
    saldo_posterior = saldo_anterior + pesaje.importe_total

    # Crear descripción
    peso_tn = pesaje.peso_neto / Decimal("1000")
    descripcion = f"Pesaje #{pesaje.numero_pesaje}"
    if pesaje.material:
        descripcion += f" - {pesaje.material}"
    descripcion += f" ({peso_tn:.2f} tn)"

    # Crear movimiento de cuenta corriente
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


def _generar_remito_automatico(db: Session, pesaje: Pesaje, usuario_id: UUID) -> Remito:
    """
    Genera un remito automáticamente al crear un pesaje
    """
    numero_remito = _obtener_proximo_numero_remito(db)

    # Determinar patente según tipo de entrega
    if pesaje.tipo_entrega == "propio" and pesaje.camion:
        patente = pesaje.camion.patente
    else:
        patente = pesaje.patente_externa

    # Determinar cliente
    cliente_nombre = None
    if pesaje.cliente_id and pesaje.cliente:
        cliente_nombre = pesaje.cliente.nombre
    elif pesaje.transportista:
        cliente_nombre = pesaje.transportista

    db_remito = Remito(
        numero_remito=numero_remito,
        pesaje_id=pesaje.id,
        fecha=pesaje.fecha.date() if hasattr(pesaje.fecha, 'date') else pesaje.fecha,
        cliente=cliente_nombre or "Cliente no especificado",
        producto=pesaje.material or "Material no especificado",
        peso_neto=pesaje.peso_neto,
        camion_patente=patente,
        chofer=pesaje.chofer,
        observaciones=pesaje.observaciones,
        created_by=usuario_id
    )

    db.add(db_remito)

    # Marcar pesaje como con remito generado
    pesaje.remito_generado = True

    db.commit()
    db.refresh(db_remito)

    return db_remito


def actualizar(db: Session, pesaje_id: UUID, pesaje_data: PesajeUpdate) -> Pesaje:
    """
    Actualiza un pesaje existente

    Recalcula peso neto si se actualizan tara o bruto
    """
    db_pesaje = obtener_por_id(db, pesaje_id)

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Si ya tiene remito generado, no permitir edición
    if db_pesaje.remito_generado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar un pesaje que ya tiene remito generado"
        )

    update_data = pesaje_data.model_dump(exclude_unset=True)

    # Aplicar actualizaciones
    for field, value in update_data.items():
        setattr(db_pesaje, field, value)

    # Recalcular peso neto
    db_pesaje.peso_neto = db_pesaje.peso_bruto - db_pesaje.peso_tara

    # Validar pesos
    if db_pesaje.peso_bruto <= db_pesaje.peso_tara:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El peso bruto debe ser mayor que el peso tara"
        )

    db.commit()
    db.refresh(db_pesaje)

    return db_pesaje


def eliminar(db: Session, pesaje_id: UUID) -> dict:
    """
    Elimina un pesaje
    """
    db_pesaje = obtener_por_id(db, pesaje_id)

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Si tiene orden de entrega asociada, desasociar primero
    if db_pesaje.orden_entrega_id:
        db_pesaje.orden_entrega_id = None

    db.delete(db_pesaje)
    db.commit()

    return {"message": "Pesaje eliminado correctamente"}


def obtener_estadisticas_periodo(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date
) -> dict:
    """
    Obtiene estadísticas de pesajes para un período

    Returns:
        Diccionario con estadísticas
    """
    pesajes = obtener_por_fecha(db, fecha_desde, fecha_hasta)

    if not pesajes:
        return {
            "total_pesajes": 0,
            "total_toneladas": Decimal("0"),
            "promedio_peso_neto": Decimal("0"),
            "materiales": []
        }

    # Calcular estadísticas
    total_pesajes = len(pesajes)
    total_kg = sum(p.peso_neto for p in pesajes)
    total_toneladas = total_kg / Decimal("1000")
    promedio = total_kg / total_pesajes if total_pesajes > 0 else Decimal("0")

    # Agrupar por material
    materiales_dict = {}
    for pesaje in pesajes:
        material = pesaje.material or "Sin especificar"
        if material not in materiales_dict:
            materiales_dict[material] = {
                "material": material,
                "cantidad": 0,
                "total_kg": Decimal("0")
            }
        materiales_dict[material]["cantidad"] += 1
        materiales_dict[material]["total_kg"] += pesaje.peso_neto

    materiales = list(materiales_dict.values())

    return {
        "total_pesajes": total_pesajes,
        "total_toneladas": round(total_toneladas, 2),
        "promedio_peso_neto": round(promedio, 2),
        "materiales": materiales
    }
