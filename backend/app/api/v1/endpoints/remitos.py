"""
Endpoints API para Remitos
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Literal
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin_or_operador, require_admin
from app.models.usuario import Usuario
from app.schemas.remito import RemitoSchema, RemitoCreate, RemitoFromPesaje
from app.services import remito_service
from app.tasks.reportes import generar_ticket_pesaje_pdf

router = APIRouter()


@router.get("/", response_model=List[RemitoSchema])
async def listar_remitos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los remitos con paginación"""
    return remito_service.obtener_todos(db, skip, limit)


@router.post("/", response_model=RemitoSchema, status_code=201)
async def crear_remito(
    remito: RemitoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Crea un remito manualmente

    **Requiere rol:** Administrador u Operador

    - El número de remito se asigna automáticamente
    """
    return remito_service.crear(db, remito, current_user.id)


@router.post("/generar-desde-pesaje", response_model=RemitoSchema, status_code=201)
async def generar_remito_desde_pesaje(
    data: RemitoFromPesaje,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_operador)
):
    """
    Genera un remito automáticamente desde un pesaje

    **Requiere rol:** Administrador u Operador

    Este es el flujo principal de generación de remitos:
    - Toma los datos del pesaje
    - Crea el remito con número autoincremental
    - Marca el pesaje como procesado
    - Genera PDF en background (Celery)
    """
    return remito_service.generar_desde_pesaje(db, data.pesaje_id, current_user.id)


@router.get("/{remito_id}", response_model=RemitoSchema)
async def obtener_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un remito específico por ID"""
    remito = remito_service.obtener_por_id(db, remito_id)

    if not remito:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remito no encontrado"
        )

    return remito


@router.delete("/{remito_id}")
async def eliminar_remito(
    remito_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina un remito

    **Requiere rol:** Administrador u Operador

    Al eliminar, desmarca el pesaje asociado como no procesado
    """
    return remito_service.eliminar(db, remito_id)


@router.get("/{remito_id}/pdf")
async def descargar_pdf_remito(
    remito_id: UUID,
    tipo: Literal["original", "duplicado", "triplicado"] = Query("original", description="Tipo de copia"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descarga el PDF del remito/ticket de pesaje

    **Parámetros:**
    - tipo: "original", "duplicado" o "triplicado" (aparece en el encabezado del documento)
    """
    remito = remito_service.obtener_por_id(db, remito_id)

    if not remito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remito no encontrado"
        )

    # Obtener datos del pesaje asociado
    pesaje_data = {}
    if remito.pesaje:
        pesaje = remito.pesaje
        pesaje_data = {
            "numero_pesaje": pesaje.numero_pesaje,
            "fecha": pesaje.fecha,
            "camion_patente": pesaje.camion.patente if pesaje.camion else (pesaje.patente_externa or "-"),
            "acoplado": pesaje.acoplado,
            "transportista": pesaje.transportista,
            "remitente": pesaje.remitente,
            "cliente_destino": pesaje.cliente_destino,
            "producto": pesaje.producto,
            "material": pesaje.material,
            "numero_guia": pesaje.numero_guia,
            "chofer": pesaje.chofer,
            "peso_bruto": pesaje.peso_bruto,
            "peso_tara": pesaje.peso_tara,
            "peso_neto": pesaje.peso_neto,
            "operario": pesaje.operario,
            "observaciones": pesaje.observaciones,
        }

    # Generar PDF con el tipo de copia
    pdf_buffer = generar_ticket_pesaje_pdf(pesaje_data, tipo_copia=tipo)

    # Nombre del archivo
    filename = f"remito_{remito.numero_remito}_{tipo}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
