"""
Modelos para Listas de Precios.

Una ListaPrecio es un conjunto de precios por material que se puede
asignar a cualquier cliente al momento de realizar un pesaje.

Ejemplo de uso:
- "Lista Mayorista" con precios especiales
- "Lista Minorista" con precios estándar
- "Lista Especial Cliente X" con precios negociados
"""
from sqlalchemy import Column, String, Boolean, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ListaPrecio(BaseModel):
    """
    Lista de precios con nombre.
    Contiene múltiples items (uno por cada material con su precio).
    """
    __tablename__ = "listas_precios"

    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False, index=True)

    # Relación con los items de la lista
    items = relationship(
        "ItemListaPrecio",
        back_populates="lista",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self):
        return f"<ListaPrecio {self.nombre}>"

    def obtener_precio_material(self, material: str):
        """
        Obtiene el item de precio para un material específico.
        Retorna None si no hay precio para ese material.
        """
        for item in self.items:
            if item.material.lower() == material.lower():
                return item
        return None


class ItemListaPrecio(BaseModel):
    """
    Item individual de una lista de precios.
    Define el precio y factor de conversión para un material específico.
    """
    __tablename__ = "items_lista_precio"

    # Relación con la lista
    lista_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listas_precios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Material (debe coincidir con MATERIALES_DISPONIBLES)
    material = Column(String(100), nullable=False, index=True)

    # Precio por unidad (tonelada o m³ si usa conversión)
    precio_unitario = Column(Numeric(12, 2), nullable=False)

    # Factor de conversión a m³ (opcional)
    # Si está definido, el precio_unitario es por m³
    # Fórmula: m³ = toneladas / factor_conversion_m3
    # Ejemplos: 0-20 usa 1.66, 6-19 usa 1.5
    factor_conversion_m3 = Column(Numeric(6, 3), nullable=True)

    # Relaciones
    lista = relationship("ListaPrecio", back_populates="items")

    # Constraint: único material por lista
    __table_args__ = (
        UniqueConstraint('lista_id', 'material', name='uq_item_lista_material'),
    )

    def __repr__(self):
        return f"<ItemListaPrecio {self.material}: ${self.precio_unitario}>"

    def calcular_importe(self, peso_neto_kg: float) -> dict:
        """
        Calcula el importe para un peso neto dado.

        Returns:
            dict con:
            - importe: monto calculado
            - cantidad: cantidad facturada (toneladas o m³)
            - unidad: 'tn' o 'm3'
            - precio_unitario: precio por unidad
            - peso_toneladas: peso en toneladas
            - factor_conversion: factor usado (o None)
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
