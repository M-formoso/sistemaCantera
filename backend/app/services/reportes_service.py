"""
Servicio para generación de Reportes
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from app.models.pesaje import Pesaje
from app.models.empresa import Empresa
from app.models.camion import Camion
from app.models.servicio import Servicio
from app.models.combustible import SuministroCombustible, CargaCisterna
from app.models.finanzas import MovimientoFinanciero
from app.models.repuesto import Repuesto
from app.models.movimiento_stock import MovimientoStock

from app.schemas.reportes import (
    VentaPorMaterial, ReporteVentasMaterial,
    VentaPorSemana, ReporteVentasSemanal,
    GastoPorCategoria, ReporteGastos,
    MaquinaActividad, ReporteMaquinaria,
    ClienteTop, ReporteTopClientes,
    ResumenGeneral
)


def _get_fecha_default(fecha_desde: Optional[date], fecha_hasta: Optional[date]):
    """Obtiene fechas por defecto si no se especifican"""
    if not fecha_hasta:
        fecha_hasta = date.today()
    if not fecha_desde:
        # Por defecto, últimos 30 días
        fecha_desde = fecha_hasta - timedelta(days=30)
    return fecha_desde, fecha_hasta


def obtener_ventas_por_material(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> ReporteVentasMaterial:
    """
    Obtiene las ventas agrupadas por tipo de material/árido
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Query agrupado por material
    resultados = db.query(
        Pesaje.material,
        func.count(Pesaje.id).label('cantidad'),
        func.sum(Pesaje.peso_neto).label('total_kg'),
        func.sum(Pesaje.importe_total).label('importe')
    ).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado'
    ).group_by(Pesaje.material).all()

    materiales = []
    total_kg = Decimal("0")
    total_importe = Decimal("0")
    total_pesajes = 0

    for r in resultados:
        material_nombre = r.material or "Sin especificar"
        kg = r.total_kg or Decimal("0")
        importe = r.importe or Decimal("0")
        cantidad = r.cantidad or 0

        total_kg += kg
        total_importe += importe
        total_pesajes += cantidad

        precio_promedio = (importe / kg) if kg > 0 else Decimal("0")

        materiales.append(VentaPorMaterial(
            material=material_nombre,
            cantidad_pesajes=cantidad,
            total_kg=kg,
            total_toneladas=kg / Decimal("1000"),
            importe_total=importe,
            precio_promedio=round(precio_promedio, 2)
        ))

    # Ordenar por total_kg descendente
    materiales.sort(key=lambda x: x.total_kg, reverse=True)

    return ReporteVentasMaterial(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        materiales=materiales,
        total_kg=total_kg,
        total_toneladas=total_kg / Decimal("1000"),
        total_importe=total_importe,
        cantidad_pesajes=total_pesajes
    )


