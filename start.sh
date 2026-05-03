#!/bin/bash

# Resolve the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "    VNSTOCK Execution Engine Launcher"
echo "=================================================="

# 1. Virtual Environment Setup
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/activate" ]; then
    if [ -d ".venv" ]; then
        echo "[!] Detected incompatible environment. Recreating..."
        rm -rf .venv
    fi
    echo "[+] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "[+] Activating environment..."
    source .venv/bin/activate
fi

# 2. Launch Application
echo ""
echo "[+] Starting Web UI Dashboard..."
echo "[+] Browser will open at http://127.0.0.1:8000"
echo ""

# Launch browser after a short delay
(sleep 2 && open "http://127.0.0.1:8000") &

# Start the web application
uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload
