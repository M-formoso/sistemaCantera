"""
Servicio de lógica de negocio para Servicios/Mantenimientos
Este es uno de los servicios más críticos del sistema
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import date, timedelta
from fastapi import HTTPException, status

from app.models.servicio import Servicio, ServicioRepuesto, EstadoServicioEnum
from app.models.repuesto import Repuesto
from app.models.movimiento_stock import TipoMovimientoEnum
from app.schemas.servicio import ServicioCreate, ServicioUpdate, RepuestoAsignado
from app.services import repuesto_service, camion_service


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    estado: Optional[EstadoServicioEnum] = None
) -> List[Servicio]:
    """Obtiene todos los servicios con paginación"""
    query = db.query(Servicio)

    if estado:
        query = query.filter(Servicio.estado == estado)

    return query.order_by(desc(Servicio.fecha)).offset(skip).limit(limit).all()


def obtener_por_id(db: Session, servicio_id: UUID) -> Optional[Servicio]:
    """Obtiene un servicio por ID"""
    return db.query(Servicio).filter(Servicio.id == servicio_id).first()


def obtener_por_camion(db: Session, camion_id: UUID) -> List[Servicio]:
    """Obtiene servicios de un camión específico"""
    return db.query(Servicio).filter(
        Servicio.camion_id == camion_id
    ).order_by(desc(Servicio.fecha)).all()


def obtener_programados(db: Session, dias: int = 7) -> List[Servicio]:
    """
    Obtiene servicios programados en los próximos X días

    Args:
        db: Sesión de base de datos
        dias: Número de días a futuro

    Returns:
        Lista de servicios programados
    """
    hoy = date.today()
    fecha_limite = hoy + timedelta(days=dias)

    return db.query(Servicio).filter(
        and_(
            Servicio.estado == EstadoServicioEnum.PROGRAMADO,
            Servicio.fecha >= hoy,
            Servicio.fecha <= fecha_limite
        )
    ).order_by(Servicio.fecha).all()


def crear_con_repuestos(
    db: Session,
    servicio_data: ServicioCreate,
    usuario_id: UUID
) -> Servicio:
    """
    Crea un servicio y asigna repuestos descontando stock automáticamente

    Este es el flujo crítico del sistema:
    1. Verifica que el camión exista
    2. Crea el servicio
    3. Por cada repuesto:
       - Verifica stock disponible
       - Crea relación servicio-repuesto
       - Descuenta stock automáticamente
       - Crea movimiento de stock
       - Verifica si quedó bajo stock mínimo
    4. Calcula costo total

    Args:
        db: Sesión de base de datos
        servicio_data: Datos del servicio
        usuario_id: ID del usuario que crea el servicio

    Returns:
        Servicio creado

    Raises:
        HTTPException: Si el camión no existe o hay stock insuficiente
    """
    # 1. Verificar que el camión exista
    camion = camion_service.obtener_por_id(db, servicio_data.camion_id)
    if not camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    # 2. Crear servicio (sin repuestos por ahora)
    repuestos_data = servicio_data.repuestos
    servicio_dict = servicio_data.model_dump(exclude={'repuestos'})

    db_servicio = Servicio(
        **servicio_dict,
        created_by=usuario_id,
        costo_total=servicio_data.costo_mano_obra  # Inicial, se actualizará
    )
    db.add(db_servicio)
    db.flush()  # Para obtener el ID sin hacer commit

    costo_repuestos = Decimal("0")

    # 3. Procesar cada repuesto
    for rep_asignado in repuestos_data:
        repuesto = repuesto_service.obtener_por_id(db, rep_asignado.repuesto_id)

        if not repuesto:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repuesto con ID {rep_asignado.repuesto_id} no encontrado"
            )

        # Verificar stock disponible
        if repuesto.stock_actual < rep_asignado.cantidad:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente de '{repuesto.nombre}'. Stock actual: {repuesto.stock_actual}, requerido: {rep_asignado.cantidad}"
            )

        # Calcular subtotal
        precio = repuesto.precio_unitario or Decimal("0")
        subtotal = rep_asignado.cantidad * precio

        # Crear relación servicio-repuesto
        servicio_repuesto = ServicioRepuesto(
            servicio_id=db_servicio.id,
            repuesto_id=repuesto.id,
            cantidad=rep_asignado.cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )
        db.add(servicio_repuesto)

        # Descontar stock usando el servicio de repuestos
        # Usar identificador correcto según tipo de equipo
        equipo_identificador = camion.nombre or camion.codigo_interno if camion.categoria == 'maquina' else camion.patente
        equipo_label = "Máquina" if camion.categoria == 'maquina' else "Camión"

        repuesto_service.ajustar_stock(
            db=db,
            repuesto_id=repuesto.id,
            cantidad=rep_asignado.cantidad,
            tipo=TipoMovimientoEnum.EGRESO,
            usuario_id=usuario_id,
            referencia_tipo="servicio",
            referencia_id=db_servicio.id,
            observaciones=f"Servicio {db_servicio.tipo.value} - {equipo_label} {equipo_identificador}"
        )

        costo_repuestos += subtotal

        # Verificar si quedó bajo stock mínimo (crear alerta con Celery)
        if repuesto.stock_actual <= repuesto.stock_minimo:
            # Importar aquí para evitar circular imports
            try:
                from app.tasks.alertas import crear_alerta_stock_bajo
                crear_alerta_stock_bajo.delay(str(repuesto.id))
            except ImportError:
                # Si Celery no está disponible, solo loguear
                print(f"⚠️ Alerta: Stock bajo de {repuesto.nombre}")

    # 4. Calcular costo total
    db_servicio.costo_total = servicio_data.costo_mano_obra + costo_repuestos

    # 5. Actualizar datos del equipo (camión o máquina)
    camion.ultimo_servicio = servicio_data.fecha

    # Calcular próxima fecha de servicio (por defecto, 3 meses después o según intervalo configurado)
    # Usar intervalo de días si está configurado, sino 90 días por defecto
    intervalo_dias = camion.intervalo_servicio_dias or 90
    camion.proximo_servicio_fecha = servicio_data.fecha + timedelta(days=intervalo_dias)

    if servicio_data.kilometraje_servicio:
        # Para máquinas, se usa el horómetro en lugar del kilometraje
        if camion.categoria == 'maquina':
            camion.ultimo_servicio_horas = servicio_data.kilometraje_servicio
            camion.horometro_actual = servicio_data.kilometraje_servicio
            # Calcular próximo mantenimiento basado en intervalo de horas
            if camion.intervalo_servicio_horas:
                camion.proximo_servicio_horas = servicio_data.kilometraje_servicio + camion.intervalo_servicio_horas
        else:
            camion.ultimo_servicio_km = servicio_data.kilometraje_servicio
            camion.kilometraje_actual = servicio_data.kilometraje_servicio
            # Calcular próximo servicio basado en intervalo
            if camion.intervalo_servicio_km:
                camion.proximo_servicio_km = servicio_data.kilometraje_servicio + camion.intervalo_servicio_km

    db.commit()
    db.refresh(db_servicio)

    # Verificar si hay alertas de próximo servicio para otros camiones
    try:
        from app.tasks.alertas import verificar_proximos_servicios
        verificar_proximos_servicios.delay()
    except ImportError:
        pass

    return db_servicio


def actualizar(db: Session, servicio_id: UUID, servicio_data: ServicioUpdate) -> Servicio:
    """
    Actualiza un servicio existente

    NOTA: No permite actualizar repuestos asignados para evitar complejidad
    en la gestión de stock. Para modificar repuestos, se debe crear un nuevo servicio.
    """
    db_servicio = obtener_por_id(db, servicio_id)

    if not db_servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )

    # Actualizar campos
    update_data = servicio_data.model_dump(exclude_unset=True)

    # Si se actualiza costo_mano_obra, recalcular costo_total
    if 'costo_mano_obra' in update_data:
        costo_repuestos = sum(
            sr.subtotal or Decimal("0")
            for sr in db_servicio.servicios_repuestos
        )
        db_servicio.costo_total = update_data['costo_mano_obra'] + costo_repuestos

    for field, value in update_data.items():
        if field != 'costo_total':  # No actualizar directamente
            setattr(db_servicio, field, value)

    db.commit()
    db.refresh(db_servicio)

    return db_servicio


def eliminar(db: Session, servicio_id: UUID) -> dict:
    """
    Elimina un servicio

    IMPORTANTE: Al eliminar un servicio, NO se devuelve el stock de los repuestos
    para mantener la integridad del historial. Si se necesita devolver stock,
    debe hacerse manualmente con un ajuste de stock.
    """
    db_servicio = obtener_por_id(db, servicio_id)

    if not db_servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )

    # Eliminar relaciones servicio-repuesto
    db.query(ServicioRepuesto).filter(
        ServicioRepuesto.servicio_id == servicio_id
    ).delete()

    # Eliminar servicio
    db.delete(db_servicio)
    db.commit()

    return {
        "message": "Servicio eliminado",
        "detail": "El stock de los repuestos NO fue devuelto. Si necesita devolver stock, haga un ajuste manual."
    }
