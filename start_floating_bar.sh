#!/bin/bash

# AdaptiBreak Floating Bar Launcher
# Launched automatically when "Start Session" is clicked

cd /Users/kaan/Desktop/adaptibreak-1

echo "[INFO] Starting camera preview..."
source venv/bin/activate
python camera_preview.py &
CAMERA_PID=$!

echo "[INFO] Starting floating bar..."
cd floating_bar_app
flutter run -d macos 2>&1

# When floating bar exits, also stop camera preview
kill $CAMERA_PID 2>/dev/null

echo "[INFO] Session components stopped"

