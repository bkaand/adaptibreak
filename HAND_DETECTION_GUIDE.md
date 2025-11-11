# Hand Position Detection - Feature Guide

## Overview

**Hand position detection** has been added to AdaptiBreak to provide additional fatigue indicators. Research shows that when people get tired during study sessions, they exhibit specific hand behaviors like:

- **Head resting on hands** (supporting head)
- **Eye/face rubbing** (touching face)
- **Fidgeting** (excessive hand movement)

These are natural fatigue indicators that complement the existing face-based detection (blinks, yawns, head pose).

---

## Technical Implementation

### MediaPipe Hands Integration

The system now uses **MediaPipe Hands** alongside MediaPipe Face Mesh:
- Tracks up to **2 hands** (both hands)
- Detects **21 landmarks per hand** (wrist, fingers, palm)
- Real-time processing at ~30 FPS

### Detection Algorithms

#### 1. **Hands Near Face**
Detects when hands are in proximity to the face (common fatigue behavior).

**Algorithm:**
```python
# Calculate distance between hand center and face center
hand_center = (wrist + index_tip + middle_tip) / 3
distance = sqrt((hand_x - face_x)² + (hand_y - face_y)²)

# Threshold: 0.15 (normalized coordinates)
if distance < HAND_NEAR_FACE_THRESHOLD:
    hands_near_face = True
```

**Visual Indicator:** Orange text `[NEAR FACE]`

#### 2. **Hands Covering Face**
Detects very close proximity (eye rubbing, face touching).

**Algorithm:**
```python
# Stricter threshold for actual face contact
if distance < HAND_COVERING_FACE_THRESHOLD:  # 0.12
    hands_covering_face = True
```

**Visual Indicator:** Orange text `[COVERING]`

#### 3. **Fidgeting Detection**
Detects excessive hand movement between frames.

**Algorithm:**
```python
# Track hand position changes
movement = sqrt((curr_x - prev_x)² + (curr_y - prev_y)²)

# Threshold: 0.05 movement between frames
if movement > FIDGET_MOVEMENT_THRESHOLD:
    fidgeting = True
```

**Visual Indicator:** `[FIDGETING]`

---

## Configuration Parameters

All thresholds are configurable in `config.py`:

```python
# Enable/disable hand tracking
DETECT_HANDS = True

# Detection thresholds
MAX_NUM_HANDS = 2                           # Track both hands
MIN_HAND_DETECTION_CONFIDENCE = 0.7         # Initial detection
MIN_HAND_TRACKING_CONFIDENCE = 0.5          # Tracking confidence

# Proximity thresholds (normalized 0-1)
HAND_NEAR_FACE_THRESHOLD = 0.15            # Hand near face
HAND_COVERING_FACE_THRESHOLD = 0.12        # Hand covering face
FIDGET_MOVEMENT_THRESHOLD = 0.05           # Fidgeting detection
```

---

## Fatigue Score Integration

Hand position is now part of the **composite fatigue score**:

### Updated Weights:
```python
WEIGHT_BLINK = 0.25         # 25% (was 30%)
WEIGHT_YAWN = 0.30          # 30% (was 40%)
WEIGHT_HEAD_POSE = 0.25     # 25% (was 30%)
WEIGHT_HAND_POSITION = 0.20 # 20% (NEW!)
```

### Hand Score Calculation:
```python
# Count hand-near-face events in last 30 seconds
hand_near_face_rate = events_in_30s / 30.0

# Score increases with frequency
hand_score = min(hand_near_face_rate * 2.0, 1.0)
# 0.5+ rate (15+ events/30s) = maximum score
```

### Final Fatigue Score:
```
Fatigue = 0.25×Blink + 0.30×Yawn + 0.25×HeadPose + 0.20×HandPosition
```

---

## Visual Feedback

### In Demo (`demo_fatigue_detector.py`):

The demo now shows real-time hand detection:

```
Face: Detected
Blink Rate: 20.1 /min
Yawns: 0
EAR: 0.285
MAR: 0.423
Hands: 2 [NEAR FACE] [FIDGETING]  ← NEW!
Fatigue: 0.34
[████████░░░░░░░░░░░░]
```

**Color Coding:**
- **White** = Hands detected, but not near face
- **Orange** = Hands near face (potential fatigue)

**Hand Landmarks:**
- Drawn in **magenta/purple** color
- Shows skeleton of both hands
- 21 landmarks per hand

---

## Break Suggestion Logic

Hand detection is included in break suggestion reasons:

```python
if hand_near_face_events >= 10 in last 30 seconds:
    reasons.append("hands near face")
```

**Example Outputs:**
```
⚠️ BREAK SUGGESTED: yawning detected and hands near face
⚠️ BREAK SUGGESTED: increased blinking and forward posture and hands near face
```

---

## Data Logging

New metrics are tracked and logged:

### Session Statistics:
```python
stats = {
    'hand_near_face_events': 47,      # Total events
    'hand_covering_face_events': 12,  # Very close contact
    'fidget_events': 156              # Movement detections
}
```

These are included in:
- CSV session logs (`data/sessions/`)
- Summary statistics
- Evaluation reports

---

## How to Use

### 1. **Run the Demo**
```bash
cd /Users/kaan/Desktop/adaptibreak
python3 demo_fatigue_detector.py
```

**What to expect:**
- Green facial landmarks (face mesh)
- **Purple/magenta hand skeleton** (hands)
- Hand position indicators update in real-time
- Try resting your head on your hand to trigger detection!

### 2. **Testing Hand Detection**

