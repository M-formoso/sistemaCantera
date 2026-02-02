# Próximos Pasos de Desarrollo

Este documento describe los pasos siguientes para completar el desarrollo del Sistema Cantera La Rufina.

## ✅ Completado

- [x] Estructura base del proyecto (monorepo)
- [x] Configuración Docker Compose
- [x] Backend FastAPI con estructura de carpetas
- [x] Modelos SQLAlchemy (todas las entidades)
- [x] Schemas Pydantic básicos
- [x] Sistema de autenticación JWT
- [x] Configuración de Alembic
- [x] Frontend React + TypeScript + Vite
- [x] Configuración Tailwind CSS

## 🚧 Pendiente - Backend

### 1. Completar Schemas Pydantic (Alta Prioridad)

Crear schemas completos para:
- ✅ `schemas/auth.py` - Completado
- ✅ `schemas/usuario.py` - Completado
- ✅ `schemas/common.py` - Completado
- ⏸️ `schemas/camion.py`
- ⏸️ `schemas/repuesto.py`
- ⏸️ `schemas/servicio.py`
- ⏸️ `schemas/pesaje.py`
- ⏸️ `schemas/remito.py`
- ⏸️ `schemas/combustible.py`

### 2. Servicios de Lógica de Negocio

Crear servicios para cada módulo:
- ⏸️ `services/camion_service.py`
- ⏸️ `services/repuesto_service.py`
- ⏸️ `services/servicio_service.py` (con lógica de descuento de stock)
- ⏸️ `services/pesaje_service.py`
- ⏸️ `services/remito_service.py` (con generación desde pesaje)
- ⏸️ `services/combustible_service.py`
- ⏸️ `services/dashboard_service.py`
- ⏸️ `services/reporte_service.py`

### 3. Endpoints API REST

Crear endpoints completos en `api/v1/endpoints/`:
- ✅ `auth.py` - Completado
- ⏸️ `camiones.py`
- ⏸️ `repuestos.py`
- ⏸️ `servicios.py`
- ⏸️ `pesajes.py`
- ⏸️ `remitos.py`
- ⏸️ `combustible.py`
- ⏸️ `dashboard.py`
- ⏸️ `reportes.py`
- ⏸️ `upload.py` (para Cloudinary)

### 4. Tareas Celery

Crear tareas asíncronas en `tasks/`:
- ⏸️ `alertas.py`
  - `crear_alerta_stock_bajo()`
  - `verificar_nivel_cisterna()`
  - `verificar_servicios_proximos()`
- ⏸️ `reportes.py`
  - `generar_pdf_remito()`
  - `generar_reporte_excel()`

### 5. Tests

Crear tests unitarios y de integración:
- ⏸️ `tests/api/test_auth.py`
- ⏸️ `tests/api/test_camiones.py`
- ⏸️ `tests/api/test_servicios.py`
- ⏸️ `tests/api/test_pesajes.py`
- ⏸️ `tests/services/test_servicio_service.py`

## 🚧 Pendiente - Frontend

### 1. Configuración Base

- ⏸️ `src/lib/utils.ts` - Utilidades (cn, etc)
- ⏸️ `src/constants/index.ts` - Constantes
- ⏸️ `src/services/api.ts` - Cliente Axios configurado
- ⏸️ `src/types/index.ts` - Tipos TypeScript

### 2. Stores Zustand

- ⏸️ `stores/authStore.ts` - Estado de autenticación
- ⏸️ `stores/uiStore.ts` - Estado de UI (sidebar, modals)

### 3. Servicios API

Crear servicios para cada módulo:
- ⏸️ `services/authService.ts`
- ⏸️ `services/camionesService.ts`
- ⏸️ `services/repuestosService.ts`
- ⏸️ `services/serviciosService.ts`
- ⏸️ `services/pesajesService.ts`
- ⏸️ `services/remitosService.ts`
- ⏸️ `services/combustibleService.ts`
- ⏸️ `services/dashboardService.ts`

### 4. Componentes shadcn/ui

