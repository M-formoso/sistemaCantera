"""
Servicio de lógica de negocio para Pesajes
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status

from app.models.base import get_argentina_now

from app.models.pesaje import Pesaje
from app.models.remito import Remito
from app.models.empresa import Empresa
from app.models.camion import Camion
from app.models.camion_cliente import CamionCliente
from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.models.orden_entrega import OrdenEntrega, EstadoOrdenEntrega
from app.schemas.pesaje import PesajeCreate, PesajeUpdate, PesajeIniciarCreate, PesajeCompletarCreate, PesajeCancelarCreate
from app.models.usuario import Usuario
from app.services import camion_service


def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    incluir_cancelados: bool = False,
    solo_cancelados: bool = False
) -> List[Pesaje]:
    """
    Obtiene todos los pesajes con paginación, enriquecidos con datos relacionados.

    Args:
        incluir_cancelados: Si True, incluye pesajes cancelados junto con los demás
        solo_cancelados: Si True, solo devuelve pesajes cancelados (para auditoría)
    """
    from app.models.camion import Camion

    query = db.query(Pesaje)

    # Filtrar por estado
    if solo_cancelados:
        query = query.filter(Pesaje.estado == "cancelado")
    elif not incluir_cancelados:
        # Excluir cancelados - usar OR para manejar NULLs y valores antiguos
        query = query.filter(
            or_(
                Pesaje.estado != "cancelado",
                Pesaje.estado.is_(None)
            )
        )

    pesajes = query.order_by(desc(Pesaje.fecha)).offset(skip).limit(limit).all()

    # Enriquecer con datos
    for p in pesajes:
        _enriquecer_pesaje(db, p)

    return pesajes


def _enriquecer_pesaje(db: Session, pesaje: Pesaje) -> None:
    """Enriquece un pesaje con datos relacionados (patentes, nombres, etc)"""
    from app.models.camion import Camion

    # Patente del camión propio
    if pesaje.camion_id:
        camion = db.query(Camion).filter(Camion.id == pesaje.camion_id).first()
        if camion:
            pesaje.camion_patente = camion.patente

    # Nombre del transportista
    if pesaje.transportista_id:
        transportista = db.query(Empresa).filter(Empresa.id == pesaje.transportista_id).first()
        if transportista:
            pesaje.transportista_nombre = transportista.nombre

    # Nombre del cliente
    if pesaje.cliente_id:
        cliente = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
        if cliente:
            pesaje.cliente_nombre = cliente.nombre

    # Si está cancelado, agregar nombre de quien lo canceló
    if pesaje.cancelado_por:
        usuario = db.query(Usuario).filter(Usuario.id == pesaje.cancelado_por).first()
        if usuario:
            pesaje.cancelado_por_nombre = usuario.nombre


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

    # Si tiene cliente, registrar en cuenta corriente (aunque no tenga importe)
    if db_pesaje.cliente_id:
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
    Registra un cargo en la cuenta corriente del cliente al crear un pesaje.
    Si no tiene importe, registra con $0 (pendiente de precio).
    """
    # Obtener empresa y saldo actual
    empresa = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
    if not empresa:
        return None

    # Usar importe_total o 0 si no tiene
    importe = pesaje.importe_total or Decimal("0")

    saldo_anterior = empresa.saldo_cuenta_corriente or Decimal("0")
    saldo_posterior = saldo_anterior + importe

    # Crear descripción
    peso_tn = pesaje.peso_neto / Decimal("1000")
    descripcion = f"Pesaje #{pesaje.numero_pesaje}"
    if pesaje.material:
        descripcion += f" - {pesaje.material}"
    descripcion += f" ({peso_tn:.2f} tn)"

    # Detalle con info de precio
    if pesaje.precio_fijo:
        detalle = f"Precio fijo: ${pesaje.precio_fijo:,.2f}"
    elif pesaje.precio_unitario:
        detalle = f"Precio/tn: ${pesaje.precio_unitario:,.2f}"
        if pesaje.flete and pesaje.flete > 0:
            detalle += f" + Flete: ${pesaje.flete:,.2f}"
    elif importe == 0:
        detalle = "Pendiente de precio"
    else:
        detalle = None

    # Crear movimiento de cuenta corriente
    movimiento = MovimientoCuentaCorriente(
        empresa_id=pesaje.cliente_id,
        tipo="cargo",
        monto=importe,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        fecha=pesaje.fecha.date() if hasattr(pesaje.fecha, 'date') else pesaje.fecha,
        descripcion=descripcion,
        detalle=detalle,
        pesaje_id=pesaje.id,
        created_by=usuario_id
    )

    # Actualizar saldo de empresa
    empresa.saldo_cuenta_corriente = saldo_posterior

    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)

    return movimiento


