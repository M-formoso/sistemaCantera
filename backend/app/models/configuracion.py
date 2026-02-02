from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Configuracion(BaseModel):
    """Modelo de Configuración del Sistema"""

    __tablename__ = "configuracion"

    clave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(JSON, nullable=False)
    descripcion = Column(Text)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    def __repr__(self):
        return f"<Configuracion {self.clave}>"
