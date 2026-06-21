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
    exit /b 1
)

:: Guardar la ruta completa del proyecto para pasarla a las subventanas
set "PROJECT_DIR=%~dp0"

echo [1/2] Levantando motor de Inferencia (Backend Python)...
:: Usar la ruta completa al python del venv para evitar conflictos con el Python global
start "EEG Backend API" cmd /k "cd /d "%PROJECT_DIR%" && set PYTHONPATH=%PROJECT_DIR% && .venv\Scripts\python.exe src\api\main.py"

echo [2/2] Levantando Interfaz Web (Frontend React)...
:: Abre otra ventana para Vite
start "EEG Frontend UI" cmd /k "cd /d "%PROJECT_DIR%dashboard" && npm run dev"

echo.
echo ========================================================
echo  Esperando que los servidores se inicien...
echo ========================================================
echo.

:: ── Esperar al Backend (puerto 8000) ──────────────────────
echo Esperando al backend (puerto 8000)...
set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=30

:wait_backend
set /a ATTEMPTS+=1
if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo [ERROR] El backend no respondio despues de 60 segundos.
    echo Revisa la consola del backend para ver errores.
    pause
    exit /b 1
)

powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Intento %ATTEMPTS%/%MAX_ATTEMPTS% - Backend no listo, reintentando en 2s...
    ping 127.0.0.1 -n 3 > nul
    goto wait_backend
)
echo   [OK] Backend listo!

:: ── Esperar al Frontend (puerto 5173) ─────────────────────
echo Esperando al frontend (puerto 5173)...
set /a ATTEMPTS=0

:wait_frontend
set /a ATTEMPTS+=1
if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo [ERROR] El frontend no respondio despues de 60 segundos.
    echo Revisa la consola del frontend para ver errores.
    pause
    exit /b 1
)

powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5173/' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Intento %ATTEMPTS%/%MAX_ATTEMPTS% - Frontend no listo, reintentando en 2s...
    ping 127.0.0.1 -n 3 > nul
    goto wait_frontend
)
echo   [OK] Frontend listo!

echo.
echo ========================================================
echo  Sistema Iniciado correctamente!
echo  Se abrieron dos consolas que mantienen el sistema vivo.
echo  Para apagar todo, simplemente cerra esas dos consolas.
echo ========================================================
echo.

start http://localhost:5173
