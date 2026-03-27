#!/usr/bin/env python3
"""
Servidor local para leer balanza industrial via RS232.

Este script debe ejecutarse en la PC donde está conectada la balanza.
Expone un servidor HTTP en localhost:5555 que el sistema web consulta
para obtener el peso actual.

Configuración de la balanza:
- Puerto: RS232 (COM port en Windows)
- Velocidad: 4800 bps
- Formato: 8N1 (8 bits datos, sin paridad, 1 bit stop)
- Dato: 7 bytes (6 bytes de peso)
"""

import sys
import os
import time
import json
import threading
import signal

# Deshabilitar Ctrl+C para evitar cierre accidental
def ignorar_signal(signum, frame):
    print("")
    print("[AVISO] Para cerrar el servidor, cierre la ventana con la X")
    print("        El servidor debe permanecer abierto para que funcione la balanza.")
    print("")

# Capturar señales de cierre
signal.signal(signal.SIGINT, ignorar_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, ignorar_signal)  # kill

# En Windows, también capturar Ctrl+Break
if sys.platform == 'win32':
    signal.signal(signal.SIGBREAK, ignorar_signal)

# Verificar e instalar pyserial si no está instalado
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("=" * 50)
    print("Instalando librería pyserial...")
    print("=" * 50)
    os.system(f'{sys.executable} -m pip install pyserial')
    print("")
    print("Librería instalada. Reiniciando...")
    print("")
    import serial
    import serial.tools.list_ports

from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de la balanza
SERIAL_CONFIG = {
    'baudrate': 4800,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': 1
}

# Puerto HTTP local
HTTP_PORT = 5555

# Variable global para el último peso leído
ultimo_peso = {
    'peso': 0,
    'unidad': 'kg',
    'timestamp': None,
    'error': None,
    'conectado': False
}

# Lock para acceso thread-safe
peso_lock = threading.Lock()


def detectar_puerto_serial():
    """Detecta automáticamente el puerto COM de la balanza."""
    puertos = serial.tools.list_ports.comports()

    for puerto in puertos:
        # Intentar con cada puerto disponible
        print(f"Puerto encontrado: {puerto.device} - {puerto.description}")

    # Retornar el primer puerto COM disponible o None
    if puertos:
        return puertos[0].device
    return None


def parsear_peso(data):
    """
    Parsea los bytes recibidos de la balanza.
    Formato: 7 bytes, 6 bytes de dato de peso.
    """
    try:
        # Limpiar el dato
        peso_str = data.decode('ascii', errors='ignore').strip()

        # Remover caracteres no numéricos excepto punto/coma
        peso_limpio = ''
        for c in peso_str:
            if c.isdigit() or c in '.,':
                peso_limpio += c

        # Reemplazar coma por punto
        peso_limpio = peso_limpio.replace(',', '.')

        if peso_limpio:
            return float(peso_limpio)
        return 0

    except Exception as e:
        print(f"Error parseando peso: {e}")
        return 0


