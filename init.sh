#!/bin/bash

echo "🚀 Inicializando Sistema Cantera La Rufina..."
echo ""

# Verificar que Docker esté corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está corriendo"
    echo "Por favor inicia Docker Desktop e intenta nuevamente"
    exit 1
fi

echo "✓ Docker está corriendo"
echo ""

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cp .env.example .env
    echo "✓ Archivo .env creado"
    echo "⚠️  IMPORTANTE: Revisa y actualiza las variables en .env"
    echo ""
fi

# Iniciar servicios
echo "🐳 Iniciando servicios Docker..."
docker-compose up -d

echo ""
echo "⏳ Esperando a que los servicios estén listos..."
sleep 15

# Ejecutar migraciones
echo ""
echo "🔄 Ejecutando migraciones de base de datos..."
docker-compose exec -T backend alembic upgrade head

# Inicializar datos
echo ""
echo "📊 Inicializando datos básicos..."
docker-compose exec -T backend python -c "from app.db.session import SessionLocal; from app.db.init_db import init_db; db = SessionLocal(); init_db(db); db.close()"

echo ""
echo "✅ ¡Sistema inicializado correctamente!"
echo ""
echo "📱 Accede a la aplicación:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "👤 Usuario por defecto:"
echo "   - Email: admin@canterarufina.com"
echo "   - Password: admin123"
echo ""
echo "⚠️  IMPORTANTE: Cambia la contraseña del administrador en producción"
echo ""
echo "Para ver los logs:"
echo "   docker-compose logs -f"
echo ""
echo "Para detener los servicios:"
echo "   docker-compose down"
