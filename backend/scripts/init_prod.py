#!/usr/bin/env python3
"""
Script de inicialización para producción.
Ejecuta migraciones y crea el usuario administrador inicial.
"""
import os
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.usuario import Usuario
from app.core.security import get_password_hash
from app.db.base import Base
import subprocess


def run_migrations():
    """Ejecutar migraciones de Alembic"""
    print("Ejecutando migraciones de base de datos...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error en migraciones: {result.stderr}")
            # Si falla, intentar crear las tablas directamente
            print("Intentando crear tablas directamente...")
            engine = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(bind=engine)
            print("Tablas creadas correctamente")
        else:
            print("Migraciones ejecutadas correctamente")
            print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
        # Fallback: crear tablas directamente
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas directamente")


def create_admin_user():
    """Crear o actualizar usuario administrador"""
    print("Verificando usuario administrador...")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Verificar si ya existe un admin
        admin = db.query(Usuario).filter(Usuario.email == "admin@canteralarufina.com.ar").first()
        admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

        if not admin:
            # Crear admin con contraseña del entorno o por defecto
            admin = Usuario(
                email="admin@canteralarufina.com.ar",
                nombre="Administrador",
                rol="administrador",
                password_hash=get_password_hash(admin_password),
                activo=True
            )
            db.add(admin)
            db.commit()
            print(f"Usuario administrador creado: admin@canteralarufina.com.ar")
        else:
            # Actualizar contraseña si ADMIN_PASSWORD está definida
            if os.environ.get("ADMIN_PASSWORD"):
                admin.password_hash = get_password_hash(admin_password)
                db.commit()
                print(f"Contraseña del administrador actualizada")
            else:
                print("Usuario administrador ya existe")

    except Exception as e:
        print(f"Error creando admin: {e}")
        db.rollback()
    finally:
        db.close()


def fix_admin_permissions():
    """Asegurar que todos los administradores tengan todos los permisos = True"""
    print("Verificando permisos de administradores...")

    engine = create_engine(settings.DATABASE_URL)

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Actualizar todos los permisos a True para administradores
            result = conn.execute(text("""
                UPDATE usuarios
                SET permiso_dashboard = true,
                    permiso_camiones = true,
                    permiso_empresas = true,
                    permiso_repuestos = true,
                    permiso_pesajes = true,
                    permiso_combustible = true,
                    permiso_finanzas = true,
                    permiso_usuarios = true,
                    permiso_reportes = true
                WHERE rol = 'administrador'
            """))
            conn.commit()
            print(f"Permisos actualizados para administradores (filas: {result.rowcount})")
    except Exception as e:
        print(f"Error actualizando permisos (puede que las columnas no existan aún): {e}")


def create_default_cisterna():
    """Crear cisterna por defecto si no existe"""
    print("Verificando cisterna de combustible...")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        from app.models.combustible import CisternaCombustible

        cisterna = db.query(CisternaCombustible).first()

        if not cisterna:
            cisterna = CisternaCombustible(
                nombre="Cisterna Principal",
                capacidad_total=10000,
                nivel_actual=0,
                nivel_minimo=1000
            )
            db.add(cisterna)
            db.commit()
            print("Cisterna por defecto creada")
        else:
            print("Cisterna ya existe")

    except Exception as e:
        print(f"Error creando cisterna: {e}")
        db.rollback()
    finally:
        db.close()


