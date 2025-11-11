# AdaptiBreak: Complete Project Overview

## 📋 Project Summary

**AdaptiBreak** is a research-focused application that uses **MediaPipe facial landmark detection** to provide personalized study break suggestions based on real-time fatigue indicators. This system compares adaptive break timing against traditional Pomodoro technique for HCI research purposes.

### Key Innovation
Instead of fixed 25-minute intervals, AdaptiBreak detects:
- 👁️ **Blink patterns** (frequency anomalies)
- 🥱 **Yawning** (mouth aspect ratio)
- 🧍 **Head posture** (tilt and forward lean)

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AdaptiBreak System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Webcam     │───▶│  MediaPipe   │───▶│   Fatigue    │  │
│  │   Input      │    │  Face Mesh   │    │  Detection   │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                   │          │
│  ┌──────────────┐    ┌──────────────┐           │          │
│  │  Flashcard   │    │    Break     │◀──────────┘          │
│  │   Study      │◀──▶│  Suggestion  │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Recall Test │───▶│  Evaluation  │───▶│     Data     │  │
│  │  (20 items)  │    │  (SUS, etc.) │    │   Logging    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
adaptibreak/
│
├── main.py                      # Main application & GUI
├── fatigue_detector.py          # MediaPipe-based fatigue detection
├── evaluation.py                # SUS questionnaire & recall test
├── data_logger.py               # Session data logging & privacy
├── config.py                    # Configuration & thresholds
├── flashcards.json              # 50 vocabulary items
│
├── demo_fatigue_detector.py     # Quick demo (no full study)
├── analyze_results.py           # Statistical analysis & plots
│
├── requirements.txt             # Python dependencies
├── README.md                    # Full documentation
├── QUICK_START.md              # Quick start guide
├── PROJECT_OVERVIEW.md         # This file
├── .gitignore                  # Git ignore rules
└── run.sh                      # Automated launcher script
```

## 🔬 Research Design

### Study Type
**Within-Subjects Design** with counterbalancing

### Conditions
1. **Fixed-Timer Mode** (Control)
   - 25-minute work intervals
   - 5-minute breaks
   - Traditional Pomodoro

2. **Adaptive Mode** (Experimental)
   - Dynamic break suggestions
   - Fatigue-based timing
   - Webcam monitoring

### Procedure (Per Session)
1. **Consent & Demographics** (5 min)
2. **Study Phase** (45 min) - Flashcard learning
3. **Recall Test** (10 min) - 20 multiple-choice questions
4. **Evaluation** (10 min) - SUS + feedback

Total: ~70 minutes per session × 2 sessions per participant

### Measures

**Objective:**
- Test score (% correct on recall test)
- Blink rate (blinks/minute)
- Yawn frequency
- Head posture angles
- Fatigue score (0-1)

**Subjective:**
- Fatigue rating (1-5 scale)
- Concentration rating (1-5)
- Alertness rating (1-5)
- SUS score (0-100)
- Qualitative feedback

## 🎯 Research Hypotheses

### H1: Performance
Adaptive breaks will improve or maintain test performance compared to fixed intervals.

**Metric:** Recall test score (%)  
**Expected:** Adaptive ≥ Fixed

### H2: Fatigue
Adaptive breaks will reduce perceived fatigue during study sessions.

**Metric:** Self-reported fatigue rating (1-5)  
**Expected:** Adaptive < Fixed (lower = less tired)

### H3: Usability
The adaptive system will achieve acceptable usability scores.

**Metric:** SUS score  
**Expected:** SUS ≥ 68 (above average)

## 🧠 Fatigue Detection Algorithm

### Eye Aspect Ratio (EAR)
```
       ||p2 - p6|| + ||p3 - p5||
EAR = ──────────────────────────
            2 × ||p1 - p4||
```
- **Threshold:** < 0.25 indicates blink
- **Normal range:** 12-20 blinks/min
- **Fatigue:** < 12 or > 30 blinks/min

### Mouth Aspect Ratio (MAR)
```
       ||p2 - p8||
MAR = ────────────
       ||p1 - p5||
```
- **Threshold:** > 0.6 indicates yawn
- **Detection:** Sustained for 15+ frames

### Head Pose
- **Tilt angle:** Side-to-side head tilt
- **Forward angle:** Forward lean detection
- **Thresholds:** >15° tilt, >20° forward = fatigue

### Fatigue Score (0-1)
```python
fatigue = 0.3 × blink_score + 
          0.4 × yawn_score + 
          0.3 × posture_score
