# Importar Cuentas Corrientes desde Excel

Este documento explica cómo importar los datos históricos del archivo `CUENTAS CORRIENTES.xlsx` al sistema.

## Resumen de Datos

El Excel contiene:
- **105 hojas** (clientes)
- **Hoja "BASE DE DATOS"**: Lista de 44 clientes con contacto y teléfono
- **Hojas individuales**: Movimientos históricos por cliente con saldo final

## Opciones de Importación

### Opción 1: Vía API (Recomendada)

Esta opción ejecuta el script desde tu computadora local y envía los datos al sistema en Railway.

#### Requisitos
```bash
pip install pandas openpyxl requests
```

#### Pasos

1. **Obtén la URL de tu API en Railway**
   - Ve a Railway → tu proyecto → backend → Settings
   - Copia la URL (ej: `https://backend-production-xxxx.up.railway.app`)

2. **Configura las variables de entorno**
   ```bash
   export API_URL="https://backend-production-xxxx.up.railway.app"
   ```

3. **Ejecuta el script**
   ```bash
   cd backend/scripts
   python importar_via_api.py
   ```

4. **Ingresa las credenciales de admin** cuando se soliciten

---

### Opción 2: Conexión Directa a BD (Avanzado)

Esta opción requiere acceso directo a la base de datos PostgreSQL.

#### Requisitos
```bash
pip install pandas openpyxl psycopg2-binary sqlalchemy
```

#### Pasos

1. **Obtén la URL de la BD de Railway**
   - Ve a Railway → PostgreSQL → Connect → Database URL
   - La URL tiene formato: `postgresql://user:pass@host:port/db`

2. **Configura la variable de entorno**
   ```bash
   export DATABASE_URL="postgresql://..."
   ```

3. **Ejecuta el script**
   ```bash
   cd backend/scripts
   python importar_cuentas_corrientes.py "../CUENTAS CORRIENTES.xlsx"
   ```

---

### Opción 3: Railway Shell (En el servidor)

Si prefieres ejecutar el script directamente en Railway:

1. **Sube el archivo Excel al proyecto** (o a un bucket S3)

2. **Abre una shell en Railway**
   ```bash
   railway run bash
   ```

3. **Instala dependencias**
   ```bash
   pip install pandas openpyxl
   ```

4. **Ejecuta el script**
   ```bash
   python scripts/importar_cuentas_corrientes.py /ruta/al/excel.xlsx
   ```

---

## Qué hace el script

1. **Crea las empresas (clientes)**
   - Lee la hoja "BASE DE DATOS"
   - Crea cada cliente con nombre, contacto y teléfono
   - Si el cliente ya existe, lo omite

2. **Importa los saldos**
   - Lee cada hoja de cliente
   - Extrae el saldo final (última columna TOTAL con valor)
   - Crea un movimiento de tipo "ajuste" con el saldo histórico
   - Actualiza el saldo de cuenta corriente de la empresa

## Resultado Esperado

Después de ejecutar el script:
- ~105 clientes creados o actualizados
- Cada cliente tendrá su saldo histórico cargado
- Los movimientos aparecen como "Saldo histórico importado desde Excel"

## Verificación

Para verificar que la importación fue exitosa:

1. Ve al sistema web → Empresas
2. Verifica que aparezcan los clientes importados
3. Ve a Cuentas Corrientes
4. Verifica que cada cliente tenga su saldo

## Notas Importantes

- El script es **idempotente**: si lo ejecutas dos veces, no duplica datos
- Los movimientos históricos detallados NO se importan, solo el saldo final
- Si necesitas los movimientos detallados, consulta al desarrollador
- Mantén un backup del Excel original

## Solución de Problemas

### Error: "No se encontró usuario admin"
- Asegúrate de tener un usuario admin en el sistema
- Crea uno desde el panel de administración si es necesario

### Error: "Connection refused"
- Verifica que la URL de la API sea correcta
- Verifica que el backend esté corriendo en Railway

### Error de autenticación
- Verifica usuario y contraseña
- El token puede haber expirado, vuelve a loguearte
