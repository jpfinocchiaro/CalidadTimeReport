@echo off
cd /d "%~dp0"
title Calidad Time Report
echo ============================================
echo   Calidad - Time Report
echo ============================================
echo.
echo Verificando dependencias (solo la primera vez tarda)...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: no se pudo instalar dependencias.
    echo Verifica que Python este instalado y en PATH.
    pause
    exit /b 1
)
echo.
echo Abriendo navegador en http://127.0.0.1:5000
echo Para detener la app: cerra esta ventana o Ctrl+C
echo.
start "" "http://127.0.0.1:5000"
python app.py
pause
