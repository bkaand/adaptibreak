# AdaptiBreak: Biometric Feedback for Personalized Study Break Timing

**CS 449/549 – Human–Computer Interaction | Sabancı University – Fall 2025**

AdaptiBreak is an intelligent study break system that uses webcam-based biometric detection to suggest optimal break times based on real-time fatigue indicators, rather than fixed intervals like traditional Pomodoro timers.

## Features

- 🎥 **Webcam-based Fatigue Detection**: Uses MediaPipe for facial landmark tracking
- 😴 **Biometric Indicators**: Monitors blink frequency, yawning, and head posture
- 🧠 **Adaptive Break Suggestions**: Intelligent break timing based on detected fatigue
- ⏱️ **Pomodoro Comparison**: Includes traditional fixed-timer mode for research comparison
- 📚 **Integrated Study Interface**: Flashcard-based learning with vocabulary testing
- 🔒 **Privacy-First**: All processing is local, no data leaves your device
- 📊 **Research Metrics**: Built-in SUS questionnaire and performance tracking

## System Requirements

- Python 3.8 or higher
- Webcam (built-in or external)
- macOS, Windows, or Linux

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/kaan/Desktop/adaptibreak
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main.py
```

### Study Modes

1. **Fixed-Timer Mode (Pomodoro)**
   - 25-minute study sessions
   - 5-minute break intervals
   - Traditional timer-based approach

2. **Adaptive Mode**
   - Dynamic break suggestions based on fatigue
   - Real-time biometric monitoring
   - Personalized to your cognitive state

### Participant Instructions

1. Position yourself in front of the webcam with good lighting
2. Read and accept the consent form
3. Complete the demographic questionnaire
4. Study the flashcards (45 minutes)
5. Take the vocabulary recall test (10 minutes)
6. Fill out the usability survey (SUS + feedback)

## How It Works

```
Webcam Input → MediaPipe Face Detection → Feature Extraction
                                              ↓
  Break Suggestion ← Fatigue Estimation ← (Blinks, Yawns, Head Tilt)
```

### Fatigue Indicators

- **Blink Frequency**: Abnormal blink rates (too fast or too slow)
- **Yawning**: Detected through mouth aspect ratio changes
- **Head Posture**: Forward lean or tilting indicating fatigue

## Project Structure

```
adaptibreak/
├── main.py                 # Main application entry point
├── fatigue_detector.py     # MediaPipe-based fatigue detection
├── study_app.py            # Study interface and flashcard system
├── config.py               # Configuration and constants
├── data_logger.py          # Session data logging
├── evaluation.py           # SUS questionnaire and metrics
├── flashcards.json         # Vocabulary flashcard dataset
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Data and Privacy

- **Local Processing**: All webcam data is processed locally on your device
- **No Recording**: Webcam frames are analyzed in real-time and immediately discarded
- **Anonymous Data**: Only aggregated statistics are logged (no personal identifiers)
- **Voluntary**: Participants can stop at any time without penalty

## Research Design

This is a **within-subjects study** comparing two conditions:

- **Hypothesis 1**: Adaptive breaks will reduce perceived fatigue
- **Hypothesis 2**: The system will achieve high usability scores (SUS > 70)

### Evaluation Metrics

- 📝 **Performance**: Vocabulary recall test scores
- 😓 **Fatigue**: Self-rated tiredness (1-5 scale)
- 🎯 **Usability**: System Usability Scale (SUS)
- 💬 **Qualitative**: User feedback on comfort and usefulness

## Team Members

- **Bilgekağan Durmaz** – Technical Lead & Implementation
- **Cihat Bera Şimşek** – Research & Literature Review
- **Aynur Aybüke Memiş** – Study Design & Data Analysis
- **Mustafa Mert Yıldızbaş** – UI/UX Design & Testing
- **Bora Urasoğlu** – Participant Coordination & Ethics

## Troubleshooting

### Webcam Not Detected
- Ensure your webcam is connected and not in use by other applications
- Grant camera permissions when prompted
- Try restarting the application

### Poor Detection Accuracy
- Improve lighting conditions (face should be well-lit)
- Position yourself 50-80cm from the webcam
- Avoid backlighting or harsh shadows

### Performance Issues
- Close other resource-intensive applications
- Reduce webcam resolution in config.py if needed
- Ensure your Python environment has proper GPU support

## Citation

If you use this project in your research, please cite:

```
Durmaz, B., Şimşek, C. B., Memiş, A. A., Yıldızbaş, M. M., & Urasoğlu, B. (2025).
AdaptiBreak: Biometric Feedback for Personalized Study Break Timing.
CS 449/549 Human-Computer Interaction, Sabancı University.
```

## License

This project is for academic purposes only. Created for CS 449/549 – Human-Computer Interaction course at Sabancı University, Fall 2025.

## References

- Lugaresi, C., et al. (2019). MediaPipe: A framework for perception pipelines. arXiv:1906.08172
- Ariga, A., & Lleras, A. (2011). Brief and rare mental "breaks" keep you focused. Cognition, 118(3), 439–443
- Cirillo, F. (2006). The Pomodoro Technique. https://francescocirillo.com

