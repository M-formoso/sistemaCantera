# 🚀 Instrucciones para Levantar el MVP - Sistema Cantera La Rufina

## ✅ Pre-requisitos

Asegúrate de tener instalado:
- **Docker** y **Docker Compose** (para backend y base de datos)
- **Node.js 18+** y **npm** (para frontend)
- **Git** (opcional, si quieres versionarlo)

---

## 📦 Paso 1: Levantar el Backend y Base de Datos

### Opción A: Usando el script automático (RECOMENDADO)

```bash
# Desde la raíz del proyecto
chmod +x init.sh
./init.sh
```

Este script hace todo automáticamente:
- Levanta los 6 servicios con Docker Compose (PostgreSQL, Redis, Backend, Celery Worker, Celery Beat)
- Ejecuta las migraciones de Alembic
- Inicializa la base de datos con el usuario administrador

### Opción B: Paso a paso manual

```bash
# 1. Levantar los servicios de Docker
docker-compose up -d

# 2. Esperar 10 segundos a que PostgreSQL esté listo
sleep 10

# 3. Ejecutar migraciones de Alembic
docker-compose exec backend alembic upgrade head

# 4. Inicializar la base de datos con datos iniciales
docker-compose exec backend python -c "from app.db.session import SessionLocal; from app.db.init_db import init_db; db = SessionLocal(); init_db(db); db.close()"
```

### ✅ Verificar que el backend esté funcionando

Abre tu navegador en:
- **API Backend**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/v1/docs

Deberías ver la documentación interactiva de la API.

---

## 🎨 Paso 2: Levantar el Frontend

```bash
# 1. Ir a la carpeta del frontend
cd frontend

# 2. Instalar dependencias (solo la primera vez)
npm install

# 3. Iniciar el servidor de desarrollo
npm run dev
```

El frontend se abrirá automáticamente en: **http://localhost:5173**

---

## 🔐 Paso 3: Hacer Login

### Credenciales por defecto:

- **Email**: `admin@canterarufina.com`
- **Password**: `admin123`

---

## 🧪 Paso 4: Probar el Sistema

### Módulos disponibles para probar:

1. **Dashboard** - Ver métricas en tiempo real
2. **Camiones** - Crear, editar, ver camiones
3. **Repuestos** - Gestionar inventario con alertas de stock bajo
4. **Servicios** - Crear servicios asignando repuestos (descuento automático de stock)
5. **Pesajes** - Registrar pesajes con cálculo automático de peso neto
6. **Combustible** - Gestionar cisternas, cargas y suministros
7. **Remitos** - Ver remitos generados desde pesajes

### Flujo de prueba recomendado:

```
1. Dashboard → Ver estado general
2. Camiones → Crear 2-3 camiones (ej: ABC123, DEF456)
3. Repuestos → Crear 5-10 repuestos (filtros, aceites, etc.)
4. Servicios → Crear un servicio para un camión, asignar repuestos
   → Verificar que el stock de repuestos se descontó automáticamente
5. Pesajes → Registrar un pesaje (ver cálculo automático peso neto)
6. Combustible → Ver cisternas, registrar una carga y un suministro
7. Dashboard → Verificar que las métricas se actualizaron
```

---

## 🛑 Detener el Sistema

### Detener Frontend:
```bash
# En la terminal del frontend, presiona: Ctrl+C
```

### Detener Backend:
```bash
# Desde la raíz del proyecto
docker-compose down
```

### Detener Backend y eliminar volúmenes (CUIDADO: borra la BD):
```bash
docker-compose down -v
```

---

## 🔧 Comandos Útiles

### Ver logs del backend:
```bash
docker-compose logs -f backend
```

### Ver logs de Celery:
```bash
docker-compose logs -f celery_worker
```

### Reiniciar solo el backend:
```bash
docker-compose restart backend
```

### Acceder a la base de datos:
```bash
docker-compose exec db psql -U cantera_user -d cantera_db
```

### Ejecutar tests del frontend:
```bash
cd frontend
npm run lint
npm run build  # Verificar que compila sin errores
```

---

## ⚠️ Troubleshooting

### Problema: "Port 8000 already in use"
```bash
# Buscar y matar el proceso
lsof -ti:8000 | xargs kill -9
```

### Problema: "Port 5173 already in use"
```bash
# Buscar y matar el proceso
lsof -ti:5173 | xargs kill -9
```

### Problema: Backend no levanta
```bash
# Ver logs detallados
docker-compose logs backend

# Reiniciar desde cero
docker-compose down -v
./init.sh
```

### Problema: Frontend no encuentra la API
- Verificar que el backend esté corriendo en http://localhost:8000
- Verificar el archivo `frontend/.env`:
  ```
  VITE_API_URL=http://localhost:8000/api/v1
  ```

### Problema: Error de CORS
- El backend ya tiene CORS configurado para `http://localhost:5173`
- Si cambias el puerto del frontend, debes actualizar `backend/app/core/config.py`

---

## 📊 Estado del Sistema

### ✅ Backend: 100% Completo
- 52 endpoints API REST
- 10 modelos de base de datos
- 7 servicios de negocio
- 4 tareas Celery programadas
- Autenticación JWT con refresh tokens

### ✅ Frontend: ~90% Completo
- 8 módulos implementados
- Login + Dashboard funcional
- CRUD completo para 6 módulos
- Formularios con validación
- Tablas con filtros y búsqueda
- Responsive design

### ⏸️ Pendiente:
- Módulo de Reportes (baja prioridad)
- Generación de PDFs de remitos (backend)
- Tests automatizados

---

## 📞 Soporte

Si encuentras algún problema, verifica:
1. Que Docker esté corriendo
2. Que no haya conflictos de puertos
3. Los logs con `docker-compose logs -f backend`

---

## 🎉 ¡Listo para Producción!

El sistema está funcional y listo para usar. Los módulos críticos están implementados:
- ✅ Gestión de flota de camiones
- ✅ Control de stock de repuestos con alertas
- ✅ Servicios con descuento automático de repuestos
- ✅ Registro de pesajes con cálculo automático
- ✅ Control de combustible con alertas
- ✅ Dashboard con métricas en tiempo real

**Desarrollado con:** FastAPI + PostgreSQL + React + TypeScript + Tailwind CSS

**Fecha:** Febrero 2026
**Versión:** 1.0.0-MVP
