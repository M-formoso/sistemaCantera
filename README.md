# Sistema de Gestión Cantera La Rufina

Sistema completo de gestión operativa para Cantera La Rufina, que incluye control de máquinas, repuestos, pesajes, combustible y reportes.

## 📋 Características

- **Control de Máquinas y Servicios**: Gestión de camiones, mantenimientos y repuestos
- **Pesajes y Remitos**: Sistema de pesaje con generación automática de remitos
- **Control de Combustible**: Gestión de cisterna y suministros a camiones
- **Stock de Repuestos**: Control de inventario con alertas de stock bajo
- **Dashboard**: Vista general de operaciones del día
- **Reportes**: Informes operativos y estadísticas

## 🛠️ Stack Tecnológico

### Backend
- Python 3.11+
- FastAPI 0.104+
- PostgreSQL 15+
- SQLAlchemy 2.0
- Alembic (migraciones)
- Celery + Redis (tareas asíncronas)
- JWT para autenticación

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS + shadcn/ui
- Zustand (state management)
- TanStack Query (data fetching)
- React Hook Form + Zod

### Infraestructura
- Docker + Docker Compose
- Nginx (producción)
- Cloudinary (imágenes)

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose instalados
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd sistemaCantera
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. **Iniciar servicios con Docker Compose**
```bash
docker-compose up -d
```

4. **Ejecutar migraciones de base de datos**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Inicializar datos básicos**
```bash
docker-compose exec backend python -c "from app.db.session import SessionLocal; from app.db.init_db import init_db; db = SessionLocal(); init_db(db); db.close()"
```

6. **Acceder a la aplicación**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### Usuario por Defecto

- **Email**: admin@canterarufina.com
- **Password**: admin123

⚠️ **IMPORTANTE**: Cambiar esta contraseña en producción

## 📁 Estructura del Proyecto

```
sistemaCantera/
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── api/v1/            # Endpoints API
│   │   ├── core/              # Configuración y seguridad
│   │   ├── db/                # Database setup
│   │   ├── models/            # Modelos SQLAlchemy
│   │   ├── schemas/           # Schemas Pydantic
│   │   ├── services/          # Lógica de negocio
│   │   ├── tasks/             # Tareas Celery
│   │   └── utils/             # Utilidades
│   ├── alembic/               # Migraciones
│   ├── tests/                 # Tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   ├── services/          # API calls
│   │   ├── stores/            # Zustand stores
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Utilidades
│   ├── package.json
│   └── Dockerfile
│
├── docs/                       # Documentación
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Desarrollo

### Backend

#### Ejecutar sin Docker
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000
```

#### Crear nueva migración
```bash
docker-compose exec backend alembic revision --autogenerate -m "descripcion"
docker-compose exec backend alembic upgrade head
```

#### Ejecutar tests
```bash
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=app tests/
```

#### Workers Celery
```bash
# Worker
docker-compose exec celery_worker celery -A app.core.celery_app worker --loglevel=info

# Beat (tareas programadas)
docker-compose exec celery_beat celery -A app.core.celery_app beat --loglevel=info
```

### Frontend

#### Ejecutar sin Docker
```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

#### Build para producción
```bash
npm run build
npm run preview
```

#### Linting
```bash
npm run lint
```

## 📊 Módulos del Sistema

### 1. Autenticación
- Login con JWT
- Roles: Administrador, Operador, Solo Lectura
- Cambio de contraseña
- Refresh tokens

### 2. Camiones y Servicios
- CRUD de camiones
- Registro de servicios/mantenimientos
- Asignación de repuestos con descuento automático de stock
- Historial completo de servicios

### 3. Stock de Repuestos
- Gestión de inventario
- Alertas de stock bajo
- Historial de movimientos
- Categorías y ubicaciones

### 4. Pesajes y Remitos
- Registro de pesajes (tara, bruto, neto)
- Generación automática de remitos
- Exportación a PDF
- Envío por email

### 5. Control de Combustible
- Gestión de cisterna principal
- Registro de cargas
- Suministros a camiones
- Cálculo de consumo y rendimiento

### 6. Dashboard
- Resumen del día
- Indicadores clave
- Alertas importantes
- Gráficos de tendencias

### 7. Reportes
- Reportes de pesajes
- Reportes de combustible
- Reportes de mantenimiento
- Exportación a PDF/Excel

## 🔒 Seguridad

- Autenticación JWT con access y refresh tokens
- Passwords hasheados con bcrypt
- Validación de permisos por rol
- CORS configurado
- Logs de actividad
- Variables de entorno para secretos

## 📝 Variables de Entorno

Ver `.env.example` para todas las variables disponibles.

Variables críticas:
- `DATABASE_URL`: Conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `REDIS_URL`: Conexión a Redis
- `CLOUDINARY_*`: Configuración de Cloudinary (opcional)
- `SMTP_*`: Configuración de email (opcional)

## 🐛 Troubleshooting

### El backend no se conecta a la base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs
docker-compose logs db
docker-compose logs backend
```

### Error en migraciones
```bash
# Revertir última migración
docker-compose exec backend alembic downgrade -1

# Ver historial de migraciones
docker-compose exec backend alembic history
```

### Frontend no carga
```bash
# Verificar que el backend esté corriendo
curl http://localhost:8000/health

# Reinstalar dependencias
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentación Adicional

- [API Documentation](http://localhost:8000/api/v1/docs) - Swagger UI
- [Database Schema](./docs/database-schema.md)
- [Agent Instructions](./docs/agent.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Contacto

Cantera La Rufina - info@canterarufina.com

---

**Versión**: 1.0.0
**Última actualización**: Enero 2025
