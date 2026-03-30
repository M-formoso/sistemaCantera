"""
Endpoints de Tesorería
API para gestión de cheques, movimientos de caja, cuentas bancarias y gastos
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.services.tesoreria_service import TesoreriaService
from app.schemas.tesoreria import (
    # Constantes
    TIPOS_CHEQUE, ORIGENES_CHEQUE, ESTADOS_CHEQUE, METODOS_PAGO, BANCOS_ARGENTINA, CATEGORIAS_GASTO,
    # Cheques
    ChequeCreate, ChequeUpdate, ChequeResponse, ChequeList, PaginatedCheques,
    DepositarChequeRequest, CobrarChequeRequest, RechazarChequeRequest, EntregarChequeRequest,
    # Movimientos
    MovimientoTesoreriaCreate, MovimientoTesoreriaResponse, MovimientoTesoreriaList,
    PaginatedMovimientos, AnularMovimientoRequest,
    # Cajas
    CajaEfectivoCreate, CajaEfectivoUpdate, CajaEfectivoResponse,
    MovimientoCajaCreate, MovimientoCajaResponse,
    # Cuentas bancarias
    CuentaBancariaCreate, CuentaBancariaUpdate, CuentaBancariaResponse,
    MovimientoBancarioCreate, MovimientoBancarioResponse,
    # Gastos
    GastoCreate, GastoUpdate, GastoResponse, GastoList, PaginatedGastos,
    # Recibos
    ReciboCreate, ReciboResponse,
    # Resumen
    ResumenTesoreria, MovimientosConsolidadosResponse
)

router = APIRouter()


# ==================== CONSTANTES ====================

@router.get("/constantes/tipos-cheque")
def get_tipos_cheque():
    """Obtiene tipos de cheque disponibles"""
    return TIPOS_CHEQUE


@router.get("/constantes/origenes-cheque")
def get_origenes_cheque():
    """Obtiene orígenes de cheque disponibles"""
    return ORIGENES_CHEQUE


@router.get("/constantes/estados-cheque")
def get_estados_cheque():
    """Obtiene estados de cheque disponibles"""
    return ESTADOS_CHEQUE


@router.get("/constantes/metodos-pago")
def get_metodos_pago():
    """Obtiene métodos de pago disponibles"""
    return METODOS_PAGO


@router.get("/constantes/bancos")
def get_bancos():
    """Obtiene lista de bancos"""
    return BANCOS_ARGENTINA


@router.get("/constantes/categorias-gasto")
def get_categorias_gasto():
    """Obtiene categorías de gasto"""
    return CATEGORIAS_GASTO


# ==================== RESUMEN ====================

@router.get("/resumen", response_model=ResumenTesoreria)
def get_resumen(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene resumen de tesorería"""
    service = TesoreriaService(db)
    return service.get_resumen(fecha_desde, fecha_hasta)


# ==================== CHEQUES ====================

@router.get("/cheques", response_model=PaginatedCheques)
def get_cheques(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    estado: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    origen: Optional[str] = Query(None),
    empresa_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    solo_en_cartera: bool = Query(False),
    vencidos: bool = Query(False),
    proximos_vencer: bool = Query(False),
    dias_vencimiento: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene lista de cheques con filtros"""
    service = TesoreriaService(db)
    return service.get_cheques(
        skip=skip,
        limit=limit,
        estado=estado,
        tipo=tipo,
        origen=origen,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
        solo_en_cartera=solo_en_cartera,
        vencidos=vencidos,
        proximos_vencer=proximos_vencer,
        dias_vencimiento=dias_vencimiento
    )


@router.get("/cheques/{cheque_id}", response_model=ChequeResponse)
def get_cheque(
    cheque_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un cheque por ID"""
    service = TesoreriaService(db)
    cheque = service.get_cheque(cheque_id)
    if not cheque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cheque no encontrado"
        )
    return service._enrich_cheque(cheque)


