# AdaptiBreak - Quick Start Guide

Welcome to AdaptiBreak! This guide will help you get started quickly.

## Prerequisites

- **Python 3.8+** installed
- **Webcam** (built-in or external)
- **macOS/Linux** or Windows

## Installation (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
cd /Users/kaan/Desktop/adaptibreak
chmod +x run.sh
./run.sh
```

The script will automatically:
- Create a virtual environment
- Install dependencies
- Launch the application

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 main.py
```

## First Run

### 1. Grant Camera Permissions
When you first run the app, macOS will ask for camera permissions. Click **Allow**.

### 2. Informed Consent
Read and accept the informed consent form to participate in the study.

### 3. Demographics
Fill out the brief demographic questionnaire (anonymous).

### 4. Select Study Mode

**Fixed-Timer Mode (Pomodoro)**
- 25-minute work intervals
- 5-minute break intervals
- Traditional approach

**Adaptive Mode**
- Dynamic break suggestions
- Based on fatigue detection
- Webcam monitoring active

### 5. Study Session (45 minutes)
- Review vocabulary flashcards
- Navigate with Previous/Next buttons
- System monitors your fatigue (adaptive mode)
- Take breaks when suggested

### 6. Recall Test (10 minutes)
- Test your memory of the vocabulary
- Multiple-choice format
- 20 questions

### 7. Evaluation (10 minutes)
- Rate your fatigue level
- Complete SUS usability questionnaire
- Provide qualitative feedback

### 8. Results & Summary
View your session summary and save data.

## Study Protocol

For research participants, you should complete **both conditions** on separate days:

1. **Day 1**: Complete one mode (randomly assigned)
2. **Day 2**: Complete the other mode
3. **Counterbalanced**: Order is randomized to reduce bias

## Troubleshooting

### Webcam Not Working

```bash
# Check if camera is detected
ls /dev/video*  # Linux
system_profiler SPCameraDataType  # macOS
```

**Solutions:**
- Close other apps using the camera (Zoom, Teams, etc.)
- Grant camera permissions in System Settings
- Try unplugging/replugging external webcam
- Restart the application

### Poor Fatigue Detection

**Tips for better accuracy:**
- Sit 50-80 cm from the webcam
- Ensure good lighting (face should be well-lit)
- Avoid backlighting (don't sit in front of a window)
- Keep your face visible (no hats, masks, or hands covering face)

### Application Crashes

```bash
# Check Python version (should be 3.8+)
python3 --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check logs
cat study_sessions/*/session_metadata.json
```

### Dependencies Won't Install

If MediaPipe installation fails:

```bash
# Update pip
pip install --upgrade pip

# Install specific version
pip install mediapipe==0.10.8

# macOS: Install Xcode Command Line Tools if needed
xcode-select --install
```

## Data Location

Session data is saved in: `study_sessions/`

Each session creates a folder with:
- `session_metadata.json` - Session info
- `biometric_data.csv` - Fatigue metrics over time
- `break_events.json` - Break suggestions and responses
- `flashcard_events.json` - Flashcard viewing log
- `evaluation.json` - Test scores, SUS, feedback
- `demographics.json` - Anonymous participant info

## Privacy & Ethics

✓ All webcam processing is **local** (on your device)  
✓ **No images** are stored or transmitted  
✓ Only **aggregated statistics** are saved  
✓ Data is **anonymous** (participant ID only)  
✓ You can **stop at any time** without penalty

## Data Analysis

After collecting data from all participants:

```python
from data_logger import AggregateAnalyzer

# Compare conditions
comparison = AggregateAnalyzer.compare_conditions()
print(comparison)

# Export for statistical analysis
df = AggregateAnalyzer.export_for_analysis()
```

## Configuration

Customize detection thresholds in `config.py`:

```python
# Fatigue detection sensitivity
FATIGUE_SCORE_THRESHOLD = 0.6  # 0-1 (higher = less sensitive)

# Blink rate thresholds
NORMAL_BLINK_MIN = 12  # blinks/minute
NORMAL_BLINK_MAX = 20

# Break timing
ADAPTIVE_MIN_WORK_TIME = 10 * 60  # minimum 10 min before break
```

## Support

**Issues?** Check these:
1. Camera permissions granted?
2. Python 3.8+ installed?
3. Dependencies installed correctly?
4. Sufficient lighting?
5. Other apps using camera?

**Contact:**
- Instructor: Asst. Prof. Polat Göktaş
- Course: CS 449/549, Sabancı University

## Research Usage

This system is designed for academic research on adaptive learning systems and biometric feedback. Key features:

- **Within-subjects design**: Each participant experiences both conditions
- **Counterbalancing**: Random order assignment
- **Objective metrics**: Test performance, biometric data
- **Subjective metrics**: SUS scores, fatigue ratings, feedback
- **Privacy-first**: Local processing, no data transmission

## Next Steps

1. ✓ Install and test the system
2. ✓ Complete pilot testing (2-3 participants)
3. ✓ Adjust thresholds based on pilot data
4. ✓ Recruit 20-25 participants
5. ✓ Run full study (2 sessions per participant)
6. ✓ Analyze data and compare conditions
7. ✓ Write up findings

Good luck with your study! 🎓

