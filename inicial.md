Sistema de Gestión de Cantera "La Rufina" - Documentación Técnica Completa
📋 Información del Proyecto
Nombre: Sistema de Gestión Cantera La Rufina
Versión: 1.0.0
Usuarios estimados: ~20 (operadores + administradores)
Tipo: Sistema de gestión operativa
Entorno: Web responsive (desktop + mobile)

🛠️ Stack Tecnológico
Backend

Framework: FastAPI 0.104+
Lenguaje: Python 3.11+
ORM: SQLAlchemy 2.0
Migraciones: Alembic
Validación: Pydantic v2
Autenticación: python-jose (JWT) + passlib
Base de Datos: PostgreSQL 15+
Workers: Celery + Redis
Storage: Cloudinary (imágenes de camiones)
Testing: Pytest + pytest-asyncio

Frontend

Framework: React 18 + Vite
Lenguaje: TypeScript 5+
Styling: Tailwind CSS
Componentes UI: shadcn/ui + lucide-react
State Management: Zustand
Data Fetching: TanStack Query (React Query)
Formularios: React Hook Form + Zod
Tablas: TanStack Table
Router: React Router v6
HTTP Client: Axios
Colores: Paleta ámbar/naranja para la marca

Infraestructura

Containerización: Docker + Docker Compose
Proxy Reverso: Nginx (producción)
Deploy: VPS (Railway/DigitalOcean)
Monitoreo: Sentry
CI/CD: GitHub Actions (opcional)

Desarrollo

Linting: Ruff (Python) + ESLint (TypeScript)
Formatting: Black + Prettier
Pre-commit: husky + lint-staged
Version Control: Git + GitHub


📁 Estructura del Proyecto (Monorepo)
cantera-rufina/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── layout/          # Header, Sidebar, Footer
│   │   │   ├── maquinas/        # Componentes módulo máquinas
│   │   │   ├── pesajes/         # Componentes módulo pesajes
│   │   │   ├── combustible/     # Componentes módulo combustible
│   │   │   ├── repuestos/       # Componentes stock repuestos
│   │   │   └── shared/          # Componentes compartidos
│   │   ├── pages/
│   │   │   ├── auth/            # Login
│   │   │   ├── dashboard/       # Dashboard principal
│   │   │   ├── maquinas/        # CRUD máquinas y servicios
│   │   │   ├── pesajes/         # CRUD pesajes y remitos
│   │   │   ├── combustible/     # CRUD combustible
│   │   │   ├── reportes/        # Reportes operativos
│   │   │   └── configuracion/   # Settings del sistema
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API calls
│   │   ├── stores/              # Zustand stores
│   │   ├── types/               # TypeScript types
│   │   ├── utils/               # Utilidades
│   │   ├── constants/           # Constantes
│   │   └── lib/                 # Config shadcn/ui
│   ├── public/
│   ├── .env.example
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── camiones.py
│   │   │   │   │   ├── repuestos.py
│   │   │   │   │   ├── servicios.py
│   │   │   │   │   ├── pesajes.py
│   │   │   │   │   ├── remitos.py
│   │   │   │   │   ├── combustible.py
│   │   │   │   │   ├── reportes.py
│   │   │   │   │   └── upload.py
│   │   │   │   └── api.py       # Router principal
│   │   ├── core/
│   │   │   ├── config.py        # Settings con Pydantic
│   │   │   ├── security.py      # JWT, hashing
│   │   │   ├── deps.py          # Dependencies FastAPI
│   │   │   └── celery_app.py    # Celery config
│   │   ├── db/
│   │   │   ├── base.py          # Base SQLAlchemy
│   │   │   ├── session.py       # DB session
│   │   │   └── init_db.py       # Datos iniciales
│   │   ├── models/
│   │   │   ├── base.py          # Base model
│   │   │   ├── usuario.py
│   │   │   ├── camion.py
│   │   │   ├── repuesto.py
│   │   │   ├── servicio.py
│   │   │   ├── pesaje.py
│   │   │   ├── remito.py
│   │   │   ├── combustible.py
│   │   │   └── asociaciones.py
│   │   ├── schemas/
│   │   │   ├── usuario.py       # Pydantic schemas
│   │   │   ├── camion.py
│   │   │   ├── repuesto.py
│   │   │   ├── servicio.py
│   │   │   ├── pesaje.py
│   │   │   ├── remito.py
│   │   │   ├── combustible.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── camion_service.py
│   │   │   ├── repuesto_service.py
│   │   │   ├── servicio_service.py
│   │   │   ├── pesaje_service.py
│   │   │   ├── remito_service.py
│   │   │   ├── combustible_service.py
│   │   │   ├── reporte_service.py
│   │   │   └── upload_service.py
│   │   ├── tasks/               # Celery tasks
│   │   │   ├── alertas.py       # Alertas de stock
│   │   │   └── reportes.py      # Generación reportes
│   │   ├── utils/
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   └── main.py              # App FastAPI
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── api/
│   │   ├── services/
│   │   └── conftest.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── pyproject.toml
│
├── docs/
│   ├── agent.md                 # Instrucciones para Claude Code
│   ├── skills/
│   │   ├── fastapi-crud.md      # Skill: Generar CRUDs
│   │   ├── react-forms.md       # Skill: Formularios React
│   │   ├── database-design.md   # Skill: Diseño BD
│   │   ├── auth-flow.md         # Skill: Autenticación
│   │   └── docker-setup.md      # Skill: Docker config
│   ├── api-documentation.md     # Docs de la API
│   ├── database-schema.md       # Esquema de BD
│   └── deployment.md            # Guía de deployment
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE

🗂️ Módulos del Sistema
1. Autenticación y Usuarios
Descripción: Sistema de login y roles
Roles:

Administrador: Acceso total al sistema
Operador: Acceso a pesajes y combustible
Solo Lectura: Ver reportes únicamente

Funcionalidades:

✅ Login con JWT (access token + refresh token)
✅ Recuperación de contraseña
✅ Cambio de contraseña
✅ Gestión de permisos por rol
✅ Logs de actividad

Endpoints:
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
GET    /api/v1/auth/me
PUT    /api/v1/auth/change-password

2. Control de Máquinas y Servicios
Descripción: Gestión de camiones, repuestos y mantenimientos
2.1 Inventario de Camiones
Funcionalidades:

✅ CRUD de camiones
✅ Datos: Patente, Modelo, Marca, Año
✅ Estados: Operativo, En servicio, Fuera de servicio
✅ Horómetro/Kilómetros actuales
✅ Foto del camión
✅ Chofer asignado
✅ Historial completo de servicios
✅ Alertas de mantenimiento programado

Endpoints:
GET    /api/v1/camiones
POST   /api/v1/camiones
GET    /api/v1/camiones/{id}
PUT    /api/v1/camiones/{id}
DELETE /api/v1/camiones/{id}
GET    /api/v1/camiones/{id}/servicios
GET    /api/v1/camiones/{id}/consumo-combustible
2.2 Stock de Repuestos
Funcionalidades:

✅ CRUD de repuestos
✅ Catálogo: Nombre, código, categoría
✅ Stock actual y stock mínimo
✅ Precio unitario
✅ Proveedor
✅ Ubicación en depósito
✅ Alertas de stock bajo
✅ Historial de movimientos

Endpoints:
GET    /api/v1/repuestos
POST   /api/v1/repuestos
GET    /api/v1/repuestos/{id}
PUT    /api/v1/repuestos/{id}
DELETE /api/v1/repuestos/{id}
GET    /api/v1/repuestos/stock-bajo
GET    /api/v1/repuestos/{id}/movimientos
2.3 Registro de Servicios
Funcionalidades:

✅ Crear servicio/mantenimiento
✅ Asignar a camión
✅ Fecha y tipo de servicio (preventivo, correctivo, emergencia)
✅ Descripción del trabajo realizado
✅ Asignación de repuestos utilizados (con descuento automático de stock)
✅ Costo de mano de obra
✅ Costo total calculado
✅ Lectura de horómetro/km al momento del servicio
✅ Mecánico que realizó el trabajo
✅ Estados: Programado, En proceso, Completado
✅ Adjuntar fotos/documentos

Endpoints:
GET    /api/v1/servicios
POST   /api/v1/servicios
GET    /api/v1/servicios/{id}
PUT    /api/v1/servicios/{id}
DELETE /api/v1/servicios/{id}
POST   /api/v1/servicios/{id}/asignar-repuestos
GET    /api/v1/servicios/programados
GET    /api/v1/servicios/por-camion/{camion_id}

3. Pesajes y Remitos
Descripción: Sistema de pesaje de camiones y generación de remitos
3.1 Registro de Pesajes
Funcionalidades:

✅ Registrar peso tara (camión vacío)
✅ Registrar peso bruto (camión cargado)
✅ Cálculo automático de peso neto (bruto - tara)
✅ Fecha y hora del pesaje
✅ Patente del camión (selección desde BD)
✅ Material/árido cargado
✅ Chofer
✅ Cliente/Destino
✅ Observaciones
✅ Generar remito automáticamente