Instalar componentes básicos con CLI:
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add table
npx shadcn-ui@latest add form
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add select
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add alert
```

### 5. Componentes de Layout

- ⏸️ `components/layout/Header.tsx`
- ⏸️ `components/layout/Sidebar.tsx`
- ⏸️ `components/layout/MainLayout.tsx`

### 6. Páginas Principales

#### Autenticación
- ⏸️ `pages/auth/LoginPage.tsx`

#### Dashboard
- ⏸️ `pages/dashboard/DashboardPage.tsx`
  - Widget de pesajes del día
  - Widget de nivel de combustible
  - Widget de alertas
  - Widget de camiones operativos

#### Máquinas
- ⏸️ `pages/maquinas/CamionesPage.tsx` (lista)
- ⏸️ `pages/maquinas/CamionDetailPage.tsx`
- ⏸️ `pages/maquinas/RepuestosPage.tsx`
- ⏸️ `pages/maquinas/ServiciosPage.tsx`

#### Pesajes
- ⏸️ `pages/pesajes/PesajesPage.tsx`
- ⏸️ `pages/pesajes/PesajeFormPage.tsx`
- ⏸️ `pages/pesajes/RemitosPage.tsx`

#### Combustible
- ⏸️ `pages/combustible/CombustiblePage.tsx`
- ⏸️ `pages/combustible/SuministrosPage.tsx`

#### Reportes
- ⏸️ `pages/reportes/ReportesPage.tsx`

### 7. Componentes de Módulos

#### Máquinas
- ⏸️ `components/maquinas/CamionForm.tsx`
- ⏸️ `components/maquinas/CamionCard.tsx`
- ⏸️ `components/maquinas/ServicioForm.tsx`
- ⏸️ `components/maquinas/RepuestoSelector.tsx`

#### Pesajes
- ⏸️ `components/pesajes/PesajeForm.tsx`
- ⏸️ `components/pesajes/PesajesList.tsx`
- ⏸️ `components/pesajes/RemitoPreview.tsx`

#### Combustible
- ⏸️ `components/combustible/CisternaMeter.tsx`
- ⏸️ `components/combustible/SuministroForm.tsx`

### 8. Hooks Personalizados

- ⏸️ `hooks/useAuth.ts`
- ⏸️ `hooks/useCamiones.ts`
- ⏸️ `hooks/usePesajes.ts`
- ⏸️ `hooks/useDebounce.ts`

### 9. Router

- ⏸️ Configurar React Router con rutas protegidas
- ⏸️ Implementar ProtectedRoute component
- ⏸️ Configurar redirecciones según roles

## 📝 Orden Sugerido de Implementación

### Fase 1: Backend Core (1-2 días)
1. Completar schemas Pydantic
2. Crear servicios de negocio básicos
3. Implementar endpoints de Camiones
4. Implementar endpoints de Repuestos
5. Crear primera migración y probar

### Fase 2: Frontend Core (1-2 días)
1. Configurar cliente API
2. Crear authStore y authService
3. Implementar LoginPage
4. Crear MainLayout
5. Implementar Dashboard básico

### Fase 3: Módulo Camiones y Servicios (2-3 días)
**Backend:**
- Endpoints de Servicios con lógica de repuestos
- Endpoints de movimientos de stock

**Frontend:**
- Páginas de camiones
- Formularios de servicios
- Selector de repuestos

### Fase 4: Módulo Pesajes y Remitos (2-3 días)
**Backend:**
- Endpoints de Pesajes
- Endpoints de Remitos
- Generación de PDF

**Frontend:**
- Formulario de pesaje
- Lista de pesajes
- Vista de remitos
- Descarga de PDF

### Fase 5: Módulo Combustible (1-2 días)
**Backend:**
- Endpoints de combustible
- Lógica de cisterna

**Frontend:**
- Medidor de cisterna
- Formularios de carga y suministro
- Gráficos de consumo

### Fase 6: Dashboard y Reportes (2-3 días)
**Backend:**
- Servicio de dashboard con estadísticas
- Servicios de reportes
- Exportación a Excel/PDF

**Frontend:**
- Widgets del dashboard
- Páginas de reportes
- Filtros y exportación

### Fase 7: Tareas Asíncronas y Alertas (1 día)
- Implementar tareas Celery
- Sistema de alertas
- Notificaciones en frontend

### Fase 8: Testing y Refinamiento (2-3 días)
- Tests unitarios backend
- Tests de integración
- Manejo de errores
- Validaciones
- UX/UI refinement

## 🔑 Componentes Críticos

Estos componentes son críticos y deben implementarse con especial atención:

1. **Servicio con Repuestos** (`servicio_service.py`)
   - Transacciones atómicas
   - Descuento automático de stock
   - Generación de alertas

2. **Generación de Remitos** (`remito_service.py`)
   - Autoincremento de números
   - Generación de PDF
   - Envío por email

3. **Control de Combustible** (`combustible_service.py`)
   - Actualización de nivel de cisterna
   - Cálculos de consumo y rendimiento

4. **Dashboard** (`dashboard_service.py`)
   - Queries optimizadas
   - Cálculos agregados eficientes

## 📦 Dependencias Adicionales

### Backend
```bash
# Para PDF
pip install reportlab weasyprint

# Para Excel
pip install openpyxl pandas
```

### Frontend
```bash
# Dependencias de shadcn/ui que faltan
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install @radix-ui/react-label @radix-ui/react-select
npm install @radix-ui/react-tabs @radix-ui/react-toast
npm install tailwindcss-animate

# Para gráficos
npm install recharts

# Para fechas
npm install date-fns

# Para tablas
npm install @tanstack/react-table
```

## 🎯 Métricas de Progreso

**Backend**: ~40% completado
- Estructura y configuración: ✅ 100%
- Modelos: ✅ 100%
- Autenticación: ✅ 100%
- Schemas: ⏸️ 30%
- Servicios: ⏸️ 0%
- Endpoints: ⏸️ 10%
- Tareas Celery: ⏸️ 0%
- Tests: ⏸️ 0%

**Frontend**: ~20% completado
- Configuración: ✅ 100%
- Componentes UI base: ⏸️ 0%
- Servicios API: ⏸️ 0%
- Páginas: ⏸️ 0%
- Stores: ⏸️ 0%
- Componentes: ⏸️ 0%

**Progreso General**: ~30% completado

## 💡 Tips de Desarrollo

1. **Usa los skills de docs/skills/** cuando necesites generar CRUDs completos
2. **Sigue las convenciones** definidas en `docs/agent.md`
3. **Testea cada módulo** antes de pasar al siguiente
4. **Commits frecuentes** con mensajes descriptivos
5. **Documenta funciones complejas** con docstrings
6. **Valida en frontend Y backend** (doble validación)

## 🐛 Problemas Conocidos a Resolver

1. Falta completar package.json con todas las dependencias de shadcn/ui
2. Necesita configuración de variables de entorno de producción
3. Falta configuración de Nginx para producción
4. Falta implementación de backup automatizado

---

**Última actualización**: 28 Enero 2025
