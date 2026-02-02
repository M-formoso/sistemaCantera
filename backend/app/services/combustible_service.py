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

from app.models.combustible import CisternaCombustible, CargaCisterna, SuministroCombustible
from app.schemas.combustible import (
    CisternaConfig, CisternaUpdate,
    CargaCisternaCreate, SuministroCombustibleCreate
)
from app.services import camion_service


# ==================== CISTERNA ====================

def obtener_cisterna(db: Session) -> Optional[CisternaCombustible]:
    """Obtiene la configuración de la cisterna"""
    return db.query(CisternaCombustible).first()


def configurar_cisterna(db: Session, config: CisternaConfig) -> CisternaCombustible:
    """
    Crea o actualiza la configuración de la cisterna

    Solo debe haber UNA cisterna en el sistema
    """
    cisterna = obtener_cisterna(db)

    if cisterna:
        # Actualizar existente
        cisterna.capacidad_total = config.capacidad_total
        cisterna.nivel_alerta = config.nivel_alerta
    else:
        # Crear nueva
        cisterna = CisternaCombustible(
            capacidad_total=config.capacidad_total,
            nivel_actual=Decimal("0"),
            nivel_alerta=config.nivel_alerta
        )
        db.add(cisterna)

    db.commit()
    db.refresh(cisterna)

    return cisterna


def actualizar_cisterna(db: Session, update_data: CisternaUpdate) -> CisternaCombustible:
    """Actualiza la cisterna (solo admin)"""
    cisterna = obtener_cisterna(db)

    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no configurada"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(cisterna, field, value)

    db.commit()
    db.refresh(cisterna)

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
    cisterna = obtener_cisterna(db)

    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no configurada. Configure la cisterna primero."
        )

    # Calcular costo por litro
    costo_por_litro = None
    if carga_data.costo_total:
        costo_por_litro = carga_data.costo_total / carga_data.litros

    # Crear carga
    db_carga = CargaCisterna(
        **carga_data.model_dump(),
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

    cisterna = obtener_cisterna(db)

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
    """Obtiene todos los suministros"""
    return db.query(SuministroCombustible).order_by(desc(SuministroCombustible.fecha)).offset(skip).limit(limit).all()


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
    cisterna = obtener_cisterna(db)
    if not cisterna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cisterna no configurada"
        )

    # Verificar que haya combustible suficiente
    if cisterna.nivel_actual < suministro_data.litros:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay combustible suficiente en la cisterna. Nivel actual: {cisterna.nivel_actual}L, requerido: {suministro_data.litros}L"
        )

    # Crear suministro
    db_suministro = SuministroCombustible(
        **suministro_data.model_dump(),
        created_by=usuario_id
    )

    db.add(db_suministro)

    # Descontar de cisterna
    cisterna.nivel_actual -= suministro_data.litros

    # Verificar si quedó bajo nivel de alerta
    if cisterna.nivel_actual <= cisterna.nivel_alerta:
        # Crear alerta con Celery
        try:
            from app.tasks.alertas import verificar_nivel_cisterna
            verificar_nivel_cisterna.delay()
        except ImportError:
            print(f"⚠️ Alerta: Nivel de cisterna bajo ({cisterna.nivel_actual}L)")

    db.commit()
    db.refresh(db_suministro)

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

    cisterna = obtener_cisterna(db)

    # Devolver litros a la cisterna
    cisterna.nivel_actual += db_suministro.litros

    # No exceder capacidad
    if cisterna.nivel_actual > cisterna.capacidad_total:
        cisterna.nivel_actual = cisterna.capacidad_total

    db.delete(db_suministro)
    db.commit()

    return {"message": "Suministro eliminado correctamente"}


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