Campos del pesaje:
- Fecha/hora
- Camión (patente)
- Chofer
- Peso tara (kg)
- Peso bruto (kg)
- Peso neto (calculado)
- Material cargado
- Cliente/Destino
- Observaciones
Endpoints:
GET    /api/v1/pesajes
POST   /api/v1/pesajes
GET    /api/v1/pesajes/{id}
PUT    /api/v1/pesajes/{id}
DELETE /api/v1/pesajes/{id}
GET    /api/v1/pesajes/por-fecha
GET    /api/v1/pesajes/por-camion/{camion_id}
POST   /api/v1/pesajes/{id}/generar-remito
3.2 Remitos
Funcionalidades:

✅ Generación automática desde pesaje
✅ Edición manual de remitos
✅ Número de remito (autoincremental)
✅ Datos: Cliente, producto, peso neto, fecha
✅ Observaciones adicionales
✅ Exportar a PDF para imprimir
✅ Enviar por email
✅ Historial de remitos

Endpoints:
GET    /api/v1/remitos
POST   /api/v1/remitos
GET    /api/v1/remitos/{id}
PUT    /api/v1/remitos/{id}
DELETE /api/v1/remitos/{id}
GET    /api/v1/remitos/{id}/pdf
GET    /api/v1/remitos/por-cliente
POST   /api/v1/remitos/{id}/enviar-email

4. Control de Combustible
Descripción: Gestión de cisterna y suministro a camiones
4.1 Cisterna Principal
Funcionalidades:

✅ Capacidad total de la cisterna
✅ Nivel actual de combustible
✅ Indicador visual de porcentaje
✅ Alertas cuando está bajo (< 20%)
✅ Historial de recargas

Endpoints:
GET    /api/v1/combustible/cisterna
PUT    /api/v1/combustible/cisterna/config
GET    /api/v1/combustible/cisterna/nivel-actual
4.2 Cargas de Cisterna
Funcionalidades:

✅ Registrar recarga de cisterna
✅ Fecha y hora de carga
✅ Litros ingresados
✅ Proveedor
✅ Costo total
✅ Número de factura/remito
✅ Actualización automática del nivel
✅ Cálculo de costo por litro

Endpoints:
GET    /api/v1/combustible/cargas
POST   /api/v1/combustible/cargas
GET    /api/v1/combustible/cargas/{id}
PUT    /api/v1/combustible/cargas/{id}
DELETE /api/v1/combustible/cargas/{id}
4.3 Suministro a Camiones
Funcionalidades:

✅ Registrar carga de combustible a camión
✅ Fecha y hora
✅ Patente del camión (selección)
✅ Litros suministrados
✅ Chofer que recibe
✅ Lectura de odómetro/horómetro
✅ Descuento automático del nivel de cisterna
✅ Observaciones

Endpoints:
GET    /api/v1/combustible/suministros
POST   /api/v1/combustible/suministros
GET    /api/v1/combustible/suministros/{id}
PUT    /api/v1/combustible/suministros/{id}
DELETE /api/v1/combustible/suministros/{id}
GET    /api/v1/combustible/suministros/por-camion/{camion_id}

5. Dashboard Principal
Descripción: Vista general de operaciones del día
Widgets:

📊 Resumen de pesajes del día (cantidad y toneladas totales)
⛽ Nivel de combustible en cisterna (visual + porcentaje)
🚨 Alertas de stock bajo en repuestos
🚛 Camiones operativos vs en servicio
📋 Últimos 10 pesajes registrados
🔧 Servicios programados próximos 7 días
📈 Gráfico de pesajes últimos 30 días
⛽ Gráfico de consumo de combustible por camión

Endpoints:
GET    /api/v1/dashboard/resumen-dia
GET    /api/v1/dashboard/alertas
GET    /api/v1/dashboard/estadisticas-mes

6. Reportes
Descripción: Informes operativos y estadísticas
Reportes disponibles:
6.1 Pesajes:

Total de pesajes por período
Toneladas totales por material
Pesajes por camión
Pesajes por cliente
Gráficos de tendencias

6.2 Combustible:

Consumo total por período
Consumo por camión
Promedio de consumo por camión
Rendimiento (km o horas por litro)
Costo total de combustible
Comparativa entre camiones

6.3 Mantenimiento:

Servicios realizados por período
Costo total de mantenimiento
Costo por camión
Repuestos más utilizados
Distribución por tipo de servicio

6.4 Stock:

Estado actual de repuestos
Movimientos de stock
Valor total de inventario
Repuestos bajo stock mínimo

Funcionalidades:

✅ Filtros por fecha (desde/hasta)
✅ Filtros por camión
✅ Exportar a PDF
✅ Exportar a Excel
✅ Gráficos interactivos

