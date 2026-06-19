#!/usr/bin/env bash

echo "=========================================="
echo "Starting Indian Market Backtester"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[INFO] Checking dependencies..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Launch application
echo "[INFO] Launching Streamlit dashboard..."
streamlit run ui/app.py
