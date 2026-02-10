# Despliegue en Railway - Sistema Cantera La Rufina

## Requisitos Previos
- Cuenta en [Railway](https://railway.app)
- Repositorio en GitHub con el codigo actualizado
- (Opcional) Dominio personalizado

---

## PASO 1: Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) e inicia sesion
2. Click en **New Project** > **Empty Project**
3. Dale un nombre al proyecto (ej: `cantera-la-rufina`)

---

## PASO 2: Agregar PostgreSQL

1. En el proyecto, click en **+ New** > **Database** > **Add PostgreSQL**
2. Railway crea automaticamente la base de datos
3. La variable `DATABASE_URL` estara disponible automaticamente

---

## PASO 3: Agregar Redis

1. Click en **+ New** > **Database** > **Add Redis**
2. Railway crea automaticamente Redis
3. La variable `REDIS_URL` estara disponible automaticamente

---

## PASO 4: Desplegar Backend

1. Click en **+ New** > **GitHub Repo**
2. Conecta tu cuenta de GitHub si no lo has hecho
3. Selecciona tu repositorio `sistemaCantera`
4. En la configuracion del servicio, configura:
   - **Root Directory**: `backend`
   - Railway detectara automaticamente el `railway.toml`

5. Ve a la pestana **Variables** y agrega:

```env
# Referencias automaticas (Railway las resuelve)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# Generar con: openssl rand -hex 32
SECRET_KEY=<tu-clave-secreta-de-32-caracteres>

# Password del admin inicial
ADMIN_PASSWORD=<password-seguro>

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Actualizar despues con URL del frontend
BACKEND_CORS_ORIGINS=["https://cantera-frontend.up.railway.app"]

# Entorno
ENVIRONMENT=production
```

6. Click en **Deploy** para iniciar el despliegue
7. Espera a que termine (las migraciones se ejecutan automaticamente)
8. Ve a **Settings** > **Networking** > **Generate Domain**
9. Anota el dominio generado (ej: `cantera-backend-xxx.up.railway.app`)

---

## PASO 5: Desplegar Frontend

1. Click en **+ New** > **GitHub Repo**
2. Selecciona el mismo repositorio `sistemaCantera`
3. En la configuracion:
   - **Root Directory**: `frontend`

4. Ve a **Variables** y agrega:

```env
# URL del backend (la que anotaste en el paso anterior)
VITE_API_URL=https://cantera-backend-xxx.up.railway.app/api/v1
```

5. Click en **Deploy**
6. Ve a **Settings** > **Networking** > **Generate Domain**
7. Anota el dominio del frontend

---

## PASO 6: Actualizar CORS del Backend

1. Vuelve al servicio **backend**
2. Ve a **Variables**
3. Actualiza `BACKEND_CORS_ORIGINS` con la URL exacta del frontend:

```env
BACKEND_CORS_ORIGINS=["https://cantera-frontend-xxx.up.railway.app"]
```

4. El backend se redesplegara automaticamente

---

## PASO 7: Verificar Despliegue

1. Accede a la URL del frontend
2. Inicia sesion con:
   - **Email**: `admin@canteralarufina.com.ar`
   - **Password**: El que configuraste en `ADMIN_PASSWORD`
3. **IMPORTANTE**: Cambia la password despues del primer login

---

## (Opcional) Dominio Personalizado

### Para el Backend:
1. Ve al servicio backend > **Settings** > **Networking** > **Custom Domain**
2. Agrega: `api-sistema.canteralarufina.com.ar`
3. Railway te dara un CNAME para configurar en tu DNS

### Para el Frontend:
1. Ve al servicio frontend > **Settings** > **Networking** > **Custom Domain**
2. Agrega: `sistema.canteralarufina.com.ar`
3. Configura el CNAME en tu DNS

### En tu proveedor de DNS:
| Tipo  | Nombre      | Valor                           |
|-------|-------------|---------------------------------|
| CNAME | sistema     | <cname-dado-por-railway>        |
| CNAME | api-sistema | <cname-dado-por-railway>        |

---

## (Opcional) Celery Worker

Si necesitas tareas en segundo plano:

1. Click en **+ New** > **GitHub Repo**
2. Selecciona el mismo repositorio
3. **Root Directory**: `backend`
4. Ve a **Settings** > **Deploy** y cambia el **Start Command**:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

5. Agrega las mismas variables que el backend

---

## Troubleshooting

### Error de CORS
- Verifica que `BACKEND_CORS_ORIGINS` tenga la URL exacta del frontend
- Formato correcto: `["https://tu-frontend.railway.app"]`
- Sin trailing slash al final

### Error de conexion a base de datos
- Verifica que `DATABASE_URL` este referenciando correctamente: `${{Postgres.DATABASE_URL}}`
- Revisa los logs del backend en Railway

### Frontend muestra error de API
- Verifica que `VITE_API_URL` termine en `/api/v1`
- Si cambias esta variable, debes **redesplegar** el frontend (no solo restart)

### Migraciones no ejecutan
- Revisa los logs del backend
- El `start.sh` ejecuta las migraciones automaticamente

### El backend no inicia
- Verifica que todas las variables obligatorias esten configuradas
- `DATABASE_URL`, `SECRET_KEY` son obligatorias
- Revisa los logs en Railway

---

## Comandos Utiles (Railway CLI)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Ver logs
railway logs

# Conectar a PostgreSQL
railway connect postgres

# Ejecutar comando en el backend
railway run python scripts/init_prod.py
```

---

## Costos Estimados

Railway cobra por uso. Estimacion mensual:
- **PostgreSQL**: ~$5-10/mes
- **Redis**: ~$5/mes
- **Backend**: ~$5-10/mes
- **Frontend**: ~$5/mes
- **Celery** (opcional): ~$5/mes

**Total**: ~$20-35/mes

Railway ofrece $5 de credito gratis mensual.
