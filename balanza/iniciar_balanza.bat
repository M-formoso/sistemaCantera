@echo off
echo ==========================================
echo Servidor de Balanza - Cantera La Rufina
echo ==========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado.
    echo Descargue Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Instalar dependencias si es necesario
echo Verificando dependencias...
pip install pyserial --quiet

echo.
echo Iniciando servidor de balanza...
echo Presione Ctrl+C para detener
echo.

REM Iniciar el servidor (detecta puerto automáticamente)
python balanza_server.py

pause
