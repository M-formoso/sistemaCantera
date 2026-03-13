from sqlalchemy import Column, String, Integer, Boolean, Numeric, Enum as SQLEnum, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class CategoriaEquipoEnum(str, enum.Enum):
    """Categoría: Camión o Máquina"""
    CAMION = "camion"
    MAQUINA = "maquina"


class TipoCamionEnum(str, enum.Enum):
    """Tipos de camión"""
    VOLCADOR = "volcador"
    ACOPLADO = "acoplado"
    MIXER = "mixer"
    OTRO = "otro"


class TipoMaquinaEnum(str, enum.Enum):
    """Tipos de máquina"""
    PALA_CARGADORA = "pala_cargadora"
    RETROEXCAVADORA = "retroexcavadora"
    EXCAVADORA = "excavadora"
    MOTONIVELADORA = "motoniveladora"
    COMPACTADORA = "compactadora"
    TRITURADORA = "trituradora"
    GENERADOR = "generador"
    BOMBA = "bomba"
    OTRO = "otro"


class EstadoCamionEnum(str, enum.Enum):
    """Estados de camión/máquina"""
    OPERATIVO = "operativo"
    EN_SERVICIO = "en_servicio"
    FUERA_SERVICIO = "fuera_servicio"


class Camion(BaseModel):
    """Modelo de Camión/Máquina (equipo unificado)"""

    __tablename__ = "camiones"

    # Tipo de equipo: camión o máquina
    categoria = Column(String(20), default="camion", nullable=False)

    # Identificación
    patente = Column(String(20), unique=True, nullable=True, index=True)  # Nullable para máquinas sin patente
    nombre = Column(String(100))  # Nombre del equipo (especialmente para máquinas)
    codigo_interno = Column(String(50))  # Código interno de la empresa

    marca = Column(String(100))
    modelo = Column(String(100))
    año = Column(Integer)
    numero_serie = Column(String(100))  # Número de serie/chasis

    # Tipo específico
    tipo = Column(SQLEnum(TipoCamionEnum), default=TipoCamionEnum.VOLCADOR)
    tipo_maquina = Column(String(50), nullable=True)  # Para máquinas

    estado = Column(SQLEnum(EstadoCamionEnum), default=EstadoCamionEnum.OPERATIVO, nullable=False)

    # Métricas - Camiones usan km, Máquinas usan horas
    kilometraje_actual = Column(Integer, default=0)
    horometro_actual = Column(Numeric(10, 2), default=0)  # Horas de uso
    horas_promedio_diarias = Column(Numeric(5, 2), default=0)  # Horas promedio por día

    chofer_habitual = Column(String(100))  # Operador habitual
    foto = Column(String(500))  # URL de Cloudinary
    observaciones = Column(Text)
    activo = Column(Boolean, default=True, nullable=False)

    # Campos de servicio
    ultimo_servicio = Column(Date, nullable=True)
    ultimo_servicio_km = Column(Integer, nullable=True)
    ultimo_servicio_horas = Column(Numeric(10, 2), nullable=True)  # Para máquinas
    proximo_servicio_km = Column(Integer, nullable=True)
    proximo_servicio_horas = Column(Numeric(10, 2), nullable=True)  # Para máquinas
    proximo_servicio_fecha = Column(Date, nullable=True)
    intervalo_servicio_km = Column(Integer, default=10000)  # Cada cuántos km hacer servicio
    intervalo_servicio_horas = Column(Integer, default=250)  # Cada cuántas horas hacer servicio
    intervalo_servicio_dias = Column(Integer, default=90)  # Cada cuántos días hacer servicio (por fecha)

    # Documentación (URLs de Cloudinary)
    tarjeta_verde_url = Column(String(500))
    tarjeta_verde_vencimiento = Column(Date)
    seguro_url = Column(String(500))
    seguro_compania = Column(String(100))
    seguro_poliza = Column(String(100))
    seguro_vencimiento = Column(Date)
    vtv_url = Column(String(500))
    vtv_vencimiento = Column(Date)
    cedula_url = Column(String(500))  # Cédula verde/azul

    # Relaciones
    servicios = relationship("Servicio", back_populates="camion")
    pesajes = relationship("Pesaje", back_populates="camion")
    suministros_combustible = relationship("SuministroCombustible", back_populates="camion")
    documentos = relationship("DocumentoEquipo", back_populates="equipo", cascade="all, delete-orphan")

    # Nueva relación N:N con repuestos compatibles
    repuestos_compatibles = relationship("RepuestoEquipo", back_populates="camion", cascade="all, delete-orphan")

    def __repr__(self):
        identificador = self.patente or self.nombre or self.codigo_interno
        return f"<Equipo {identificador}>"


class TipoDocumentoEnum(str, enum.Enum):
    """Tipos de documento para equipos"""
    TARJETA_VERDE = "tarjeta_verde"
    SEGURO = "seguro"
    VTV = "vtv"
    CEDULA = "cedula"
    TITULO = "titulo"
    HABILITACION = "habilitacion"
    MANUAL = "manual"
    FACTURA_COMPRA = "factura_compra"
    OTRO = "otro"


class DocumentoEquipo(BaseModel):
    """Documentos adjuntos a equipos (camiones/máquinas)"""

    __tablename__ = "documentos_equipo"

    equipo_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    archivo_url = Column(String(500), nullable=False)
    archivo_nombre = Column(String(255))
    archivo_tipo = Column(String(50))  # MIME type
    archivo_tamaño = Column(Integer)  # bytes
    fecha_vencimiento = Column(Date)
    notas = Column(Text)

    # Relaciones
    equipo = relationship("Camion", back_populates="documentos")
