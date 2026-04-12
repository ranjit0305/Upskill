#!/bin/bash

# Upskill Backend Server Start Script for Mac/Linux

echo "Starting Upskill Backend Server..."
echo ""

# Navigate to the backend directory if not already there
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment (venv) not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements if they haven't been installed or uvicorn is missing
if [ ! -f "venv/pip_installed" ] || ! ./venv/bin/python3 -m uvicorn --version > /dev/null 2>&1; then
    echo "Installing/verifying dependencies. This may take a minute..."
    ./venv/bin/python3 -m pip install --upgrade pip
    ./venv/bin/python3 -m pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        touch venv/pip_installed
    else
        echo "Error: Failed to install dependencies."
        exit 1
    fi
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ".env file not found. Copying .env.example..."
    cp .env.example .env
    echo "Please update the .env file with your configuration."
fi

echo ""
echo "Starting uvicorn server..."
python3 -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