```
- **Break suggested when:** fatigue ≥ 0.6 (sustained)

## 🔐 Privacy & Ethics

### Privacy Measures
✅ All processing is **local** (on-device)  
✅ **Zero webcam storage** - frames discarded immediately  
✅ Only **aggregated fatigue scores** logged  
✅ **No facial images** or raw landmark data saved  
✅ **Anonymous participant IDs** (e.g., P001)  

### Ethical Compliance
- ✅ Informed consent required
- ✅ Voluntary participation
- ✅ Right to withdraw anytime
- ✅ Data anonymization
- ✅ Academic use only

## 📊 Expected Results

Based on prior literature:

### Test Performance
- **Fixed:** 65-75% (baseline)
- **Adaptive:** 68-78% (slight improvement expected)
- **Effect size:** Small to medium (d ≈ 0.3-0.5)

### SUS Scores
- **Fixed:** 70-75 (above average)
- **Adaptive:** 65-72 (potentially lower due to novelty)
- **Target:** Both > 68 (acceptable)

### Fatigue Ratings
- **Fixed:** 3.2-3.8 / 5
- **Adaptive:** 2.8-3.4 / 5 (lower is better)
- **Difference:** Moderate effect expected

## 🚀 Running the System

### Quick Start
```bash
cd /Users/kaan/Desktop/adaptibreak
./run.sh
```

### Manual Run
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Test Fatigue Detection Only
```bash
python3 demo_fatigue_detector.py
```

### Analyze Results
```bash
python3 analyze_results.py
```

## 📈 Data Analysis Pipeline

### 1. Data Collection
- Run study sessions via `main.py`
- Data auto-saved in `study_sessions/`

### 2. Analysis
```bash
python3 analyze_results.py
```

Generates:
- Test performance comparison
- Fatigue ratings visualization
- SUS score analysis
- Biometric patterns
- Comprehensive report
- Statistical tests (t-tests, correlations)

### 3. Statistical Tests
- **t-test**: Compare test scores between conditions
- **Pearson correlation**: Objective vs subjective fatigue
- **Descriptive statistics**: Means, SDs, ranges

## 🎓 Academic Context

### Course
CS 449/549 - Human-Computer Interaction  
Sabancı University, Fall 2025

### Related Literature
- **Ariga & Lleras (2011)**: Brief breaks maintain attention
- **Lugaresi et al. (2019)**: MediaPipe framework
- **Sweller et al. (1998)**: Cognitive load theory
- **Ji et al. (2004)**: Real-time fatigue monitoring

### Applications
- Educational technology
- E-learning platforms
- Productivity tools
- Workplace wellness systems
- Driver fatigue monitoring (future work)

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.8+**
- **OpenCV** - Webcam capture
- **MediaPipe** - Facial landmark detection
- **Tkinter** - GUI framework
- **NumPy** - Numerical computing
- **Pandas** - Data analysis
- **Matplotlib/Seaborn** - Visualization

### Key Libraries
```
opencv-python==4.8.1.78
mediapipe==0.10.8
numpy==1.24.3
pandas==2.1.3
matplotlib==3.8.2
seaborn==0.13.0
```

## 🎯 Future Enhancements

### Short-term
- [ ] Add real-time biometric visualization dashboard
- [ ] Implement machine learning for personalized thresholds
- [ ] Multi-language support for flashcards
- [ ] Sound notifications for break suggestions

### Long-term
- [ ] Mobile app version (iOS/Android)
- [ ] Integration with calendar/productivity apps
- [ ] Heart rate variability (HRV) monitoring
- [ ] Eye-tracking integration
- [ ] Adaptive learning difficulty adjustment
- [ ] Cloud-based cohort comparison (anonymized)

## 📝 Citation

If you use this system in your research:

```bibtex
@software{adaptibreak2025,
  title={AdaptiBreak: Biometric Feedback for Personalized Study Break Timing},
  author={Durmaz, Bilgekağan and Şimşek, Cihat Bera and 
          Memiş, Aynur Aybüke and Yıldızbaş, Mustafa Mert and 
          Urasoğlu, Bora},
  year={2025},
  institution={Sabancı University},
  course={CS 449/549 Human-Computer Interaction}
}
```

## 👥 Team Contributions

| Member | Role | Contributions |
|--------|------|---------------|
| **Bilgekağan Durmaz** | Technical Lead | MediaPipe integration, fatigue algorithm |
| **Cihat Bera Şimşek** | Research | Literature review, hypothesis formation |
| **Aynur Aybüke Memiş** | Data Analysis | Study design, statistical analysis |
| **Mustafa Mert Yıldızbaş** | UI/UX | Interface design, usability testing |
| **Bora Urasoğlu** | Coordination | Ethics, participant recruitment |

## 📞 Support & Contact

**Questions?**
- Check `QUICK_START.md` for troubleshooting
- Review `README.md` for detailed documentation
- Run `demo_fatigue_detector.py` for testing

**Instructor:** Asst. Prof. Polat Göktaş  
**Course:** CS 449/549, Sabancı University

---

**Built with ❤️ for better learning experiences**

*Last updated: October 31, 2025*

