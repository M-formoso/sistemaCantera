# Skill: Docker Setup

## Objetivo
Configurar Docker y Docker Compose para desarrollo y producción del proyecto.

## Estructura de Contenedores

```
docker-compose.yml
├── postgres      # Base de datos
├── redis         # Cache y Celery broker
├── backend       # FastAPI
├── celery-worker # Procesamiento asíncrono
├── celery-beat   # Tareas programadas
└── frontend      # React (solo desarrollo)
```

## Docker Compose - Desarrollo

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cantera-postgres
    environment:
      POSTGRES_USER: cantera
      POSTGRES_PASSWORD: cantera_password
      POSTGRES_DB: cantera_rufina
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cantera"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cantera-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cantera-backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://cantera:cantera_password@postgres:5432/cantera_rufina
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=dev-secret-key-change-in-production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cantera-celery-worker
    command: celery -A app.core.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://cantera:cantera_password@postgres:5432/cantera_rufina
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cantera-celery-beat
    command: celery -A app.core.celery_app beat --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://cantera:cantera_password@postgres:5432/cantera_rufina
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cantera-frontend
    command: npm run dev -- --host
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1

volumes:
  postgres_data:
  redis_data:
```

## Dockerfile - Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Dockerfile - Frontend

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copiar package files
COPY package*.json .

# Instalar dependencias
RUN npm ci

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 5173

# Comando por defecto (desarrollo)
CMD ["npm", "run", "dev", "--", "--host"]
```

## Docker Compose - Producción

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: cantera-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend

  postgres:
    image: postgres:15-alpine
    container_name: cantera-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cantera-redis
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: cantera-backend
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    expose:
      - 8000
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}
      - CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}
      - CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: cantera-celery-worker
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: cantera-celery-beat
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name cantera-rufina.com www.cantera-rufina.com;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support (si se usa)
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

## Comandos Útiles

```bash
# Desarrollo
docker-compose up -d                    # Iniciar todos los servicios
docker-compose logs -f backend          # Ver logs del backend
docker-compose exec backend bash        # Entrar al contenedor
docker-compose down                     # Detener servicios
docker-compose down -v                  # Detener y eliminar volúmenes

# Migraciones
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "mensaje"

# Base de datos
docker-compose exec postgres psql -U cantera -d cantera_rufina
docker-compose exec postgres pg_dump -U cantera cantera_rufina > backup.sql

# Producción
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f

# Rebuild
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

## Variables de Entorno (.env)

```bash
# .env (desarrollo)
POSTGRES_USER=cantera
POSTGRES_PASSWORD=cantera_password
POSTGRES_DB=cantera_rufina
DATABASE_URL=postgresql://cantera:cantera_password@localhost:5432/cantera_rufina

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

VITE_API_URL=http://localhost:8000/api/v1
```

## Checklist de Implementación

- [ ] Crear docker-compose.yml para desarrollo
- [ ] Crear Dockerfile para backend
- [ ] Crear Dockerfile para frontend
- [ ] Configurar volúmenes para persistencia
- [ ] Configurar healthchecks
- [ ] Crear .env.example
- [ ] Configurar nginx para producción
- [ ] Probar construcción de imágenes
- [ ] Probar migraciones en Docker
- [ ] Documentar comandos útiles