@router.post("/cheques", response_model=ChequeResponse, status_code=status.HTTP_201_CREATED)
def create_cheque(
    data: ChequeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo cheque"""
    # Verificar permisos
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.create_cheque(data, current_user.id)
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/cheques/{cheque_id}", response_model=ChequeResponse)
def update_cheque(
    cheque_id: UUID,
    data: ChequeUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un cheque"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para editar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.update_cheque(cheque_id, data)
        if not cheque:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cheque no encontrado"
            )
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cheques/{cheque_id}/depositar", response_model=ChequeResponse)
def depositar_cheque(
    cheque_id: UUID,
    data: DepositarChequeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Deposita un cheque en una cuenta bancaria"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para depositar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.depositar_cheque(cheque_id, data, current_user.id)
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cheques/{cheque_id}/cobrar", response_model=ChequeResponse)
def cobrar_cheque(
    cheque_id: UUID,
    data: CobrarChequeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Confirma el cobro de un cheque"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para cobrar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.cobrar_cheque(cheque_id, data, current_user.id)
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cheques/{cheque_id}/rechazar", response_model=ChequeResponse)
def rechazar_cheque(
    cheque_id: UUID,
    data: RechazarChequeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Rechaza un cheque y revierte el pago si es de cliente"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para rechazar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.rechazar_cheque(cheque_id, data, current_user.id)
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cheques/{cheque_id}/entregar", response_model=ChequeResponse)
def entregar_cheque(
    cheque_id: UUID,
    data: EntregarChequeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Entrega un cheque a un tercero como forma de pago"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para entregar cheques"
        )

    service = TesoreriaService(db)
    try:
        cheque = service.entregar_cheque(cheque_id, data, current_user.id)
        return service._enrich_cheque(cheque)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/cheques/{cheque_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cheque(
    cheque_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un cheque"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar cheques"
        )

    service = TesoreriaService(db)
    try:
        if not service.delete_cheque(cheque_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cheque no encontrado"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== MOVIMIENTOS DE TESORERÍA ====================

@router.get("/movimientos", response_model=PaginatedMovimientos)
def get_movimientos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tipo: Optional[str] = Query(None),
    es_ingreso: Optional[bool] = Query(None),
    metodo_pago: Optional[str] = Query(None),
    empresa_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    incluir_anulados: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene lista de movimientos de tesorería"""
    service = TesoreriaService(db)
    return service.get_movimientos_tesoreria(
        skip=skip,
        limit=limit,
        tipo=tipo,
        es_ingreso=es_ingreso,
        metodo_pago=metodo_pago,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
        incluir_anulados=incluir_anulados
    )


@router.post("/movimientos", response_model=MovimientoTesoreriaResponse, status_code=status.HTTP_201_CREATED)
def create_movimiento(
    data: MovimientoTesoreriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo movimiento de tesorería"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar movimientos"
        )

    service = TesoreriaService(db)
    movimiento = service.create_movimiento_tesoreria(data, current_user.id)
    return service._enrich_movimiento_tesoreria(movimiento)


@router.post("/movimientos/{movimiento_id}/anular", response_model=MovimientoTesoreriaResponse)
def anular_movimiento(
    movimiento_id: UUID,
    data: AnularMovimientoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Anula un movimiento de tesorería"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden anular movimientos"
        )

    service = TesoreriaService(db)
    try:
        movimiento = service.anular_movimiento_tesoreria(movimiento_id, data, current_user.id)
        return service._enrich_movimiento_tesoreria(movimiento)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== MOVIMIENTOS CONSOLIDADOS ====================

@router.get("/movimientos-consolidados", response_model=MovimientosConsolidadosResponse)
def get_movimientos_consolidados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tipo: Optional[str] = Query(None),
    es_ingreso: Optional[bool] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene movimientos consolidados de todas las fuentes"""
    service = TesoreriaService(db)
    return service.get_movimientos_consolidados(
        skip=skip,
        limit=limit,
        tipo=tipo,
        es_ingreso=es_ingreso,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


# ==================== CAJAS DE EFECTIVO ====================

@router.get("/cajas", response_model=List[CajaEfectivoResponse])
def get_cajas(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene todas las cajas de efectivo"""
    service = TesoreriaService(db)
    return service.get_cajas(solo_activas)


@router.get("/cajas/{caja_id}", response_model=CajaEfectivoResponse)
def get_caja(
    caja_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una caja por ID"""
    service = TesoreriaService(db)
    caja = service.get_caja(caja_id)
    if not caja:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caja no encontrada"
        )
    return caja


@router.post("/cajas", response_model=CajaEfectivoResponse, status_code=status.HTTP_201_CREATED)
def create_caja(
    data: CajaEfectivoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva caja de efectivo"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear cajas"
        )

    service = TesoreriaService(db)
    return service.create_caja(data)


@router.put("/cajas/{caja_id}", response_model=CajaEfectivoResponse)
def update_caja(
    caja_id: UUID,
    data: CajaEfectivoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una caja de efectivo"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden editar cajas"
        )

    service = TesoreriaService(db)
    caja = service.update_caja(caja_id, data)
    if not caja:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caja no encontrada"
        )
    return caja


@router.post("/cajas/movimientos", response_model=MovimientoCajaResponse, status_code=status.HTTP_201_CREATED)
def create_movimiento_caja(
    data: MovimientoCajaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un movimiento en una caja de efectivo"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar movimientos de caja"
        )

    service = TesoreriaService(db)
    try:
        return service.create_movimiento_caja(data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/cajas/{caja_id}/movimientos")
def get_movimientos_caja(
    caja_id: UUID,
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene movimientos de una caja específica"""
    service = TesoreriaService(db)
    return service.get_movimientos_caja(
        caja_id=caja_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )


# ==================== CUENTAS BANCARIAS ====================

@router.get("/cuentas-bancarias", response_model=List[CuentaBancariaResponse])
def get_cuentas_bancarias(
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene todas las cuentas bancarias"""
    service = TesoreriaService(db)
    return service.get_cuentas_bancarias(solo_activas)


@router.get("/cuentas-bancarias/{cuenta_id}", response_model=CuentaBancariaResponse)
def get_cuenta_bancaria(
    cuenta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una cuenta bancaria por ID"""
    service = TesoreriaService(db)
    cuenta = service.get_cuenta_bancaria(cuenta_id)
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    return cuenta


@router.post("/cuentas-bancarias", response_model=CuentaBancariaResponse, status_code=status.HTTP_201_CREATED)
def create_cuenta_bancaria(
    data: CuentaBancariaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva cuenta bancaria"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear cuentas bancarias"
        )

    service = TesoreriaService(db)
    return service.create_cuenta_bancaria(data)


@router.put("/cuentas-bancarias/{cuenta_id}", response_model=CuentaBancariaResponse)
def update_cuenta_bancaria(
    cuenta_id: UUID,
    data: CuentaBancariaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una cuenta bancaria"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden editar cuentas bancarias"
        )

    service = TesoreriaService(db)
    cuenta = service.update_cuenta_bancaria(cuenta_id, data)
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    return cuenta


@router.get("/cuentas-bancarias/{cuenta_id}/movimientos")
def get_movimientos_bancarios(
    cuenta_id: UUID,
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene movimientos de una cuenta bancaria específica"""
    service = TesoreriaService(db)
    return service.get_movimientos_bancarios(
        cuenta_id=cuenta_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )


# ==================== GASTOS ====================

@router.get("/gastos", response_model=PaginatedGastos)
def get_gastos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    categoria: Optional[str] = Query(None),
    metodo_pago: Optional[str] = Query(None),
    empresa_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    incluir_anulados: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene lista de gastos"""
    service = TesoreriaService(db)
    return service.get_gastos(
        skip=skip,
        limit=limit,
        categoria=categoria,
        metodo_pago=metodo_pago,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
        incluir_anulados=incluir_anulados
    )


@router.get("/gastos/{gasto_id}", response_model=GastoResponse)
def get_gasto(
    gasto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un gasto por ID"""
    service = TesoreriaService(db)
    gasto = service.get_gasto(gasto_id)
    if not gasto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    return service._enrich_gasto(gasto)


@router.post("/gastos", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def create_gasto(
    data: GastoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo gasto"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar gastos"
        )

    service = TesoreriaService(db)
    try:
        gasto = service.create_gasto(data, current_user.id)
        return service._enrich_gasto(gasto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/gastos/{gasto_id}", response_model=GastoResponse)
def update_gasto(
    gasto_id: UUID,
    data: GastoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un gasto"""
    if current_user.rol not in ["administrador"] and not current_user.permiso_finanzas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para editar gastos"
        )

    service = TesoreriaService(db)
    try:
        gasto = service.update_gasto(gasto_id, data)
        if not gasto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gasto no encontrado"
            )
        return service._enrich_gasto(gasto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/gastos/{gasto_id}/anular", response_model=GastoResponse)
def anular_gasto(
    gasto_id: UUID,
    data: AnularMovimientoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Anula un gasto"""
    if current_user.rol not in ["administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden anular gastos"
        )

    service = TesoreriaService(db)
    try:
        gasto = service.anular_gasto(gasto_id, data.motivo, current_user.id)
        return service._enrich_gasto(gasto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== RECIBOS ====================

@router.get("/recibos")
def get_recibos(
    empresa_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene lista de recibos"""
    service = TesoreriaService(db)
    return service.get_recibos(
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )
