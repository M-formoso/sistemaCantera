from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    camiones,
    repuestos,
    servicios,
    pesajes,
    remitos,
    combustible,
    dashboard
)

# Crear router principal de la API v1
api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(camiones.router, prefix="/camiones", tags=["Camiones"])
api_router.include_router(repuestos.router, prefix="/repuestos", tags=["Repuestos"])
api_router.include_router(servicios.router, prefix="/servicios", tags=["Servicios"])
api_router.include_router(pesajes.router, prefix="/pesajes", tags=["Pesajes"])
api_router.include_router(remitos.router, prefix="/remitos", tags=["Remitos"])
api_router.include_router(combustible.router, prefix="/combustible", tags=["Combustible"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
