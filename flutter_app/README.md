# AdaptiBreak Flutter GUI

Desktop interface for AdaptiBreak.

## Run It

```bash
flutter pub get
flutter run -d macos  # or windows/linux
```

Make sure the Python backend is running first:
```bash
cd .. && python backend_api.py
```

Backend: http://127.0.0.1:8000

## Structure

```
lib/
├── main.dart           # Main app
└── services/
    └── api_service.dart   # Backend API calls
```