def sincronizar_pesaje_cuenta_corriente(db: Session, pesaje_id: UUID, usuario_id: UUID) -> dict:
    """
    Sincroniza un pesaje existente con la cuenta corriente del cliente.
    Útil para pesajes históricos que no tienen movimiento registrado.

    Retorna:
        - {"status": "creado", "movimiento_id": ...} si se creó el movimiento
        - {"status": "ya_existe", "movimiento_id": ...} si ya existía
        - {"status": "sin_cliente"} si el pesaje no tiene cliente asignado
        - {"status": "no_completado"} si el pesaje no está completado
    """
    from app.models.cuenta_corriente import MovimientoCuentaCorriente

    # Obtener pesaje
    pesaje = db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()
    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Verificar que esté completado
    if pesaje.estado != "completado":
        return {"status": "no_completado", "message": "El pesaje no está completado"}

    # Verificar que tenga cliente
    if not pesaje.cliente_id:
        return {"status": "sin_cliente", "message": "El pesaje no tiene cliente asignado"}

    # Verificar si ya existe un movimiento para este pesaje
    movimiento_existente = db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.pesaje_id == pesaje_id
    ).first()

    if movimiento_existente:
        return {
            "status": "ya_existe",
            "movimiento_id": str(movimiento_existente.id),
            "message": f"Ya existe movimiento en cuenta corriente (monto: ${float(movimiento_existente.monto):.2f})"
        }

    # Crear el movimiento
    movimiento = _registrar_en_cuenta_corriente(db, pesaje, usuario_id)

    if movimiento:
        return {
            "status": "creado",
            "movimiento_id": str(movimiento.id),
            "message": f"Movimiento creado exitosamente (monto: ${float(movimiento.monto):.2f})"
        }
    else:
        return {"status": "error", "message": "No se pudo crear el movimiento"}


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

    # Obtener importe del pesaje (si tiene)
    importe_pesaje = pesaje.importe_total or 0

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
        importe=importe_pesaje,
        saldo_pendiente=importe_pesaje,  # Inicialmente todo el importe está pendiente
        created_by=usuario_id
    )

    db.add(db_remito)

    # Marcar pesaje como con remito generado
    pesaje.remito_generado = True

    db.commit()
    db.refresh(db_remito)

    return db_remito


