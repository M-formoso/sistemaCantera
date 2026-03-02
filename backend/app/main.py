import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.api import api_router


class CORSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware que intercepta redirects (307/308) y:
    1. Fuerza HTTPS para evitar Mixed Content
    2. Agrega headers CORS para que el navegador pueda seguir el redirect
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Si es un redirect (307 o 308), agregar headers CORS y forzar HTTPS
        if response.status_code in (307, 308):
            location = response.headers.get("location", "")

            # Forzar HTTPS si es HTTP
            if location.startswith("http://"):
                location = "https://" + location[7:]

            # Crear nuevo redirect con headers CORS
            new_response = RedirectResponse(
                url=location,
                status_code=response.status_code
            )
            # Agregar headers CORS al redirect
            new_response.headers["Access-Control-Allow-Origin"] = "*"
            new_response.headers["Access-Control-Allow-Methods"] = "*"
            new_response.headers["Access-Control-Allow-Headers"] = "*"
            return new_response

        return response


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configurar CORS - permitir todos los orígenes ya que usamos Bearer tokens
# IMPORTANTE: CORS debe agregarse PRIMERO para que se ejecute ÚLTIMO (antes de procesar la request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=False,  # No usamos cookies, usamos Bearer tokens
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
    expose_headers=["Content-Disposition", "Content-Type"],
    max_age=600,  # Cache preflight por 10 minutos
)

# Middleware para manejar redirects con CORS
app.add_middleware(CORSRedirectMiddleware)

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

            # Verificar columnas para doble pesaje en tabla pesajes
            if 'pesajes' in tablas_existentes:
                columns = [col['name'] for col in inspector.get_columns('pesajes')]

                # Agregar columna estado si no existe
                if 'estado' not in columns:
                    print("⚠️ Columna estado no existe en pesajes, creándola...")
                    conn.execute(text("""
                        ALTER TABLE pesajes ADD COLUMN estado VARCHAR(20) DEFAULT 'completado'
                    """))
                    conn.execute(text("UPDATE pesajes SET estado = 'completado' WHERE estado IS NULL"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pesajes_estado ON pesajes(estado)"))
                    conn.commit()
                    print("✅ Columna estado creada exitosamente")

                # Agregar columna fecha_completado si no existe
                if 'fecha_completado' not in columns:
                    print("⚠️ Columna fecha_completado no existe en pesajes, creándola...")
                    conn.execute(text("""
                        ALTER TABLE pesajes ADD COLUMN fecha_completado TIMESTAMP
                    """))
                    conn.commit()
                    print("✅ Columna fecha_completado creada exitosamente")

            # Crear tabla camiones_clientes si no existe
            if 'camiones_clientes' not in tablas_existentes:
                print("⚠️ Tabla camiones_clientes no existe, creándola...")
                conn.execute(text("""
                    CREATE TABLE camiones_clientes (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        cliente_id UUID NOT NULL REFERENCES empresas(id),
                        patente VARCHAR(20) NOT NULL,
                        descripcion VARCHAR(100),
                        chofer_habitual VARCHAR(100),
                        activo BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                conn.execute(text("CREATE INDEX ix_camiones_clientes_cliente_id ON camiones_clientes(cliente_id)"))
                conn.execute(text("CREATE INDEX ix_camiones_clientes_patente ON camiones_clientes(patente)"))
                conn.commit()
                print("✅ Tabla camiones_clientes creada exitosamente")

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