Endpoints:
GET    /api/v1/reportes/pesajes
GET    /api/v1/reportes/combustible
GET    /api/v1/reportes/mantenimiento
GET    /api/v1/reportes/stock
POST   /api/v1/reportes/export-pdf
POST   /api/v1/reportes/export-excel

7. Configuración
Descripción: Parámetros del sistema
Funcionalidades:

✅ Datos de la cantera (nombre, logo, datos contacto)
✅ Configuración de cisterna (capacidad, alertas)
✅ Tipos de materiales/áridos
✅ Categorías de repuestos
✅ Gestión de usuarios
✅ Backup de datos

Endpoints:
GET    /api/v1/config/general
PUT    /api/v1/config/general
GET    /api/v1/config/materiales
POST   /api/v1/config/materiales
GET    /api/v1/config/categorias-repuestos
POST   /api/v1/config/categorias-repuestos

💾 Esquema de Base de Datos
Tablas Principales
usuarios
sql- id: UUID (PK)
- email: VARCHAR(255) UNIQUE NOT NULL
- password_hash: VARCHAR(255) NOT NULL
- nombre: VARCHAR(100) NOT NULL
- rol: ENUM ('administrador', 'operador', 'solo_lectura')
- activo: BOOLEAN DEFAULT TRUE
- ultimo_acceso: TIMESTAMP
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
camiones
sql- id: UUID (PK)
- patente: VARCHAR(20) UNIQUE NOT NULL
- marca: VARCHAR(100)
- modelo: VARCHAR(100)
- año: INTEGER
- tipo: ENUM ('volcador', 'acoplado', 'mixer', 'otro')
- estado: ENUM ('operativo', 'en_servicio', 'fuera_servicio')
- kilometraje_actual: INTEGER
- horometro_actual: DECIMAL(10,2)
- chofer_habitual: VARCHAR(100)
- foto: VARCHAR(500)
- observaciones: TEXT
- activo: BOOLEAN DEFAULT TRUE
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
repuestos
sql- id: UUID (PK)
- codigo: VARCHAR(50) UNIQUE
- nombre: VARCHAR(255) NOT NULL
- categoria: VARCHAR(100)
- stock_actual: DECIMAL(10,2) NOT NULL
- stock_minimo: DECIMAL(10,2) DEFAULT 0
- unidad: VARCHAR(20)  -- unidades, litros, kg, etc
- precio_unitario: DECIMAL(10,2)
- proveedor: VARCHAR(255)
- ubicacion_deposito: VARCHAR(100)
- activo: BOOLEAN DEFAULT TRUE
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
servicios
sql- id: UUID (PK)
- camion_id: UUID (FK camiones)
- fecha: DATE NOT NULL
- tipo: ENUM ('preventivo', 'correctivo', 'emergencia')
- descripcion: TEXT NOT NULL
- kilometraje_servicio: INTEGER
- horometro_servicio: DECIMAL(10,2)
- mecanico: VARCHAR(255)
- costo_mano_obra: DECIMAL(10,2)
- costo_total: DECIMAL(10,2)  -- calculado
- estado: ENUM ('programado', 'en_proceso', 'completado')
- observaciones: TEXT
- documentos: JSONB  -- URLs de fotos/docs
- created_by: UUID (FK usuarios)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
servicios_repuestos (relación many-to-many)
sql- id: UUID (PK)
- servicio_id: UUID (FK servicios)
- repuesto_id: UUID (FK repuestos)
- cantidad: DECIMAL(10,2) NOT NULL
- precio_unitario: DECIMAL(10,2)
- subtotal: DECIMAL(10,2)  -- calculado
- created_at: TIMESTAMP
movimientos_stock
sql- id: UUID (PK)
- repuesto_id: UUID (FK repuestos)
- tipo: ENUM ('ingreso', 'egreso')
- cantidad: DECIMAL(10,2) NOT NULL
- referencia_tipo: VARCHAR(50)  -- 'servicio', 'compra', 'ajuste'
- referencia_id: UUID NULL  -- ID del servicio, compra, etc
- observaciones: TEXT
- usuario_id: UUID (FK usuarios)
- created_at: TIMESTAMP
pesajes
sql- id: UUID (PK)
- numero_pesaje: INTEGER UNIQUE AUTO_INCREMENT
- fecha: TIMESTAMP NOT NULL
- camion_id: UUID (FK camiones)
- chofer: VARCHAR(100)
- peso_tara: DECIMAL(10,2) NOT NULL  -- kg
- peso_bruto: DECIMAL(10,2) NOT NULL  -- kg
- peso_neto: DECIMAL(10,2)  -- calculado (bruto - tara)
- material: VARCHAR(100)
- cliente_destino: VARCHAR(255)
- observaciones: TEXT
- remito_generado: BOOLEAN DEFAULT FALSE
- created_by: UUID (FK usuarios)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
remitos
sql- id: UUID (PK)
- numero_remito: INTEGER UNIQUE AUTO_INCREMENT
- pesaje_id: UUID (FK pesajes) NULL
- fecha: DATE NOT NULL
- cliente: VARCHAR(255) NOT NULL
- producto: VARCHAR(100) NOT NULL
- peso_neto: DECIMAL(10,2) NOT NULL
- camion_patente: VARCHAR(20)
- chofer: VARCHAR(100)
- observaciones: TEXT
- pdf_url: VARCHAR(500)
- enviado_email: BOOLEAN DEFAULT FALSE
- created_by: UUID (FK usuarios)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
cisterna_combustible
sql- id: UUID (PK)
- capacidad_total: DECIMAL(10,2) NOT NULL  -- litros
- nivel_actual: DECIMAL(10,2) NOT NULL  -- litros
- nivel_alerta: DECIMAL(10,2) DEFAULT 1000  -- litros para alertar
- updated_at: TIMESTAMP
cargas_cisterna
sql- id: UUID (PK)
- fecha: TIMESTAMP NOT NULL
- litros: DECIMAL(10,2) NOT NULL
- proveedor: VARCHAR(255)
- costo_total: DECIMAL(10,2)
- costo_por_litro: DECIMAL(6,2)  -- calculado
- numero_factura: VARCHAR(100)
- observaciones: TEXT
- created_by: UUID (FK usuarios)
- created_at: TIMESTAMP
suministros_combustible
sql- id: UUID (PK)
- fecha: TIMESTAMP NOT NULL
- camion_id: UUID (FK camiones)
- litros: DECIMAL(10,2) NOT NULL
- chofer: VARCHAR(100)
- kilometraje: INTEGER
- horometro: DECIMAL(10,2)
- observaciones: TEXT
- created_by: UUID (FK usuarios)
- created_at: TIMESTAMP
configuracion
sql- id: UUID (PK)
- clave: VARCHAR(100) UNIQUE NOT NULL
- valor: JSONB NOT NULL
- descripcion: TEXT
- updated_by: UUID (FK usuarios)
- updated_at: TIMESTAMP