def obtener_ventas_semanales(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    material: Optional[str] = None
) -> ReporteVentasSemanal:
    """
    Obtiene las ventas agrupadas por semana
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Base query
    query = db.query(
        extract('isoyear', Pesaje.fecha).label('anio'),
        extract('week', Pesaje.fecha).label('semana'),
        func.count(Pesaje.id).label('cantidad'),
        func.sum(Pesaje.peso_neto).label('total_kg'),
        func.sum(Pesaje.importe_total).label('importe')
    ).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado'
    )

    if material:
        query = query.filter(Pesaje.material == material)

    resultados = query.group_by(
        extract('isoyear', Pesaje.fecha),
        extract('week', Pesaje.fecha)
    ).order_by(
        extract('isoyear', Pesaje.fecha),
        extract('week', Pesaje.fecha)
    ).all()

    semanas = []
    total_kg = Decimal("0")
    total_importe = Decimal("0")

    for r in resultados:
        anio = int(r.anio)
        semana = int(r.semana)
        kg = r.total_kg or Decimal("0")
        importe = r.importe or Decimal("0")
        cantidad = r.cantidad or 0

        total_kg += kg
        total_importe += importe

        # Calcular fechas de inicio y fin de semana
        fecha_inicio = date.fromisocalendar(anio, semana, 1)
        fecha_fin = date.fromisocalendar(anio, semana, 7)

        semanas.append(VentaPorSemana(
            semana=semana,
            anio=anio,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cantidad_pesajes=cantidad,
            total_kg=kg,
            total_toneladas=kg / Decimal("1000"),
            importe_total=importe
        ))

    return ReporteVentasSemanal(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        material=material,
        semanas=semanas,
        total_kg=total_kg,
        total_toneladas=total_kg / Decimal("1000"),
        total_importe=total_importe
    )


def obtener_reporte_gastos(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> ReporteGastos:
    """
    Obtiene el reporte de gastos por categoría
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Gastos de combustible (cargas)
    total_combustible = db.query(func.sum(CargaCisterna.costo_total)).filter(
        func.date(CargaCisterna.fecha) >= fecha_desde,
        func.date(CargaCisterna.fecha) <= fecha_hasta
    ).scalar() or Decimal("0")

    # Gastos de servicios
    total_servicios = db.query(func.sum(Servicio.costo_total)).filter(
        Servicio.fecha >= fecha_desde,
        Servicio.fecha <= fecha_hasta
    ).scalar() or Decimal("0")

    # Gastos de repuestos (movimientos de salida valorados)
    # Usamos el costo de compra de los repuestos consumidos
    total_repuestos = db.query(
        func.sum(MovimientoStock.cantidad * Repuesto.precio_compra)
    ).join(Repuesto).filter(
        MovimientoStock.tipo == 'salida',
        func.date(MovimientoStock.fecha) >= fecha_desde,
        func.date(MovimientoStock.fecha) <= fecha_hasta
    ).scalar() or Decimal("0")

    # Otros egresos de finanzas
    otros_gastos = db.query(func.sum(MovimientoFinanciero.monto)).filter(
        MovimientoFinanciero.tipo == 'egreso',
        func.date(MovimientoFinanciero.fecha) >= fecha_desde,
        func.date(MovimientoFinanciero.fecha) <= fecha_hasta
    ).scalar() or Decimal("0")

    total_gastos = total_combustible + total_servicios + total_repuestos + otros_gastos

    # Armar categorías
    categorias = []

    if total_combustible > 0:
        categorias.append(GastoPorCategoria(
            categoria="Combustible",
            cantidad=db.query(CargaCisterna).filter(
                func.date(CargaCisterna.fecha) >= fecha_desde,
                func.date(CargaCisterna.fecha) <= fecha_hasta
            ).count(),
            total=total_combustible,
            porcentaje=round((total_combustible / total_gastos * 100) if total_gastos > 0 else Decimal("0"), 2)
        ))

    if total_servicios > 0:
        categorias.append(GastoPorCategoria(
            categoria="Servicios/Mantenimiento",
            cantidad=db.query(Servicio).filter(
                Servicio.fecha >= fecha_desde,
                Servicio.fecha <= fecha_hasta
            ).count(),
            total=total_servicios,
            porcentaje=round((total_servicios / total_gastos * 100) if total_gastos > 0 else Decimal("0"), 2)
        ))

    if total_repuestos > 0:
        categorias.append(GastoPorCategoria(
            categoria="Repuestos",
            cantidad=db.query(MovimientoStock).filter(
                MovimientoStock.tipo == 'salida',
                func.date(MovimientoStock.fecha) >= fecha_desde,
                func.date(MovimientoStock.fecha) <= fecha_hasta
            ).count(),
            total=total_repuestos,
            porcentaje=round((total_repuestos / total_gastos * 100) if total_gastos > 0 else Decimal("0"), 2)
        ))

    if otros_gastos > 0:
        categorias.append(GastoPorCategoria(
            categoria="Otros Gastos",
            cantidad=db.query(MovimientoFinanciero).filter(
                MovimientoFinanciero.tipo == 'egreso',
                func.date(MovimientoFinanciero.fecha) >= fecha_desde,
                func.date(MovimientoFinanciero.fecha) <= fecha_hasta
            ).count(),
            total=otros_gastos,
            porcentaje=round((otros_gastos / total_gastos * 100) if total_gastos > 0 else Decimal("0"), 2)
        ))

    # Ordenar por total descendente
    categorias.sort(key=lambda x: x.total, reverse=True)

    return ReporteGastos(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categorias=categorias,
        total_gastos=total_gastos,
        total_combustible=total_combustible,
        total_servicios=total_servicios,
        total_repuestos=total_repuestos
    )