def actualizar(db: Session, pesaje_id: UUID, pesaje_data: PesajeUpdate, usuario = None) -> Pesaje:
    """
    Actualiza un pesaje existente

    Recalcula peso neto si se actualizan tara o bruto
    Recalcula importe_total si se actualiza precio_unitario

    Nota: Si ya tiene remito generado:
    - Administradores pueden editar todo
    - Otros usuarios solo pueden modificar precio_unitario, importe_total y observaciones
    """
    from app.models.usuario import RolEnum

    db_pesaje = obtener_por_id(db, pesaje_id)

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    update_data = pesaje_data.model_dump(exclude_unset=True)

    # Verificar si el usuario es administrador
    es_admin = usuario and usuario.rol == RolEnum.ADMINISTRADOR

    # Si ya tiene remito generado y NO es admin, restringir campos
    if db_pesaje.remito_generado and not es_admin:
        campos_permitidos = {'precio_unitario', 'flete', 'precio_fijo', 'importe_total', 'observaciones'}
        campos_no_permitidos = set(update_data.keys()) - campos_permitidos

        if campos_no_permitidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se puede modificar precio, importe y observaciones en pesajes con remito. Campos no permitidos: {', '.join(campos_no_permitidos)}"
            )

    # Aplicar actualizaciones
    for field, value in update_data.items():
        setattr(db_pesaje, field, value)

    # Recalcular peso neto si se modificaron los pesos
    if db_pesaje.peso_bruto and db_pesaje.peso_tara:
        db_pesaje.peso_neto = db_pesaje.peso_bruto - db_pesaje.peso_tara

        # Validar pesos
        if db_pesaje.peso_bruto <= db_pesaje.peso_tara:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El peso bruto debe ser mayor que el peso tara"
            )

    # Recalcular importe_total si se actualizaron campos de precio
    campos_precio = {'precio_unitario', 'flete', 'precio_fijo'}
    if campos_precio.intersection(update_data.keys()) and db_pesaje.peso_neto:
        # Calcular según escenario:
        # 1. Si hay precio_fijo: importe = precio_fijo
        # 2. Si hay precio_unitario: importe = (toneladas * precio_unitario) + flete
        if db_pesaje.precio_fijo:
            db_pesaje.importe_total = db_pesaje.precio_fijo
        elif db_pesaje.precio_unitario:
            peso_toneladas = db_pesaje.peso_neto / Decimal("1000")
            importe_material = peso_toneladas * db_pesaje.precio_unitario
            flete = db_pesaje.flete or Decimal("0")
            db_pesaje.importe_total = importe_material + flete

    # Si tiene remito asociado, actualizarlo con los nuevos datos del pesaje
    if db_pesaje.remito:
        remito = db_pesaje.remito

        # Actualizar datos del remito que vienen del pesaje
        remito.peso_neto = db_pesaje.peso_neto
        remito.producto = db_pesaje.material or remito.producto
        remito.observaciones = db_pesaje.observaciones

        # Actualizar cliente
        if db_pesaje.cliente:
            remito.cliente = db_pesaje.cliente.nombre
        elif db_pesaje.cliente_nombre:
            remito.cliente = db_pesaje.cliente_nombre

        # Actualizar patente del camión
        if db_pesaje.camion:
            remito.camion_patente = db_pesaje.camion.patente
        elif db_pesaje.patente_externa:
            remito.camion_patente = db_pesaje.patente_externa

        # Actualizar chofer
        remito.chofer = db_pesaje.chofer

    db.commit()
    db.refresh(db_pesaje)

    return db_pesaje


def cancelar_pesaje(
    db: Session,
    pesaje_id: UUID,
    datos_cancelacion: PesajeCancelarCreate,
    usuario_id: UUID
) -> Pesaje:
    """
    Cancela un pesaje (soft-delete con auditoría).

    - El pesaje NO se elimina, se marca como 'cancelado'
    - Se registra el motivo de cancelación (obligatorio)
    - Se registra quién lo canceló y cuándo
    - Si tenía cliente, se registra en cuenta corriente como movimiento de cancelación

    Esto permite:
    - Mantener trazabilidad completa
    - Evitar manipulaciones indebidas
    - Auditar todos los cambios
    """
    db_pesaje = obtener_por_id(db, pesaje_id)

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    if db_pesaje.estado == "cancelado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pesaje ya fue cancelado"
        )

    ahora = get_argentina_now()

    # Obtener nombre del usuario que cancela
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"

    # Si era un pesaje completado y tenía cliente, registrar reversión en cuenta corriente
    if db_pesaje.estado == "completado" and db_pesaje.cliente_id and db_pesaje.importe_total:
        # Buscar el movimiento de cuenta corriente original
        movimiento_original = db.query(MovimientoCuentaCorriente).filter(
            MovimientoCuentaCorriente.pesaje_id == pesaje_id
        ).first()

        if movimiento_original:
            # Obtener saldo actual del cliente
            cliente = db.query(Empresa).filter(Empresa.id == db_pesaje.cliente_id).first()
            saldo_anterior = cliente.saldo_cuenta_corriente if cliente else Decimal("0")

            # Crear movimiento de reversión (crédito)
            movimiento_cancelacion = MovimientoCuentaCorriente(
                empresa_id=db_pesaje.cliente_id,
                tipo="ajuste",
                concepto=f"CANCELACIÓN Pesaje #{db_pesaje.numero_pesaje} - {datos_cancelacion.motivo}",
                monto=-db_pesaje.importe_total,  # Negativo para revertir
                saldo_anterior=saldo_anterior,
                saldo_posterior=saldo_anterior - db_pesaje.importe_total,
                fecha=ahora,
                pesaje_id=pesaje_id,
                created_by=usuario_id
            )
            db.add(movimiento_cancelacion)

            # Actualizar saldo del cliente
            if cliente:
                cliente.saldo_cuenta_corriente = saldo_anterior - db_pesaje.importe_total

    # Si tiene orden de entrega asociada, revertir la carga
    if db_pesaje.orden_entrega_id and db_pesaje.peso_neto:
        orden = db.query(OrdenEntrega).filter(OrdenEntrega.id == db_pesaje.orden_entrega_id).first()
        if orden:
            orden.cargas_entregadas = max(0, (orden.cargas_entregadas or 0) - 1)
            orden.peso_total_entregado = max(
                Decimal("0"),
                (orden.peso_total_entregado or Decimal("0")) - db_pesaje.peso_neto
            )
            # Recalcular estado
            if orden.cargas_entregadas == 0:
                orden.estado = EstadoOrdenEntrega.PENDIENTE
            elif orden.cargas_entregadas < orden.cantidad_cargas:
                orden.estado = EstadoOrdenEntrega.EN_PROCESO

    # Marcar pesaje como cancelado (soft-delete)
    db_pesaje.estado = "cancelado"
    db_pesaje.motivo_cancelacion = datos_cancelacion.motivo
    db_pesaje.fecha_cancelacion = ahora
    db_pesaje.cancelado_por = usuario_id

    db.commit()
    db.refresh(db_pesaje)

    # Enriquecer con datos para respuesta
    db_pesaje.cancelado_por_nombre = nombre_usuario

    return db_pesaje


