@echo off
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ==================================================
echo Setting up virtual environment and dependencies...
echo ==================================================

IF EXIST ".venv" (
    IF NOT EXIST ".venv\Scripts\activate" (
        echo Detected non-Windows .venv or corrupted environment.
        echo Recreating .venv for Windows...
        rmdir /s /q .venv
        python -m venv .venv
    )
) ELSE (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

IF EXIST "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt
) ELSE (
    echo Warning: requirements.txt not found.
)

cls
echo ==================================================
echo Please choose your interface:
echo [1] Web UI Dashboard (Recommended - Easiest)
echo [2] Classic Terminal CLI
echo ==================================================
set /p choice="Enter choice (1 or 2, default 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo Starting Web UI Dashboard...
    echo Open your browser at http://127.0.0.1:8000
    start /b "" cmd /c "timeout /t 3 > nul && start http://127.0.0.1:8000"
    uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload
) else (
    echo Starting Terminal CLI...
    python app.py
)

pause
