"""
Servicio de lógica de negocio para Precios por Cliente
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.precio_cliente import PrecioCliente
from app.models.empresa import Empresa
from app.schemas.precio_cliente import PrecioClienteCreate, PrecioClienteUpdate


def obtener_todos(db: Session, skip: int = 0, limit: int = 100) -> List[PrecioCliente]:
    """Obtiene todos los precios con paginación"""
    precios = db.query(PrecioCliente).offset(skip).limit(limit).all()

    # Enriquecer con nombre de cliente
    for precio in precios:
        cliente = db.query(Empresa).filter(Empresa.id == precio.cliente_id).first()
        if cliente:
            precio.cliente_nombre = cliente.nombre

    return precios


def obtener_por_cliente(db: Session, cliente_id: UUID) -> List[PrecioCliente]:
    """Obtiene todos los precios de un cliente"""
    precios = db.query(PrecioCliente).filter(
        PrecioCliente.cliente_id == cliente_id
    ).all()

    # Obtener nombre del cliente
    cliente = db.query(Empresa).filter(Empresa.id == cliente_id).first()
    cliente_nombre = cliente.nombre if cliente else None

    for precio in precios:
        precio.cliente_nombre = cliente_nombre

    return precios


def obtener_por_cliente_material(
    db: Session,
    cliente_id: UUID,
    material: str
) -> Optional[PrecioCliente]:
    """
    Obtiene el precio configurado para un cliente y material específico.
    Retorna None si no hay precio configurado.
    """
    precio = db.query(PrecioCliente).filter(
        PrecioCliente.cliente_id == cliente_id,
        func.lower(PrecioCliente.material) == material.lower()
    ).first()

    if precio:
        cliente = db.query(Empresa).filter(Empresa.id == cliente_id).first()
        if cliente:
            precio.cliente_nombre = cliente.nombre

    return precio


def crear(db: Session, precio_data: PrecioClienteCreate, usuario_id: UUID) -> PrecioCliente:
    """Crea un nuevo precio para cliente+material"""

    # Verificar que el cliente existe
    cliente = db.query(Empresa).filter(Empresa.id == precio_data.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Verificar que no exista ya un precio para este cliente+material
    existente = db.query(PrecioCliente).filter(
        PrecioCliente.cliente_id == precio_data.cliente_id,
        func.lower(PrecioCliente.material) == precio_data.material.lower()
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un precio para {cliente.nombre} - {precio_data.material}"
        )

    # Crear precio
    db_precio = PrecioCliente(
        cliente_id=precio_data.cliente_id,
        material=precio_data.material,
        precio_unitario=precio_data.precio_unitario,
        factor_conversion_m3=precio_data.factor_conversion_m3,
        created_by=usuario_id
    )

    db.add(db_precio)
    db.commit()
    db.refresh(db_precio)

    db_precio.cliente_nombre = cliente.nombre

    return db_precio


def actualizar(
    db: Session,
    precio_id: UUID,
    precio_data: PrecioClienteUpdate
) -> PrecioCliente:
    """Actualiza un precio existente"""

    db_precio = db.query(PrecioCliente).filter(PrecioCliente.id == precio_id).first()

    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Precio no encontrado"
        )

    update_data = precio_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_precio, field, value)

    db.commit()
    db.refresh(db_precio)

    # Enriquecer con nombre de cliente
    cliente = db.query(Empresa).filter(Empresa.id == db_precio.cliente_id).first()
    if cliente:
        db_precio.cliente_nombre = cliente.nombre

    return db_precio


def eliminar(db: Session, precio_id: UUID) -> dict:
    """Elimina un precio"""

    db_precio = db.query(PrecioCliente).filter(PrecioCliente.id == precio_id).first()

    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Precio no encontrado"
        )

    db.delete(db_precio)
    db.commit()

    return {"message": "Precio eliminado correctamente"}


def calcular_importe(
    db: Session,
    cliente_id: UUID,
    material: str,
    peso_neto_kg: float
) -> dict:
    """
    Calcula el importe para un cliente, material y peso dado.

    Retorna:
    - Si hay precio configurado: diccionario con cálculo completo
    - Si no hay precio: diccionario con precio_encontrado=False
    """
    precio = obtener_por_cliente_material(db, cliente_id, material)

    if not precio:
        return {
            "precio_encontrado": False,
            "mensaje": "No hay precio configurado para este cliente y material"
        }

    # Usar el método del modelo para calcular
    calculo = precio.calcular_importe(peso_neto_kg)
    calculo["precio_encontrado"] = True
    calculo["material"] = material

    return calculo


def crear_multiples(
    db: Session,
    cliente_id: UUID,
    precios: List[dict],
    usuario_id: UUID
) -> List[PrecioCliente]:
    """
    Crea o actualiza múltiples precios para un cliente.
    Útil para configurar todos los precios de un cliente de una vez.

    precios: Lista de dicts con {material, precio_unitario, factor_conversion_m3?}
    """
    cliente = db.query(Empresa).filter(Empresa.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    resultados = []

    for precio_data in precios:
        material = precio_data.get("material")
        precio_unitario = precio_data.get("precio_unitario")
        factor_conversion = precio_data.get("factor_conversion_m3")

        if not material or precio_unitario is None:
            continue

        # Buscar si ya existe
        existente = db.query(PrecioCliente).filter(
            PrecioCliente.cliente_id == cliente_id,
            func.lower(PrecioCliente.material) == material.lower()
        ).first()

        if existente:
            # Actualizar
            existente.precio_unitario = Decimal(str(precio_unitario))
            existente.factor_conversion_m3 = Decimal(str(factor_conversion)) if factor_conversion else None
            existente.cliente_nombre = cliente.nombre
            resultados.append(existente)
        else:
            # Crear nuevo
            nuevo = PrecioCliente(
                cliente_id=cliente_id,
                material=material,
                precio_unitario=Decimal(str(precio_unitario)),
                factor_conversion_m3=Decimal(str(factor_conversion)) if factor_conversion else None,
                created_by=usuario_id
            )
            db.add(nuevo)
            nuevo.cliente_nombre = cliente.nombre
            resultados.append(nuevo)

    db.commit()

    # Refresh todos
    for r in resultados:
        db.refresh(r)

    return resultados
