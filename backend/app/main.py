import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.api import api_router


class CORSErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    1. Intercepta redirects (307/308) y agrega CORS + HTTPS
    2. Captura errores 500 y agrega headers CORS para que el navegador pueda ver el error
    """
    async def dispatch(self, request: Request, call_next):
        try:
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
                new_response.headers["Access-Control-Allow-Origin"] = "*"
                new_response.headers["Access-Control-Allow-Methods"] = "*"
                new_response.headers["Access-Control-Allow-Headers"] = "*"
                return new_response

            # Agregar CORS a respuestas de error (4xx, 5xx)
            if response.status_code >= 400:
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"

            return response
        except Exception as e:
            # Si hay una excepción no manejada, devolver 500 con CORS
            from fastapi.responses import JSONResponse
            import traceback
            print(f"[MIDDLEWARE ERROR] {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"detail": str(e)},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )


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

# Middleware para manejar errores y redirects con CORS
app.add_middleware(CORSErrorMiddleware)

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

                # Hacer peso_bruto, peso_tara y peso_neto nullable para doble pesaje
                print("⚠️ Verificando que peso_bruto, peso_tara y peso_neto sean nullable...")
                try:
                    conn.execute(text("ALTER TABLE pesajes ALTER COLUMN peso_bruto DROP NOT NULL"))
                    conn.commit()
                    print("✅ peso_bruto ahora es nullable")
                except Exception as e:
                    if "does not have a not-null constraint" not in str(e):
                        print(f"   peso_bruto: {e}")
                    conn.rollback()

                try:
                    conn.execute(text("ALTER TABLE pesajes ALTER COLUMN peso_tara DROP NOT NULL"))
                    conn.commit()
                    print("✅ peso_tara ahora es nullable")
                except Exception as e:
                    if "does not have a not-null constraint" not in str(e):
                        print(f"   peso_tara: {e}")
                    conn.rollback()

                try:
                    conn.execute(text("ALTER TABLE pesajes ALTER COLUMN peso_neto DROP NOT NULL"))
                    conn.commit()
                    print("✅ peso_neto ahora es nullable")
                except Exception as e:
                    if "does not have a not-null constraint" not in str(e):
                        print(f"   peso_neto: {e}")
                    conn.rollback()

            # Verificar columna categoria en camiones
            if 'camiones' in tablas_existentes:
                columns = [col['name'] for col in inspector.get_columns('camiones')]
                if 'categoria' not in columns:
                    print("⚠️ Columna categoria no existe en camiones, creándola...")
                    conn.execute(text("""
                        ALTER TABLE camiones ADD COLUMN categoria VARCHAR(20) DEFAULT 'camion'
                    """))
                    conn.execute(text("UPDATE camiones SET categoria = 'camion' WHERE categoria IS NULL"))
                    conn.commit()
                    print("✅ Columna categoria creada exitosamente")
                else:
                    print("✅ Columna categoria ya existe en camiones")

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

            # Crear tabla listas_precios si no existe
            if 'listas_precios' not in tablas_existentes:
                print("⚠️ Tabla listas_precios no existe, creándola...")
                conn.execute(text("""
                    CREATE TABLE listas_precios (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        descripcion TEXT,
                        activo BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        created_by UUID REFERENCES usuarios(id)
                    )
                """))
                conn.execute(text("CREATE INDEX ix_listas_precios_nombre ON listas_precios(nombre)"))
                conn.execute(text("CREATE INDEX ix_listas_precios_activo ON listas_precios(activo)"))
                conn.commit()
                print("✅ Tabla listas_precios creada exitosamente")

            # Crear tabla items_lista_precio si no existe
            if 'items_lista_precio' not in tablas_existentes:
                print("⚠️ Tabla items_lista_precio no existe, creándola...")
                conn.execute(text("""
                    CREATE TABLE items_lista_precio (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        lista_id UUID NOT NULL REFERENCES listas_precios(id) ON DELETE CASCADE,
                        material VARCHAR(100) NOT NULL,
                        precio_unitario NUMERIC(12,2) NOT NULL,
                        factor_conversion_m3 NUMERIC(6,3),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        created_by UUID REFERENCES usuarios(id),
                        UNIQUE(lista_id, material)
                    )
                """))
                conn.execute(text("CREATE INDEX ix_items_lista_precio_lista_id ON items_lista_precio(lista_id)"))
                conn.execute(text("CREATE INDEX ix_items_lista_precio_material ON items_lista_precio(material)"))
                conn.commit()
                print("✅ Tabla items_lista_precio creada exitosamente")

            # Agregar columna lista_precio_id a pesajes si no existe
            if 'pesajes' in tablas_existentes:
                columns = [col['name'] for col in inspector.get_columns('pesajes')]
                if 'lista_precio_id' not in columns:
                    print("⚠️ Columna lista_precio_id no existe en pesajes, creándola...")
                    conn.execute(text("""
                        ALTER TABLE pesajes ADD COLUMN lista_precio_id UUID REFERENCES listas_precios(id)
                    """))
                    conn.execute(text("CREATE INDEX ix_pesajes_lista_precio_id ON pesajes(lista_precio_id)"))
                    conn.commit()
                    print("✅ Columna lista_precio_id creada exitosamente")

    except Exception as e:
        print(f"⚠️ Error en startup verificando BD: {e}")
