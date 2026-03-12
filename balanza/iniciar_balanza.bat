@echo off
title Servidor Balanza - Cantera La Rufina
echo ============================================
echo   Servidor de Balanza - COM2
echo   Sistema Cantera La Rufina
echo ============================================
echo.

REM Verificar si Python está en el PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo.
    echo Por favor:
    echo 1. Instale Python desde: https://www.python.org/downloads/
    echo 2. Durante la instalacion marque "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Verificando dependencias...
python -c "import serial" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando pyserial...
    pip install pyserial
    echo.
)

echo Iniciando servidor en puerto COM2...
echo Presione Ctrl+C para detener
echo.

python balanza_server.py COM2

echo.
echo ============================================
echo El servidor se ha detenido.
echo ============================================
pause
