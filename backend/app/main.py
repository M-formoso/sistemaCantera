import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.api import api_router


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware que intercepta redirects y fuerza HTTPS.
    Esto evita el error de Mixed Content cuando FastAPI hace redirect de trailing slashes.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Si es un redirect (307 o 308), forzar HTTPS en la URL de destino
        if response.status_code in (307, 308):
            location = response.headers.get("location", "")
            if location.startswith("http://"):
                # Cambiar http:// por https://
                new_location = "https://" + location[7:]
                return RedirectResponse(
                    url=new_location,
                    status_code=response.status_code
                )

        return response


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Middleware para forzar HTTPS en redirects (debe ir ANTES de CORS)
app.add_middleware(HTTPSRedirectMiddleware)

# Configurar CORS - lista explícita de orígenes permitidos
cors_origins = [
    "https://sistema.canteralarufina.com.ar",
    "https://canteralarufina.com.ar",
    "https://frontend-production-d4d3.up.railway.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight por 10 minutos
)

# Incluir routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Gestión Cantera La Rufina",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio: verifica y crea columnas faltantes en la BD
    """
    from app.db.session import engine
    from sqlalchemy import text, inspect

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)

            # Verificar si existe la columna camion_id en repuestos
            columns = [col['name'] for col in inspector.get_columns('repuestos')]
            if 'camion_id' not in columns:
                print("⚠️ Columna camion_id no existe en repuestos, creándola...")
                conn.execute(text("""
                    ALTER TABLE repuestos
                    ADD COLUMN camion_id UUID REFERENCES camiones(id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_repuestos_camion_id ON repuestos(camion_id)
                """))
                conn.commit()
                print("✅ Columna camion_id creada exitosamente")

    except Exception as e:
        print(f"⚠️ Error en startup verificando columnas: {e}")