def obtener_reporte_maquinaria(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> ReporteMaquinaria:
    """
    Obtiene el reporte de actividad de maquinaria/camiones
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Obtener todos los camiones activos
    camiones = db.query(Camion).filter(Camion.activo == True).all()

    maquinas = []
    total_combustible = Decimal("0")
    total_costo_servicios = Decimal("0")
    maquinas_activas = 0

    for camion in camiones:
        # Pesajes del camión en el período
        pesajes = db.query(Pesaje).filter(
            Pesaje.camion_id == camion.id,
            func.date(Pesaje.fecha) >= fecha_desde,
            func.date(Pesaje.fecha) <= fecha_hasta,
            Pesaje.estado == 'completado'
        ).all()

        cantidad_pesajes = len(pesajes)
        total_kg = sum((p.peso_neto or Decimal("0")) for p in pesajes)

        # Días únicos con actividad
        dias_activos = len(set(p.fecha.date() for p in pesajes))

        # Combustible suministrado
        combustible = db.query(func.sum(SuministroCombustible.litros)).filter(
            SuministroCombustible.camion_id == camion.id,
            func.date(SuministroCombustible.fecha) >= fecha_desde,
            func.date(SuministroCombustible.fecha) <= fecha_hasta
        ).scalar() or Decimal("0")

        total_combustible += combustible

        # Servicios realizados
        servicios = db.query(Servicio).filter(
            Servicio.camion_id == camion.id,
            Servicio.fecha >= fecha_desde,
            Servicio.fecha <= fecha_hasta
        ).all()

        cantidad_servicios = len(servicios)
        costo_servicios = sum((s.costo_total or Decimal("0")) for s in servicios)
        total_costo_servicios += costo_servicios

        # Solo incluir si tuvo alguna actividad
        if cantidad_pesajes > 0 or combustible > 0 or cantidad_servicios > 0:
            maquinas_activas += 1

            identificador = camion.patente or camion.nombre or camion.codigo_interno or "Sin identificar"

            maquinas.append(MaquinaActividad(
                id=camion.id,
                identificador=identificador,
                tipo="camion",
                cantidad_pesajes=cantidad_pesajes,
                total_kg=total_kg,
                total_combustible=combustible,
                cantidad_servicios=cantidad_servicios,
                costo_servicios=costo_servicios,
                dias_activa=dias_activos
            ))

    # Ordenar por cantidad de pesajes
    maquinas.sort(key=lambda x: x.cantidad_pesajes, reverse=True)

    return ReporteMaquinaria(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        maquinas=maquinas,
        total_maquinas_activas=maquinas_activas,
        total_combustible=total_combustible,
        total_costo_servicios=total_costo_servicios
    )


def obtener_top_clientes(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limite: int = 10
) -> ReporteTopClientes:
    """
    Obtiene los clientes con más compras en el período
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Query agrupado por cliente
    resultados = db.query(
        Pesaje.cliente_id,
        func.count(Pesaje.id).label('cantidad'),
        func.sum(Pesaje.peso_neto).label('total_kg'),
        func.sum(Pesaje.importe_total).label('importe')
    ).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado',
        Pesaje.cliente_id.isnot(None)
    ).group_by(Pesaje.cliente_id).order_by(desc('total_kg')).limit(limite).all()

    # Calcular total general para porcentajes
    total_general = db.query(func.sum(Pesaje.importe_total)).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado'
    ).scalar() or Decimal("0")

    clientes = []
    total_clientes_distintos = db.query(func.count(func.distinct(Pesaje.cliente_id))).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado',
        Pesaje.cliente_id.isnot(None)
    ).scalar() or 0

    for r in resultados:
        cliente = db.query(Empresa).filter(Empresa.id == r.cliente_id).first()
        if not cliente:
            continue

        kg = r.total_kg or Decimal("0")
        importe = r.importe or Decimal("0")
        porcentaje = (importe / total_general * 100) if total_general > 0 else Decimal("0")

        clientes.append(ClienteTop(
            id=cliente.id,
            nombre=cliente.nombre,
            cantidad_pesajes=r.cantidad,
            total_kg=kg,
            total_toneladas=kg / Decimal("1000"),
            importe_total=importe,
            porcentaje_total=round(porcentaje, 2)
        ))

    return ReporteTopClientes(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        clientes=clientes,
        total_clientes=total_clientes_distintos,
        total_general=total_general
    )


def obtener_resumen_general(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> ResumenGeneral:
    """
    Obtiene un resumen general del período
    """
    fecha_desde, fecha_hasta = _get_fecha_default(fecha_desde, fecha_hasta)

    # Ventas
    ventas = db.query(
        func.count(Pesaje.id).label('cantidad'),
        func.sum(Pesaje.peso_neto).label('total_kg'),
        func.sum(Pesaje.importe_total).label('importe')
    ).filter(
        func.date(Pesaje.fecha) >= fecha_desde,
        func.date(Pesaje.fecha) <= fecha_hasta,
        Pesaje.estado == 'completado'
    ).first()

    cantidad_pesajes = ventas.cantidad or 0
    total_kg = ventas.total_kg or Decimal("0")
    importe_ventas = ventas.importe or Decimal("0")

    # Gastos
    gastos = obtener_reporte_gastos(db, fecha_desde, fecha_hasta)

    # Maquinaria activa
    maquinaria = obtener_reporte_maquinaria(db, fecha_desde, fecha_hasta)

    # Cliente top
    top_clientes = obtener_top_clientes(db, fecha_desde, fecha_hasta, limite=1)
    cliente_top = top_clientes.clientes[0] if top_clientes.clientes else None

    # Material top
    ventas_material = obtener_ventas_por_material(db, fecha_desde, fecha_hasta)
    material_top = ventas_material.materiales[0] if ventas_material.materiales else None

    return ResumenGeneral(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cantidad_pesajes=cantidad_pesajes,
        total_kg=total_kg,
        total_toneladas=total_kg / Decimal("1000"),
        importe_total_ventas=importe_ventas,
        total_gastos=gastos.total_gastos,
        gasto_combustible=gastos.total_combustible,
        gasto_servicios=gastos.total_servicios,
        gasto_repuestos=gastos.total_repuestos,
        maquinas_activas=maquinaria.total_maquinas_activas,
        cliente_top_nombre=cliente_top.nombre if cliente_top else None,
        cliente_top_kg=cliente_top.total_kg if cliente_top else None,
        material_top_nombre=material_top.material if material_top else None,
        material_top_kg=material_top.total_kg if material_top else None
    )


def obtener_materiales_disponibles(db: Session) -> List[str]:
    """
    Obtiene la lista de materiales únicos que se han pesado
    """
    materiales = db.query(Pesaje.material).filter(
        Pesaje.material.isnot(None),
        Pesaje.material != ''
    ).distinct().all()

    return sorted([m[0] for m in materiales if m[0]])
