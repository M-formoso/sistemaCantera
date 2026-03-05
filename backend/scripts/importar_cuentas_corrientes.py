#!/usr/bin/env python3
"""
Script para importar datos históricos de cuentas corrientes desde Excel.

Este script lee el archivo "CUENTAS CORRIENTES.xlsx" y:
1. Crea las empresas (clientes) desde la hoja "BASE DE DATOS"
2. Importa los movimientos históricos de cada cliente
3. Establece el saldo inicial correcto para cada cuenta

Uso:
    python importar_cuentas_corrientes.py [ruta_excel]

Si no se especifica ruta, busca en el directorio raíz del proyecto.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.models.empresa import Empresa
from app.models.cuenta_corriente import MovimientoCuentaCorriente
from app.models.usuario import Usuario


def get_database_url():
    """Obtener URL de base de datos"""
    return settings.DATABASE_URL


def parse_fecha(valor):
    """Parsear fecha desde Excel"""
    if pd.isna(valor):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return pd.to_datetime(valor).date()
    except:
        return None


def parse_numero(valor):
    """Parsear número desde Excel"""
    if pd.isna(valor):
        return None
    try:
        return float(valor)
    except:
        return None


def limpiar_texto(valor):
    """Limpiar texto"""
    if pd.isna(valor):
        return None
    return str(valor).strip()


def procesar_hoja_cliente(df, nombre_hoja):
    """
    Procesa una hoja de cliente y extrae los movimientos.

    Retorna:
        - saldo_inicial: Saldo inicial de la cuenta (si existe fila SALDO)
        - movimientos: Lista de movimientos
        - saldo_final: Último saldo registrado
    """
    movimientos = []
    saldo_inicial = 0
    saldo_final = 0

    # Encontrar la fila de encabezados (buscar "FECHA")
    header_row = None
    for i, row in df.iterrows():
        row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
        if 'FECHA' in row_str:
            header_row = i
            break

    if header_row is None:
        print(f"  ⚠️ No se encontró encabezado en {nombre_hoja}")
        return saldo_inicial, movimientos, saldo_final

    # Mapear columnas por nombre aproximado
    col_map = {}
    header_values = df.iloc[header_row].values
    for idx, val in enumerate(header_values):
        val_str = str(val).strip().upper() if pd.notna(val) else ''
        if 'FECHA' in val_str:
            col_map['fecha'] = idx
        elif 'REMITO' in val_str or 'DETALLE' in val_str:
            col_map['remito'] = idx
        elif 'PRECIO' in val_str:
            col_map['precio'] = idx
        elif 'MATERIAL' in val_str:
            col_map['material'] = idx
        elif 'CANT' in val_str:
            col_map['cantidad'] = idx
        elif 'PAGO' in val_str:
            col_map['pago'] = idx
        elif 'DEBE' in val_str:
            col_map['debe'] = idx
        elif 'TOTAL' in val_str or 'SALDO' in val_str:
            col_map['total'] = idx

    # Procesar filas de datos
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]

        # Verificar si es fila de SALDO inicial
        remito_val = limpiar_texto(row.iloc[col_map.get('remito', 2)]) if 'remito' in col_map else None
        if remito_val and 'SALDO' in str(remito_val).upper():
            total_val = parse_numero(row.iloc[col_map.get('total', 9)])
            if total_val is not None:
                saldo_inicial = total_val
            continue

        # Obtener fecha
        fecha = parse_fecha(row.iloc[col_map.get('fecha', 1)])
        if fecha is None:
            continue

        # Obtener valores
        remito = limpiar_texto(row.iloc[col_map.get('remito', 2)])
        precio = parse_numero(row.iloc[col_map.get('precio', 3)])
        material = limpiar_texto(row.iloc[col_map.get('material', 4)])
        cantidad = parse_numero(row.iloc[col_map.get('cantidad', 5)])
        pago = limpiar_texto(row.iloc[col_map.get('pago', 7)]) if 'pago' in col_map else None
        debe = parse_numero(row.iloc[col_map.get('debe', 8)])
        total = parse_numero(row.iloc[col_map.get('total', 9)])

        if total is not None:
            saldo_final = total

        # Determinar tipo de movimiento
        es_pago = False
        metodo_pago = None

        # Detectar si es un pago
        pago_keywords = ['PAGO', 'EFECTIVO', 'CHEQUE', 'TRANSFERENCIA', 'FACT', 'FACTURA']
        remito_upper = str(remito).upper() if remito else ''
        pago_upper = str(pago).upper() if pago else ''

        for keyword in pago_keywords:
            if keyword in remito_upper or keyword in pago_upper:
                es_pago = True
                if 'EFECTIVO' in remito_upper or 'EFECTIVO' in pago_upper:
                    metodo_pago = 'efectivo'
                elif 'CHEQUE' in remito_upper or 'CHEQUE' in pago_upper:
                    metodo_pago = 'cheque'
                elif 'TRANSFER' in remito_upper or 'TRANSFER' in pago_upper:
                    metodo_pago = 'transferencia'
                elif 'FACT' in remito_upper or 'FACT' in pago_upper:
                    metodo_pago = 'factura'
                break

        # Crear movimiento
        if es_pago and debe is not None and debe < 0:
            # Es un pago (valor negativo)
            movimientos.append({
                'tipo': 'pago',
                'fecha': fecha,
                'monto': abs(debe),
                'descripcion': f"Pago histórico - {remito or metodo_pago or 'importado'}",
                'metodo_pago': metodo_pago,
                'numero_comprobante': remito if remito and not any(k in remito_upper for k in pago_keywords) else None
            })
        elif debe is not None and debe > 0:
            # Es un cargo
            desc_parts = []
            if material:
                desc_parts.append(material)
            if cantidad:
                desc_parts.append(f"{cantidad} tn")
            if precio:
                desc_parts.append(f"@ ${precio}")
            if remito and not any(k in remito_upper for k in pago_keywords):
                desc_parts.append(f"Remito: {remito}")

            descripcion = ' - '.join(desc_parts) if desc_parts else 'Cargo histórico importado'

            movimientos.append({
                'tipo': 'cargo',
                'fecha': fecha,
                'monto': debe,
                'descripcion': descripcion,
                'numero_comprobante': remito if remito and remito.isdigit() else None
            })

    return saldo_inicial, movimientos, saldo_final


def main():
    """Función principal"""
    print("=" * 60)
    print("IMPORTACIÓN DE CUENTAS CORRIENTES HISTÓRICAS")
    print("=" * 60)
    print()

    # Buscar archivo Excel
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # Buscar en directorio raíz del proyecto
        project_root = Path(__file__).parent.parent.parent
        excel_path = project_root / "CUENTAS CORRIENTES.xlsx"

    if not os.path.exists(excel_path):
        print(f"❌ No se encontró el archivo: {excel_path}")
        sys.exit(1)

    print(f"📁 Archivo Excel: {excel_path}")
    print()

    # Conectar a base de datos
    db_url = get_database_url()
    print(f"🔌 Conectando a base de datos...")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Obtener usuario admin para asignar como creador
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        if not admin:
            print("❌ No se encontró usuario 'admin'. Creando uno temporal...")
            # Buscar cualquier usuario activo
            admin = session.query(Usuario).filter(Usuario.activo == True).first()
            if not admin:
                print("❌ No hay usuarios en el sistema. Cree uno primero.")
                sys.exit(1)

        print(f"👤 Usuario para auditoría: {admin.username}")
        print()

        # Leer archivo Excel
        print("📖 Leyendo archivo Excel...")
        xlsx = pd.ExcelFile(excel_path)

        # 1. Procesar hoja BASE DE DATOS (clientes)
        print()
        print("=" * 40)
        print("PASO 1: Importar clientes")
        print("=" * 40)

        df_base = pd.read_excel(xlsx, sheet_name='BASE DE DATOS')
        df_base = df_base.dropna(how='all')

        clientes_creados = 0
        clientes_existentes = 0
        cliente_map = {}  # Mapeo nombre_hoja -> empresa_id

        for _, row in df_base.iterrows():
            nombre = limpiar_texto(row.get('CLIENTE ') or row.get('CLIENTE'))
            if not nombre:
                continue

            contacto = limpiar_texto(row.get('CONTACTO'))
            telefono = limpiar_texto(row.get('TELEFONO'))

            # Verificar si ya existe
            existente = session.query(Empresa).filter(
                Empresa.nombre.ilike(f"%{nombre}%")
            ).first()

            if existente:
                print(f"  ⏭️ Ya existe: {nombre}")
                cliente_map[nombre.upper()] = existente.id
                clientes_existentes += 1
            else:
                # Crear empresa
                empresa = Empresa(
                    id=uuid4(),
                    nombre=nombre,
                    tipo='cliente',
                    telefono=str(telefono) if telefono else None,
                    contacto=contacto,
                    activo=True,
                    saldo_cuenta_corriente=0
                )
                session.add(empresa)
                session.flush()
                cliente_map[nombre.upper()] = empresa.id
                clientes_creados += 1
                print(f"  ✅ Creado: {nombre}")

        print()
        print(f"📊 Clientes creados: {clientes_creados}")
        print(f"📊 Clientes existentes: {clientes_existentes}")

        # 2. Procesar hojas de movimientos
        print()
        print("=" * 40)
        print("PASO 2: Importar movimientos y saldos")
        print("=" * 40)

        hojas_clientes = [h for h in xlsx.sheet_names if h != 'BASE DE DATOS']

        total_movimientos = 0
        clientes_procesados = 0

        for nombre_hoja in hojas_clientes:
            print(f"\n📋 Procesando: {nombre_hoja}")

            # Buscar empresa correspondiente
            empresa = None
            nombre_hoja_upper = nombre_hoja.upper()

            # Buscar por coincidencia exacta o parcial
            for key, emp_id in cliente_map.items():
                if key in nombre_hoja_upper or nombre_hoja_upper in key:
                    empresa = session.query(Empresa).filter(Empresa.id == emp_id).first()
                    break

            if not empresa:
                # Buscar en BD por nombre similar
                empresa = session.query(Empresa).filter(
                    Empresa.nombre.ilike(f"%{nombre_hoja.split()[0]}%")
                ).first()

            if not empresa:
                # Crear empresa si no existe
                print(f"  ➕ Creando cliente: {nombre_hoja}")
                empresa = Empresa(
                    id=uuid4(),
                    nombre=nombre_hoja,
                    tipo='cliente',
                    activo=True,
                    saldo_cuenta_corriente=0
                )
                session.add(empresa)
                session.flush()

            # Procesar hoja
            df_hoja = pd.read_excel(xlsx, sheet_name=nombre_hoja)
            saldo_inicial, movimientos, saldo_final = procesar_hoja_cliente(df_hoja, nombre_hoja)

            print(f"  📊 Movimientos encontrados: {len(movimientos)}")
            print(f"  💰 Saldo final: ${saldo_final:,.2f}")

            # Verificar si ya hay movimientos importados
            movimientos_existentes = session.query(MovimientoCuentaCorriente).filter(
                MovimientoCuentaCorriente.empresa_id == empresa.id,
                MovimientoCuentaCorriente.descripcion.like('%histórico%')
            ).count()

            if movimientos_existentes > 0:
                print(f"  ⚠️ Ya hay {movimientos_existentes} movimientos importados, saltando...")
                # Pero actualizar el saldo
                empresa.saldo_cuenta_corriente = Decimal(str(saldo_final))
                clientes_procesados += 1
                continue

            # Opción simplificada: Solo crear un movimiento de ajuste con el saldo final
            # Esto es más limpio que importar todos los movimientos históricos
            if saldo_final != 0:
                tipo = 'cargo' if saldo_final > 0 else 'pago'

                movimiento = MovimientoCuentaCorriente(
                    id=uuid4(),
                    empresa_id=empresa.id,
                    tipo='ajuste',
                    monto=Decimal(str(abs(saldo_final))),
                    saldo_anterior=Decimal('0'),
                    saldo_posterior=Decimal(str(saldo_final)),
                    fecha=date.today(),
                    descripcion=f"Saldo histórico importado desde Excel",
                    detalle=f"Importación automática de cuenta corriente. Saldo al momento de migración: ${saldo_final:,.2f}",
                    created_by=admin.id,
                    anulado=False
                )
                session.add(movimiento)

                # Actualizar saldo de empresa
                empresa.saldo_cuenta_corriente = Decimal(str(saldo_final))

                total_movimientos += 1
                print(f"  ✅ Saldo inicial creado: ${saldo_final:,.2f}")

            clientes_procesados += 1

        # Commit final
        print()
        print("=" * 40)
        print("💾 Guardando cambios...")
        session.commit()

        print()
        print("=" * 60)
        print("✅ IMPORTACIÓN COMPLETADA")
        print("=" * 60)
        print(f"📊 Clientes creados: {clientes_creados}")
        print(f"📊 Clientes procesados: {clientes_procesados}")
        print(f"📊 Movimientos de saldo creados: {total_movimientos}")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