def leer_balanza(puerto_com):
    """Thread que lee continuamente la balanza."""
    global ultimo_peso

    intentos_fallidos = 0
    max_intentos_log = 5  # Solo loguear cada N intentos para no llenar la consola
    ultimo_log_peso = 0  # Para no spamear la consola con el mismo peso
    lecturas_consecutivas = 0  # Contador de lecturas exitosas

    while True:
        try:
            # Abrir puerto serial con configuración más robusta
            ser = serial.Serial(
                port=puerto_com,
                baudrate=SERIAL_CONFIG['baudrate'],
                bytesize=SERIAL_CONFIG['bytesize'],
                parity=SERIAL_CONFIG['parity'],
                stopbits=SERIAL_CONFIG['stopbits'],
                timeout=SERIAL_CONFIG['timeout'],
                write_timeout=1,
                inter_byte_timeout=0.1
            )

            print(f"[OK] Conectado a balanza en {puerto_com}")
            intentos_fallidos = 0  # Resetear contador
            lecturas_consecutivas = 0

            with peso_lock:
                ultimo_peso['conectado'] = True
                ultimo_peso['error'] = None

            # Limpiar buffer inicial
            ser.reset_input_buffer()

            sin_datos_contador = 0  # Contador de ciclos sin datos

            while True:
                try:
                    bytes_disponibles = ser.in_waiting

                    # Leer datos (7 bytes según especificación)
                    if bytes_disponibles >= 7:
                        data = ser.read(7)
                        peso = parsear_peso(data)
                        sin_datos_contador = 0  # Resetear contador
                        lecturas_consecutivas += 1

                        with peso_lock:
                            ultimo_peso['peso'] = peso
                            ultimo_peso['timestamp'] = time.time()
                            ultimo_peso['error'] = None
                            ultimo_peso['conectado'] = True

                        # Solo mostrar si el peso cambió significativamente
                        if abs(peso - ultimo_log_peso) > 0.5 or lecturas_consecutivas % 100 == 1:
                            print(f"Peso: {peso} kg")
                            ultimo_log_peso = peso

                    # También intentar leer línea completa (por si la balanza envía diferente)
                    elif bytes_disponibles > 0:
                        data = ser.readline()
                        if data:
                            peso = parsear_peso(data)
                            sin_datos_contador = 0
                            if peso > 0:
                                lecturas_consecutivas += 1
                                with peso_lock:
                                    ultimo_peso['peso'] = peso
                                    ultimo_peso['timestamp'] = time.time()
                                    ultimo_peso['error'] = None
                                    ultimo_peso['conectado'] = True
                                if abs(peso - ultimo_log_peso) > 0.5:
                                    print(f"Peso: {peso} kg")
                                    ultimo_log_peso = peso
                    else:
                        sin_datos_contador += 1
                        # Si pasan 30 segundos sin datos, mostrar advertencia
                        if sin_datos_contador == 300:  # 300 * 0.1s = 30 segundos
                            print(f"[WARN] Sin datos de la balanza por 30 segundos...")
                        # Si pasan 60 segundos sin datos, intentar reconectar
                        if sin_datos_contador >= 600:  # 60 segundos
                            print(f"[WARN] Sin datos por 60 segundos, reconectando...")
                            break  # Salir del loop para reconectar

                    time.sleep(0.1)

                except serial.SerialException as e:
                    # Error de puerto serial - necesita reconectar
                    print(f"[ERROR] Error de puerto serial: {e}")
                    break  # Salir para reconectar

                except Exception as e:
                    # Error dentro del loop de lectura - continuar sin cerrar conexión
                    print(f"[WARN] Error leyendo datos: {e}")
                    time.sleep(0.5)

            # Cerrar puerto antes de reintentar
            try:
                ser.close()
            except:
                pass

        except serial.SerialException as e:
            intentos_fallidos += 1
            with peso_lock:
                ultimo_peso['conectado'] = False
                ultimo_peso['error'] = f"Error serial: {e}"

            # Solo loguear cada N intentos para no llenar la consola
            if intentos_fallidos == 1 or intentos_fallidos % max_intentos_log == 0:
                print(f"[ERROR] Conexión serial fallida (intento #{intentos_fallidos}): {e}")
                print(f"        Reintentando en 3 segundos...")

            time.sleep(3)  # Reducido de 5 a 3 segundos

        except Exception as e:
            intentos_fallidos += 1
            with peso_lock:
                ultimo_peso['conectado'] = False
                ultimo_peso['error'] = f"Error: {e}"

            if intentos_fallidos == 1 or intentos_fallidos % max_intentos_log == 0:
                print(f"[ERROR] Error inesperado (intento #{intentos_fallidos}): {e}")
                print(f"        Reintentando en 3 segundos...")

            time.sleep(3)


