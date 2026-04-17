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
    PesajePendienteSchema, BusquedaPatenteResult,
    PesajeCancelarCreate, PesajeCanceladoSchema,
    HistorialPesajeSchema
)
from app.services import pesaje_service

router = APIRouter()


@router.get("/", response_model=List[PesajeSchema])
async def listar_pesajes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente, completado, cancelado, todos"),
    incluir_cancelados: bool = Query(False, description="Incluir pesajes cancelados"),
    solo_cancelados: bool = Query(False, description="Solo pesajes cancelados (para auditoría)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista todos los pesajes con paginación.

    Por defecto NO incluye pesajes cancelados.
    - incluir_cancelados=true: Incluye cancelados junto con los demás
    - solo_cancelados=true: Solo muestra cancelados (para auditoría)
    """
    return pesaje_service.obtener_todos(db, skip, limit, incluir_cancelados, solo_cancelados)


@router.get("/pendientes", response_model=List[PesajePendienteSchema])
async def listar_pesajes_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista pesajes pendientes (solo tara registrada, esperando peso bruto).

    NOTA: Automáticamente marca como 'expirado' los pesajes pendientes con más de 7 días.
    Los pesajes expirados se pueden ver en la sección "No Concretados".
    """
    # Marcar como expirados los pesajes pendientes viejos (más de 7 días)
    pesaje_service.limpiar_pesajes_pendientes_viejos(db, dias_limite=7)

    return pesaje_service.obtener_pendientes(db)


@router.get("/no-concretados", response_model=List[PesajeSchema])
async def listar_pesajes_no_concretados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista pesajes no concretados (cancelados y expirados).

    Incluye:
    - Pesajes cancelados manualmente
    - Pesajes expirados (pendientes que no se completaron en 7 días)

    Desde esta vista se pueden eliminar definitivamente si es necesario.
    """
    return pesaje_service.obtener_no_concretados(db, skip, limit)


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


@router.post("/{pesaje_id}/cancelar", response_model=PesajeSchema)
async def cancelar_pesaje(
    pesaje_id: UUID,
    datos: PesajeCancelarCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Cancela un pesaje (soft-delete con auditoría obligatoria)

    **Requiere rol:** Administrador

    IMPORTANTE:
    - El pesaje NO se elimina, se marca como 'cancelado'
    - Es OBLIGATORIO proporcionar un motivo (mínimo 10 caracteres)
    - Se registra quién canceló y cuándo
    - Si era un pesaje completado con cliente, se revierte en cuenta corriente
    - Los pesajes cancelados siguen visibles con filtro especial

    Esto garantiza trazabilidad completa y evita manipulaciones.
    """
    return pesaje_service.cancelar_pesaje(db, pesaje_id, datos, current_user.id)


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
async def eliminar_pesaje_permanente(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina PERMANENTEMENTE un pesaje (solo casos excepcionales)

    **Requiere rol:** Administrador

    ADVERTENCIA: Esto elimina el registro completamente de la base de datos.
    Para cancelaciones normales, usar POST /{pesaje_id}/cancelar que hace soft-delete
    con auditoría completa.

    Solo usar este endpoint en casos excepcionales donde sea necesario
    eliminar completamente un registro (ej: datos de prueba).
    """
    from fastapi import HTTPException
    import traceback
    try:
        return pesaje_service.eliminar_permanente(db, pesaje_id)
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


@router.delete("/pendientes/limpiar-viejos")
async def limpiar_pesajes_pendientes_viejos(
    dias: int = Query(1, ge=1, le=30, description="Días máximos de antigüedad"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Elimina pesajes pendientes que tienen más de X días sin completarse.

    **Requiere rol:** Administrador

    Los pesajes pendientes son aquellos donde solo se registró la tara
    pero nunca se completó con el peso bruto.

    Por defecto elimina pesajes con más de 1 día de antigüedad.
    """
    return pesaje_service.limpiar_pesajes_pendientes_viejos(db, dias)


@router.get("/pendientes/viejos")
async def obtener_pesajes_pendientes_viejos(
    dias: int = Query(1, ge=1, le=30, description="Días máximos de antigüedad"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista pesajes pendientes que tienen más de X días sin completarse.
    Útil para revisar antes de eliminar.
    """
    return pesaje_service.obtener_pesajes_pendientes_viejos(db, dias)


@router.post("/{pesaje_id}/sincronizar-cuenta-corriente")
async def sincronizar_cuenta_corriente(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Sincroniza un pesaje existente con la cuenta corriente del cliente.

    **Requiere rol:** Administrador

    Útil para:
    - Pesajes históricos que no tienen movimiento registrado
    - Pesajes que por algún error no se registraron en cuenta corriente

    Retorna el estado de la sincronización:
    - "creado": Se creó el movimiento
    - "ya_existe": Ya existía un movimiento para este pesaje
    - "sin_cliente": El pesaje no tiene cliente asignado
    - "no_completado": El pesaje no está completado
    """
    return pesaje_service.sincronizar_pesaje_cuenta_corriente(db, pesaje_id, current_user.id)


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

    # Usar la fecha del pesaje (puede ser fecha manual/vieja), con hora de fecha_completado si existe
    fecha_pesaje = pesaje.fecha

    # Calcular peso en toneladas
    peso_neto_kg = float(pesaje.peso_neto) if pesaje.peso_neto else 0
    peso_neto_tn = peso_neto_kg / 1000

    # Buscar factor de conversión a m³ en la lista de precios del cliente
    factor_conversion = None
    cantidad_m3 = None
    unidad_facturacion = "tn"
    precio_unitario = float(pesaje.precio_unitario) if pesaje.precio_unitario else None
    importe_total = float(pesaje.importe_total) if pesaje.importe_total else None

    # Obtener lista de precios del cliente o del pesaje
    lista_precio = None
    if pesaje.lista_precio_id:
        from app.models.lista_precio import ListaPrecio
        lista_precio = db.query(ListaPrecio).filter(ListaPrecio.id == pesaje.lista_precio_id).first()
    elif pesaje.cliente_id:
        # Buscar lista de precios asignada al cliente
        from app.models.empresa import Empresa
        cliente = db.query(Empresa).filter(Empresa.id == pesaje.cliente_id).first()
        if cliente and cliente.lista_precio_id:
            from app.models.lista_precio import ListaPrecio
            lista_precio = db.query(ListaPrecio).filter(ListaPrecio.id == cliente.lista_precio_id).first()

    # Si hay lista de precios, buscar el factor de conversión para el material
    if lista_precio and pesaje.material:
        item_precio = lista_precio.obtener_precio_material(pesaje.material)
        if item_precio and item_precio.factor_conversion_m3:
            factor_conversion = float(item_precio.factor_conversion_m3)
            cantidad_m3 = peso_neto_tn / factor_conversion
            unidad_facturacion = "m3"

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
        "peso_neto": peso_neto_kg,
        "peso_neto_tn": peso_neto_tn,
        "operario": pesaje.operario,
        "observaciones": pesaje.observaciones,
        # Datos de conversión y precio
        "factor_conversion": factor_conversion,
        "cantidad_m3": cantidad_m3,
        "unidad_facturacion": unidad_facturacion,
        "precio_unitario": precio_unitario,
        "importe_total": importe_total,
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


@router.get("/{pesaje_id}/historial", response_model=List[HistorialPesajeSchema])
async def obtener_historial_pesaje(
    pesaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el historial de modificaciones de un pesaje.

    Retorna lista de acciones: CREACION, MODIFICACION, ELIMINACION
    Con fecha, hora y nombre del usuario que realizó la acción.
    """
    return pesaje_service.obtener_historial(db, pesaje_id)