**To trigger "Hands Near Face":**
1. Rest your chin on your hand
2. Put your hand on your cheek
3. Touch your face

**To trigger "Hands Covering Face":**
1. Rub your eyes
2. Cover your face with both hands

**To trigger "Fidgeting":**
1. Wave your hands in frame
2. Repeatedly move hands near your face

### 3. **Disable Hand Detection (if needed)**

Edit `config.py`:
```python
DETECT_HANDS = False  # Set to False
```

This can be useful if:
- Performance is an issue
- You want face-only detection
- Testing baseline without hands

---

## Performance Impact

### Computational Cost:
- **MediaPipe Face Mesh:** ~15ms per frame
- **MediaPipe Hands:** ~10ms per frame (both hands)
- **Total:** ~25ms per frame ≈ **30-40 FPS**

### Optimization:
- Hand detection only runs when face is detected
- Uses GPU acceleration (if available)
- Lightweight enough for real-time use

---

## Research Implications

### For Your HCI Study:

**Hypothesis:**
"Hand position detection will improve fatigue detection accuracy by identifying behavioral indicators beyond facial expressions."

**Evaluation Metrics:**
1. **Precision:** Do hand-based break suggestions correlate with self-reported fatigue?
2. **User Perception:** Do participants find hand detection useful or intrusive?
3. **Privacy Concerns:** How do participants feel about hand tracking vs face-only?

**Data to Collect:**
- Hand-near-face events per session
- Correlation between hand events and break acceptance
- Qualitative feedback on hand detection

**Expected Findings:**
- Hand detection captures fatigue behaviors missed by face analysis alone
- Particularly useful for detecting "tired posture" (head resting on hands)
- May increase false positives if participants naturally gesture while thinking

---

## Calibration Tips

### Adjusting Sensitivity:

**Too sensitive?** (Detecting normal hand gestures)
```python
# Increase thresholds (less sensitive)
HAND_NEAR_FACE_THRESHOLD = 0.20  # from 0.15
FIDGET_MOVEMENT_THRESHOLD = 0.08  # from 0.05
```

**Not sensitive enough?** (Missing actual fatigue behaviors)
```python
# Decrease thresholds (more sensitive)
HAND_NEAR_FACE_THRESHOLD = 0.12  # from 0.15
FIDGET_MOVEMENT_THRESHOLD = 0.03  # from 0.05
```

**Reduce weight in fatigue score:**
```python
# If hand detection is too noisy
WEIGHT_HAND_POSITION = 0.10  # from 0.20
WEIGHT_BLINK = 0.30          # increase others proportionally
```

---

## Troubleshooting

### Issue: Hands not detected

**Solution:**
1. Ensure good lighting (hands need to be visible)
2. Keep hands in frame with face
3. Check camera quality (low-res cameras may struggle)

### Issue: False positives

**Cause:** Natural gestures detected as fatigue

**Solution:**
1. Increase `HAND_NEAR_FACE_THRESHOLD`
2. Require more events for break suggestion (increase from 10 to 20)
3. Add time filtering (only count sustained proximity)

### Issue: Performance drops

**Solution:**
1. Reduce `MAX_NUM_HANDS` to 1 (track only one hand)
2. Lower camera resolution
3. Disable hand detection for low-spec machines

---

## Example: Complete Detection Scenario

**Scenario:** Student gets tired after 30 minutes

**Timeline:**
```
0:00 - Session starts
├─ Hands not visible (studying, typing)
├─ Face detected normally
└─ Fatigue: 0.12 (low)

15:00 - Getting tired
├─ Blink rate increases: 18 → 24 /min
├─ Occasional hand-to-face touches (4 events)
└─ Fatigue: 0.38 (moderate)

28:00 - Significantly fatigued
├─ Blink rate: 28 /min (high)
├─ 1 yawn detected
├─ Head resting on hand (sustained, 15+ events)
├─ Fidgeting (restless movements)
└─ Fatigue: 0.67 (high)

28:30 - BREAK SUGGESTED
└─ Reason: "increased blinking and yawning detected and hands near face"
```

**Key:** Hand detection caught the "head resting on hand" behavior that confirmed fatigue, triggering the break suggestion.

---

## Next Steps

1. **Test the demo** with hand detection enabled
2. **Try different hand positions** to see detection in action
3. **Run pilot sessions** to collect initial data
4. **Calibrate thresholds** based on your observations
5. **Gather user feedback** on hand tracking privacy/comfort

---

## Technical Details

### Hand Landmarks (21 points):
```
 8: Index finger tip
12: Middle finger tip
16: Ring finger tip
20: Pinky finger tip
 4: Thumb tip
 0: Wrist
```

### Face Reference Points:
```
  1: Nose tip (face center)
234: Left face boundary
454: Right face boundary
 10: Forehead
152: Chin
```

### Distance Calculation:
```
Normalized coordinates (0-1):
- 0.15 = ~15% of frame width/height
- Allows resolution-independent thresholds
```

---

## Summary

✅ **Hand detection is now fully integrated!**

**Features:**
- 3 detection types: Near face, Covering face, Fidgeting
- 20% weight in fatigue score
- Real-time visual feedback (purple hand skeleton)
- Configurable thresholds
- Logged for analysis

**Run this to see it in action:**
```bash
python3 demo_fatigue_detector.py
```

**Try:** Rest your head on your hand and watch the detection! 👋😴

---

*Last Updated: November 11, 2025*  
*AdaptiBreak: Biometric Feedback for Personalized Study Break Timing*

