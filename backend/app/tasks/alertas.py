"""
Tareas Celery para Sistema de Alertas
"""
from celery import shared_task
from app.db.session import SessionLocal
from app.services import repuesto_service, combustible_service, servicio_service
from datetime import date, timedelta


@shared_task
def crear_alerta_stock_bajo(repuesto_id: str):
    """
    Crea alerta cuando un repuesto queda bajo stock mínimo

    Esta tarea se ejecuta automáticamente cuando:
    - Se asigna un repuesto a un servicio y el stock queda bajo

    Args:
        repuesto_id: ID del repuesto (string UUID)
    """
    db = SessionLocal()
    try:
        from uuid import UUID
        repuesto = repuesto_service.obtener_por_id(db, UUID(repuesto_id))

        if not repuesto:
            return {"status": "error", "message": "Repuesto no encontrado"}

        if repuesto.stock_actual > repuesto.stock_minimo:
            return {"status": "ok", "message": "Stock OK, no requiere alerta"}

        # Aquí se podría implementar:
        # 1. Crear registro en tabla de alertas
        # 2. Enviar email a administradores
        # 3. Enviar notificación push
        # Por ahora solo loguear
        print(f"🚨 ALERTA: Stock bajo de '{repuesto.nombre}'")
        print(f"   - Stock actual: {repuesto.stock_actual} {repuesto.unidad}")
        print(f"   - Stock mínimo: {repuesto.stock_minimo} {repuesto.unidad}")
        print(f"   - Código: {repuesto.codigo}")

        return {
            "status": "alert_created",
            "repuesto_id": repuesto_id,
            "repuesto_nombre": repuesto.nombre,
            "stock_actual": float(repuesto.stock_actual),
            "stock_minimo": float(repuesto.stock_minimo)
        }

    finally:
        db.close()


@shared_task
def verificar_nivel_cisterna():
    """
    Verifica el nivel de la cisterna y crea alerta si está bajo

    Esta tarea se ejecuta:
    - Automáticamente cada día a las 8:00 AM (configurado en celery_app.py)
    - Manualmente cuando se crea un suministro que deja el nivel bajo
    """
    db = SessionLocal()
    try:
        cisterna = combustible_service.obtener_cisterna(db)

        if not cisterna:
            return {"status": "error", "message": "Cisterna no configurada"}

        if cisterna.nivel_actual > cisterna.nivel_alerta:
            return {"status": "ok", "message": "Nivel de cisterna OK"}

        # Calcular porcentaje
        porcentaje = (cisterna.nivel_actual / cisterna.capacidad_total * 100) if cisterna.capacidad_total > 0 else 0

        # Crear alerta
        print(f"🚨 ALERTA: Nivel bajo de combustible en cisterna")
        print(f"   - Nivel actual: {cisterna.nivel_actual} litros ({porcentaje:.1f}%)")
        print(f"   - Nivel de alerta: {cisterna.nivel_alerta} litros")
        print(f"   - Capacidad total: {cisterna.capacidad_total} litros")

        return {
            "status": "alert_created",
            "nivel_actual": float(cisterna.nivel_actual),
            "nivel_alerta": float(cisterna.nivel_alerta),
            "porcentaje": round(porcentaje, 1)
        }

    finally:
        db.close()


@shared_task
def verificar_servicios_proximos():
    """
    Verifica servicios programados en los próximos 7 días y crea alertas

    Esta tarea se ejecuta:
    - Automáticamente cada día a las 9:00 AM (configurado en celery_app.py)
    """
    db = SessionLocal()
    try:
        # Obtener servicios programados próximos 7 días
        servicios_proximos = servicio_service.obtener_programados(db, dias=7)

        if not servicios_proximos:
            return {"status": "ok", "message": "No hay servicios programados próximos"}

        # Agrupar por urgencia
        hoy = date.today()
        urgentes = []  # Hoy y mañana
        proximos = []  # Resto de la semana

        for servicio in servicios_proximos:
            dias_restantes = (servicio.fecha - hoy).days

            info = {
                "id": str(servicio.id),
                "camion_patente": servicio.camion.patente,
                "fecha": servicio.fecha.isoformat(),
                "tipo": servicio.tipo.value,
                "descripcion": servicio.descripcion[:100],
                "dias_restantes": dias_restantes
            }

            if dias_restantes <= 1:
                urgentes.append(info)
            else:
                proximos.append(info)

        # Crear alertas
        if urgentes:
            print(f"🚨 ALERTA: {len(urgentes)} servicios URGENTES (hoy o mañana)")
            for s in urgentes:
                print(f"   - {s['camion_patente']} - {s['tipo']} - {s['fecha']}")

        if proximos:
            print(f"📅 INFO: {len(proximos)} servicios programados esta semana")

        return {
            "status": "alerts_created",
            "total_servicios": len(servicios_proximos),
            "urgentes": urgentes,
            "proximos": proximos
        }

    finally:
        db.close()


@shared_task
def generar_reporte_diario():
    """
    Genera un reporte diario de operaciones

    Esta tarea podría ejecutarse cada noche para:
    - Resumen de pesajes del día
    - Consumo de combustible
    - Servicios realizados
    - Estado general

    Por ahora es un placeholder para futuras implementaciones
    """
    db = SessionLocal()
    try:
        from app.services import dashboard_service

        resumen = dashboard_service.obtener_resumen_dia(db)

        print(f"📊 REPORTE DIARIO - {date.today()}")
        print(f"   Pesajes: {resumen['pesajes']['cantidad']} ({resumen['pesajes']['toneladas']} tons)")
        print(f"   Combustible: {resumen['combustible']['nivel_actual']}L ({resumen['combustible']['porcentaje']}%)")
        print(f"   Camiones operativos: {resumen['camiones']['operativos']}/{resumen['camiones']['total']}")
        print(f"   Alertas: {resumen['alertas']['repuestos_bajo_stock']} repuestos bajo stock")

        return {
            "status": "report_generated",
            "fecha": date.today().isoformat(),
            "resumen": resumen
        }

    finally:
        db.close()
