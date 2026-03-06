"""
Endpoints API para Facturación
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.schemas.factura import (
    FacturaSchema, FacturaCreate, FacturaUpdate, FacturaConDetalles,
    PagoFacturaSchema, PagoFacturaCreate,
    PagoRemitoSchema, PagoRemitoCreate,
    RemitoParaFactura, EstadoCuentaCliente, ResumenFacturacionCliente,
    AsociarRemitosRequest
)
from app.services import factura_service

router = APIRouter()


# =============================================
# FACTURAS
# =============================================

@router.get("/facturas", response_model=List[FacturaSchema])
async def listar_facturas(
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_comprobante: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista facturas con filtros opcionales"""
    facturas = factura_service.obtener_facturas(
        db, empresa_id, estado, tipo_comprobante,
        fecha_desde, fecha_hasta, skip, limit
    )

    result = []
    for factura in facturas:
        data = FacturaSchema.model_validate(factura)
        data.empresa_nombre = factura.empresa.nombre if factura.empresa else None
        data.porcentaje_pagado = factura.porcentaje_pagado
        data.esta_pagada = factura.esta_pagada
        result.append(data)

    return result


@router.get("/facturas/pendientes", response_model=List[FacturaSchema])
async def listar_facturas_pendientes(
    empresa_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista facturas pendientes de pago"""
    facturas = factura_service.obtener_facturas_pendientes(db, empresa_id)

    result = []
    for factura in facturas:
        data = FacturaSchema.model_validate(factura)
        data.empresa_nombre = factura.empresa.nombre if factura.empresa else None
        data.porcentaje_pagado = factura.porcentaje_pagado
        data.esta_pagada = factura.esta_pagada
        result.append(data)

    return result


@router.get("/facturas/{factura_id}", response_model=FacturaConDetalles)
async def obtener_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una factura con todos sus detalles"""
    factura = factura_service.obtener_factura_por_id(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    data = FacturaConDetalles.model_validate(factura)
    data.empresa_nombre = factura.empresa.nombre if factura.empresa else None
    data.porcentaje_pagado = factura.porcentaje_pagado
    data.esta_pagada = factura.esta_pagada

    # Cargar remitos
    data.remitos_detalle = [
        RemitoParaFactura.model_validate(r) for r in factura.remitos
    ]

    # Cargar pagos
    data.pagos_detalle = [
        PagoFacturaSchema.model_validate(p) for p in factura.pagos if not p.anulado
    ]

    return data


@router.post("/facturas", response_model=FacturaSchema, status_code=201)
async def crear_factura(
    factura: FacturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crea una nueva factura

    Puede asociar remitos existentes mediante `remito_ids`.
    El total se calcula automáticamente si no se especifica.
    """
    nueva_factura = factura_service.crear_factura(db, factura, current_user.id)

    data = FacturaSchema.model_validate(nueva_factura)
    data.empresa_nombre = nueva_factura.empresa.nombre if nueva_factura.empresa else None
    data.porcentaje_pagado = nueva_factura.porcentaje_pagado
    data.esta_pagada = nueva_factura.esta_pagada

    return data


@router.put("/facturas/{factura_id}", response_model=FacturaSchema)
async def actualizar_factura(
    factura_id: UUID,
    factura_data: FacturaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza datos de una factura (solo admin)"""
    factura = factura_service.actualizar_factura(db, factura_id, factura_data)

    data = FacturaSchema.model_validate(factura)
    data.empresa_nombre = factura.empresa.nombre if factura.empresa else None
    return data


@router.delete("/facturas/{factura_id}")
async def anular_factura(
    factura_id: UUID,
    motivo: str = Query(..., min_length=5),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Anula una factura (solo admin)"""
    factura = factura_service.anular_factura(db, factura_id, motivo)
    return {"message": f"Factura {factura.numero_factura} anulada", "id": str(factura.id)}


# =============================================
# PAGOS DE FACTURA
# =============================================

@router.get("/facturas/{factura_id}/pagos", response_model=List[PagoFacturaSchema])
async def listar_pagos_factura(
    factura_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista los pagos de una factura"""
    return factura_service.obtener_pagos_factura(db, factura_id)


@router.post("/facturas/{factura_id}/pagos", response_model=PagoFacturaSchema, status_code=201)
async def registrar_pago_factura(
    factura_id: UUID,
    pago: PagoFacturaCreate,
    registrar_en_cc: bool = Query(True, description="Registrar en cuenta corriente"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Registra un pago a una factura

    Formas de pago disponibles:
    - efectivo, transferencia, cheque, e_cheque
    - tarjeta_debito, tarjeta_credito
    - retencion_iibb, retencion_ganancias, retencion_suss, retencion_iva
    """
    # Asegurar que el factura_id coincida
    pago.factura_id = factura_id

    nuevo_pago = factura_service.registrar_pago_factura(
        db, pago, current_user.id, registrar_en_cc
    )
    return PagoFacturaSchema.model_validate(nuevo_pago)


@router.delete("/pagos-factura/{pago_id}")
async def anular_pago_factura(
    pago_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Anula un pago de factura (solo admin)"""
    pago = factura_service.anular_pago_factura(db, pago_id)
    return {"message": "Pago anulado", "id": str(pago.id)}


# =============================================
# PAGOS DE REMITO (SIN FACTURA)
# =============================================

@router.post("/remitos/{remito_id}/pagos", response_model=PagoRemitoSchema, status_code=201)
async def registrar_pago_remito(
    remito_id: UUID,
    pago: PagoRemitoCreate,
    registrar_en_cc: bool = Query(True, description="Registrar en cuenta corriente"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Registra un pago directo a un remito (sin factura)

    Solo funciona si el remito no ha sido facturado.
    """
    pago.remito_id = remito_id

    nuevo_pago = factura_service.registrar_pago_remito(
        db, pago, current_user.id, registrar_en_cc
    )
    return PagoRemitoSchema.model_validate(nuevo_pago)


# =============================================
# REMITOS PENDIENTES
# =============================================

@router.get("/clientes/{empresa_id}/remitos-pendientes", response_model=List[RemitoParaFactura])
async def listar_remitos_pendientes_cliente(
    empresa_id: UUID,
    solo_sin_facturar: bool = Query(True),
    solo_con_saldo: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista remitos pendientes de un cliente

    Útil para:
    - Seleccionar remitos al crear una factura
    - Ver qué remitos tienen saldo pendiente de cobro
    """
    remitos = factura_service.obtener_remitos_pendientes_cliente(
        db, empresa_id, solo_sin_facturar, solo_con_saldo
    )
    return [RemitoParaFactura.model_validate(r) for r in remitos]


# =============================================
# ESTADO DE CUENTA
# =============================================

@router.get("/clientes/{empresa_id}/estado-cuenta", response_model=EstadoCuentaCliente)
async def obtener_estado_cuenta(
    empresa_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el estado de cuenta completo de un cliente

    Incluye todos los movimientos: cargos, pagos, ajustes
    """
    return factura_service.obtener_estado_cuenta_cliente(
        db, empresa_id, fecha_desde, fecha_hasta
    )


@router.get("/clientes/{empresa_id}/estado-cuenta/pdf")
async def descargar_estado_cuenta_pdf(
    empresa_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Descarga el estado de cuenta en PDF"""
    from app.tasks.reportes_facturacion import generar_estado_cuenta_pdf

    estado_cuenta = factura_service.obtener_estado_cuenta_cliente(
        db, empresa_id, fecha_desde, fecha_hasta
    )

    pdf_buffer = generar_estado_cuenta_pdf(estado_cuenta)

    filename = f"estado_cuenta_{estado_cuenta.empresa_nombre.replace(' ', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