def eliminar_permanente(db: Session, pesaje_id: UUID) -> dict:
    """
    Elimina PERMANENTEMENTE un pesaje (solo para admin, casos excepcionales).
    ADVERTENCIA: Esto elimina el registro completamente de la base de datos.

    Para cancelaciones normales, usar cancelar_pesaje() que hace soft-delete.
    """
    from app.models.remito import Remito

    db_pesaje = obtener_por_id(db, pesaje_id)

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Si tiene orden de entrega asociada, desasociar primero
    if db_pesaje.orden_entrega_id:
        db_pesaje.orden_entrega_id = None

    # Eliminar remitos asociados
    db.query(Remito).filter(Remito.pesaje_id == pesaje_id).delete()

    # Desasociar movimientos de cuenta corriente (no eliminarlos, solo quitar la referencia)
    db.query(MovimientoCuentaCorriente).filter(
        MovimientoCuentaCorriente.pesaje_id == pesaje_id
    ).update({MovimientoCuentaCorriente.pesaje_id: None})

    db.delete(db_pesaje)
    db.commit()

    return {"message": "Pesaje eliminado permanentemente"}


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


# ============== FUNCIONES PARA FLUJO DOBLE PESAJE ==============

def obtener_pendientes(db: Session) -> List[Pesaje]:
    """
    Obtiene todos los pesajes en estado pendiente (solo tara registrada)
    Ordenados por fecha (más antiguos primero)
    """
    pesajes = db.query(Pesaje).filter(
        Pesaje.estado == "pendiente"
    ).order_by(Pesaje.fecha).all()

    # Enriquecer con datos
    for p in pesajes:
        if p.camion_id:
            camion = db.query(Camion).filter(Camion.id == p.camion_id).first()
            if camion:
                p.camion_patente = camion.patente

        if p.transportista_id:
            transportista = db.query(Empresa).filter(Empresa.id == p.transportista_id).first()
            if transportista:
                p.transportista_nombre = transportista.nombre

        if p.cliente_id:
            cliente = db.query(Empresa).filter(Empresa.id == p.cliente_id).first()
            if cliente:
                p.cliente_nombre = cliente.nombre

        # Calcular minutos esperando
        if p.fecha:
            delta = get_argentina_now() - p.fecha
            p.minutos_esperando = int(delta.total_seconds() / 60)

    return pesajes


