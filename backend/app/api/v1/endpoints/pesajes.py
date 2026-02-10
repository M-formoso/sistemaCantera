"""
Endpoints API para Pesajes
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador
from app.models.usuario import Usuario
from app.schemas.pesaje import PesajeSchema, PesajeCreate, PesajeUpdate
from app.services import pesaje_service

router = APIRouter()


@router.get("/", response_model=List[PesajeSchema])
async def listar_pesajes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los pesajes con paginación"""
    return pesaje_service.obtener_todos(db, skip, limit)


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
    Crea un nuevo pesaje

    **Requiere rol:** Administrador u Operador

    - El número de pesaje se asigna automáticamente
    - El peso neto se calcula automáticamente (bruto - tara)
    """
    return pesaje_service.crear(db, pesaje, current_user.id)


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
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Actualiza un pesaje existente

    **Requiere rol:** Administrador u Operador

    NOTA: No se puede editar si ya tiene remito generado
    """
    return pesaje_service.actualizar(db, pesaje_id, pesaje_data)


@router.delete("/{pesaje_id}")
async def eliminar_pesaje(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Elimina un pesaje

    **Requiere rol:** Administrador u Operador

    NOTA: No se puede eliminar si ya tiene remito generado
    """
    return pesaje_service.eliminar(db, pesaje_id)


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
    """
    pesaje = pesaje_service.obtener_por_id(db, pesaje_id)

    if not pesaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesaje no encontrado"
        )

    # Preparar datos para el PDF
    pesaje_data = {
        "numero_pesaje": pesaje.numero_pesaje,
        "fecha": pesaje.fecha,
        "camion_patente": pesaje.camion.patente if pesaje.camion else None,
        "acoplado": pesaje.acoplado,
        "transportista": pesaje.transportista,
        "remitente": pesaje.remitente,
        "cliente_destino": pesaje.cliente_destino,
        "producto": pesaje.producto,
        "material": pesaje.material,
        "numero_guia": pesaje.numero_guia,
        "chofer": pesaje.chofer,
        "peso_bruto": float(pesaje.peso_bruto),
        "peso_tara": float(pesaje.peso_tara),
        "peso_neto": float(pesaje.peso_neto),
        "operario": pesaje.operario,
        "observaciones": pesaje.observaciones,
    }

    # Generar PDF
    from app.tasks.reportes import generar_ticket_pesaje_pdf
    pdf_buffer = generar_ticket_pesaje_pdf(pesaje_data)

    # Nombre del archivo
    filename = f"ticket_pesaje_{pesaje.numero_pesaje}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