🤖 Archivo para Claude Code
📄 docs/agent.md
markdown# Agent Instructions - Sistema Cantera La Rufina

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

### 4. Convenciones de Código

**Python:**
```python
# Nombres descriptivos en español
def obtener_pesajes_por_camion(camion_id: UUID) -> List[PesajeSchema]:
    pass

# Type hints SIEMPRE
def crear_servicio_con_repuestos(
    db: Session,
    servicio_data: ServicioCreate,
    repuestos: List[RepuestoAsignado]
) -> Servicio:
    pass

# Docstrings para funciones públicas
def descontar_stock_repuesto(db: Session, repuesto_id: UUID, cantidad: Decimal) -> None:
    """
    Descuenta stock de un repuesto y crea movimiento.
    
    Args:
        db: Sesión de base de datos
        repuesto_id: ID del repuesto
        cantidad: Cantidad a descontar
    
    Raises:
        HTTPException: Si no hay stock suficiente
    """
    pass
```

**TypeScript:**
```typescript
// Interfaces descriptivas
interface PesajeFormData {
  camionId: string;
  chofer: string;
  pesoTara: number;
  pesoBruto: number;
  material: string;
  clienteDestino: string;
}

// Cálculos en funciones puras
const calcularPesoNeto = (bruto: number, tara: number): number => {
  return bruto - tara;
};

// Formateo argentino
const formatearPeso = (peso: number): string => {
  return new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(peso);
};
```

### 5. Estructura de Archivos

**Al crear nuevos módulos backend:**
```
1. models/{modulo}.py
2. schemas/{modulo}.py
3. services/{modulo}_service.py
4. api/v1/endpoints/{modulo}.py
5. tests/api/test_{modulo}.py
```

**Frontend por feature:**
```
src/
├── components/{modulo}/
│   ├── {Modulo}List.tsx
│   ├── {Modulo}Form.tsx
│   ├── {Modulo}Detail.tsx
│   └── index.ts
├── pages/{modulo}/
│   ├── index.tsx
│   ├── create.tsx
│   └── [id].tsx
├── services/{modulo}Service.ts
└── types/{modulo}.ts
```

### 6. Patrones Requeridos

**CRUD Completo (ejemplo Camiones):**
```python
# backend/app/api/v1/endpoints/camiones.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.schemas.camion import CamionSchema, CamionCreate, CamionUpdate
from app.services import camion_service

router = APIRouter()

@router.get("/", response_model=List[CamionSchema])
async def listar_camiones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todos los camiones con paginación."""
    return camion_service.obtener_todos(
        db,
        skip=skip,
        limit=limit,
        solo_activos=solo_activos
    )

@router.post("/", response_model=CamionSchema, status_code=201)
async def crear_camion(
    camion: CamionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo camión."""
    return camion_service.crear(db, camion)

@router.get("/{id}", response_model=CamionSchema)
async def obtener_camion(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene un camión específico."""
    camion = camion_service.obtener_por_id(db, id)
    if not camion:
        raise HTTPException(status_code=404, detail="Camión no encontrado")
    return camion

@router.get("/{id}/servicios", response_model=List[ServicioSchema])
async def obtener_servicios_camion(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene historial de servicios de un camión."""
    return camion_service.obtener_servicios(db, id)

@router.get("/{id}/consumo-combustible")
async def obtener_consumo_combustible(
    id: UUID,
    fecha_desde: date = None,
    fecha_hasta: date = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene estadísticas de consumo de combustible."""
    return camion_service.calcular_consumo(db, id, fecha_desde, fecha_hasta)
```

**React Component con Cálculo Automático:**
```typescript
// components/pesajes/PesajeForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useEffect } from 'react';

const pesajeSchema = z.object({
  camionId: z.string().uuid(),
  chofer: z.string().min(1),
  pesoTara: z.number().positive(),
  pesoBruto: z.number().positive(),
  material: z.string().min(1),
  clienteDestino: z.string().min(1),
  observaciones: z.string().optional(),
});

type PesajeFormData = z.infer;

export function PesajeForm() {
  const form = useForm({
    resolver: zodResolver(pesajeSchema),
  });

  const pesoTara = form.watch('pesoTara');
  const pesoBruto = form.watch('pesoBruto');

  // Calcular peso neto automáticamente
  const pesoNeto = pesoBruto && pesoTara ? pesoBruto - pesoTara : 0;

  const onSubmit = async (data: PesajeFormData) => {
    // Incluir peso neto calculado
    const pesajeCompleto = {
      ...data,
      pesoNeto
    };
    // Enviar a API...
  };

  return (
    
      {/* Campos del formulario */}
      
      {/* Mostrar peso neto calculado */}
      
        Peso Neto Calculado:
        
          {pesoNeto.toLocaleString('es-AR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })} kg
        
      
    
  );
}
```

### 7. Seguridad

**CRÍTICO:**
- ✅ Validación de permisos en TODOS los endpoints
- ✅ Solo administradores pueden crear/editar/eliminar
- ✅ Operadores pueden crear pesajes y suministros
- ✅ Passwords hasheados con bcrypt
- ✅ JWT con expiración (access: 30min, refresh: 7 días)
- ✅ Logs de todas las operaciones críticas

### 8. Testing

**Mínimo requerido:**
```python
# tests/api/test_pesajes.py
def test_crear_pesaje_calcula_peso_neto(client, auth_headers, db, camion):
    response = client.post(
        "/api/v1/pesajes/",
        json={
            "camion_id": str(camion.id),
            "chofer": "Juan Pérez",
            "peso_tara": 8000.0,
            "peso_bruto": 28000.0,
            "material": "Arena",
            "cliente_destino": "Constructor S.A."
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["peso_neto"] == 20000.0  # 28000 - 8000

def test_servicio_descuenta_stock_repuestos(client, auth_headers, db, camion, repuesto):
    stock_inicial = repuesto.stock_actual
    
    response = client.post(
        "/api/v1/servicios/",
        json={
            "camion_id": str(camion.id),
            "fecha": "2024-01-15",
            "tipo": "correctivo",
            "descripcion": "Cambio de filtro",
            "costo_mano_obra": 5000.0,
            "repuestos": [
                {
                    "repuesto_id": str(repuesto.id),
                    "cantidad": 2
                }
            ]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    
    # Verificar que se descontó stock
    db.refresh(repuesto)
    assert repuesto.stock_actual == stock_inicial - 2
```

---

## Casos de Uso Frecuentes

