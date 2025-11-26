# AdaptiBreak Flutter GUI - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd flutter_app && flutter pub get && cd ..
```

### 2. Enable Flutter Desktop (First Time)
```bash
flutter config --enable-macos-desktop  # or windows/linux
```

### 3. Run the App
```bash
# Option 1: One-command launch
./run_flutter_app.sh

# Option 2: Manual launch
# Terminal 1: python backend_api.py
# Terminal 2: cd flutter_app && flutter run -d macos
```

---

## Architecture

```
Flutter Desktop GUI (Material 3)
    ↕ HTTP REST API (localhost:8000)
FastAPI Backend
    ↕ Threading
FatigueDetector (MediaPipe + OpenCV)
    ↕
Webcam
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check backend status |
| `/start` | POST | Start detection session |
| `/status` | GET | Get current metrics |
| `/stop` | POST | Stop session |

---

## Features

✅ Modern Material 3 design  
✅ Real-time fatigue monitoring  
✅ No alerts or popups (passive UI)  
✅ Optional floating bar (220×50px)  
✅ Fully offline processing  

---

## Troubleshooting

**Backend not available:**
```bash
curl http://127.0.0.1:8000/health
python backend_api.py  # Restart if needed
```

**Webcam issues:**
- macOS: System Preferences → Security → Camera
- Windows: Settings → Privacy → Camera
- Linux: `sudo usermod -a -G video $USER`

**Flutter errors:**
```bash
cd flutter_app
flutter clean && flutter pub get
flutter run
```

---

## Customization

**Change colors** (`flutter_app/lib/main.dart`):
```dart
colorScheme: ColorScheme.fromSeed(
  seedColor: const Color(0xFF4287f5),  // Change this
),
```

**Update frequency** (`flutter_app/lib/main.dart`):
```dart
Timer.periodic(const Duration(seconds: 2), ...)  // Change interval
```

---

## Files Created

```
adaptibreak-1/
├── backend_api.py           # FastAPI server
├── run_flutter_app.sh       # Launch script
└── flutter_app/             # Flutter desktop app
    ├── lib/
    │   ├── main.dart
    │   ├── floating_bar.dart
    │   └── services/api_service.dart
    └── pubspec.yaml
```

---

That's it! Run `./run_flutter_app.sh` to get started.
