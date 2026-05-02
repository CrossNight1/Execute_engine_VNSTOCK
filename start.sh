#!/bin/bash

# Resolve the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Setting up virtual environment and dependencies..."
echo "=================================================="

# Create .venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found."
fi

clear
echo "=================================================="
echo "Please choose your interface:"
echo "[1] Web UI Dashboard (Recommended - Easiest)"
echo "[2] Classic Terminal CLI"
echo "=================================================="
read -p "Enter choice (1 or 2, default 1): " choice
choice=${choice:-1}

if [ "$choice" = "1" ]; then
    echo "Starting Web UI Dashboard..."
    echo "Open your browser at http://127.0.0.1:8000"
    # Wait for uvicorn to start then open browser
    (sleep 1.5 && open "http://127.0.0.1:8000") &
    uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload
else
    echo "Starting Terminal CLI..."
    python app.py
fi

# Deactivate venv on exit
deactivate