### 1. Crear servicio con asignación de repuestos
```python
# backend/app/services/servicio_service.py
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.servicio import Servicio, ServicioRepuesto
from app.models.movimiento_stock import MovimientoStock
from app.schemas.servicio import ServicioCreate, RepuestoAsignado
from app.services import repuesto_service

def crear_con_repuestos(
    db: Session,
    servicio_data: ServicioCreate,
    repuestos: List[RepuestoAsignado],
    usuario_id: UUID
) -> Servicio:
    """Crea servicio y asigna repuestos descontando stock."""
    
    # 1. Crear servicio
    db_servicio = Servicio(**servicio_data.model_dump())
    db.add(db_servicio)
    db.flush()  # Para obtener el ID
    
    costo_repuestos = Decimal(0)
    
    # 2. Procesar cada repuesto
    for rep_asignado in repuestos:
        repuesto = repuesto_service.obtener_por_id(db, rep_asignado.repuesto_id)
        
        if not repuesto:
            raise HTTPException(404, f"Repuesto no encontrado")
        
        if repuesto.stock_actual < rep_asignado.cantidad:
            raise HTTPException(400, f"Stock insuficiente de {repuesto.nombre}")
        
        # Crear relación servicio-repuesto
        servicio_repuesto = ServicioRepuesto(
            servicio_id=db_servicio.id,
            repuesto_id=repuesto.id,
            cantidad=rep_asignado.cantidad,
            precio_unitario=repuesto.precio_unitario,
            subtotal=rep_asignado.cantidad * repuesto.precio_unitario
        )
        db.add(servicio_repuesto)
        
        # Descontar stock
        repuesto.stock_actual -= rep_asignado.cantidad
        
        # Crear movimiento de stock
        movimiento = MovimientoStock(
            repuesto_id=repuesto.id,
            tipo='egreso',
            cantidad=rep_asignado.cantidad,
            referencia_tipo='servicio',
            referencia_id=db_servicio.id,
            usuario_id=usuario_id
        )
        db.add(movimiento)
        
        costo_repuestos += servicio_repuesto.subtotal
        
        # Verificar si quedó bajo stock mínimo
        if repuesto.stock_actual <= repuesto.stock_minimo:
            # Crear alerta (via Celery task)
            from app.tasks.alertas import crear_alerta_stock_bajo
            crear_alerta_stock_bajo.delay(str(repuesto.id))
    
    # 3. Calcular costo total
    db_servicio.costo_total = servicio_data.costo_mano_obra + costo_repuestos
    
    db.commit()
    db.refresh(db_servicio)
    return db_servicio
```

### 2. Generar remito desde pesaje
```python
# backend/app/services/remito_service.py
def generar_desde_pesaje(db: Session, pesaje_id: UUID, usuario_id: UUID) -> Remito:
    """Genera remito automáticamente desde un pesaje."""
    
    pesaje = db.query(Pesaje).filter(Pesaje.id == pesaje_id).first()
    if not pesaje:
        raise HTTPException(404, "Pesaje no encontrado")
    
    if pesaje.remito_generado:
        raise HTTPException(400, "Este pesaje ya tiene un remito generado")
    
    # Obtener próximo número de remito
    ultimo_remito = db.query(Remito).order_by(Remito.numero_remito.desc()).first()
    proximo_numero = (ultimo_remito.numero_remito + 1) if ultimo_remito else 1
    
    # Crear remito con datos del pesaje
    remito = Remito(
        numero_remito=proximo_numero,
        pesaje_id=pesaje.id,
        fecha=pesaje.fecha.date(),
        cliente=pesaje.cliente_destino,
        producto=pesaje.material,
        peso_neto=pesaje.peso_neto,
        camion_patente=pesaje.camion.patente,
        chofer=pesaje.chofer,
        observaciones=pesaje.observaciones,
        created_by=usuario_id
    )
    
    db.add(remito)
    
    # Marcar pesaje como procesado
    pesaje.remito_generado = True
    
    db.commit()
    db.refresh(remito)
    
    # Generar PDF (async task)
    from app.tasks.reportes import generar_pdf_remito
    generar_pdf_remito.delay(str(remito.id))
    
    return remito
```

