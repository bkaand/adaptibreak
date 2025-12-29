#!/bin/bash

# AdaptiBreak Flutter App Launcher
# Starts both Python backend and Flutter frontend

echo "=========================================="
echo "  AdaptiBreak - Modern Desktop GUI"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Flutter is available
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found. Please install Flutter SDK."
    echo "   Visit: https://docs.flutter.dev/get-started/install"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "📦 Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    deactivate
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flutter dependencies are installed
if [ ! -d "flutter_app/.dart_tool" ]; then
    echo "📦 Installing Flutter dependencies..."
    cd flutter_app
    flutter pub get
    cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    deactivate
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Python backend
echo "🚀 Starting Python backend..."
python backend_api.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check for errors above."
    exit 1
fi

# Test backend health
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may not be ready yet..."
fi

# Start Flutter app
echo ""
echo "🎨 Starting Flutter GUI..."
echo "=========================================="
cd flutter_app

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
else
    echo "⚠️  Unknown platform, trying 'macos'..."
    PLATFORM="macos"
fi

flutter run -d $PLATFORM

# Cleanup when Flutter exits
cd ..
cleanup

