#!/usr/bin/env python3
"""
Servidor de Balanza - VERSION DEBUG con logs detallados
"""

import serial
import serial.tools.list_ports
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
import sys

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
    'conectado': False,
    'bytes_recibidos': 0,
    'ultimo_dato_raw': None
}

peso_lock = threading.Lock()


def listar_puertos():
    """Lista todos los puertos COM con detalle."""
    print("\n" + "=" * 60)
    print("PUERTOS SERIALES DETECTADOS:")
    print("=" * 60)
    puertos = serial.tools.list_ports.comports()

    if not puertos:
        print("  [!] No se detectaron puertos seriales")
        return []

    for p in puertos:
        print(f"  Puerto: {p.device}")
        print(f"    - Descripcion: {p.description}")
        print(f"    - Fabricante: {p.manufacturer}")
        print(f"    - VID:PID: {p.vid}:{p.pid}" if p.vid else "    - VID:PID: N/A")
        print(f"    - Serial: {p.serial_number}" if p.serial_number else "    - Serial: N/A")
        print("")

    print("=" * 60 + "\n")
    return puertos


def parsear_peso(data):
    """Parsea los bytes recibidos de la balanza."""
    try:
        peso_str = data.decode('ascii', errors='ignore').strip()
        peso_limpio = ''
        for c in peso_str:
            if c.isdigit() or c in '.,':
                peso_limpio += c
        peso_limpio = peso_limpio.replace(',', '.')

        if peso_limpio:
            return float(peso_limpio)
        return 0
    except Exception as e:
        print(f"  [ERROR] Parseando peso: {e}")
        return 0


def leer_balanza(puerto_com):
    """Thread que lee continuamente la balanza con logs detallados."""
    global ultimo_peso
    contador_lecturas = 0

    while True:
        try:
            print(f"\n[SERIAL] Intentando conectar a {puerto_com}...")
            print(f"[SERIAL] Config: {SERIAL_CONFIG}")

            with serial.Serial(puerto_com, **SERIAL_CONFIG) as ser:
                print(f"[SERIAL] CONECTADO a {puerto_com}")
                print(f"[SERIAL] Esperando datos de la balanza...")
                print(f"[SERIAL] (Si no aparecen datos, puede ser el puerto incorrecto)\n")

                with peso_lock:
                    ultimo_peso['conectado'] = True
                    ultimo_peso['error'] = None

                ultimo_log = time.time()

                while True:
                    bytes_disponibles = ser.in_waiting

                    # Log cada 5 segundos si no hay datos
                    if time.time() - ultimo_log > 5:
                        if bytes_disponibles == 0:
                            print(f"[SERIAL] Sin datos recibidos... (bytes en buffer: 0)")
                        ultimo_log = time.time()

                    if bytes_disponibles > 0:
                        # Leer todos los bytes disponibles
                        data = ser.read(bytes_disponibles)
                        contador_lecturas += 1

                        # Mostrar datos raw
                        print(f"\n[DATO #{contador_lecturas}] Recibidos {len(data)} bytes:")
                        print(f"  - Raw (hex): {data.hex()}")
                        print(f"  - Raw (bytes): {list(data)}")
                        try:
                            texto = data.decode('ascii', errors='replace')
                            print(f"  - Como texto: '{texto}'")
                        except:
                            print(f"  - Como texto: (no decodificable)")

                        peso = parsear_peso(data)
                        print(f"  - Peso parseado: {peso} kg")

                        with peso_lock:
                            ultimo_peso['peso'] = peso
                            ultimo_peso['timestamp'] = time.time()
                            ultimo_peso['error'] = None
                            ultimo_peso['bytes_recibidos'] = contador_lecturas
                            ultimo_peso['ultimo_dato_raw'] = data.hex()

                    time.sleep(0.1)

        except serial.SerialException as e:
            print(f"\n[ERROR SERIAL] {e}")
            with peso_lock:
                ultimo_peso['conectado'] = False
                ultimo_peso['error'] = str(e)
            print(f"[SERIAL] Reintentando en 5 segundos...")
            time.sleep(5)

        except Exception as e:
            print(f"\n[ERROR] {type(e).__name__}: {e}")
            with peso_lock:
                ultimo_peso['error'] = str(e)
            time.sleep(5)


class BalanzaHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/peso' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            with peso_lock:
                response = dict(ultimo_peso)

            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()

            with peso_lock:
                response = {
                    'conectado': ultimo_peso['conectado'],
                    'error': ultimo_peso['error'],
                    'bytes_recibidos': ultimo_peso['bytes_recibidos']
                }

            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/puertos':
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
        pass


def probar_todos_los_puertos():
    """Prueba cada puerto para ver cuál recibe datos."""
    puertos = serial.tools.list_ports.comports()

    print("\n" + "=" * 60)
    print("PROBANDO TODOS LOS PUERTOS (5 segundos cada uno)...")
    print("=" * 60)

    for p in puertos:
        print(f"\n[TEST] Probando {p.device} ({p.description})...")
        try:
            with serial.Serial(p.device, **SERIAL_CONFIG) as ser:
                print(f"  - Puerto abierto OK")
                inicio = time.time()
                datos_recibidos = False

                while time.time() - inicio < 5:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        print(f"  - DATOS RECIBIDOS: {data.hex()}")
                        print(f"  - Como texto: {data.decode('ascii', errors='replace')}")
                        datos_recibidos = True
                        break
                    time.sleep(0.1)

                if not datos_recibidos:
                    print(f"  - Sin datos en 5 segundos")

        except Exception as e:
            print(f"  - ERROR: {e}")

    print("\n" + "=" * 60 + "\n")


def main():
    print("\n" + "=" * 60)
    print("SERVIDOR DE BALANZA - MODO DEBUG")
    print("Sistema Cantera La Rufina")
    print("=" * 60)

    # Listar puertos
    listar_puertos()

    # Si se pasa --test, probar todos los puertos
    if '--test' in sys.argv:
        probar_todos_los_puertos()
        input("Presione Enter para continuar...")

    # Obtener puerto
    puerto_com = None
    for arg in sys.argv[1:]:
        if arg.startswith('COM') or arg.startswith('/dev/'):
            puerto_com = arg
            break

    if not puerto_com:
        print("[!] No se especifico puerto.")
        print("    Uso: python balanza_server_debug.py COM3")
        print("    O para probar todos: python balanza_server_debug.py --test")
        print("")
        puerto_com = input("Ingrese puerto COM (ej: COM3): ").strip()
        if not puerto_com:
            print("Saliendo...")
            return

    print(f"\n[CONFIG] Puerto serial: {puerto_com}")
    print(f"[CONFIG] Servidor HTTP: http://localhost:{HTTP_PORT}")
    print(f"\n[INFO] Los datos de la balanza se mostraran aqui abajo...")
    print("[INFO] Si no aparecen datos, probablemente es el puerto incorrecto.\n")

    # Iniciar thread de lectura
    thread_balanza = threading.Thread(target=leer_balanza, args=(puerto_com,), daemon=True)
    thread_balanza.start()

    # Iniciar servidor HTTP
    try:
        server = HTTPServer(('127.0.0.1', HTTP_PORT), BalanzaHandler)
        print(f"[HTTP] Servidor iniciado en puerto {HTTP_PORT}")
        print("[HTTP] Endpoints: /peso, /status, /puertos")
        print("\nPresione Ctrl+C para detener\n")
        print("-" * 60)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor detenido")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == '__main__':
    main()
