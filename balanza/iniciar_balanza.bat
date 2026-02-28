@echo off
title Servidor Balanza - COM2
echo ============================================
echo   Servidor de Balanza - COM2
echo   Sistema Cantera La Rufina
echo ============================================
echo.

REM Ruta de Python (ajustar si es diferente)
set PYTHON_PATH=C:\Users\usuario\AppData\Local\Programs\Python\Python314\python.exe

REM Si no existe, probar otras rutas comunes
if not exist "%PYTHON_PATH%" set PYTHON_PATH=C:\Users\usuario\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON_PATH%" set PYTHON_PATH=C:\Python314\python.exe
if not exist "%PYTHON_PATH%" set PYTHON_PATH=C:\Python313\python.exe
if not exist "%PYTHON_PATH%" set PYTHON_PATH=C:\Python312\python.exe
if not exist "%PYTHON_PATH%" set PYTHON_PATH=python

echo Iniciando servidor en puerto COM2...
echo Presione Ctrl+C para detener
echo.

"%PYTHON_PATH%" balanza_server.py COM2

pause
