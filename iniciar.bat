@echo off
:: Asegurar que el script corra en la carpeta correcta
cd /d "%~dp0"

echo ========================================================
echo       EEG Seizure Detection - Dashboard Launcher
echo ========================================================
echo.

IF NOT EXIST ".venv" (
    echo [ADVERTENCIA] No se detecto el entorno virtual .venv
    echo Por favor asegurate de instalar las dependencias primero.
    echo/
    pause
)

echo [1/2] Levantando motor de Inferencia (Backend Python)...
:: Abre una nueva ventana negra y ejecuta main.py (que inicializa Uvicorn)
start "EEG Backend API" cmd /k "call .venv\Scripts\activate && set PYTHONPATH=%cd% && python src\api\main.py"

echo [2/2] Levantando Interfaz Web (Frontend React)...
:: Abre otra ventana para Vite
start "EEG Frontend UI" cmd /k "cd dashboard && npm run dev"

echo.
echo ========================================================
echo  ¡Sistema Iniciado! 
echo  Se abrieron dos consolas nuevas que mantienen el sistema vivo.
echo  Para apagar todo, simplemente cerra esas dos consolas.
echo ========================================================
echo.
echo Abriendo el navegador...
ping 127.0.0.1 -n 4 > nul
start http://localhost:5173
