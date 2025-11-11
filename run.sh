#!/bin/bash
# AdaptiBreak Startup Script
# Quick launcher for the AdaptiBreak application

echo "========================================="
echo "  AdaptiBreak - Study Break System"
echo "  CS 449/549 - Sabancı University"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import cv2, mediapipe" 2>/dev/null; then
    echo "Dependencies not found. Installing..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Run the application
echo ""
echo "Starting AdaptiBreak..."
echo "----------------------------------------"
python3 main.py

# Deactivate when done
deactivate

