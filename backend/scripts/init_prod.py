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

    print("=" * 50)
    print("Inicialización completada!")
    print("=" * 50)
