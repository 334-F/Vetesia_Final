@echo off
chcp 65001 > nul
echo ==================================================
echo       VetÉsia - Inicio Rápido Monolítico
echo ==================================================
echo.
echo Iniciando aplicacion Web Monolitica en puerto 5000...
start "VetÉsia - Web" cmd /k "venv\Scripts\python app.py"

echo.
echo ==================================================
echo ¡Servidor Monolitico iniciado!
echo Abre: http://localhost:5000
echo ==================================================
echo.
echo Abriendo la aplicacion en tu navegador web...
timeout /t 2 /nobreak > nul
start http://localhost:5000
exit
