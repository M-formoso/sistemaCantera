# Despliegue en Railway - Sistema Cantera La Rufina

## Dominio Final
- **Frontend**: `https://sistema.canteralarufina.com.ar`
- **API Backend**: `https://api-sistema.canteralarufina.com.ar`

---

## Paso 1: Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) e inicia sesión
2. Crea un nuevo proyecto: **New Project** → **Empty Project**
3. Nombra el proyecto: `cantera-la-rufina`

---

## Paso 2: Agregar Base de Datos PostgreSQL

1. En el proyecto, click en **+ New** → **Database** → **Add PostgreSQL**
2. Railway creará automáticamente la base de datos
3. Click en el servicio PostgreSQL y ve a **Variables**
4. Copia el valor de `DATABASE_URL` (lo necesitarás después)

---

## Paso 3: Agregar Redis

1. Click en **+ New** → **Database** → **Add Redis**
2. Railway creará automáticamente Redis
3. Click en el servicio Redis y ve a **Variables**
4. Copia el valor de `REDIS_URL` (lo necesitarás después)

---

## Paso 4: Desplegar Backend

1. Click en **+ New** → **GitHub Repo**
2. Selecciona tu repositorio `sistemaCantera`
3. En la configuración del servicio:
   - **Root Directory**: `backend`
   - Railway detectará automáticamente el `railway.toml`

4. Ve a **Variables** y agrega las siguientes:

```env
DATABASE_URL=<pegar URL de PostgreSQL>
REDIS_URL=<pegar URL de Redis>
CELERY_BROKER_URL=<pegar URL de Redis>
CELERY_RESULT_BACKEND=<pegar URL de Redis>
SECRET_KEY=<generar con: openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=["https://sistema.canteralarufina.com.ar"]
ADMIN_PASSWORD=<contraseña-segura-para-admin>
```

5. Ve a **Settings** → **Networking** → **Generate Domain**
   - Anota el dominio generado (ej: `cantera-backend-xxx.up.railway.app`)

6. Para usar dominio personalizado:
   - Ve a **Settings** → **Networking** → **Custom Domain**
   - Agrega: `api-sistema.canteralarufina.com.ar`
   - Railway te dará un registro CNAME para configurar en tu DNS

---

## Paso 5: Inicializar Base de Datos

Después de que el backend esté desplegado:

1. En Railway, click en el servicio backend
2. Ve a **Settings** → **Deploy** → **Start Command**
3. Temporalmente cambia el comando a:
```bash
python scripts/init_prod.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```
4. Click en **Deploy** para redesplegar
5. Una vez inicializado, vuelve al comando normal:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## Paso 6: Desplegar Frontend

1. Click en **+ New** → **GitHub Repo**
2. Selecciona el mismo repositorio
3. En la configuración:
   - **Root Directory**: `frontend`

4. Ve a **Variables** y agrega:

```env
VITE_API_URL=https://api-sistema.canteralarufina.com.ar/api/v1
```

5. Ve a **Settings** → **Networking** → **Custom Domain**
   - Agrega: `sistema.canteralarufina.com.ar`
   - Railway te dará un registro CNAME para configurar en tu DNS

---

## Paso 7: Configurar DNS en tu Dominio

En el panel de control de tu dominio `canteralarufina.com.ar`, agrega estos registros CNAME:

| Tipo  | Nombre       | Valor                              |
|-------|--------------|-------------------------------------|
| CNAME | sistema      | <valor-dado-por-railway-frontend>  |
| CNAME | api-sistema  | <valor-dado-por-railway-backend>   |

**Nota**: Los cambios de DNS pueden tardar hasta 48 horas en propagarse.

---

## Paso 8: (Opcional) Desplegar Celery Worker

Si necesitas tareas asíncronas:

1. Click en **+ New** → **GitHub Repo**
2. Selecciona el mismo repositorio
3. **Root Directory**: `backend`
4. Ve a **Settings** → **Deploy** → **Start Command**:
```bash
celery -A app.core.celery_app worker --loglevel=info
```
5. Agrega las mismas variables de entorno que el backend

---

## Verificación Final

1. Accede a `https://sistema.canteralarufina.com.ar`
2. Inicia sesión con:
   - **Email**: `admin@canteralarufina.com.ar`
   - **Contraseña**: La que configuraste en `ADMIN_PASSWORD`
3. **¡IMPORTANTE!**: Cambia la contraseña inmediatamente después del primer login

---

## Comandos Útiles de Railway CLI

Instalar Railway CLI:
```bash
npm install -g @railway/cli
```

Comandos:
```bash
# Login
railway login

# Ver logs del backend
railway logs -s cantera-backend

# Conectar a la base de datos
railway connect postgres

# Ejecutar comando en el servicio
railway run python scripts/init_prod.py
```

---

## Costos Estimados en Railway

Railway cobra por uso. Estimación mensual para este proyecto:
- **PostgreSQL**: ~$5-10/mes
- **Redis**: ~$5/mes
- **Backend**: ~$5-10/mes
- **Frontend**: ~$5/mes
- **Celery Worker** (opcional): ~$5/mes

**Total estimado**: ~$20-35/mes

Railway ofrece $5 de crédito gratis mensual.

---

## Troubleshooting

### Error de CORS
- Verifica que `BACKEND_CORS_ORIGINS` incluya el dominio del frontend
- El formato debe ser: `["https://sistema.canteralarufina.com.ar"]`

### Error de conexión a base de datos
- Verifica que `DATABASE_URL` esté configurado correctamente
- Railway usa el formato: `postgresql://user:pass@host:port/db`

### Frontend no carga
- Verifica que `VITE_API_URL` apunte al backend correcto
- Incluye `/api/v1` al final de la URL

### Migraciones no ejecutan
- Ejecuta manualmente: `railway run alembic upgrade head`
