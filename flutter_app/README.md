# AdaptiBreak Flutter GUI

Modern desktop interface for AdaptiBreak fatigue detection.

## Setup

```bash
flutter pub get
flutter run -d macos  # or windows/linux
```

## Features

- Material 3 design
- Real-time fatigue monitoring
- Passive floating bar
- No alerts or popups

## Structure

```
lib/
├── main.dart              # Main window
├── floating_bar.dart      # Floating bar component
└── services/
    └── api_service.dart   # API client
```

## Backend Required

Start the Python backend first:
```bash
cd .. && python backend_api.py
```

Backend runs at `http://127.0.0.1:8000`
