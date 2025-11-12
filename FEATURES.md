# AdaptiBreak - Detection Features

This document describes all detection features implemented in AdaptiBreak.

---

## Detection Systems

### 1. 👁️ Blink Detection (Eye Aspect Ratio)
- **Detects:** Abnormal blink frequencies indicating fatigue
- **Method:** Eye Aspect Ratio (EAR) calculation
- **Normal:** 12-20 blinks/minute
- **Fatigue indicators:** <5 or >30 blinks/minute

### 2. 🥱 Yawn Detection (Mouth Aspect Ratio)
- **Detects:** Yawning as fatigue indicator
- **Method:** Mouth Aspect Ratio (MAR) calculation
- **Threshold:** Sustained mouth opening >0.95 ratio for ~1.3 seconds
- **Fatigue indicator:** 2+ yawns in 10 minutes

### 3. 🧠 Head Pose Tracking
- **Detects:** Poor head posture from fatigue
- **Metrics:**
  - Tilt angle (side-to-side lean)
  - Forward angle (slouching forward)
- **Thresholds:** >15° tilt, >20° forward

### 4. 👋 Hand Position Detection
- **Detects:** Fatigue-related hand behaviors
- **Tracks:**
  - Hands near face (head resting)
  - Hands covering face (eye rubbing)
  - Fidgeting movements
- **Method:** Hand-face distance and movement analysis

### 5. 💪 Shoulder Posture Detection
- **Detects:** Poor ergonomics and tension
- **Tracks:**
  - Shoulder tilt (uneven shoulders >10°)
  - Forward slouching (shoulders ahead of hips)
  - Raised shoulders (tension/stress)
- **Method:** MediaPipe Pose landmark analysis
- **Setup:** Keep shoulders visible in frame

### 6. 💧 Drinking Behavior Tracking
- **Detects:** Hydration patterns
- **Methods:**
  - Hand-to-mouth gesture recognition (primary)
  - Optional object detection for cups/bottles
- **Patterns analyzed:**
  - Normal: 2-6 drinks/hour
  - Low: <1 drink/hour (dehydration risk)
  - High: >10 drinks/hour (restlessness indicator)

---

## Fatigue Scoring

```
Fatigue Score = 
    20% × Blink patterns +
    25% × Yawning +
    20% × Head posture +
    15% × Hand position +
    20% × Shoulder posture
```

**Break suggested when:** Score ≥ 0.6 sustained for 10 seconds

---

## Configuration

All thresholds adjustable in `config.py`:

```python
# Enable/disable features
DETECT_HANDS = True
DETECT_SHOULDERS = True
DETECT_DRINKING = True

# Adjust thresholds
EAR_THRESHOLD = 0.23              # Blink sensitivity
MAR_THRESHOLD = 0.95              # Yawn sensitivity
SHOULDER_TILT_THRESHOLD = 10      # Shoulder tilt (degrees)
DRINK_TO_MOUTH_THRESHOLD = 0.15   # Drinking gesture distance
```

---

## Troubleshooting

### Poor Detection
- Ensure good lighting on face and upper body
- Keep shoulders visible in frame
- Position camera 50-80cm away at eye level
- Avoid backlighting

### False Positives
- Adjust thresholds in `config.py`
- Increase `MIN_DETECTION_CONFIDENCE` values
- Check lighting conditions

### Performance Issues
- Disable features you don't need
- Reduce webcam resolution in config
- Close other camera-using applications

---

## Testing

Run the demo to test all features:
```bash
python demo_fatigue_detector.py
```

Test each feature:
- ✅ Blink naturally - should count blinks
- ✅ Yawn - should detect after sustained opening
- ✅ Lean head forward/sideways - should detect posture
- ✅ Rest head on hand - should detect hand near face
- ✅ Slouch shoulders - should detect poor posture
- ✅ Drink from cup - should count drinking gesture

---

## Privacy

- ✅ All processing is local (no cloud)
- ✅ No images/videos stored
- ✅ Only aggregate metrics logged
- ✅ All features can be disabled
- ✅ Anonymous data collection

---

## Technical Details

**MediaPipe Models Used:**
- Face Mesh: 468 facial landmarks
- Hands: 21 hand landmarks per hand
- Pose: 33 body landmarks

**Performance:**
- FPS: 25-30 on modern hardware
- CPU: 10-15% usage
- RAM: ~200MB

**Dependencies:**
- OpenCV 4.8+
- MediaPipe 0.10.8
- NumPy, Pillow

---

For full technical documentation, see code comments in `fatigue_detector.py`.

