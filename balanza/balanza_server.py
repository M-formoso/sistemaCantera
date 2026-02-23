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

import serial
import serial.tools.list_ports
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
import sys
import os

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

    while True:
        try:
            # Abrir puerto serial
            with serial.Serial(puerto_com, **SERIAL_CONFIG) as ser:
                print(f"Conectado a balanza en {puerto_com}")

                with peso_lock:
                    ultimo_peso['conectado'] = True
                    ultimo_peso['error'] = None

                while True:
                    # Leer datos (7 bytes según especificación)
                    if ser.in_waiting >= 7:
                        data = ser.read(7)
                        peso = parsear_peso(data)

                        with peso_lock:
                            ultimo_peso['peso'] = peso
                            ultimo_peso['timestamp'] = time.time()
                            ultimo_peso['error'] = None

                        print(f"Peso leído: {peso} kg")

                    # También intentar leer línea completa (por si la balanza envía diferente)
                    elif ser.in_waiting > 0:
                        data = ser.readline()
                        if data:
                            peso = parsear_peso(data)
                            if peso > 0:
                                with peso_lock:
                                    ultimo_peso['peso'] = peso
                                    ultimo_peso['timestamp'] = time.time()
                                    ultimo_peso['error'] = None
                                print(f"Peso leído (línea): {peso} kg")

                    time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Error de conexión serial: {e}")
            with peso_lock:
                ultimo_peso['conectado'] = False
                ultimo_peso['error'] = str(e)
            time.sleep(5)  # Esperar antes de reintentar

        except Exception as e:
            print(f"Error inesperado: {e}")
            with peso_lock:
                ultimo_peso['error'] = str(e)
            time.sleep(5)


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
        puerto_com = detectar_puerto_serial()

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
        print(f"Servidor iniciado en puerto {HTTP_PORT}")
        print("Presione Ctrl+C para detener")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")


if __name__ == '__main__':
    main()
