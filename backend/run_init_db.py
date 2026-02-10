"""
Script para ejecutar la inicialización de la base de datos
"""
from app.db.session import SessionLocal
from app.db.init_db import init_db

def main():
    """Ejecuta la inicialización de la base de datos"""
    print("Inicializando base de datos...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    print("¡Inicialización completada!")

if __name__ == "__main__":
    main()
