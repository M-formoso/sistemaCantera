#!/bin/bash
set -e

echo "=========================================="
echo "Sistema Cantera La Rufina - Iniciando..."
echo "=========================================="

echo ""
echo "Verificando variables de entorno..."

# Verificar variables obligatorias
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL no esta configurada"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY no esta configurada"
    exit 1
fi

echo "DATABASE_URL: configurada"
echo "SECRET_KEY: configurada (${#SECRET_KEY} caracteres)"
echo "ALGORITHM: ${ALGORITHM:-HS256}"
echo "ENVIRONMENT: ${ENVIRONMENT:-production}"

echo ""
echo "Ejecutando migraciones de base de datos..."
alembic upgrade head || {
    echo "Advertencia: Las migraciones fallaron, intentando crear tablas directamente..."
    python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
}

echo ""
echo "Inicializando datos (admin + cisterna)..."
python scripts/init_prod.py || echo "Advertencia: No se pudieron crear datos iniciales (puede que ya existan)"

echo ""
echo "=========================================="
echo "Iniciando servidor FastAPI..."
echo "=========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