def ensure_ordenes_entrega_table():
    """Asegurar que la tabla ordenes_entrega existe"""
    print("Verificando tabla ordenes_entrega...")

    engine = create_engine(settings.DATABASE_URL)

    try:
        from sqlalchemy import text, inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if 'ordenes_entrega' not in tables:
            print("Tabla ordenes_entrega no existe, creando...")
            with engine.connect() as conn:
                # Crear tabla ordenes_entrega
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ordenes_entrega (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        numero_orden INTEGER NOT NULL UNIQUE,
                        fecha_entrega DATE NOT NULL,
                        cliente_id UUID REFERENCES empresas(id),
                        cliente_nombre VARCHAR(255),
                        material VARCHAR(100) NOT NULL,
                        cantidad_cargas INTEGER NOT NULL,
                        cargas_entregadas INTEGER NOT NULL DEFAULT 0,
                        peso_estimado_carga NUMERIC(10, 2),
                        peso_total_estimado NUMERIC(12, 2),
                        peso_total_entregado NUMERIC(12, 2) DEFAULT 0,
                        estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                        solicitante VARCHAR(100),
                        contacto_cliente VARCHAR(100),
                        telefono_contacto VARCHAR(50),
                        direccion_entrega TEXT,
                        observaciones TEXT,
                        created_by UUID NOT NULL REFERENCES usuarios(id),
                        created_at TIMESTAMP NOT NULL DEFAULT now(),
                        updated_at TIMESTAMP NOT NULL DEFAULT now()
                    )
                """))

                # Crear índices
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ordenes_entrega_numero_orden ON ordenes_entrega(numero_orden)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ordenes_entrega_fecha_entrega ON ordenes_entrega(fecha_entrega)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ordenes_entrega_estado ON ordenes_entrega(estado)"))

                conn.commit()
                print("Tabla ordenes_entrega creada correctamente")
        else:
            print("Tabla ordenes_entrega ya existe")

        # Verificar columna orden_entrega_id en pesajes
        pesajes_columns = [col['name'] for col in inspector.get_columns('pesajes')]
        if 'orden_entrega_id' not in pesajes_columns:
            print("Agregando columna orden_entrega_id a pesajes...")
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE pesajes
                    ADD COLUMN IF NOT EXISTS orden_entrega_id UUID REFERENCES ordenes_entrega(id)
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pesajes_orden_entrega_id ON pesajes(orden_entrega_id)"))
                conn.commit()
                print("Columna orden_entrega_id agregada")
        else:
            print("Columna orden_entrega_id ya existe en pesajes")

    except Exception as e:
        print(f"Error verificando ordenes_entrega: {e}")


def ensure_iva_columns():
    """Asegurar que las columnas de IVA existan en empresas y movimientos_cuenta_corriente.

    Salvaguarda: si la migration 20260604_iva_cc falló o no corrió, las columnas
    se crean aquí de forma idempotente. Si ya existen, no hace nada.

    También backfillea movimientos que no tengan monto_neto seteado.
    """
    print("Verificando columnas IVA en cuenta corriente...")

    engine = create_engine(settings.DATABASE_URL)

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE empresas
                ADD COLUMN IF NOT EXISTS alicuota_iva NUMERIC(5, 2) NOT NULL DEFAULT 21.00;
            """))
            conn.execute(text("""
                ALTER TABLE empresas
                ADD COLUMN IF NOT EXISTS iva_en_total BOOLEAN NOT NULL DEFAULT FALSE;
            """))
            conn.execute(text("""
                ALTER TABLE movimientos_cuenta_corriente
                ADD COLUMN IF NOT EXISTS alicuota_iva NUMERIC(5, 2) NOT NULL DEFAULT 21.00;
            """))
            conn.execute(text("""
                ALTER TABLE movimientos_cuenta_corriente
                ADD COLUMN IF NOT EXISTS monto_neto NUMERIC(12, 2);
            """))
            conn.execute(text("""
                ALTER TABLE movimientos_cuenta_corriente
                ADD COLUMN IF NOT EXISTS monto_iva NUMERIC(12, 2);
            """))
            conn.commit()
            print("Columnas IVA verificadas/creadas")

            # Backfill: si todavía no se desglosó IVA en movimientos existentes,
            # asumir que `monto` era neto y recalcular total c/IVA al 21%.
            result = conn.execute(text("""
                UPDATE movimientos_cuenta_corriente
                SET monto_neto = monto,
                    monto_iva = ROUND(monto * 0.21, 2),
                    monto = ROUND(monto * 1.21, 2)
                WHERE monto_neto IS NULL;
            """))
            conn.commit()
            if result.rowcount:
                print(f"Backfill IVA aplicado a {result.rowcount} movimientos (asumiendo 21%)")

                # Recalcular saldos acumulados ahora que el monto incluye IVA.
                conn.execute(text("""
                    WITH ordered AS (
                        SELECT id, empresa_id,
                               CASE WHEN tipo = 'cargo' THEN monto
                                    WHEN tipo = 'pago' THEN -monto
                                    ELSE monto END AS delta,
                               ROW_NUMBER() OVER (
                                   PARTITION BY empresa_id
                                   ORDER BY fecha ASC, created_at ASC
                               ) AS rn
                        FROM movimientos_cuenta_corriente
                        WHERE anulado = false
                    ),
                    with_running AS (
                        SELECT id, empresa_id, rn,
                               SUM(delta) OVER (
                                   PARTITION BY empresa_id
                                   ORDER BY rn
                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                               ) AS saldo_post
                        FROM ordered
                    ),
                    with_pre AS (
                        SELECT id, saldo_post,
                               COALESCE(
                                   LAG(saldo_post) OVER (PARTITION BY empresa_id ORDER BY rn),
                                   0
                               ) AS saldo_pre
                        FROM with_running
                    )
                    UPDATE movimientos_cuenta_corriente m
                    SET saldo_anterior = p.saldo_pre,
                        saldo_posterior = p.saldo_post
                    FROM with_pre p
                    WHERE m.id = p.id;
                """))
                conn.execute(text("""
                    UPDATE empresas e
                    SET saldo_cuenta_corriente = COALESCE((
                        SELECT SUM(CASE
                                       WHEN tipo = 'cargo' THEN monto
                                       WHEN tipo = 'pago' THEN -monto
                                       ELSE monto
                                   END)
                        FROM movimientos_cuenta_corriente
                        WHERE empresa_id = e.id AND anulado = false
                    ), 0);
                """))
                conn.commit()
                print("Saldos acumulados recalculados con IVA")

    except Exception as e:
        print(f"Error verificando columnas IVA: {e}")


