# Agent Instructions - Sistema Cantera La Rufina

## Contexto del Proyecto

Estás trabajando en un **Sistema de Gestión para Cantera "La Rufina"** que administra:
- Control de camiones y servicios de mantenimiento
- Stock de repuestos con asignación automática
- Pesajes de camiones y generación de remitos
- Control de combustible (cisterna y suministros)
- Reportes operativos

**Usuarios del sistema:** ~20 (operadores + administradores)
**Acceso:** Web responsive (desktop + mobile)

---

## Stack Tecnológico

### Backend
- Python 3.11+ con FastAPI 0.104+
- PostgreSQL 15+ como base de datos
- SQLAlchemy 2.0 como ORM
- Alembic para migraciones
- Pydantic v2 para validación
- JWT con python-jose para autenticación
- Celery + Redis para tareas asíncronas (alertas de stock)
- Pytest para testing

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui para componentes
- **Colores:** Paleta ámbar/naranja (#f59e0b, #fb923c) para la marca
- Zustand para state management
- TanStack Query para data fetching
- React Hook Form + Zod para formularios
- TanStack Table para tablas
- React Router v6

### Infraestructura
- Monorepo con Docker Compose
- Nginx como proxy reverso (producción)
- Cloudinary para storage de imágenes de camiones

---

## Principios de Desarrollo

### 1. Arquitectura

**Backend:**
- Sigue arquitectura en capas: Endpoints → Services → Models
- NUNCA pongas lógica de negocio en los endpoints
- Usa dependency injection de FastAPI
- Todos los endpoints deben tener validación Pydantic
- Implementa soft deletes (campo `activo`, no eliminar registros)
- Transacciones de BD para operaciones críticas (asignación de repuestos con descuento de stock)

**Frontend:**
- Componentes pequeños y reutilizables
- Custom hooks para lógica compartida
- Separación: components / pages / services / stores
- TypeScript SIEMPRE, no uses `any`
- Loading states y error handling en todas las operaciones

### 2. Características Específicas del Proyecto

**Cálculos Automáticos:**
- Peso neto = Peso bruto - Peso tara (en pesajes)
- Nivel cisterna = Nivel anterior + Cargas - Suministros
- Costo total servicio = Costo mano obra + Suma(repuestos)
- Stock repuesto = Stock anterior - Cantidad usada en servicio

**Alertas Automáticas:**
- Stock bajo cuando stock_actual <= stock_minimo
- Cisterna baja cuando nivel_actual <= nivel_alerta
- Servicios programados próximos 7 días

**Formato Argentino:**
- Fechas: DD/MM/YYYY
- Números: separador de miles con punto (1.000)
- Decimales: coma (10,5)
- Moneda: $ (peso argentino)

### 3. Flujos Críticos

**Flujo de Pesaje → Remito:**
1. Operador registra pesaje (tara, bruto, material, cliente)
2. Sistema calcula peso neto automáticamente
3. Operador presiona "Generar Remito"
4. Sistema crea remito con datos del pesaje
5. Genera PDF descargable
6. Opcionalmente envía por email

**Flujo de Servicio con Repuestos:**
1. Se crea servicio asignado a un camión
2. Se seleccionan repuestos utilizados con cantidades
3. Sistema calcula subtotal por repuesto (cantidad × precio)
4. Sistema calcula costo total (mano obra + repuestos)
5. **CRÍTICO:** Sistema descuenta automáticamente stock de cada repuesto
6. Sistema crea movimiento de stock por cada repuesto (tipo: egreso)
7. Si algún repuesto queda con stock <= stock_mínimo, genera alerta

**Flujo de Suministro de Combustible:**
1. Operador registra litros suministrados a camión
2. Sistema descuenta automáticamente del nivel de cisterna
3. Si nivel cisterna <= nivel_alerta, genera alerta
4. Guarda lectura de km/horómetro para cálculo de rendimiento

### 4. Seguridad

**CRÍTICO:**
- ✅ Validación de permisos en TODOS los endpoints
- ✅ Solo administradores pueden crear/editar/eliminar
- ✅ Operadores pueden crear pesajes y suministros
- ✅ Passwords hasheados con bcrypt
- ✅ JWT con expiración (access: 30min, refresh: 7 días)
- ✅ Logs de todas las operaciones críticas

---

## Estructura del Proyecto (Monorepo)

```
cantera-rufina/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI + Python
├── docs/              # Documentación y skills
│   ├── agent.md       # Este archivo
│   └── skills/        # Skills específicos del proyecto
└── docker-compose.yml # Orquestación
```

---

## Variables de Entorno Importantes

```bash
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/cantera_rufina
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery & Redis
REDIS_URL=redis://localhost:6379/0

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Plan de Desarrollo

### Fase 1: Setup Inicial
1. Crear estructura de carpetas (backend + frontend)
2. Configurar Docker Compose
3. Configurar PostgreSQL
4. Setup inicial de FastAPI
5. Setup inicial de React + Vite

### Fase 2: Autenticación (Prioridad 1)
1. Model Usuario
2. Endpoints de auth (login, refresh)
3. JWT implementation
4. Roles (administrador, operador, solo_lectura)
5. Frontend: login page + auth context

### Fase 3: Módulos Core (Prioridad 2)
1. **Camiones:** CRUD completo
2. **Repuestos:** CRUD + alertas stock bajo
3. **Servicios:** CRUD + asignación repuestos + descuento stock
4. **Pesajes:** CRUD + cálculo peso neto
5. **Remitos:** Generación desde pesaje + PDF

### Fase 4: Combustible (Prioridad 3)
1. Cisterna (configuración)
2. Cargas de cisterna
3. Suministros a camiones
4. Alertas nivel bajo

### Fase 5: Dashboard y Reportes
1. Dashboard principal con widgets
2. Reportes de pesajes
3. Reportes de combustible
4. Reportes de mantenimiento
5. Exportación a PDF/Excel

---

## Comandos Útiles

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d
docker-compose logs -f backend
docker-compose exec backend alembic upgrade head

# Tests
pytest
pytest --cov=app tests/
```

---

## Uso de Skills

Este proyecto cuenta con skills especializados en `/docs/skills/`:
- `fastapi-crud.md` - Generación de CRUDs completos en FastAPI
- `react-forms.md` - Formularios React con validación
- `database-design.md` - Diseño de base de datos
- `auth-flow.md` - Implementación de autenticación JWT
- `docker-setup.md` - Configuración Docker

Consulta estos skills cuando necesites implementar funcionalidad específica.
