#!/bin/bash

# AdaptiBreak Demo Launcher
# Starts all components for the demo

echo "=========================================="
echo "  AdaptiBreak Demo Launcher"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down all components..."
    kill $BACKEND_PID 2>/dev/null
    kill $CAMERA_PID 2>/dev/null
    kill $FLOATING_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend API
echo "Starting Backend API..."
python backend_api.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend is running"
else
    echo "[..] Backend may still be starting..."
fi

# Start Camera Preview
echo "Starting Camera Preview..."
python camera_preview.py &
CAMERA_PID=$!

# Wait a moment
sleep 2

# Start Floating Bar
echo "Starting Floating Bar..."
cd floating_bar_app
flutter run -d macos &
FLOATING_PID=$!
cd ..

echo ""
echo "=========================================="
echo "  All components started!"
echo "=========================================="
echo ""
echo "  Camera Preview: Running"
echo "  Floating Bar: Running"
echo "  Backend API: http://127.0.0.1:8000"
echo ""
echo "  Press Ctrl+C to stop all components"
echo "=========================================="

# Wait for any process to exit
wait

