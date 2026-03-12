# Importar todos los modelos para que Alembic los detecte
from app.models.base import BaseModel
from app.models.usuario import Usuario
from app.models.camion import Camion, DocumentoEquipo
from app.models.repuesto import Repuesto, RepuestoEquipo
from app.models.servicio import Servicio, ServicioRepuesto
from app.models.movimiento_stock import MovimientoStock
from app.models.pesaje import Pesaje
from app.models.remito import Remito
from app.models.combustible import CisternaCombustible, CargaCisterna, SuministroCombustible
from app.models.configuracion import Configuracion
from app.models.empresa import Empresa
from app.models.finanzas import CategoriaFinanzas, MovimientoFinanciero, CuentaBancaria
from app.models.orden_entrega import OrdenEntrega
from app.models.camion_cliente import CamionCliente
from app.models.cuenta_corriente import MovimientoCuentaCorriente, CobroCliente, ItemCobroCliente
from app.models.trabajo import Trabajo, TrabajoRepuesto
from app.models.factura import Factura, PagoFactura, PagoRemito, factura_remito

__all__ = [
    "BaseModel",
    "Usuario",
    "Camion",
    "DocumentoEquipo",
    "Repuesto",
    "RepuestoEquipo",
    "Servicio",
    "ServicioRepuesto",
    "MovimientoStock",
    "Pesaje",
    "Remito",
    "CisternaCombustible",
    "CargaCisterna",
    "SuministroCombustible",
    "Configuracion",
    "Empresa",
    "CategoriaFinanzas",
    "MovimientoFinanciero",
    "CuentaBancaria",
    "OrdenEntrega",
    "CamionCliente",
    "MovimientoCuentaCorriente",
    "CobroCliente",
    "ItemCobroCliente",
    "Trabajo",
    "TrabajoRepuesto",
    "Factura",
    "PagoFactura",
    "PagoRemito",
    "factura_remito",
]
