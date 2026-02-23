# Servidor de Balanza - Sistema Cantera La Rufina

Este programa conecta la balanza industrial con el sistema web de pesajes.

## Requisitos

- Windows con Python 3.8+ instalado
- La balanza conectada via cable RS232 (DB9)
- Adaptador USB-Serial si la PC no tiene puerto DB9

## Instalación

1. Instalar Python desde https://www.python.org/downloads/
   - Marcar "Add Python to PATH" durante la instalación

2. Conectar la balanza al puerto COM

3. Ejecutar `iniciar_balanza.bat`

## Uso

1. Hacer doble clic en `iniciar_balanza.bat`
2. El programa detectará automáticamente el puerto de la balanza
3. Dejar el programa corriendo mientras se usa el sistema de pesajes
4. En el sistema web, usar el botón "Leer Balanza" para capturar el peso

## Configuración Manual

Si hay varios puertos COM, ejecutar especificando el puerto:

```
python balanza_server.py COM3
```

Para ver los puertos disponibles, abrir el Administrador de Dispositivos > Puertos (COM y LPT)

## Especificaciones Técnicas

- Puerto serial: RS232 via DB9
- Velocidad: 4800 bps
- Formato: 8N1 (8 bits datos, sin paridad, 1 bit stop)
- Dato: 7 bytes (6 bytes de peso)

## Endpoints HTTP

El servidor expone estos endpoints en `http://localhost:5555`:

- `GET /peso` - Retorna el peso actual
- `GET /status` - Estado de conexión
- `GET /puertos` - Lista puertos COM disponibles

## Solución de Problemas

**"No se detectó ningún puerto serial"**
- Verificar que el cable de la balanza esté conectado
- Verificar en Administrador de Dispositivos que aparezca el puerto COM

**El peso no se actualiza**
- La balanza debe estar encendida y transmitiendo
- Verificar que el puerto COM sea el correcto
