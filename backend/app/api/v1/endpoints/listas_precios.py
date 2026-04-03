"""
Endpoints para gestión de Listas de Precios
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.lista_precio import (
    ListaPrecioCreate,
    ListaPrecioUpdate,
    ListaPrecioSchema,
    ListaPrecioResumen,
    ItemListaPrecioCreate,
    ItemListaPrecioSchema,
    ListaPrecioItemsBatch,
    CalculoPrecioLista,
    MaterialesDisponiblesResponse
)
from app.schemas.pesaje import MATERIALES_DISPONIBLES
from app.services import lista_precio_service

router = APIRouter()


# ============== MATERIALES ==============

@router.get("/materiales", response_model=MaterialesDisponiblesResponse)
def obtener_materiales():
    """
    Obtiene la lista de materiales disponibles para configurar precios
    """
    return {"materiales": MATERIALES_DISPONIBLES}


# ============== LISTAS DE PRECIOS ==============

@router.get("/", response_model=List[ListaPrecioSchema])
def obtener_listas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activas: bool = Query(False, description="Filtrar solo listas activas"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todas las listas de precios con sus items
    """
    return lista_precio_service.obtener_todas(db, skip, limit, solo_activas)


@router.get("/resumen", response_model=List[ListaPrecioResumen])
def obtener_listas_resumen(
    solo_activas: bool = Query(True, description="Filtrar solo listas activas"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un resumen de las listas (sin items) para selectores
    """
    listas = lista_precio_service.obtener_todas(db, 0, 500, solo_activas)
    return [
        ListaPrecioResumen(
            id=lista.id,
            nombre=lista.nombre,
            descripcion=lista.descripcion,
            activo=lista.activo,
            cantidad_items=len(lista.items)
        )
        for lista in listas
    ]


@router.get("/{lista_id}", response_model=ListaPrecioSchema)
def obtener_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una lista de precios por ID con todos sus items
    """
    lista = lista_precio_service.obtener_por_id(db, lista_id)
    if not lista:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    return lista


@router.post("/", response_model=ListaPrecioSchema)
def crear_lista(
    lista_data: ListaPrecioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea una nueva lista de precios.

    Puede incluir items al momento de la creación.

    Ejemplo:
    ```json
    {
        "nombre": "Lista Mayorista",
        "descripcion": "Precios para mayoristas",
        "activo": true,
        "items": [
            {"material": "0.20", "precio_unitario": 17500, "factor_conversion_m3": 1.66},
            {"material": "6.19", "precio_unitario": 18000, "factor_conversion_m3": 1.5},
            {"material": "10.30", "precio_unitario": 15000}
        ]
    }
    ```
    """
    return lista_precio_service.crear(db, lista_data, current_user.id)


@router.put("/{lista_id}", response_model=ListaPrecioSchema)
def actualizar_lista(
    lista_id: UUID,
    lista_data: ListaPrecioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza los datos de una lista (nombre, descripción, activo).
    No modifica los items.
    """
    return lista_precio_service.actualizar(db, lista_id, lista_data)


@router.delete("/{lista_id}")
def eliminar_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina una lista de precios y todos sus items
    """
    return lista_precio_service.eliminar(db, lista_id)


@router.post("/{lista_id}/duplicar", response_model=ListaPrecioSchema)
def duplicar_lista(
    lista_id: UUID,
    nuevo_nombre: str = Query(..., description="Nombre para la nueva lista"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Duplica una lista de precios con todos sus items
    """
    return lista_precio_service.duplicar(db, lista_id, nuevo_nombre, current_user.id)


# ============== ITEMS DE LISTA ==============

@router.post("/{lista_id}/items", response_model=ItemListaPrecioSchema)
def agregar_item(
    lista_id: UUID,
    item_data: ItemListaPrecioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Agrega un item (material con precio) a una lista
    """
    return lista_precio_service.agregar_item(db, lista_id, item_data, current_user.id)


@router.put("/{lista_id}/items/batch", response_model=ListaPrecioSchema)
def actualizar_items_batch(
    lista_id: UUID,
    batch_data: ListaPrecioItemsBatch,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza todos los items de una lista de una vez.

    - Crea items nuevos
    - Actualiza items existentes
    - Elimina items que no están en la lista

    Ejemplo:
    ```json
    {
        "items": [
            {"material": "0.20", "precio_unitario": 17500, "factor_conversion_m3": 1.66},
            {"material": "6.19", "precio_unitario": 18000, "factor_conversion_m3": 1.5}
        ]
    }
    ```
    """
    return lista_precio_service.actualizar_items_batch(
        db, lista_id, batch_data.items, current_user.id
    )


@router.delete("/items/{item_id}")
def eliminar_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un item de una lista
    """
    return lista_precio_service.eliminar_item(db, item_id)


# ============== CÁLCULO DE PRECIOS ==============

@router.get("/{lista_id}/calcular", response_model=CalculoPrecioLista)
def calcular_importe(
    lista_id: UUID,
    material: str = Query(..., description="Material a calcular"),
    peso_neto_kg: float = Query(..., description="Peso neto en kg"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Calcula el importe para un material y peso usando una lista específica.

    Si el material tiene factor de conversión a m³, devuelve el cálculo
    con la cantidad en m³ y el importe correspondiente.

    Ejemplo respuesta con conversión:
    ```json
    {
        "precio_encontrado": true,
        "lista_id": "uuid",
        "lista_nombre": "Lista Mayorista",
        "material": "0.20",
        "peso_toneladas": 20.5,
        "cantidad_facturada": 12.35,
        "unidad": "m3",
        "precio_unitario": 17500,
        "factor_conversion": 1.66,
        "importe": 216125
    }
    ```
    """
    return lista_precio_service.calcular_importe(db, lista_id, material, peso_neto_kg)
