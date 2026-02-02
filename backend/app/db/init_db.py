"""
Script para inicializar la base de datos con datos básicos
"""
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, RolEnum
from app.models.combustible import CisternaCombustible
from app.core.security import get_password_hash


def init_db(db: Session) -> None:
    """
    Inicializa la base de datos con datos básicos

    Args:
        db: Sesión de base de datos
    """
    # Verificar si ya existe un usuario administrador
    admin = db.query(Usuario).filter(Usuario.rol == RolEnum.ADMINISTRADOR).first()

    if not admin:
        # Crear usuario administrador por defecto
        admin_user = Usuario(
            email="admin@canterarufina.com",
            password_hash=get_password_hash("admin123"),  # Cambiar en producción
            nombre="Administrador",
            rol=RolEnum.ADMINISTRADOR,
            activo=True
        )
        db.add(admin_user)
        print("✓ Usuario administrador creado")
    else:
        print("✓ Usuario administrador ya existe")

    # Verificar si existe configuración de cisterna
    cisterna = db.query(CisternaCombustible).first()

    if not cisterna:
        # Crear configuración de cisterna por defecto
        cisterna = CisternaCombustible(
            capacidad_total=10000,  # 10000 litros
            nivel_actual=5000,  # 5000 litros inicial
            nivel_alerta=1000  # Alerta cuando queda menos de 1000L
        )
        db.add(cisterna)
        print("✓ Cisterna de combustible configurada")
    else:
        print("✓ Cisterna de combustible ya existe")

    db.commit()
    print("\n✅ Base de datos inicializada correctamente")
