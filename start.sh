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
if [ -f "python/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r python/requirements.txt
else
    echo "Warning: python/requirements.txt not found."
fi

echo "=================================================="
echo "Starting Execution Engine..."
echo "=================================================="

# Run the application
python3 python/app.py

# Deactivate venv on exit
deactivate
