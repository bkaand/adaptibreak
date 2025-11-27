# AdaptiBreak

CS 449/549 – Human-Computer Interaction, Fall 2025  
Sabancı University

Study break system that uses your webcam to detect when you're getting tired and suggests breaks based on that instead of fixed timers.

## The Idea

Pomodoro timers force you to take breaks every 25 minutes regardless of how you're feeling. Sometimes you're in the zone, sometimes you're already exhausted after 15 minutes. 

This uses MediaPipe to watch for fatigue signs (blinks, yawns, posture) and suggests breaks when you actually need them. We're testing if it works better than regular timers.

## Features

- Monitors blink rate, yawning, head/shoulder posture with MediaPipe
- Suggests breaks when fatigue is detected
- Traditional Pomodoro mode included for comparison
- Built-in flashcard interface for the study
- Everything runs locally, no cloud processing

## Setup

Python 3.8+, webcam, macOS/Windows/Linux

```bash
pip install -r requirements.txt
python main.py
```

### Flutter GUI (optional)

There's also a Flutter desktop interface:

```bash
flutter config --enable-macos-desktop
cd flutter_app && flutter pub get && cd ..
./run_flutter_app.sh
```

## Usage

1. Sit in front of your webcam
2. Choose Adaptive mode or Fixed timer (Pomodoro)
3. Study the flashcards
4. System suggests breaks when it detects fatigue
5. Fill out the survey after

## How It Works

Monitors several fatigue indicators:

- **Blink rate** - Normal is 12-20/min, deviations suggest fatigue
- **Yawning** - Detected via mouth aspect ratio  
- **Head posture** - Forward lean, tilting
- **Hand position** - Head resting, face touching
- **Shoulder posture** - Slouching, uneven shoulders

These get combined into a fatigue score. When it stays high for 10+ seconds, break is suggested.

## Files

```
main.py                 - Main tkinter app
backend_api.py          - FastAPI server for Flutter GUI
fatigue_detector.py     - Detection algorithms
config.py               - Settings and thresholds
evaluation.py           - SUS questionnaire
data_logger.py          - Session logging
flashcards.json         - Study materials
flutter_app/            - Desktop GUI (optional)
```

## Privacy

Everything processes locally. No frames saved or uploaded. Only logs anonymized metrics like timestamps and fatigue scores.

## Study Design

Within-subjects study comparing adaptive vs fixed timer breaks.

Hypotheses:
1. Adaptive breaks reduce perceived fatigue
2. System achieves decent usability (SUS > 70)

Measuring: vocabulary recall, self-rated fatigue, usability scores, user feedback.

## Troubleshooting

**Webcam issues** - Check permissions, close other apps using camera

**Bad detection** - Better lighting, sit 50-80cm away, keep shoulders in frame

**Lag** - Close other apps, lower webcam resolution in config.py

## Technical Stack

OpenCV + MediaPipe for landmark detection, FastAPI backend, runs ~25-30 FPS.

## References

Lugaresi et al. (2019). MediaPipe framework. arXiv:1906.08172  
Ariga & Lleras (2011). Brief mental breaks. Cognition 118(3)  
Cirillo (2006). The Pomodoro Technique
