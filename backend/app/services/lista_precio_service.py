"""
Servicio de lógica de negocio para Listas de Precios
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.lista_precio import ListaPrecio, ItemListaPrecio
from app.schemas.lista_precio import (
    ListaPrecioCreate,
    ListaPrecioUpdate,
    ItemListaPrecioCreate,
    ItemBatchUpdate
)


# ============== LISTAS DE PRECIOS ==============

def obtener_todas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activas: bool = False
) -> List[ListaPrecio]:
    """Obtiene todas las listas de precios con paginación"""
    query = db.query(ListaPrecio)

    if solo_activas:
        query = query.filter(ListaPrecio.activo == True)

    return query.order_by(ListaPrecio.nombre).offset(skip).limit(limit).all()


def obtener_por_id(db: Session, lista_id: UUID) -> Optional[ListaPrecio]:
    """Obtiene una lista por su ID"""
    return db.query(ListaPrecio).filter(ListaPrecio.id == lista_id).first()


def obtener_por_nombre(db: Session, nombre: str) -> Optional[ListaPrecio]:
    """Obtiene una lista por su nombre"""
    return db.query(ListaPrecio).filter(
        func.lower(ListaPrecio.nombre) == nombre.lower()
    ).first()


def crear(db: Session, lista_data: ListaPrecioCreate, usuario_id: UUID) -> ListaPrecio:
    """Crea una nueva lista de precios con sus items"""

    # Verificar que no exista una lista con el mismo nombre
    existente = obtener_por_nombre(db, lista_data.nombre)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una lista con el nombre '{lista_data.nombre}'"
        )

    # Crear la lista
    db_lista = ListaPrecio(
        nombre=lista_data.nombre,
        descripcion=lista_data.descripcion,
        activo=lista_data.activo,
        created_by=usuario_id
    )
    db.add(db_lista)
    db.flush()  # Para obtener el ID

    # Crear los items
    if lista_data.items:
        for item_data in lista_data.items:
            db_item = ItemListaPrecio(
                lista_id=db_lista.id,
                material=item_data.material,
                precio_unitario=item_data.precio_unitario,
                factor_conversion_m3=item_data.factor_conversion_m3,
                created_by=usuario_id
            )
            db.add(db_item)

    db.commit()
    db.refresh(db_lista)

    return db_lista


def actualizar(
    db: Session,
    lista_id: UUID,
    lista_data: ListaPrecioUpdate
) -> ListaPrecio:
    """Actualiza una lista de precios (sin modificar items)"""

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )

    update_data = lista_data.model_dump(exclude_unset=True)

    # Si se cambia el nombre, verificar que no exista otra con ese nombre
    if 'nombre' in update_data:
        existente = obtener_por_nombre(db, update_data['nombre'])
        if existente and existente.id != lista_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una lista con el nombre '{update_data['nombre']}'"
            )

    for field, value in update_data.items():
        setattr(db_lista, field, value)

    db.commit()
    db.refresh(db_lista)

    return db_lista


def eliminar(db: Session, lista_id: UUID) -> dict:
    """Elimina una lista de precios y todos sus items"""

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )

    # Los items se eliminan en cascada por la FK
    db.delete(db_lista)
    db.commit()

    return {"message": "Lista de precios eliminada correctamente"}


def duplicar(db: Session, lista_id: UUID, nuevo_nombre: str, usuario_id: UUID) -> ListaPrecio:
    """Duplica una lista de precios con un nuevo nombre"""

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )

    # Verificar que no exista una lista con el nuevo nombre
    existente = obtener_por_nombre(db, nuevo_nombre)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una lista con el nombre '{nuevo_nombre}'"
        )

    # Crear la nueva lista
    nueva_lista = ListaPrecio(
        nombre=nuevo_nombre,
        descripcion=f"Copia de {db_lista.nombre}",
        activo=True,
        created_by=usuario_id
    )
    db.add(nueva_lista)
    db.flush()

    # Copiar los items
    for item in db_lista.items:
        nuevo_item = ItemListaPrecio(
            lista_id=nueva_lista.id,
            material=item.material,
            precio_unitario=item.precio_unitario,
            factor_conversion_m3=item.factor_conversion_m3,
            created_by=usuario_id
        )
        db.add(nuevo_item)

    db.commit()
    db.refresh(nueva_lista)

    return nueva_lista


# ============== ITEMS DE LISTA ==============

def agregar_item(
    db: Session,
    lista_id: UUID,
    item_data: ItemListaPrecioCreate,
    usuario_id: UUID
) -> ItemListaPrecio:
    """Agrega un item a una lista"""

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )

    # Verificar que no exista un item con el mismo material
    for item in db_lista.items:
        if item.material.lower() == item_data.material.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un precio para el material '{item_data.material}' en esta lista"
            )

    db_item = ItemListaPrecio(
        lista_id=lista_id,
        material=item_data.material,
        precio_unitario=item_data.precio_unitario,
        factor_conversion_m3=item_data.factor_conversion_m3,
        created_by=usuario_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def actualizar_item(
    db: Session,
    item_id: UUID,
    precio_unitario: Optional[Decimal] = None,
    factor_conversion_m3: Optional[Decimal] = None
) -> ItemListaPrecio:
    """Actualiza un item de lista"""

    db_item = db.query(ItemListaPrecio).filter(ItemListaPrecio.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado"
        )

    if precio_unitario is not None:
        db_item.precio_unitario = precio_unitario

    if factor_conversion_m3 is not None:
        db_item.factor_conversion_m3 = factor_conversion_m3

    db.commit()
    db.refresh(db_item)

    return db_item


def eliminar_item(db: Session, item_id: UUID) -> dict:
    """Elimina un item de una lista"""

    db_item = db.query(ItemListaPrecio).filter(ItemListaPrecio.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado"
        )

    db.delete(db_item)
    db.commit()

    return {"message": "Item eliminado correctamente"}


def actualizar_items_batch(
    db: Session,
    lista_id: UUID,
    items: List[ItemBatchUpdate],
    usuario_id: UUID
) -> ListaPrecio:
    """
    Actualiza todos los items de una lista de una vez.
    - Crea items que no existen
    - Actualiza items existentes
    - Elimina items que no están en la lista
    """

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )

    # Mapear items existentes por material
    items_existentes = {item.material.lower(): item for item in db_lista.items}

    # Materiales que vienen en el batch
    materiales_batch = {item.material.lower() for item in items}

    # Eliminar items que ya no están
    for material, item in items_existentes.items():
        if material not in materiales_batch:
            db.delete(item)

    # Crear o actualizar items
    for item_data in items:
        material_lower = item_data.material.lower()

        if material_lower in items_existentes:
            # Actualizar existente
            db_item = items_existentes[material_lower]
            db_item.precio_unitario = item_data.precio_unitario
            db_item.factor_conversion_m3 = item_data.factor_conversion_m3
        else:
            # Crear nuevo
            db_item = ItemListaPrecio(
                lista_id=lista_id,
                material=item_data.material,
                precio_unitario=item_data.precio_unitario,
                factor_conversion_m3=item_data.factor_conversion_m3,
                created_by=usuario_id
            )
            db.add(db_item)

    db.commit()
    db.refresh(db_lista)

    return db_lista


# ============== CÁLCULO DE PRECIOS ==============

def calcular_importe(
    db: Session,
    lista_id: UUID,
    material: str,
    peso_neto_kg: float
) -> dict:
    """
    Calcula el importe para un material y peso usando una lista específica.

    Retorna:
    - Si hay precio configurado: diccionario con cálculo completo
    - Si no hay precio: diccionario con precio_encontrado=False
    """
    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        return {
            "precio_encontrado": False,
            "mensaje": "Lista de precios no encontrada"
        }

    if not db_lista.activo:
        return {
            "precio_encontrado": False,
            "mensaje": "La lista de precios no está activa"
        }

    # Buscar el item del material
    item = db_lista.obtener_precio_material(material)
    if not item:
        return {
            "precio_encontrado": False,
            "mensaje": f"No hay precio configurado para '{material}' en la lista '{db_lista.nombre}'"
        }

    # Calcular usando el método del modelo
    calculo = item.calcular_importe(peso_neto_kg)
    calculo["precio_encontrado"] = True
    calculo["lista_id"] = str(db_lista.id)
    calculo["lista_nombre"] = db_lista.nombre
    calculo["material"] = material

    return calculo


def obtener_precio_material(
    db: Session,
    lista_id: UUID,
    material: str
) -> Optional[ItemListaPrecio]:
    """Obtiene el item de precio para un material en una lista"""

    db_lista = obtener_por_id(db, lista_id)
    if not db_lista:
        return None

    return db_lista.obtener_precio_material(material)
