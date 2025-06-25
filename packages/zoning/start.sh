#!/bin/bash

echo "==================================="
echo "Lusaka Zoning Platform - Startup"
echo "==================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting development server..."
echo "- URL: http://localhost:5000"
echo "- Login: admin / admin123"
echo "- Press Ctrl+C to stop"
echo ""

# Run the development server
python run_dev.py