def buscar_por_patente(db: Session, patente: str) -> dict:
    """
    Busca información por patente del camión.
    Busca en: 1) Camiones propios, 2) Camiones de clientes, 3) Pesajes pendientes
    Retorna datos del camión, cliente asociado y pesaje pendiente si existe.
    """
    patente = patente.upper().strip()

    result = {
        "encontrado": False,
        "tipo": None,
        "camion_id": None,
        "camion_patente": None,
        "camion_marca": None,
        "camion_modelo": None,
        "camion_descripcion": None,
        "camion_tipo": None,
        "camion_año": None,
        "cliente_id": None,
        "cliente_nombre": None,
        "chofer_habitual": None,
        "acoplado": None,
        "pesaje_pendiente_id": None,
        "pesaje_pendiente_numero": None,
        "pesaje_pendiente_tara": None,
        "pesaje_pendiente_fecha": None,
    }

    # 1. Buscar en camiones propios de la cantera
    camion_propio = db.query(Camion).filter(
        func.upper(Camion.patente) == patente,
        Camion.activo == True
    ).first()

    if camion_propio:
        result["encontrado"] = True
        result["tipo"] = "propio"
        result["camion_id"] = str(camion_propio.id)
        result["camion_patente"] = camion_propio.patente
        result["camion_marca"] = camion_propio.marca
        result["camion_modelo"] = camion_propio.modelo
        result["camion_tipo"] = camion_propio.tipo.value if camion_propio.tipo else None
        result["camion_año"] = camion_propio.año
        result["chofer_habitual"] = camion_propio.chofer_habitual

        # Buscar pesaje pendiente para este camión propio
        pesaje_pendiente = db.query(Pesaje).filter(
            Pesaje.camion_id == camion_propio.id,
            Pesaje.estado == "pendiente"
        ).first()

        if pesaje_pendiente:
            result["pesaje_pendiente_id"] = str(pesaje_pendiente.id)
            result["pesaje_pendiente_numero"] = pesaje_pendiente.numero_pesaje
            result["pesaje_pendiente_tara"] = float(pesaje_pendiente.peso_tara) if pesaje_pendiente.peso_tara else None
            result["pesaje_pendiente_fecha"] = pesaje_pendiente.fecha.isoformat() if pesaje_pendiente.fecha else None

            if pesaje_pendiente.cliente_id:
                cliente = db.query(Empresa).filter(Empresa.id == pesaje_pendiente.cliente_id).first()
                if cliente:
                    result["cliente_id"] = str(cliente.id)
                    result["cliente_nombre"] = cliente.nombre

        return result

    # 2. Buscar en camiones de clientes (patentes asociadas a clientes)
    camion_cliente = db.query(CamionCliente).filter(
        func.upper(CamionCliente.patente) == patente,
        CamionCliente.activo == True
    ).first()

    if camion_cliente:
        # Obtener datos del cliente
        cliente = db.query(Empresa).filter(Empresa.id == camion_cliente.cliente_id).first()

        result["encontrado"] = True
        result["tipo"] = "cliente"
        result["camion_patente"] = camion_cliente.patente
        result["camion_descripcion"] = camion_cliente.descripcion
        result["chofer_habitual"] = camion_cliente.chofer_habitual

        if cliente:
            result["cliente_id"] = str(cliente.id)
            result["cliente_nombre"] = cliente.nombre

        # Buscar pesaje pendiente para esta patente externa
        pesaje_pendiente = db.query(Pesaje).filter(
            func.upper(Pesaje.patente_externa) == patente,
            Pesaje.estado == "pendiente"
        ).first()

        if pesaje_pendiente:
            result["pesaje_pendiente_id"] = str(pesaje_pendiente.id)
            result["pesaje_pendiente_numero"] = pesaje_pendiente.numero_pesaje
            result["pesaje_pendiente_tara"] = float(pesaje_pendiente.peso_tara) if pesaje_pendiente.peso_tara else None
            result["pesaje_pendiente_fecha"] = pesaje_pendiente.fecha.isoformat() if pesaje_pendiente.fecha else None
            result["acoplado"] = pesaje_pendiente.acoplado

        return result

    # 3. Buscar en pesajes pendientes con patente externa (transportista sin cliente registrado)
    pesaje_externo = db.query(Pesaje).filter(
        func.upper(Pesaje.patente_externa) == patente,
        Pesaje.estado == "pendiente"
    ).first()

    if pesaje_externo:
        result["encontrado"] = True
        result["tipo"] = "transportista"
        result["camion_patente"] = pesaje_externo.patente_externa
        result["pesaje_pendiente_id"] = str(pesaje_externo.id)
        result["pesaje_pendiente_numero"] = pesaje_externo.numero_pesaje
        result["pesaje_pendiente_tara"] = float(pesaje_externo.peso_tara) if pesaje_externo.peso_tara else None
        result["pesaje_pendiente_fecha"] = pesaje_externo.fecha.isoformat() if pesaje_externo.fecha else None
        result["chofer_habitual"] = pesaje_externo.chofer
        result["acoplado"] = pesaje_externo.acoplado

        if pesaje_externo.cliente_id:
            cliente = db.query(Empresa).filter(Empresa.id == pesaje_externo.cliente_id).first()
            if cliente:
                result["cliente_id"] = str(cliente.id)
                result["cliente_nombre"] = cliente.nombre

        return result

    # No encontrado - puede ser patente nueva (retorna encontrado=False)
    return result