class BalanzaHandler(BaseHTTPRequestHandler):
    """Handler HTTP para servir el peso de la balanza."""

    def _send_cors_headers(self):
        """Envía headers CORS para permitir acceso desde el frontend."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """Maneja preflight CORS."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Retorna el peso actual de la balanza."""
        if self.path == '/peso' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            with peso_lock:
                response = {
                    'peso': ultimo_peso['peso'],
                    'unidad': ultimo_peso['unidad'],
                    'conectado': ultimo_peso['conectado'],
                    'timestamp': ultimo_peso['timestamp'],
                    'error': ultimo_peso['error']
                }

            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            with peso_lock:
                response = {
                    'conectado': ultimo_peso['conectado'],
                    'error': ultimo_peso['error']
                }

            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/puertos':
            # Listar puertos disponibles
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            puertos = [
                {'puerto': p.device, 'descripcion': p.description}
                for p in serial.tools.list_ports.comports()
            ]

            self.wfile.write(json.dumps(puertos).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Silenciar logs de cada request."""
        pass


def main():
    # Detectar puerto o usar el especificado
    if len(sys.argv) > 1:
        puerto_com = sys.argv[1]
    else:
        # Puerto por defecto: COM2
        puerto_com = "COM2"

        if not puerto_com:
            print("=" * 50)
            print("ERROR: No se detectó ningún puerto serial.")
            print("Puertos disponibles:")
            for p in serial.tools.list_ports.comports():
                print(f"  - {p.device}: {p.description}")
            print("")
            print("Uso: python balanza_server.py COM3")
            print("=" * 50)

            # Iniciar servidor HTTP de todos modos para mostrar error en frontend
            puerto_com = None

    print("=" * 50)
    print("Servidor de Balanza - Sistema Cantera La Rufina")
    print("=" * 50)
    print(f"Puerto serial: {puerto_com or 'NO CONECTADO'}")
    print(f"Servidor HTTP: http://localhost:{HTTP_PORT}")
    print("")
    print("Endpoints disponibles:")
    print(f"  GET http://localhost:{HTTP_PORT}/peso    - Obtener peso actual")
    print(f"  GET http://localhost:{HTTP_PORT}/status  - Estado de conexión")
    print(f"  GET http://localhost:{HTTP_PORT}/puertos - Listar puertos COM")
    print("=" * 50)

    # Iniciar thread de lectura de balanza
    if puerto_com:
        thread_balanza = threading.Thread(target=leer_balanza, args=(puerto_com,), daemon=True)
        thread_balanza.start()
    else:
        with peso_lock:
            ultimo_peso['error'] = 'Puerto serial no configurado'

    # Iniciar servidor HTTP
    try:
        server = HTTPServer(('127.0.0.1', HTTP_PORT), BalanzaHandler)
        print(f"[OK] Servidor HTTP iniciado en puerto {HTTP_PORT}")
        print("")
        print("*" * 50)
        print("*   NO CIERRE ESTA VENTANA                       *")
        print("*   El servidor debe permanecer abierto          *")
        print("*   mientras usa el sistema de pesaje.           *")
        print("*                                                *")
        print("*   Ctrl+C está deshabilitado.                   *")
        print("*   Para cerrar, use la X de la ventana.         *")
        print("*" * 50)
        print("")
        print("=" * 50)
        server.serve_forever()
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            print("")
            print("=" * 50)
            print("[ERROR] El puerto 5555 ya está en uso.")
            print("")
            print("Esto puede significar que:")
            print("1. Ya hay otra ventana del servidor abierta")
            print("2. Otro programa está usando el puerto 5555")
            print("")
            print("Solución: Cierre la otra ventana del servidor e intente de nuevo.")
            print("=" * 50)
            # Esperar y salir
            time.sleep(10)
            sys.exit(1)
        else:
            print(f"[ERROR] Error de red: {e}")
            raise  # Re-lanzar para reintentar
    except Exception as e:
        print(f"[ERROR] Error iniciando servidor: {e}")
        raise  # Re-lanzar para reintentar


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print("")
            print("=" * 50)
            print(f"[ERROR CRITICO] {e}")
            print("=" * 50)
            print("")
            print("El servidor se reiniciará en 5 segundos...")
            time.sleep(5)
            print("Reiniciando servidor...")
            print("")
