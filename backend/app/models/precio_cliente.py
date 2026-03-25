"""
Modelo para precios por cliente y material.
Permite precargar precios para cada combinación cliente-material,
incluyendo factor de conversión a m³ para clientes que facturan por volumen.
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PrecioCliente(BaseModel):
    """
    Precio preconfigurado por cliente y material.

    Permite:
    - Definir precio por tonelada para cada cliente+material
    - Opcionalmente definir factor de conversión a m³ (ej: para HORIZONTE)

    El factor_conversion_m3 se usa así:
    - Material 0-20: factor = 1.66 (toneladas ÷ 1.66 = m³)
    - Material 6-19: factor = 1.5 (toneladas ÷ 1.5 = m³)

    Si el cliente tiene factor_conversion_m3 definido:
    - El importe se calcula: (toneladas / factor) × precio_unitario
    - Donde precio_unitario es el precio por m³
    """

    __tablename__ = "precios_cliente"

    # Relación con empresa (cliente)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False, index=True)

    # Material (debe coincidir con MATERIALES_DISPONIBLES del schema de pesaje)
    material = Column(String(100), nullable=False, index=True)

    # Precio por unidad (tonelada o m³ si usa conversión)
    precio_unitario = Column(Numeric(12, 2), nullable=False)

    # Factor de conversión a m³ (opcional)
    # Si está definido, el precio_unitario es por m³
    # Fórmula: m³ = toneladas / factor_conversion_m3
    factor_conversion_m3 = Column(Numeric(6, 3), nullable=True)

    # Relaciones
    cliente = relationship("Empresa", backref="precios")

    # Constraint: único cliente+material
    __table_args__ = (
        UniqueConstraint('cliente_id', 'material', name='uq_precio_cliente_material'),
    )

    def __repr__(self):
        return f"<PrecioCliente {self.cliente_id} - {self.material}: ${self.precio_unitario}>"

    def calcular_importe(self, peso_neto_kg: float) -> dict:
        """
        Calcula el importe para un peso neto dado.

        Returns:
            dict con:
            - importe: monto calculado
            - cantidad: cantidad facturada (toneladas o m³)
            - unidad: 'tn' o 'm3'
            - precio_unitario: precio por unidad
        """
        from decimal import Decimal

        peso_tn = Decimal(str(peso_neto_kg)) / Decimal("1000")

        if self.factor_conversion_m3:
            # Convertir a m³
            cantidad_m3 = peso_tn / self.factor_conversion_m3
            importe = cantidad_m3 * self.precio_unitario
            return {
                "importe": float(importe),
                "cantidad": float(cantidad_m3),
                "unidad": "m3",
                "precio_unitario": float(self.precio_unitario),
                "peso_toneladas": float(peso_tn),
                "factor_conversion": float(self.factor_conversion_m3)
            }
        else:
            # Precio por tonelada
            importe = peso_tn * self.precio_unitario
            return {
                "importe": float(importe),
                "cantidad": float(peso_tn),
                "unidad": "tn",
                "precio_unitario": float(self.precio_unitario),
                "peso_toneladas": float(peso_tn),
                "factor_conversion": None
            }
