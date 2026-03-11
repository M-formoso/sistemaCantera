"""
Endpoints API para Pesajes
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador, require_admin
from app.models.usuario import Usuario
from app.schemas.pesaje import (
    PesajeSchema, PesajeCreate, PesajeUpdate,
    PesajeIniciarCreate, PesajeCompletarCreate,
    PesajePendienteSchema, BusquedaPatenteResult
)
from app.services import pesaje_service

router = APIRouter()


@router.get("/", response_model=List[PesajeSchema])
async def listar_pesajes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente o completado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los pesajes con paginación"""
    return pesaje_service.obtener_todos(db, skip, limit)


@router.get("/pendientes", response_model=List[PesajePendienteSchema])
async def listar_pesajes_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista pesajes pendientes (solo tara registrada, esperando peso bruto)"""
    return pesaje_service.obtener_pendientes(db)


@router.get("/buscar-patente/{patente}", response_model=BusquedaPatenteResult)
async def buscar_por_patente(
    patente: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Busca información por patente del camión.
    Retorna datos del camión, cliente asociado y pesaje pendiente si existe.
    """
    return pesaje_service.buscar_por_patente(db, patente)


@router.get("/por-fecha")
async def listar_pesajes_por_fecha(
    fecha_desde: date,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene pesajes por rango de fechas"""
    return pesaje_service.obtener_por_fecha(db, fecha_desde, fecha_hasta)


@router.get("/del-dia")
async def listar_pesajes_del_dia(
    fecha: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene pesajes del día (hoy por defecto)"""
    return pesaje_service.obtener_del_dia(db, fecha)


@router.get("/por-camion/{camion_id}")
async def listar_pesajes_por_camion(
    camion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene pesajes de un camión específico"""
    return pesaje_service.obtener_por_camion(db, camion_id)


@router.post("/", response_model=PesajeSchema, status_code=201)
async def crear_pesaje(
    pesaje: PesajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un nuevo pesaje completo (modo tradicional)

    **Requiere rol:** Administrador u Operador

    - El número de pesaje se asigna automáticamente
    - El peso neto se calcula automáticamente (bruto - tara)
    """
    return pesaje_service.crear(db, pesaje, current_user.id)


@router.post("/iniciar", response_model=PesajeSchema, status_code=201)
async def iniciar_pesaje(
    pesaje: PesajeIniciarCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Inicia un nuevo pesaje registrando solo la tara (camión vacío)

    **Requiere rol:** Administrador u Operador

    El pesaje queda en estado 'pendiente' hasta que se complete
    con el peso bruto cuando el camión vuelva cargado.
    """
    return pesaje_service.iniciar_pesaje(db, pesaje, current_user.id)


@router.post("/{pesaje_id}/completar", response_model=PesajeSchema)
async def completar_pesaje(
    pesaje_id: UUID,
    pesaje: PesajeCompletarCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Completa un pesaje pendiente registrando el peso bruto (camión cargado)

    **Requiere rol:** Administrador u Operador

    - Calcula automáticamente el peso neto (bruto - tara)
    - Genera remito automáticamente
    - Actualiza cuenta corriente si hay importe
    """
    return pesaje_service.completar_pesaje(db, pesaje_id, pesaje, current_user.id)


@router.delete("/{pesaje_id}/cancelar")
async def cancelar_pesaje_pendiente(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Cancela un pesaje pendiente (elimina sin generar remito)

    **Requiere rol:** Administrador u Operador

    Solo funciona para pesajes en estado 'pendiente'
    """
    return pesaje_service.cancelar_pesaje_pendiente(db, pesaje_id)


@router.get("/{pesaje_id}", response_model=PesajeSchema)
async def obtener_pesaje(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un pesaje específico por ID"""
    pesaje = pesaje_service.obtener_por_id(db, pesaje_id)

    if not pesaje:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    return pesaje


@router.put("/{pesaje_id}", response_model=PesajeSchema)
async def actualizar_pesaje(
    pesaje_id: UUID,
    pesaje_data: PesajeUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Actualiza un pesaje existente

    **Requiere rol:** Administrador u Operador

    NOTA: Si ya tiene remito generado:
    - Administradores pueden editar todo
    - Otros usuarios solo pueden editar precio, importe y observaciones
    """
    return pesaje_service.actualizar(db, pesaje_id, pesaje_data, current_user)


@router.delete("/{pesaje_id}")
async def eliminar_pesaje(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina un pesaje

    **Requiere rol:** Administrador u Operador
    """
    from fastapi import HTTPException
    import traceback
    try:
        return pesaje_service.eliminar(db, pesaje_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[eliminar_pesaje] ERROR: {type(e).__name__}: {str(e)}")
        print(f"[eliminar_pesaje] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")


@router.get("/estadisticas/periodo")
async def obtener_estadisticas_periodo(
    fecha_desde: date,
    fecha_hasta: date,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene estadísticas de pesajes para un período"""
    return pesaje_service.obtener_estadisticas_periodo(db, fecha_desde, fecha_hasta)


@router.get("/{pesaje_id}/ticket-pdf")
async def descargar_ticket_pdf(
    pesaje_id: UUID,
    copias: int = Query(1, ge=1, le=3, description="Número de copias: 1=original, 2=duplicado, 3=triplicado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera y descarga el ticket de pesaje en PDF

    El PDF incluye todos los datos del control de pesada:
    - Datos del camión y transporte
    - Pesos (bruto, tara, neto)
    - Datos del producto y destino
    - Fecha, hora y operario

    Parámetros:
    - copias: 1 = solo original, 2 = original + duplicado, 3 = original + duplicado + triplicado
    """
    pesaje = pesaje_service.obtener_por_id(db, pesaje_id)

    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Obtener patente (propia o externa)
    patente = None
    if pesaje.camion:
        patente = pesaje.camion.patente
    elif pesaje.patente_externa:
        patente = pesaje.patente_externa

    # Obtener nombre del cliente
    cliente_nombre = pesaje.cliente_nombre
    if pesaje.cliente:
        cliente_nombre = pesaje.cliente.nombre

    # Obtener nombre del transportista
    transportista_nombre = pesaje.transportista
    if pesaje.transportista_empresa:
        transportista_nombre = pesaje.transportista_empresa.nombre

    # Usar fecha_completado si existe (tiene la hora real), sino usar fecha
    fecha_pesaje = pesaje.fecha_completado or pesaje.fecha

    # Preparar datos para el PDF
    pesaje_data = {
        "numero_pesaje": pesaje.numero_pesaje,
        "fecha": fecha_pesaje,
        "camion_patente": patente,
        "acoplado": pesaje.acoplado,
        "transportista": transportista_nombre,
        "cliente_destino": cliente_nombre,
        "material": pesaje.material,
        "chofer": pesaje.chofer,
        "peso_bruto": float(pesaje.peso_bruto) if pesaje.peso_bruto else 0,
        "peso_tara": float(pesaje.peso_tara) if pesaje.peso_tara else 0,
        "peso_neto": float(pesaje.peso_neto) if pesaje.peso_neto else 0,
        "operario": pesaje.operario,
        "observaciones": pesaje.observaciones,
        # Datos de importe
        "precio_unitario": float(pesaje.precio_unitario) if pesaje.precio_unitario else None,
        "flete": float(pesaje.flete) if pesaje.flete else None,
        "precio_fijo": float(pesaje.precio_fijo) if pesaje.precio_fijo else None,
        "importe_total": float(pesaje.importe_total) if pesaje.importe_total else None,
    }

    # Generar PDF con las copias solicitadas
    from app.tasks.reportes import generar_ticket_pesaje_pdf_multiple
    pdf_buffer = generar_ticket_pesaje_pdf_multiple(pesaje_data, copias)

    # Nombre del archivo
    filename = f"ticket_pesaje_{pesaje.numero_pesaje}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
