"""
Endpoints para gestión de precios por cliente y material
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.precio_cliente import (
    PrecioClienteCreate,
    PrecioClienteUpdate,
    PrecioClienteSchema,
    CalculoPrecio,
    MaterialesDisponiblesResponse
)
from app.schemas.pesaje import MATERIALES_DISPONIBLES
from app.services import precio_cliente_service

router = APIRouter()


@router.get("/materiales", response_model=MaterialesDisponiblesResponse)
def obtener_materiales():
    """
    Obtiene la lista de materiales disponibles
    """
    return {"materiales": MATERIALES_DISPONIBLES}


@router.get("/", response_model=List[PrecioClienteSchema])
def obtener_precios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todos los precios configurados
    """
    return precio_cliente_service.obtener_todos(db, skip, limit)


@router.get("/cliente/{cliente_id}", response_model=List[PrecioClienteSchema])
def obtener_precios_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todos los precios configurados para un cliente específico
    """
    return precio_cliente_service.obtener_por_cliente(db, cliente_id)


@router.get("/cliente/{cliente_id}/material/{material}", response_model=Optional[PrecioClienteSchema])
def obtener_precio_cliente_material(
    cliente_id: UUID,
    material: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el precio configurado para un cliente y material específico.
    Retorna null si no hay precio configurado.
    """
    return precio_cliente_service.obtener_por_cliente_material(db, cliente_id, material)


@router.post("/", response_model=PrecioClienteSchema)
def crear_precio(
    precio_data: PrecioClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo precio para un cliente y material
    """
    return precio_cliente_service.crear(db, precio_data, current_user.id)


@router.post("/cliente/{cliente_id}/multiple", response_model=List[PrecioClienteSchema])
def crear_precios_multiples(
    cliente_id: UUID,
    precios: List[dict],
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea o actualiza múltiples precios para un cliente.

    Body: Lista de objetos con {material, precio_unitario, factor_conversion_m3?}

    Ejemplo:
    ```json
    [
        {"material": "0.20", "precio_unitario": 17500, "factor_conversion_m3": 1.66},
        {"material": "6.19", "precio_unitario": 18000, "factor_conversion_m3": 1.5},
        {"material": "10.30", "precio_unitario": 15000}
    ]
    ```
    """
    return precio_cliente_service.crear_multiples(db, cliente_id, precios, current_user.id)


@router.put("/{precio_id}", response_model=PrecioClienteSchema)
def actualizar_precio(
    precio_id: UUID,
    precio_data: PrecioClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un precio existente
    """
    return precio_cliente_service.actualizar(db, precio_id, precio_data)


@router.delete("/{precio_id}")
def eliminar_precio(
    precio_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un precio
    """
    return precio_cliente_service.eliminar(db, precio_id)


@router.get("/calcular", response_model=dict)
def calcular_importe(
    cliente_id: UUID = Query(..., description="ID del cliente"),
    material: str = Query(..., description="Material"),
    peso_neto_kg: float = Query(..., description="Peso neto en kg"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Calcula el importe para un cliente, material y peso dado.

    Si el cliente tiene conversión a m³ configurada, devuelve el cálculo
    con la cantidad en m³ y el importe correspondiente.

    Ejemplo respuesta con conversión:
    ```json
    {
        "precio_encontrado": true,
        "peso_toneladas": 20.5,
        "cantidad_facturada": 12.35,
        "unidad": "m3",
        "precio_unitario": 17500,
        "factor_conversion": 1.66,
        "importe": 216125
    }
    ```

    Ejemplo respuesta sin conversión:
    ```json
    {
        "precio_encontrado": true,
        "peso_toneladas": 20.5,
        "cantidad_facturada": 20.5,
        "unidad": "tn",
        "precio_unitario": 15000,
        "factor_conversion": null,
        "importe": 307500
    }
    ```
    """
    return precio_cliente_service.calcular_importe(db, cliente_id, material, peso_neto_kg)
