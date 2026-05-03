@echo off
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ==================================================
echo     VNSTOCK Execution Engine Launcher
echo ==================================================

:: 1. Virtual Environment Setup
if exist .venv (
    if not exist .venv\Scripts\activate (
        echo [!] Detected incompatible environment. Recreating...
        rmdir /s /q .venv
        python -m venv .venv
        call .venv\Scripts\activate
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    ) else (
        echo [+] Activating environment...
        call .venv\Scripts\activate
    )
) else (
    echo [+] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

:: 2. Launch Application
echo.
echo [+] Starting Web UI Dashboard...
echo [+] Browser will open automatically at http://127.0.0.1:8000
echo.

:: Launch browser after a short delay to let server start
start /b "" cmd /c "timeout /t 3 > nul && start http://127.0.0.1:8000"

:: Start the web application
uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload

pause
