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

# Configurar CORS - permitir todos los orígenes ya que usamos Bearer tokens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=False,  # No usamos cookies, usamos Bearer tokens
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
    expose_headers=["Content-Disposition", "Content-Type"],
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
    Evento de inicio: verifica y crea columnas/tablas faltantes en la BD
    """
    from app.db.session import engine
    from sqlalchemy import text, inspect

    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            tablas_existentes = inspector.get_table_names()

            # Verificar si existe la columna camion_id en repuestos
            if 'repuestos' in tablas_existentes:
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

            # Crear tabla trabajos si no existe
            if 'trabajos' not in tablas_existentes:
                print("⚠️ Tabla trabajos no existe, creándola...")
                conn.execute(text("""
                    CREATE TABLE trabajos (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        camion_id UUID NOT NULL REFERENCES camiones(id),
                        fecha DATE NOT NULL,
                        descripcion TEXT NOT NULL,
                        responsable VARCHAR(100),
                        costo_mano_obra NUMERIC(12,2) DEFAULT 0,
                        costo_total NUMERIC(12,2) DEFAULT 0,
                        observaciones TEXT,
                        created_by UUID NOT NULL REFERENCES usuarios(id),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                conn.execute(text("CREATE INDEX ix_trabajos_camion_id ON trabajos(camion_id)"))
                conn.execute(text("CREATE INDEX ix_trabajos_fecha ON trabajos(fecha)"))
                conn.commit()
                print("✅ Tabla trabajos creada exitosamente")

            # Crear tabla trabajos_repuestos si no existe
            if 'trabajos_repuestos' not in tablas_existentes:
                print("⚠️ Tabla trabajos_repuestos no existe, creándola...")
                conn.execute(text("""
                    CREATE TABLE trabajos_repuestos (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        trabajo_id UUID NOT NULL REFERENCES trabajos(id) ON DELETE CASCADE,
                        repuesto_id UUID NOT NULL REFERENCES repuestos(id),
                        cantidad NUMERIC(10,2) NOT NULL DEFAULT 1,
                        precio_unitario NUMERIC(12,2),
                        subtotal NUMERIC(12,2),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                conn.execute(text("CREATE INDEX ix_trabajos_repuestos_trabajo_id ON trabajos_repuestos(trabajo_id)"))
                conn.commit()
                print("✅ Tabla trabajos_repuestos creada exitosamente")

    except Exception as e:
        print(f"⚠️ Error en startup verificando BD: {e}")
