#!/usr/bin/env python3
"""
Script para importar datos de cuentas corrientes vía API REST.

Este script lee el Excel localmente y hace peticiones HTTP al backend
desplegado en Railway. Es útil cuando no tienes acceso directo a la BD.

Uso:
    python importar_via_api.py

Requiere:
    - pip install pandas openpyxl requests
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
from datetime import date

# Configuración - se pedirá al usuario si no está definida
API_BASE_URL = os.environ.get("API_URL", "")
API_TOKEN = ""

# Headers para requests
HEADERS = {
    "Content-Type": "application/json"
}


def limpiar_texto(valor):
    """Limpiar texto"""
    if pd.isna(valor):
        return None
    return str(valor).strip()


def parse_numero(valor):
    """Parsear número desde Excel"""
    if pd.isna(valor):
        return None
    try:
        return float(valor)
    except:
        return None


def login(email: str, password: str) -> str:
    """Obtener token JWT"""
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error de login: {response.text}")


def crear_empresa(nombre: str, contacto: str = None, telefono: str = None) -> dict:
    """Crear empresa vía API"""
    data = {
        "nombre": nombre,
        "tipo": "cliente",
        "contacto": contacto,
        "telefono": telefono
    }
    response = requests.post(
        f"{API_BASE_URL}/api/v1/empresas",
        json=data,
        headers=HEADERS
    )
    if response.status_code in [200, 201]:
        return response.json()
    elif response.status_code == 400 and "ya existe" in response.text.lower():
        # Buscar empresa existente
        return buscar_empresa(nombre)
    else:
        print(f"Error creando empresa {nombre}: {response.text}")
        return None


def buscar_empresa(nombre: str) -> dict:
    """Buscar empresa por nombre"""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/empresas",
        params={"search": nombre, "tipo": "cliente"},
        headers=HEADERS
    )
    if response.status_code == 200:
        empresas = response.json()
        if isinstance(empresas, list) and len(empresas) > 0:
            return empresas[0]
        elif isinstance(empresas, dict) and "items" in empresas:
            if len(empresas["items"]) > 0:
                return empresas["items"][0]
    return None


def crear_ajuste(empresa_id: str, monto: float, descripcion: str) -> dict:
    """Crear ajuste en cuenta corriente"""
    es_credito = monto < 0  # Saldo negativo = a favor del cliente

    data = {
        "empresa_id": empresa_id,
        "monto": abs(monto),
        "es_credito": es_credito,
        "fecha": date.today().isoformat(),
        "descripcion": descripcion
    }

    response = requests.post(
        f"{API_BASE_URL}/api/v1/cuenta-corriente/ajuste",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error creando ajuste: {response.text}")
        return None


def procesar_hoja_saldo(df, nombre_hoja):
    """Obtener saldo final de una hoja de cliente"""
    saldo_final = 0

    # Buscar la columna TOTAL
    for i in range(len(df) - 1, 0, -1):
        row = df.iloc[i]
        for col_idx in [9, 8, 10]:
            if col_idx < len(row):
                val = row.iloc[col_idx]
                if pd.notna(val) and isinstance(val, (int, float)) and val != 0:
                    return float(val)

    return saldo_final


def main():
    global HEADERS, API_TOKEN, API_BASE_URL

    print("=" * 60)
    print("IMPORTACIÓN DE CUENTAS CORRIENTES VÍA API")
    print("=" * 60)
    print()

    # Buscar archivo Excel
    project_root = Path(__file__).parent.parent.parent
    excel_path = project_root / "CUENTAS CORRIENTES.xlsx"

    if not excel_path.exists():
        print(f"❌ No se encontró: {excel_path}")
        sys.exit(1)

    print(f"📁 Excel: {excel_path}")
    print()

    # Pedir URL de la API si no está configurada
    if not API_BASE_URL:
        print("🌐 Ingresa la URL de tu backend en Railway:")
        print("   (Ejemplo: https://backend-production-xxxx.up.railway.app)")
        API_BASE_URL = input("   URL: ").strip()
        if not API_BASE_URL:
            print("❌ URL requerida")
            sys.exit(1)
        # Quitar trailing slash
        API_BASE_URL = API_BASE_URL.rstrip("/")

    print(f"🌐 API: {API_BASE_URL}")
    print()

    # Login
    print("🔐 Ingresa credenciales de admin del sistema:")
    email = input("   Email: ")
    password = input("   Contraseña: ")

    try:
        API_TOKEN = login(email, password)
        HEADERS["Authorization"] = f"Bearer {API_TOKEN}"
        print("   ✅ Login exitoso")
    except Exception as e:
        print(f"   ❌ {e}")
        sys.exit(1)

    print()

    # Leer Excel
    print("📖 Leyendo Excel...")
    xlsx = pd.ExcelFile(excel_path)

    # Procesar clientes de BASE DE DATOS
    print()
    print("=" * 40)
    print("PASO 1: Crear clientes")
    print("=" * 40)

    df_base = pd.read_excel(xlsx, sheet_name='BASE DE DATOS')
    df_base = df_base.dropna(how='all')

    empresas_map = {}
    for _, row in df_base.iterrows():
        nombre = limpiar_texto(row.get('CLIENTE ') or row.get('CLIENTE'))
        if not nombre:
            continue

        contacto = limpiar_texto(row.get('CONTACTO'))
        telefono = limpiar_texto(row.get('TELEFONO'))

        empresa = crear_empresa(nombre, contacto, str(telefono) if telefono else None)
        if empresa:
            empresas_map[nombre.upper()] = empresa
            print(f"  ✅ {nombre}")
        else:
            print(f"  ❌ {nombre}")

    # Procesar saldos
    print()
    print("=" * 40)
    print("PASO 2: Importar saldos")
    print("=" * 40)

    hojas = [h for h in xlsx.sheet_names if h != 'BASE DE DATOS']

    for hoja in hojas:
        print(f"\n📋 {hoja}")

        # Buscar empresa
        empresa = None
        for key, emp in empresas_map.items():
            if key in hoja.upper() or hoja.upper() in key:
                empresa = emp
                break

        if not empresa:
            empresa = buscar_empresa(hoja.split()[0])

        if not empresa:
            empresa = crear_empresa(hoja)

        if not empresa:
            print("  ⚠️ No se pudo crear/encontrar empresa")
            continue

        # Obtener saldo
        df_hoja = pd.read_excel(xlsx, sheet_name=hoja)
        saldo = procesar_hoja_saldo(df_hoja, hoja)

        if saldo == 0:
            print(f"  ➖ Saldo: $0")
            continue

        print(f"  💰 Saldo: ${saldo:,.2f}")

        # Crear ajuste si hay saldo
        ajuste = crear_ajuste(
            empresa["id"],
            saldo,
            f"Saldo histórico importado desde Excel"
        )

        if ajuste:
            print("  ✅ Saldo importado")
        else:
            print("  ❌ Error al importar saldo")

    print()
    print("=" * 60)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("=" * 60)


if __name__ == '__main__':
    main()
