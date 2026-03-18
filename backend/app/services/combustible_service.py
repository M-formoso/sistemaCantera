"""
Servicio de lógica de negocio para Combustible
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from fastapi import HTTPException, status

from app.models.combustible import CisternaCombustible, CargaCisterna, SuministroCombustible, TransferenciaCisterna
from app.schemas.combustible import (
    CisternaConfig, CisternaUpdate, CisternaCreate,
    CargaCisternaCreate, CargaCisternaUpdate, SuministroCombustibleCreate,
    TransferenciaCisternaCreate
)
from app.services import camion_service


# ==================== CISTERNAS ====================

def obtener_todas_cisternas(db: Session) -> List[CisternaCombustible]:
    """Obtiene todas las cisternas"""
    cisternas = db.query(CisternaCombustible).all()

    # Crear un mapa de IDs a nombres para eficiencia
    cisternas_map = {c.id: c.nombre for c in cisternas}

    # Agregar campos calculados
    for cisterna in cisternas:
        if cisterna.capacidad_total > 0:
            cisterna.porcentaje_actual = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
        else:
            cisterna.porcentaje_actual = Decimal("0")
        cisterna.esta_bajo = cisterna.nivel_actual <= cisterna.nivel_minimo

        # Agregar nombre de cisterna origen si existe
        if cisterna.cisterna_origen_id and cisterna.cisterna_origen_id in cisternas_map:
            cisterna.cisterna_origen_nombre = cisternas_map[cisterna.cisterna_origen_id]

    return cisternas


def obtener_cisterna_por_id(db: Session, cisterna_id: UUID) -> Optional[CisternaCombustible]:
    """Obtiene una cisterna por ID"""
    cisterna = db.query(CisternaCombustible).filter(
        CisternaCombustible.id == cisterna_id
    ).first()

    if cisterna:
        if cisterna.capacidad_total > 0:
            cisterna.porcentaje_actual = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
        else:
            cisterna.porcentaje_actual = Decimal("0")
        cisterna.esta_bajo = cisterna.nivel_actual <= cisterna.nivel_minimo

        # Agregar nombre de cisterna origen si existe
        if cisterna.cisterna_origen_id:
            cisterna_origen = db.query(CisternaCombustible).filter(
                CisternaCombustible.id == cisterna.cisterna_origen_id
            ).first()
            if cisterna_origen:
                cisterna.cisterna_origen_nombre = cisterna_origen.nombre

    return cisterna


def crear_cisterna(db: Session, cisterna_data: CisternaCreate) -> CisternaCombustible:
    """Crea una nueva cisterna"""
    # Verificar que la cisterna origen exista si se especifica
    if cisterna_data.cisterna_origen_id:
        cisterna_origen = obtener_cisterna_por_id(db, cisterna_data.cisterna_origen_id)
        if not cisterna_origen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cisterna de origen no encontrada"
            )

    cisterna = CisternaCombustible(
        nombre=cisterna_data.nombre,
        capacidad_total=cisterna_data.capacidad_total,
        nivel_actual=Decimal("0"),
        nivel_minimo=cisterna_data.nivel_minimo,
        cisterna_origen_id=cisterna_data.cisterna_origen_id
    )

    db.add(cisterna)
    db.commit()
    db.refresh(cisterna)

    # Agregar campos calculados
    cisterna.porcentaje_actual = Decimal("0")
    cisterna.esta_bajo = True

    # Agregar nombre de cisterna origen si existe
    if cisterna_data.cisterna_origen_id and cisterna_origen:
        cisterna.cisterna_origen_nombre = cisterna_origen.nombre

    return cisterna


def obtener_cisterna(db: Session) -> Optional[CisternaCombustible]:
    """Obtiene la primera cisterna (legacy, compatibilidad)"""
    cisterna = db.query(CisternaCombustible).first()

    if cisterna:
        if cisterna.capacidad_total > 0:
            cisterna.porcentaje_actual = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
        else:
            cisterna.porcentaje_actual = Decimal("0")
        cisterna.esta_bajo = cisterna.nivel_actual <= cisterna.nivel_minimo

    return cisterna


def configurar_cisterna(db: Session, config: CisternaConfig) -> CisternaCombustible:
    """
    Crea o actualiza la configuración de la cisterna principal (legacy)
    """
    cisterna = obtener_cisterna(db)

    if cisterna:
        # Actualizar existente
        cisterna.capacidad_total = config.capacidad_total
        cisterna.nivel_minimo = config.nivel_minimo
    else:
        # Crear nueva
        cisterna = CisternaCombustible(
            nombre="Cisterna Principal",
            capacidad_total=config.capacidad_total,
            nivel_actual=Decimal("0"),
            nivel_minimo=config.nivel_minimo
        )
        db.add(cisterna)

    db.commit()
    db.refresh(cisterna)

    # Agregar campos calculados
    if cisterna.capacidad_total > 0:
        cisterna.porcentaje_actual = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
    else:
        cisterna.porcentaje_actual = Decimal("0")
    cisterna.esta_bajo = cisterna.nivel_actual <= cisterna.nivel_minimo

    return cisterna


def actualizar_cisterna(db: Session, cisterna_id: UUID, update_data: CisternaUpdate) -> CisternaCombustible:
    """Actualiza una cisterna específica"""
    cisterna = obtener_cisterna_por_id(db, cisterna_id)

    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no encontrada"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(cisterna, field, value)

    db.commit()
    db.refresh(cisterna)

    # Agregar campos calculados
    if cisterna.capacidad_total > 0:
        cisterna.porcentaje_actual = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
    else:
        cisterna.porcentaje_actual = Decimal("0")
    cisterna.esta_bajo = cisterna.nivel_actual <= cisterna.nivel_minimo

    return cisterna


# ==================== CARGAS DE CISTERNA ====================

def obtener_todas_cargas(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[CargaCisterna]:
    """Obtiene todas las cargas de cisterna"""
    return db.query(CargaCisterna).order_by(desc(CargaCisterna.fecha)).offset(skip).limit(limit).all()


def obtener_carga_por_id(db: Session, carga_id: UUID) -> Optional[CargaCisterna]:
    """Obtiene una carga por ID"""
    return db.query(CargaCisterna).filter(CargaCisterna.id == carga_id).first()


def crear_carga_cisterna(
    db: Session,
    carga_data: CargaCisternaCreate,
    usuario_id: UUID
) -> CargaCisterna:
    """
    Registra una carga de combustible a la cisterna

    Actualiza automáticamente el nivel de la cisterna
    """
    # Obtener la cisterna especificada
    cisterna = obtener_cisterna_por_id(db, carga_data.cisterna_id)

    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no encontrada"
        )

    # Calcular costo por litro
    costo_por_litro = None
    if carga_data.costo_total:
        costo_por_litro = carga_data.costo_total / carga_data.litros

    # Preparar datos y convertir fecha si es string
    carga_dict = carga_data.model_dump()
    if isinstance(carga_dict.get('fecha'), str):
        from datetime import datetime as dt
        try:
            carga_dict['fecha'] = dt.fromisoformat(carga_dict['fecha'])
        except ValueError:
            carga_dict['fecha'] = dt.strptime(carga_dict['fecha'], '%Y-%m-%d')

    # Crear carga
    db_carga = CargaCisterna(
        **carga_dict,
        costo_por_litro=costo_por_litro,
        created_by=usuario_id
    )

    db.add(db_carga)

    # Actualizar nivel de cisterna
    nuevo_nivel = cisterna.nivel_actual + carga_data.litros

    # Verificar que no exceda la capacidad
    if nuevo_nivel > cisterna.capacidad_total:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La carga excede la capacidad de la cisterna. Capacidad: {cisterna.capacidad_total}L, nivel actual: {cisterna.nivel_actual}L, carga: {carga_data.litros}L"
        )

    cisterna.nivel_actual = nuevo_nivel

    db.commit()
    db.refresh(db_carga)

    # Agregar nombre de cisterna para respuesta
    db_carga.cisterna_nombre = cisterna.nombre

    return db_carga


def actualizar_carga(db: Session, carga_id: UUID, update_data: CargaCisternaUpdate) -> CargaCisterna:
    """
    Actualiza una carga de cisterna

    Si se modifican los litros, ajusta el nivel de la cisterna
    """
    db_carga = obtener_carga_por_id(db, carga_id)

    if not db_carga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carga no encontrada"
        )

    # Obtener la cisterna asociada
    if db_carga.cisterna_id:
        cisterna = obtener_cisterna_por_id(db, db_carga.cisterna_id)
    else:
        cisterna = obtener_cisterna(db)

    # Si se modifican los litros, ajustar el nivel de la cisterna
    update_dict = update_data.model_dump(exclude_unset=True)
    if 'litros' in update_dict and cisterna:
        diferencia = update_dict['litros'] - db_carga.litros
        nuevo_nivel = cisterna.nivel_actual + diferencia

        # Verificar que no exceda la capacidad
        if nuevo_nivel > cisterna.capacidad_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La carga excede la capacidad de la cisterna. Capacidad: {cisterna.capacidad_total}L, nivel actual: {cisterna.nivel_actual}L"
            )

        # No permitir nivel negativo
        if nuevo_nivel < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ajuste resultaría en un nivel negativo de cisterna"
            )

        cisterna.nivel_actual = nuevo_nivel

    # Recalcular costo por litro si se modificó costo_total o litros
    if 'costo_total' in update_dict or 'litros' in update_dict:
        costo_total = update_dict.get('costo_total', db_carga.costo_total)
        litros = update_dict.get('litros', db_carga.litros)
        if costo_total and litros:
            db_carga.costo_por_litro = costo_total / litros

    # Actualizar campos
    for field, value in update_dict.items():
        setattr(db_carga, field, value)

    db.commit()
    db.refresh(db_carga)

    # Agregar nombre de cisterna para respuesta
    if cisterna:
        db_carga.cisterna_nombre = cisterna.nombre

    return db_carga


def eliminar_carga(db: Session, carga_id: UUID) -> dict:
    """
    Elimina una carga de cisterna

    IMPORTANTE: Descuenta los litros del nivel actual
    """
    db_carga = obtener_carga_por_id(db, carga_id)

    if not db_carga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carga no encontrada"
        )

    # Obtener la cisterna asociada
    if db_carga.cisterna_id:
        cisterna = obtener_cisterna_por_id(db, db_carga.cisterna_id)
    else:
        cisterna = obtener_cisterna(db)

    if cisterna:
        # Descontar litros del nivel actual
        cisterna.nivel_actual -= db_carga.litros

        # No permitir nivel negativo
        if cisterna.nivel_actual < 0:
            cisterna.nivel_actual = Decimal("0")

    db.delete(db_carga)
    db.commit()

    return {"message": "Carga eliminada correctamente"}


# ==================== SUMINISTROS A CAMIONES ====================

def obtener_todos_suministros(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[SuministroCombustible]:
    """Obtiene todos los suministros con info de camión y usuario"""
    from app.models.camion import Camion
    from app.models.usuario import Usuario

    suministros = db.query(SuministroCombustible).order_by(
        desc(SuministroCombustible.fecha)
    ).offset(skip).limit(limit).all()

    # Enriquecer con datos de camión, cisterna y usuario
    for s in suministros:
        # Obtener camión
        camion = db.query(Camion).filter(Camion.id == s.camion_id).first()
        if camion:
            s.camion_patente = camion.patente
            s.camion_nombre = camion.nombre
            s.camion_codigo_interno = camion.codigo_interno

        # Obtener cisterna
        cisterna = db.query(CisternaCombustible).filter(CisternaCombustible.id == s.cisterna_id).first()
        if cisterna:
            s.cisterna_nombre = cisterna.nombre

        # Obtener usuario
        usuario = db.query(Usuario).filter(Usuario.id == s.created_by).first()
        if usuario:
            s.usuario_nombre = usuario.nombre

    return suministros


def obtener_suministro_por_id(db: Session, suministro_id: UUID) -> Optional[SuministroCombustible]:
    """Obtiene un suministro por ID"""
    return db.query(SuministroCombustible).filter(SuministroCombustible.id == suministro_id).first()


def obtener_suministros_por_camion(db: Session, camion_id: UUID) -> List[SuministroCombustible]:
    """Obtiene suministros de un camión específico"""
    return db.query(SuministroCombustible).filter(
        SuministroCombustible.camion_id == camion_id
    ).order_by(desc(SuministroCombustible.fecha)).all()


def crear_suministro(
    db: Session,
    suministro_data: SuministroCombustibleCreate,
    usuario_id: UUID
) -> SuministroCombustible:
    """
    Registra un suministro de combustible a un camión

    Descuenta automáticamente del nivel de la cisterna
    """
    # Verificar que el camión exista
    camion = camion_service.obtener_por_id(db, suministro_data.camion_id)
    if not camion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camión no encontrado"
        )

    # Verificar cisterna
    cisterna = obtener_cisterna_por_id(db, suministro_data.cisterna_id)
    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no encontrada"
        )

    # Verificar que haya combustible suficiente
    if cisterna.nivel_actual < suministro_data.litros:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay combustible suficiente en la cisterna. Nivel actual: {cisterna.nivel_actual}L, requerido: {suministro_data.litros}L"
        )

    # Crear suministro - mapear kilometraje_actual a kilometraje y convertir fecha
    suministro_dict = suministro_data.model_dump()
    if 'kilometraje_actual' in suministro_dict:
        suministro_dict['kilometraje'] = suministro_dict.pop('kilometraje_actual')

    # Convertir fecha string a datetime
    if isinstance(suministro_dict.get('fecha'), str):
        from datetime import datetime as dt
        try:
            suministro_dict['fecha'] = dt.fromisoformat(suministro_dict['fecha'])
        except ValueError:
            suministro_dict['fecha'] = dt.strptime(suministro_dict['fecha'], '%Y-%m-%d')

    db_suministro = SuministroCombustible(
        **suministro_dict,
        created_by=usuario_id
    )

    db.add(db_suministro)

    # Descontar de cisterna
    cisterna.nivel_actual -= suministro_data.litros

    # Verificar si quedó bajo nivel de alerta
    if cisterna.nivel_actual <= cisterna.nivel_minimo:
        # Crear alerta con Celery (solo si está disponible)
        try:
            from app.tasks.alertas import verificar_nivel_cisterna
            verificar_nivel_cisterna.delay()
        except Exception:
            # Celery/Redis no disponible - ignorar silenciosamente
            pass

    db.commit()
    db.refresh(db_suministro)

    # Agregar info para respuesta
    db_suministro.cisterna_nombre = cisterna.nombre
    db_suministro.camion_patente = camion.patente
    db_suministro.camion_nombre = camion.nombre
    db_suministro.camion_codigo_interno = camion.codigo_interno

    return db_suministro


def actualizar_suministro(
    db: Session,
    suministro_id: UUID,
    suministro_data: "SuministroCombustibleUpdate"
) -> SuministroCombustible:
    """
    Actualiza un suministro existente

    Si se modifican los litros, ajusta el nivel de la cisterna
    """
    from app.schemas.combustible import SuministroCombustibleUpdate

    db_suministro = obtener_suministro_por_id(db, suministro_id)

    if not db_suministro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suministro no encontrado"
        )

    # Si se están modificando los litros, ajustar la cisterna
    if suministro_data.litros is not None and suministro_data.litros != db_suministro.litros:
        diferencia = suministro_data.litros - db_suministro.litros

        # Obtener la cisterna
        if db_suministro.cisterna_id:
            cisterna = obtener_cisterna_por_id(db, db_suministro.cisterna_id)
        else:
            cisterna = obtener_cisterna(db)

        if cisterna:
            # Si aumentaron los litros, descontar más de la cisterna
            # Si disminuyeron, devolver la diferencia
            nuevo_nivel = cisterna.nivel_actual - diferencia

            if nuevo_nivel < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No hay suficiente combustible en la cisterna. Disponible: {cisterna.nivel_actual} litros"
                )

            cisterna.nivel_actual = nuevo_nivel

    # Actualizar campos
    update_data = suministro_data.model_dump(exclude_unset=True)

    # Mapear kilometraje -> kilometraje_actual si viene en el update
    if 'kilometraje' in update_data:
        update_data['kilometraje_actual'] = update_data.pop('kilometraje')

    for field, value in update_data.items():
        if hasattr(db_suministro, field):
            setattr(db_suministro, field, value)

    db.commit()
    db.refresh(db_suministro)

    # Enriquecer con datos del camión
    camion = db_suministro.camion
    if camion:
        db_suministro.camion_patente = camion.patente
        db_suministro.camion_nombre = camion.nombre
        db_suministro.camion_codigo_interno = camion.codigo_interno

    return db_suministro


def eliminar_suministro(db: Session, suministro_id: UUID) -> dict:
    """
    Elimina un suministro

    IMPORTANTE: Devuelve los litros al nivel de la cisterna
    """
    db_suministro = obtener_suministro_por_id(db, suministro_id)

    if not db_suministro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suministro no encontrado"
        )

    # Obtener la cisterna asociada
    if db_suministro.cisterna_id:
        cisterna = obtener_cisterna_por_id(db, db_suministro.cisterna_id)
    else:
        cisterna = obtener_cisterna(db)

    if cisterna:
        # Devolver litros a la cisterna
        cisterna.nivel_actual += db_suministro.litros

        # No exceder capacidad
        if cisterna.nivel_actual > cisterna.capacidad_total:
            cisterna.nivel_actual = cisterna.capacidad_total

    db.delete(db_suministro)
    db.commit()

    return {"message": "Suministro eliminado correctamente"}


# ==================== TRANSFERENCIAS ENTRE CISTERNAS ====================

def obtener_todas_transferencias(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[TransferenciaCisterna]:
    """Obtiene todas las transferencias entre cisternas"""
    from app.models.usuario import Usuario

    transferencias = db.query(TransferenciaCisterna).order_by(
        desc(TransferenciaCisterna.fecha)
    ).offset(skip).limit(limit).all()

    # Enriquecer con datos de cisternas y usuario
    for t in transferencias:
        cisterna_origen = db.query(CisternaCombustible).filter(
            CisternaCombustible.id == t.cisterna_origen_id
        ).first()
        if cisterna_origen:
            t.cisterna_origen_nombre = cisterna_origen.nombre

        cisterna_destino = db.query(CisternaCombustible).filter(
            CisternaCombustible.id == t.cisterna_destino_id
        ).first()
        if cisterna_destino:
            t.cisterna_destino_nombre = cisterna_destino.nombre

        usuario = db.query(Usuario).filter(Usuario.id == t.created_by).first()
        if usuario:
            t.usuario_nombre = usuario.nombre

    return transferencias


def crear_transferencia(
    db: Session,
    transferencia_data: TransferenciaCisternaCreate,
    usuario_id: UUID
) -> TransferenciaCisterna:
    """
    Crea una transferencia de combustible entre cisternas

    - Descuenta litros de la cisterna origen
    - Suma litros a la cisterna destino
    """
    # Verificar que las cisternas sean diferentes
    if transferencia_data.cisterna_origen_id == transferencia_data.cisterna_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cisterna origen y destino deben ser diferentes"
        )

    # Obtener cisterna origen
    cisterna_origen = obtener_cisterna_por_id(db, transferencia_data.cisterna_origen_id)
    if not cisterna_origen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna de origen no encontrada"
        )

    # Obtener cisterna destino
    cisterna_destino = obtener_cisterna_por_id(db, transferencia_data.cisterna_destino_id)
    if not cisterna_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna de destino no encontrada"
        )

    # Verificar que haya combustible suficiente en origen
    if cisterna_origen.nivel_actual < transferencia_data.litros:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay combustible suficiente en la cisterna origen. Nivel actual: {cisterna_origen.nivel_actual}L, requerido: {transferencia_data.litros}L"
        )

    # Verificar que no exceda la capacidad del destino
    nuevo_nivel_destino = cisterna_destino.nivel_actual + transferencia_data.litros
    if nuevo_nivel_destino > cisterna_destino.capacidad_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La transferencia excede la capacidad de la cisterna destino. Capacidad: {cisterna_destino.capacidad_total}L, nivel actual: {cisterna_destino.nivel_actual}L, transferencia: {transferencia_data.litros}L"
        )

    # Convertir fecha string a datetime
    fecha = transferencia_data.fecha
    if isinstance(fecha, str):
        from datetime import datetime as dt
        try:
            fecha = dt.fromisoformat(fecha)
        except ValueError:
            fecha = dt.strptime(fecha, '%Y-%m-%d')

    # Crear transferencia
    db_transferencia = TransferenciaCisterna(
        cisterna_origen_id=transferencia_data.cisterna_origen_id,
        cisterna_destino_id=transferencia_data.cisterna_destino_id,
        litros=transferencia_data.litros,
        fecha=fecha,
        observaciones=transferencia_data.observaciones,
        created_by=usuario_id
    )

    db.add(db_transferencia)

    # Actualizar niveles de cisternas
    cisterna_origen.nivel_actual -= transferencia_data.litros
    cisterna_destino.nivel_actual += transferencia_data.litros

    db.commit()
    db.refresh(db_transferencia)

    # Agregar info para respuesta
    db_transferencia.cisterna_origen_nombre = cisterna_origen.nombre
    db_transferencia.cisterna_destino_nombre = cisterna_destino.nombre

    return db_transferencia


def eliminar_transferencia(db: Session, transferencia_id: UUID) -> dict:
    """
    Elimina una transferencia

    IMPORTANTE: Revierte los litros (devuelve a origen, quita de destino)
    """
    db_transferencia = db.query(TransferenciaCisterna).filter(
        TransferenciaCisterna.id == transferencia_id
    ).first()

    if not db_transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transferencia no encontrada"
        )

    # Obtener cisternas
    cisterna_origen = obtener_cisterna_por_id(db, db_transferencia.cisterna_origen_id)
    cisterna_destino = obtener_cisterna_por_id(db, db_transferencia.cisterna_destino_id)

    # Revertir la transferencia
    if cisterna_origen:
        cisterna_origen.nivel_actual += db_transferencia.litros
        # No exceder capacidad
        if cisterna_origen.nivel_actual > cisterna_origen.capacidad_total:
            cisterna_origen.nivel_actual = cisterna_origen.capacidad_total

    if cisterna_destino:
        cisterna_destino.nivel_actual -= db_transferencia.litros
        # No permitir negativo
        if cisterna_destino.nivel_actual < 0:
            cisterna_destino.nivel_actual = Decimal("0")

    db.delete(db_transferencia)
    db.commit()

    return {"message": "Transferencia eliminada correctamente"}


def obtener_consumo_por_camion(
    db: Session,
    camion_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> dict:
    """
    Obtiene estadísticas de consumo de combustible por camión

    Returns:
        Diccionario con estadísticas
    """
    query = db.query(SuministroCombustible).filter(
        SuministroCombustible.camion_id == camion_id
    )

    if fecha_desde:
        query = query.filter(func.date(SuministroCombustible.fecha) >= fecha_desde)
    if fecha_hasta:
        query = query.filter(func.date(SuministroCombustible.fecha) <= fecha_hasta)

    suministros = query.all()

    if not suministros:
        return {
            "camion_id": str(camion_id),
            "total_litros": Decimal("0"),
            "cantidad_suministros": 0,
            "promedio_por_suministro": Decimal("0")
        }

    total_litros = sum(s.litros for s in suministros)
    cantidad = len(suministros)
    promedio = total_litros / cantidad if cantidad > 0 else Decimal("0")

    return {
        "camion_id": str(camion_id),
        "total_litros": round(total_litros, 2),
        "cantidad_suministros": cantidad,
        "promedio_por_suministro": round(promedio, 2)
    }