def iniciar_pesaje(db: Session, pesaje_data: PesajeIniciarCreate, usuario_id: UUID) -> Pesaje:
    """
    Inicia un nuevo pesaje registrando solo la tara (camión vacío).
    El pesaje queda en estado 'pendiente' hasta que se complete con el peso bruto.

    Si es transportista con patente nueva y cliente seleccionado,
    guarda automáticamente la patente asociada al cliente.
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

        # Verificar que no tenga un pesaje pendiente
        pesaje_existente = db.query(Pesaje).filter(
            Pesaje.camion_id == pesaje_data.camion_id,
            Pesaje.estado == "pendiente"
        ).first()
        if pesaje_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Este camión ya tiene un pesaje pendiente (#{pesaje_existente.numero_pesaje})"
            )
    else:  # transportista
        if pesaje_data.transportista_id:
            transportista_empresa = db.query(Empresa).filter(Empresa.id == pesaje_data.transportista_id).first()
            if not transportista_empresa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transportista no encontrado"
                )

        # Verificar que no tenga un pesaje pendiente con esa patente
        if pesaje_data.patente_externa:
            pesaje_existente = db.query(Pesaje).filter(
                func.upper(Pesaje.patente_externa) == pesaje_data.patente_externa.upper(),
                Pesaje.estado == "pendiente"
            ).first()
            if pesaje_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Esta patente ya tiene un pesaje pendiente (#{pesaje_existente.numero_pesaje})"
                )

    # Verificar cliente si se proporciona
    if pesaje_data.cliente_id:
        cliente_empresa = db.query(Empresa).filter(Empresa.id == pesaje_data.cliente_id).first()
        if not cliente_empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )

    # Si es transportista con patente nueva y cliente seleccionado,
    # guardar automáticamente la patente asociada al cliente
    if (pesaje_data.tipo_entrega == "transportista"
        and pesaje_data.patente_externa
        and pesaje_data.cliente_id):

        patente_upper = pesaje_data.patente_externa.upper().strip()

        # Verificar si ya existe esta patente para este cliente
        camion_existente = db.query(CamionCliente).filter(
            CamionCliente.cliente_id == pesaje_data.cliente_id,
            func.upper(CamionCliente.patente) == patente_upper
        ).first()

        if not camion_existente:
            # Crear nuevo registro de camión de cliente
            nuevo_camion = CamionCliente(
                cliente_id=pesaje_data.cliente_id,
                patente=patente_upper,
                chofer_habitual=pesaje_data.chofer,
                activo=True
            )
            db.add(nuevo_camion)
            # No hacer commit aún, se hará con el pesaje

    # Obtener próximo número de pesaje
    numero_pesaje = _obtener_proximo_numero(db)

    # Preparar datos
    pesaje_dict = pesaje_data.model_dump(exclude={'cliente_nombre'})

    # Crear pesaje en estado pendiente
    db_pesaje = Pesaje(
        **pesaje_dict,
        numero_pesaje=numero_pesaje,
        estado="pendiente",
        peso_bruto=None,
        peso_neto=None,
        created_by=usuario_id
    )

    db.add(db_pesaje)
    db.commit()
    db.refresh(db_pesaje)

    # Agregar info para respuesta
    if camion:
        db_pesaje.camion_patente = camion.patente
    if transportista_empresa:
        db_pesaje.transportista_nombre = transportista_empresa.nombre
    if cliente_empresa:
        db_pesaje.cliente_nombre = cliente_empresa.nombre

    return db_pesaje


def completar_pesaje(db: Session, pesaje_id: UUID, pesaje_data: PesajeCompletarCreate, usuario_id: UUID) -> Pesaje:
    """
    Completa un pesaje pendiente registrando el peso bruto (camión cargado).
    Calcula el peso neto y genera remito.

    IMPORTANTE: Al completar el pesaje es OBLIGATORIO:
    - Tener un cliente asignado (cliente_id)
    - Tener un material especificado
    """
    db_pesaje = db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    if db_pesaje.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pesaje ya fue completado"
        )

    # Si viene cliente_id en los datos, actualizarlo en el pesaje
    if pesaje_data.cliente_id:
        # Verificar que el cliente exista
        cliente = db.query(Empresa).filter(Empresa.id == pesaje_data.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        db_pesaje.cliente_id = pesaje_data.cliente_id

    # ========== VALIDACIONES OBLIGATORIAS AL COMPLETAR ==========

    # 1. CLIENTE - Obligatorio
    if not db_pesaje.cliente_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe asignar un CLIENTE para completar el pesaje"
        )

    # 2. MATERIAL - Obligatorio (puede venir del pesaje pendiente o del formulario)
    material_final = pesaje_data.material or db_pesaje.material
    if not material_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar el MATERIAL para completar el pesaje"
        )

    # 3. TRANSPORTE - Obligatorio (camión propio O transportista externo)
    tiene_transporte = (
        db_pesaje.camion_id or  # Camión propio
        db_pesaje.transportista_id or  # Transportista registrado
        db_pesaje.patente_externa  # Patente externa
    )
    if not tiene_transporte:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar el TRANSPORTE (camión propio o transportista) para completar el pesaje"
        )

    # 4. PRECIO - Obligatorio (precio_unitario O precio_fijo)
    tiene_precio = (
        pesaje_data.precio_unitario or
        pesaje_data.precio_fijo or
        pesaje_data.importe_total or
        db_pesaje.precio_unitario or
        db_pesaje.precio_fijo
    )
    if not tiene_precio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar el PRECIO (por tonelada o fijo) para completar el pesaje"
        )

    # ========== FIN VALIDACIONES ==========

    # Validar que el peso bruto sea mayor que la tara
    if pesaje_data.peso_bruto <= db_pesaje.peso_tara:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El peso bruto debe ser mayor que el peso tara"
        )

    # Calcular peso neto
    peso_neto = pesaje_data.peso_bruto - db_pesaje.peso_tara

    # Obtener fecha/hora actual de Argentina
    ahora = get_argentina_now()

    # Actualizar pesaje
    db_pesaje.peso_bruto = pesaje_data.peso_bruto
    db_pesaje.peso_neto = peso_neto
    db_pesaje.estado = "completado"
    # IMPORTANTE: La fecha del pesaje es cuando se COMPLETA, no cuando se hizo la tara
    db_pesaje.fecha = ahora
    db_pesaje.fecha_completado = ahora

    # Actualizar campos opcionales
    if pesaje_data.material:
        db_pesaje.material = pesaje_data.material
    if pesaje_data.chofer:
        db_pesaje.chofer = pesaje_data.chofer
    if pesaje_data.observaciones:
        db_pesaje.observaciones = pesaje_data.observaciones
    if pesaje_data.orden_entrega_id:
        db_pesaje.orden_entrega_id = pesaje_data.orden_entrega_id

    # Campos de precio
    if pesaje_data.precio_unitario:
        db_pesaje.precio_unitario = pesaje_data.precio_unitario
    if pesaje_data.flete:
        db_pesaje.flete = pesaje_data.flete
    if pesaje_data.precio_fijo:
        db_pesaje.precio_fijo = pesaje_data.precio_fijo

    # Calcular importe_total según el escenario:
    # 1. Si hay precio_fijo: importe = precio_fijo (ignora toneladas)
    # 2. Si hay precio_unitario: importe = (toneladas * precio_unitario) + flete
    # 3. Si no hay precio: importe = 0 (pendiente)
    if pesaje_data.importe_total:
        # Si viene explícitamente, usarlo
        db_pesaje.importe_total = pesaje_data.importe_total
    elif pesaje_data.precio_fijo:
        # Escenario 3: Precio fijo por viaje
        db_pesaje.importe_total = pesaje_data.precio_fijo
    elif pesaje_data.precio_unitario:
        # Escenario 1 y 2: Precio por tonelada (+ flete opcional)
        peso_toneladas = peso_neto / Decimal("1000")
        importe_material = peso_toneladas * pesaje_data.precio_unitario
        flete = pesaje_data.flete or Decimal("0")
        db_pesaje.importe_total = importe_material + flete

    db.commit()
    db.refresh(db_pesaje)

    # Generar remito automáticamente
    _generar_remito_automatico(db, db_pesaje, usuario_id)

    # Si tiene cliente, registrar en cuenta corriente (aunque no tenga importe)
    if db_pesaje.cliente_id:
        _registrar_en_cuenta_corriente(db, db_pesaje, usuario_id)

    # Si está asociado a una orden de entrega, actualizar la orden
    if db_pesaje.orden_entrega_id:
        _actualizar_orden_entrega(db, db_pesaje.orden_entrega_id, db_pesaje.peso_neto)

    # Enriquecer respuesta
    if db_pesaje.camion_id:
        camion = db.query(Camion).filter(Camion.id == db_pesaje.camion_id).first()
        if camion:
            db_pesaje.camion_patente = camion.patente

    if db_pesaje.transportista_id:
        transportista = db.query(Empresa).filter(Empresa.id == db_pesaje.transportista_id).first()
        if transportista:
            db_pesaje.transportista_nombre = transportista.nombre

    if db_pesaje.cliente_id:
        cliente = db.query(Empresa).filter(Empresa.id == db_pesaje.cliente_id).first()
        if cliente:
            db_pesaje.cliente_nombre = cliente.nombre

    return db_pesaje


def cancelar_pesaje_pendiente(db: Session, pesaje_id: UUID) -> dict:
    """
    Cancela un pesaje pendiente (elimina sin generar remito)
    """
    db_pesaje = db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()

    if not db_pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    if db_pesaje.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden cancelar pesajes pendientes"
        )

    db.delete(db_pesaje)
    db.commit()

    return {"message": "Pesaje pendiente cancelado correctamente"}


def limpiar_pesajes_pendientes_viejos(db: Session, dias_limite: int = 3) -> dict:
    """
    Elimina pesajes pendientes que tienen más de X días sin completarse.

    Los pesajes pendientes son aquellos donde solo se registró la tara
    pero nunca se completó con el peso bruto.

    Args:
        db: Sesión de base de datos
        dias_limite: Cantidad de días máximos que puede estar pendiente (default: 3)

    Returns:
        dict con cantidad de pesajes eliminados y sus números
    """
    ahora = get_argentina_now()
    fecha_limite = ahora - timedelta(days=dias_limite)

    # Buscar pesajes pendientes más viejos que el límite
    pesajes_viejos = db.query(Pesaje).filter(
        Pesaje.estado == "pendiente",
        Pesaje.created_at < fecha_limite
    ).all()

    if not pesajes_viejos:
        return {
            "eliminados": 0,
            "numeros_pesaje": [],
            "message": "No hay pesajes pendientes viejos para eliminar"
        }

    # Guardar los números antes de eliminar
    numeros = [p.numero_pesaje for p in pesajes_viejos]

    # Eliminar los pesajes
    for pesaje in pesajes_viejos:
        db.delete(pesaje)

    db.commit()

    return {
        "eliminados": len(numeros),
        "numeros_pesaje": numeros,
        "message": f"Se eliminaron {len(numeros)} pesajes pendientes con más de {dias_limite} días"
    }


def obtener_pesajes_pendientes_viejos(db: Session, dias_limite: int = 3) -> List[Pesaje]:
    """
    Obtiene pesajes pendientes que tienen más de X días sin completarse.
    Útil para revisar antes de eliminar.

    Args:
        db: Sesión de base de datos
        dias_limite: Cantidad de días máximos que puede estar pendiente (default: 3)

    Returns:
        Lista de pesajes pendientes viejos
    """
    ahora = get_argentina_now()
    fecha_limite = ahora - timedelta(days=dias_limite)

    pesajes = db.query(Pesaje).filter(
        Pesaje.estado == "pendiente",
        Pesaje.created_at < fecha_limite
    ).order_by(Pesaje.created_at).all()

    # Enriquecer con datos
    for p in pesajes:
        _enriquecer_pesaje(db, p)

    return pesajes
