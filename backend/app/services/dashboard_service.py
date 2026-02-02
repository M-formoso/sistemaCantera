"""
Servicio de lógica de negocio para Dashboard
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any
from decimal import Decimal
from datetime import date, datetime, timedelta

from app.models.pesaje import Pesaje
from app.models.camion import Camion
from app.models.repuesto import Repuesto
from app.models.servicio import Servicio, EstadoServicioEnum
from app.services import combustible_service


def obtener_resumen_dia(db: Session) -> Dict[str, Any]:
    """
    Obtiene el resumen de operaciones del día actual

    Este es el endpoint principal del dashboard que muestra:
    - Pesajes del día
    - Nivel de combustible
    - Estado de camiones
    - Alertas
    - Servicios próximos
    - Últimos pesajes

    Returns:
        Diccionario con todos los datos del dashboard
    """
    hoy = date.today()

    # ===== PESAJES DEL DÍA =====
    pesajes_hoy = db.query(Pesaje).filter(
        func.date(Pesaje.fecha) == hoy
    ).all()

    total_pesajes = len(pesajes_hoy)
    total_kg = sum(p.peso_neto for p in pesajes_hoy)
    total_toneladas = total_kg / Decimal("1000")

    # ===== NIVEL DE COMBUSTIBLE =====
    cisterna = combustible_service.obtener_cisterna(db)

    if cisterna:
        nivel_actual = cisterna.nivel_actual
        capacidad_total = cisterna.capacidad_total
        porcentaje = (nivel_actual / capacidad_total * 100) if capacidad_total > 0 else Decimal("0")
        esta_bajo = nivel_actual <= cisterna.nivel_alerta
    else:
        nivel_actual = Decimal("0")
        capacidad_total = Decimal("0")
        porcentaje = Decimal("0")
        esta_bajo = True

    # ===== ESTADO DE CAMIONES =====
    camiones = db.query(Camion).filter(Camion.activo == True).all()

    camiones_operativos = sum(1 for c in camiones if c.estado.value == 'operativo')
    camiones_en_servicio = sum(1 for c in camiones if c.estado.value == 'en_servicio')
    camiones_fuera_servicio = sum(1 for c in camiones if c.estado.value == 'fuera_servicio')

    # ===== ALERTAS =====
    # Repuestos bajo stock
    repuestos_bajos = db.query(Repuesto).filter(
        Repuesto.stock_actual <= Repuesto.stock_minimo,
        Repuesto.activo == True
    ).count()

    # Servicios próximos (próximos 7 días)
    proximos_7_dias = hoy + timedelta(days=7)
    servicios_proximos_count = db.query(Servicio).filter(
        Servicio.estado == EstadoServicioEnum.PROGRAMADO,
        Servicio.fecha >= hoy,
        Servicio.fecha <= proximos_7_dias
    ).count()

    # ===== SERVICIOS PRÓXIMOS (lista detallada) =====
    servicios_proximos = db.query(Servicio).filter(
        Servicio.estado == EstadoServicioEnum.PROGRAMADO,
        Servicio.fecha >= hoy,
        Servicio.fecha <= proximos_7_dias
    ).order_by(Servicio.fecha).limit(5).all()

    servicios_proximos_lista = [
        {
            "id": str(s.id),
            "camion_patente": s.camion.patente,
            "fecha": s.fecha.isoformat(),
            "tipo": s.tipo.value,
            "descripcion": s.descripcion[:100]  # Truncar descripción
        }
        for s in servicios_proximos
    ]

    # ===== ÚLTIMOS PESAJES =====
    ultimos_pesajes = db.query(Pesaje).order_by(desc(Pesaje.fecha)).limit(10).all()

    ultimos_pesajes_lista = [
        {
            "id": str(p.id),
            "numero_pesaje": p.numero_pesaje,
            "fecha": p.fecha.isoformat(),
            "camion_patente": p.camion.patente,
            "material": p.material or "No especificado",
            "peso_neto": float(p.peso_neto),
            "cliente_destino": p.cliente_destino or "No especificado"
        }
        for p in ultimos_pesajes
    ]

    # ===== CONSTRUIR RESPUESTA =====
    return {
        "pesajes": {
            "cantidad": total_pesajes,
            "toneladas": float(round(total_toneladas, 2))
        },
        "combustible": {
            "nivel_actual": float(nivel_actual),
            "capacidad_total": float(capacidad_total),
            "porcentaje": float(round(porcentaje, 1)),
            "esta_bajo": esta_bajo
        },
        "camiones": {
            "operativos": camiones_operativos,
            "en_servicio": camiones_en_servicio,
            "fuera_servicio": camiones_fuera_servicio,
            "total": len(camiones)
        },
        "alertas": {
            "repuestos_bajo_stock": repuestos_bajos,
            "servicios_proximos": servicios_proximos_count,
            "nivel_combustible_bajo": esta_bajo
        },
        "servicios_proximos": servicios_proximos_lista,
        "ultimos_pesajes": ultimos_pesajes_lista
    }


def obtener_estadisticas_mes(db: Session) -> Dict[str, Any]:
    """
    Obtiene estadísticas del mes actual

    Returns:
        Diccionario con estadísticas mensuales
    """
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)

    # Pesajes del mes
    pesajes_mes = db.query(Pesaje).filter(
        func.date(Pesaje.fecha) >= primer_dia_mes
    ).all()

    total_pesajes_mes = len(pesajes_mes)
    total_kg_mes = sum(p.peso_neto for p in pesajes_mes)
    total_toneladas_mes = total_kg_mes / Decimal("1000")

    # Combustible del mes
    from app.models.combustible import SuministroCombustible
    suministros_mes = db.query(SuministroCombustible).filter(
        func.date(SuministroCombustible.fecha) >= primer_dia_mes
    ).all()

    total_combustible_mes = sum(s.litros for s in suministros_mes)

    # Servicios del mes
    servicios_mes = db.query(Servicio).filter(
        Servicio.fecha >= primer_dia_mes
    ).all()

    total_servicios_mes = len(servicios_mes)
    costo_total_servicios = sum(s.costo_total for s in servicios_mes)

    return {
        "total_pesajes_mes": total_pesajes_mes,
        "total_toneladas_mes": float(round(total_toneladas_mes, 2)),
        "total_combustible_mes": float(total_combustible_mes),
        "total_servicios_mes": total_servicios_mes,
        "costo_total_servicios": float(costo_total_servicios)
    }
