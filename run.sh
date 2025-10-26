#!/bin/bash
# Quick start script for LEITZ Label Generator

echo "=================================="
echo "  LEITZ Label Generator"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the application
echo ""
echo "🚀 Starting web interface..."
echo "   Open your browser to: http://127.0.0.1:5000"
echo ""
python app.py