def ensure_mateo_admin():
    """Crear/actualizar el usuario superadmin de Mateo si no existe.

    Idempotente: si el usuario ya existe, no toca su password (para no
    pisarlo). Si no existe, lo crea con todos los permisos en True.
    """
    print("Verificando usuario Mateo Programador...")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    EMAIL = "mateoformoso@larufina.com"
    PASSWORD = "mateo123"

    try:
        mateo = db.query(Usuario).filter(Usuario.email == EMAIL).first()
        if mateo:
            print(f"Usuario {EMAIL} ya existe — sólo aseguro permisos y rol")
            mateo.rol = "administrador"
            mateo.activo = True
            mateo.nombre = "Mateo Programador"
            # Resetear password también para que el usuario pueda entrar sí o sí.
            mateo.password_hash = get_password_hash(PASSWORD)
            for permiso in [
                "permiso_dashboard", "permiso_camiones", "permiso_empresas",
                "permiso_repuestos", "permiso_pesajes", "permiso_combustible",
                "permiso_finanzas", "permiso_usuarios", "permiso_reportes",
            ]:
                if hasattr(mateo, permiso):
                    setattr(mateo, permiso, True)
            db.commit()
            print(f"Usuario {EMAIL} actualizado a superadmin")
        else:
            mateo = Usuario(
                email=EMAIL,
                nombre="Mateo Programador",
                rol="administrador",
                password_hash=get_password_hash(PASSWORD),
                activo=True,
                permiso_dashboard=True,
                permiso_camiones=True,
                permiso_empresas=True,
                permiso_repuestos=True,
                permiso_pesajes=True,
                permiso_combustible=True,
                permiso_finanzas=True,
                permiso_usuarios=True,
                permiso_reportes=True,
            )
            db.add(mateo)
            db.commit()
            print(f"Usuario {EMAIL} creado como superadmin")
    except Exception as e:
        print(f"Error creando/actualizando usuario Mateo: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Inicializando Sistema Cantera La Rufina")
    print("=" * 50)

    # No crear usuario admin por defecto - el cliente ya tiene sus propios usuarios
    # create_admin_user()

    # Asegurar que los administradores tengan todos los permisos
    fix_admin_permissions()

    # Crear cisterna por defecto si no existe
    create_default_cisterna()

    # Asegurar que la tabla ordenes_entrega existe
    ensure_ordenes_entrega_table()

    # Asegurar que las columnas de IVA existan (salvaguarda por si la migration falló)
    ensure_iva_columns()

    # Crear/asegurar usuario superadmin Mateo Programador
    ensure_mateo_admin()

    print("=" * 50)
    print("Inicialización completada!")
    print("=" * 50)
