"""
Endpoints API para Finanzas
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.schemas.finanzas import (
    CategoriaFinanzasSchema, CategoriaFinanzasCreate, CategoriaFinanzasUpdate,
    MovimientoFinancieroSchema, MovimientoFinancieroCreate, MovimientoFinancieroUpdate,
    CuentaBancariaSchema, CuentaBancariaCreate, CuentaBancariaUpdate,
    ResumenFinanciero, ResumenPorCategoria
)
from app.services import finanzas_service

router = APIRouter()


# =============================================
# CATEGORÍAS
# =============================================

@router.get("/categorias", response_model=List[CategoriaFinanzasSchema])
async def listar_categorias(
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las categorías financieras"""
    return finanzas_service.obtener_categorias(db, tipo, solo_activos)


@router.post("/categorias", response_model=CategoriaFinanzasSchema, status_code=201)
async def crear_categoria(
    categoria: CategoriaFinanzasCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea una nueva categoría (solo admin)"""
    return finanzas_service.crear_categoria(db, categoria)


@router.put("/categorias/{categoria_id}", response_model=CategoriaFinanzasSchema)
async def actualizar_categoria(
    categoria_id: UUID,
    categoria_data: CategoriaFinanzasUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza una categoría (solo admin)"""
    return finanzas_service.actualizar_categoria(db, categoria_id, categoria_data)


# =============================================
# MOVIMIENTOS FINANCIEROS
# =============================================

@router.get("/movimientos", response_model=List[MovimientoFinancieroSchema])
async def listar_movimientos(
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    categoria_id: Optional[UUID] = None,
    camion_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista movimientos financieros con filtros"""
    movimientos = finanzas_service.obtener_movimientos(
        db, tipo, categoria_id, camion_id, empresa_id,
        fecha_desde, fecha_hasta, estado, skip, limit
    )

    return [
        finanzas_service.obtener_movimiento_con_relaciones(db, m)
        for m in movimientos
    ]


@router.get("/movimientos/{movimiento_id}", response_model=MovimientoFinancieroSchema)
async def obtener_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un movimiento por ID"""
    from fastapi import HTTPException, status
    movimiento = finanzas_service.obtener_movimiento_por_id(db, movimiento_id)

    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    return finanzas_service.obtener_movimiento_con_relaciones(db, movimiento)


@router.post("/movimientos", response_model=MovimientoFinancieroSchema, status_code=201)
async def crear_movimiento(
    movimiento: MovimientoFinancieroCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Crea un nuevo movimiento financiero"""
    nuevo = finanzas_service.crear_movimiento(db, movimiento, current_user.id)
    return finanzas_service.obtener_movimiento_con_relaciones(db, nuevo)


@router.put("/movimientos/{movimiento_id}", response_model=MovimientoFinancieroSchema)
async def actualizar_movimiento(
    movimiento_id: UUID,
    movimiento_data: MovimientoFinancieroUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un movimiento"""
    actualizado = finanzas_service.actualizar_movimiento(db, movimiento_id, movimiento_data)
    return finanzas_service.obtener_movimiento_con_relaciones(db, actualizado)


@router.delete("/movimientos/{movimiento_id}", response_model=MovimientoFinancieroSchema)
async def eliminar_movimiento(
    movimiento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Anula un movimiento (solo admin)"""
    anulado = finanzas_service.eliminar_movimiento(db, movimiento_id)
    return finanzas_service.obtener_movimiento_con_relaciones(db, anulado)


# =============================================
# RESÚMENES Y ESTADÍSTICAS
# =============================================

@router.get("/resumen", response_model=ResumenFinanciero)
async def obtener_resumen(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el resumen financiero del período"""
    return finanzas_service.obtener_resumen(db, fecha_desde, fecha_hasta)


@router.get("/resumen/categorias", response_model=List[ResumenPorCategoria])
async def obtener_resumen_por_categoria(
    tipo: Optional[Literal["ingreso", "egreso"]] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene resumen agrupado por categoría"""
    return finanzas_service.obtener_resumen_por_categoria(db, tipo, fecha_desde, fecha_hasta)


@router.get("/resumen/diario")
async def obtener_resumen_diario(
    dias: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene resumen de los últimos N días"""
    return finanzas_service.obtener_resumen_diario(db, dias)


# =============================================
# CUENTAS BANCARIAS
# =============================================

@router.get("/cuentas", response_model=List[CuentaBancariaSchema])
async def listar_cuentas(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las cuentas bancarias"""
    return finanzas_service.obtener_cuentas(db, solo_activas)


@router.get("/cuentas/{cuenta_id}", response_model=CuentaBancariaSchema)
async def obtener_cuenta(
    cuenta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una cuenta por ID"""
    from fastapi import HTTPException, status
    cuenta = finanzas_service.obtener_cuenta_por_id(db, cuenta_id)

    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    return cuenta


@router.post("/cuentas", response_model=CuentaBancariaSchema, status_code=201)
async def crear_cuenta(
    cuenta: CuentaBancariaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea una nueva cuenta bancaria (solo admin)"""
    return finanzas_service.crear_cuenta(db, cuenta)


@router.put("/cuentas/{cuenta_id}", response_model=CuentaBancariaSchema)
async def actualizar_cuenta(
    cuenta_id: UUID,
    cuenta_data: CuentaBancariaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza una cuenta bancaria (solo admin)"""
    return finanzas_service.actualizar_cuenta(db, cuenta_id, cuenta_data)
