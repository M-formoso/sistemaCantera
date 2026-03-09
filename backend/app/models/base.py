from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import pytz

from app.db.base import Base

# Zona horaria de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')


def get_argentina_now():
    """Retorna la fecha y hora actual en Argentina"""
    return datetime.now(ARGENTINA_TZ).replace(tzinfo=None)


class BaseModel(Base):
    """Modelo base con campos comunes"""

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=get_argentina_now, nullable=False)
    updated_at = Column(DateTime, default=get_argentina_now, onupdate=get_argentina_now, nullable=False)
