from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "cantera_rufina",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configuración
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

# Tareas programadas (Celery Beat)
celery_app.conf.beat_schedule = {
    "verificar-nivel-cisterna-diario": {
        "task": "app.tasks.alertas.verificar_nivel_cisterna",
        "schedule": crontab(hour=8, minute=0),  # 8:00 AM diario
    },
    "verificar-servicios-proximos": {
        "task": "app.tasks.alertas.verificar_servicios_proximos",
        "schedule": crontab(hour=9, minute=0),  # 9:00 AM diario
    },
}
