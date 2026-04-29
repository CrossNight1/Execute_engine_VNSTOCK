@echo off
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ==================================================
echo Setting up virtual environment and dependencies...
echo ==================================================

IF NOT EXIST ".venv" (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

IF EXIST "python\requirements.txt" (
    echo Installing dependencies...
    pip install -r python\requirements.txt
) ELSE (
    echo Warning: python\requirements.txt not found.
)

echo ==================================================
echo Starting Execution Engine...
echo ==================================================

python python/app.py

pause
