@echo off
:: Asegurar que el script corra en la carpeta correcta
cd /d "%~dp0"

echo ========================================================
echo       Instalador Automatico - EEG Seizure Detection
echo ========================================================
echo.

echo Comprobando si Python esta instalado...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Entra a python.org, descargalo, y asegúrate de tildar "Add Python to PATH" en la instalacion.
    pause
    exit /b
)

echo Comprobando si Node.js esta instalado...
npm --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js no esta instalado.
    echo Entra a nodejs.org, descargate la version LTS e instalala.
    pause
    exit /b
)

echo.
echo [1/3] Creando entorno virtual de Python (.venv)...
python -m venv .venv

echo [2/3] Instalando librerias de Machine Learning e Inferencia...
call .venv\Scripts\activate
pip install -r requirements.txt

echo [3/3] Instalando librerias de la Interfaz Web (React)...
cd dashboard
call npm install
cd ..

echo.
echo ========================================================
echo  ¡Instalacion Completada con Exito!
echo  Ya tenes todo listo. De ahora en mas, solo necesitas
echo  hacer doble clic en 'iniciar.bat'.
echo ========================================================
pause
