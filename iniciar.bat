@echo off
title Sistema Inversiones Barama - Flask Server
color 0A

echo ===================================================
echo   INICIANDO SISTEMA DE CONTROL INVERSIONES BARAMA  
echo ===================================================
echo.

:: 1. Ir a la carpeta del proyecto
cd /d "C:\Users\WINDOWS PRO\Desktop\web"

:: 2. Cerrar cualquier proceso previo de Python colgado
taskkill /f /im python.exe 2>nul

:: 3. Esperar 1 segundo
timeout /t 1 /nobreak >nul

:: 4. Abrir automáticamente el navegador en la dirección local
start http://127.0.0.1:5000/

:: 5. Ejecutar la aplicación usando la ruta exacta de Python 3.8
"C:\Users\WINDOWS PRO\AppData\Local\Programs\Python\Python38\python.exe" app.py

pause