### 3. Dashboard con estadísticas del día
```python
# backend/app/api/v1/endpoints/dashboard.py
@router.get("/resumen-dia")
async def obtener_resumen_dia(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene resumen de operaciones del día actual."""
    
    hoy = date.today()
    
    # Pesajes del día
    pesajes_hoy = db.query(Pesaje).filter(
        func.date(Pesaje.fecha) == hoy
    ).all()
    
    total_pesajes = len(pesajes_hoy)
    total_toneladas = sum(p.peso_neto for p in pesajes_hoy) / 1000  # kg a toneladas
    
    # Nivel de combustible
    cisterna = db.query(CisternaCombustible).first()
    porcentaje_combustible = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
    
    # Camiones por estado
    camiones = db.query(Camion).filter(Camion.activo == True).all()
    camiones_operativos = sum(1 for c in camiones if c.estado == 'operativo')
    camiones_en_servicio = sum(1 for c in camiones if c.estado == 'en_servicio')
    
    # Repuestos bajo stock
    repuestos_bajos = db.query(Repuesto).filter(
        Repuesto.stock_actual <= Repuesto.stock_minimo,
        Repuesto.activo == True
    ).count()
    
    # Servicios próximos
    proximos_7_dias = hoy + timedelta(days=7)
    servicios_programados = db.query(Servicio).filter(
        Servicio.estado == 'programado',
        Servicio.fecha.between(hoy, proximos_7_dias)
    ).count()
    
    return {
        "pesajes": {
            "cantidad": total_pesajes,
            "toneladas": round(total_toneladas, 2)
        },
        "combustible": {
            "nivel_actual": cisterna.nivel_actual,
            "capacidad_total": cisterna.capacidad_total,
            "porcentaje": round(porcentaje_combustible, 1)
        },
        "camiones": {
            "operativos": camiones_operativos,
            "en_servicio": camiones_en_servicio,
            "total": len(camiones)
        },
        "alertas": {
            "repuestos_bajo_stock": repuestos_bajos,
            "servicios_proximos": servicios_programados
        }
    }
```

---

## Tareas Celery

### Alerta de stock bajo
```python
# backend/app/tasks/alertas.py
from celery import shared_task
from app.db.session import SessionLocal
from app.services import repuesto_service, alerta_service

@shared_task
def crear_alerta_stock_bajo(repuesto_id: str):
    """Crea alerta cuando un repuesto queda bajo stock mínimo."""
    db = SessionLocal()
    try:
        from uuid import UUID
        repuesto = repuesto_service.obtener_por_id(db, UUID(repuesto_id))
        
        if not repuesto:
            return "Repuesto no encontrado"
        
        if repuesto.stock_actual > repuesto.stock_minimo:
            return "Stock OK, no requiere alerta"
        
        # Crear alerta para administradores
        from app.models.usuario import Usuario
        admins = db.query(Usuario).filter(Usuario.rol == 'administrador').all()
        
        for admin in admins:
            # Evitar duplicados - verificar si ya existe alerta activa
            alerta_existente = db.query(Alerta).filter(
                Alerta.usuario_id == admin.id,
                Alerta.tipo == 'stock_bajo',
                Alerta.entidad_id == repuesto.id,
                Alerta.resuelta == False
            ).first()
            
            if not alerta_existente:
                alerta = Alerta(
                    usuario_id=admin.id,
                    tipo='stock_bajo',
                    titulo=f'Stock bajo: {repuesto.nombre}',
                    mensaje=f'El repuesto {repuesto.nombre} (código: {repuesto.codigo}) tiene stock actual de {repuesto.stock_actual} {repuesto.unidad}, por debajo del mínimo de {repuesto.stock_minimo} {repuesto.unidad}',
                    prioridad='alta',
                    entidad_tipo='repuesto',
                    entidad_id=repuesto.id
                )
                db.add(alerta)
        
        db.commit()
        return f"Alertas creadas para {len(admins)} administradores"
        
    finally:
        db.close()

@shared_task
def verificar_nivel_cisterna():
    """Tarea programada que verifica nivel de cisterna diariamente."""
    db = SessionLocal()
    try:
        cisterna = db.query(CisternaCombustible).first()
        
        if cisterna.nivel_actual <= cisterna.nivel_alerta:
            # Crear alerta
            from app.models.usuario import Usuario
            admins = db.query(Usuario).filter(Usuario.rol == 'administrador').all()
            
            for admin in admins:
                alerta = Alerta(
                    usuario_id=admin.id,
                    tipo='combustible_bajo',
                    titulo='Nivel bajo de combustible en cisterna',
                    mensaje=f'La cisterna tiene {cisterna.nivel_actual} litros, por debajo del nivel de alerta de {cisterna.nivel_alerta} litros',
                    prioridad='critica'
                )
                db.add(alerta)
            
            db.commit()
            return f"Alertas de combustible bajo creadas para {len(admins)} admins"
        
        return "Nivel de cisterna OK"
    finally:
        db.close()
```

---

## Comandos Útiles
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
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
docker-compose down

# Tests
pytest
pytest tests/api/test_pesajes.py -v
pytest --cov=app tests/

# Celery (para alertas)
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
```

---

## Variables de Entorno
```bash
# .env.example

# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/cantera_rufina
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Celery & Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cloudinary (para fotos de camiones)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email (opcional, para envío de remitos)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=cantera.rufina@example.com

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Próximos Pasos

Cuando empieces a trabajar:

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

**¿Listo para empezar? Indica qué módulo quieres que implemente primero y te daré el código completo.**