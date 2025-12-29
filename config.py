"""
Configuration file for AdaptiBreak system.
Contains constants and thresholds for fatigue detection and study parameters.
"""

# ==================== WEBCAM & DETECTION SETTINGS ====================

# Webcam settings
WEBCAM_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# MediaPipe Face Mesh settings
MAX_NUM_FACES = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5

# ==================== FATIGUE DETECTION THRESHOLDS ====================

# Eye Aspect Ratio (EAR) for blink detection
EAR_THRESHOLD = 0.25  # Below this is considered a blink (will be calibrated per-user)
BLINK_CONSEC_FRAMES = 2  # Consecutive frames below threshold to count as blink

# Blink frequency thresholds (blinks per minute)
NORMAL_BLINK_MIN = 12
NORMAL_BLINK_MAX = 20
FATIGUE_BLINK_MIN = 5   # Too few blinks (staring/concentration fatigue)
FATIGUE_BLINK_MAX = 30  # Too many blinks (eye strain)

# Mouth Aspect Ratio (MAR) for yawn detection
MAR_THRESHOLD = 1.2  # Above this is considered a yawn (VERY strict - only wide open mouth)
YAWN_CONSEC_FRAMES = 25  # Frames to confirm yawn (~1.7 seconds at 15fps - must sustain wide open mouth)

# Head pose thresholds (in degrees)
HEAD_TILT_THRESHOLD = 15  # Side tilt indicating fatigue
HEAD_FORWARD_THRESHOLD = 20  # Forward lean indicating fatigue

# ==================== HAND POSITION DETECTION ====================

# Hand detection settings
DETECT_HANDS = True  # Enable/disable hand tracking
MAX_NUM_HANDS = 2  # Track both hands
MIN_HAND_DETECTION_CONFIDENCE = 0.7
MIN_HAND_TRACKING_CONFIDENCE = 0.5

# Hand-face proximity (indicates head resting on hands)
HAND_NEAR_FACE_THRESHOLD = 0.15  # Distance threshold (normalized coordinates)

# Hand covering face (eye rubbing, face touching)
HAND_COVERING_FACE_THRESHOLD = 0.12  # Closer proximity

# Fidgeting detection (hand movement)
FIDGET_MOVEMENT_THRESHOLD = 0.05  # Movement between frames to count as fidgeting

# ==================== SHOULDER POSTURE DETECTION ====================

# Shoulder detection settings
DETECT_SHOULDERS = True  # Enable/disable shoulder tracking
MIN_POSE_DETECTION_CONFIDENCE = 0.7
MIN_POSE_TRACKING_CONFIDENCE = 0.5

# Shoulder tilt threshold (degrees) - indicates leaning/slouching
SHOULDER_TILT_THRESHOLD = 10  # Angle difference between left and right shoulders

# Shoulder forward/hunch threshold (normalized coordinates)
SHOULDER_FORWARD_THRESHOLD = 0.08  # Distance shoulders are forward relative to hips

# Shoulder raise threshold (indicates tension/stress)
SHOULDER_RAISE_THRESHOLD = 0.05  # Height difference from baseline

# ==================== DRINKING BEHAVIOR DETECTION ====================

# Drinking detection settings
DETECT_DRINKING = True  # Enable/disable drinking behavior tracking
OBJECT_DETECTION_CONFIDENCE = 0.5  # Confidence threshold for object detection

# Drinkware objects to detect (COCO dataset class IDs)
DRINKWARE_CLASSES = ['cup', 'bottle']  # Can also detect 'wine glass', 'bowl'
DRINKWARE_CLASS_IDS = [41, 39]  # COCO IDs: 41=cup, 39=bottle

# Drinking gesture thresholds
DRINK_TO_MOUTH_THRESHOLD = 0.15  # Distance from drinkware to mouth (normalized)
DRINKING_DURATION_MIN = 1.0  # Minimum seconds for action to count as drinking
DRINKING_DURATION_MAX = 10.0  # Maximum seconds for single drinking action

# Drinking frequency analysis
NORMAL_DRINKING_RATE = (2, 6)  # Normal: 2-6 drinks per hour
HIGH_DRINKING_RATE = 10  # > 10 drinks/hour = excessive (may indicate restlessness)
LOW_DRINKING_RATE = 1  # < 1 drink/hour = potential dehydration concern

# ==================== PERCLOS SETTINGS ====================
# PERCLOS = Percentage of Eye Closure - Standard drowsiness metric
# Measures proportion of time eyes are closed over a time window

PERCLOS_WINDOW_SECONDS = 60  # Time window for PERCLOS calculation (standard is 1 minute)
PERCLOS_EYE_CLOSURE_THRESHOLD = 0.70  # EAR ratio below this = eye considered closed (70% closure)
PERCLOS_DROWSY_THRESHOLD = 0.15  # PERCLOS > 15% indicates drowsiness
PERCLOS_SEVERE_THRESHOLD = 0.30  # PERCLOS > 30% indicates severe drowsiness

# ==================== MAHALANOBIS DISTANCE SETTINGS ====================
# Mahalanobis distance measures multivariate deviation from baseline
# Accounts for correlations between fatigue indicators

MAHALANOBIS_FEATURES = ['ear', 'mar', 'head_tilt', 'head_forward', 'blink_rate']
MAHALANOBIS_WINDOW_SIZE = 30  # Number of frames for rolling calculation
MAHALANOBIS_ALERT_THRESHOLD = 3.0  # Distance > 3 sigma = significant deviation
MAHALANOBIS_WARNING_THRESHOLD = 2.0  # Distance > 2 sigma = moderate deviation
MAHALANOBIS_REGULARIZATION = 1e-6  # Regularization for covariance matrix stability

# ==================== FATIGUE SCORING ====================

# Fatigue score calculation weights (adjusted for PERCLOS and Mahalanobis)
WEIGHT_BLINK = 0.15
WEIGHT_YAWN = 0.20
WEIGHT_HEAD_POSE = 0.15
WEIGHT_HAND_POSITION = 0.10  # Hands near face/fidgeting
WEIGHT_SHOULDER_POSTURE = 0.15  # Shoulder slouching/hunching/tension
WEIGHT_PERCLOS = 0.15  # PERCLOS drowsiness indicator
WEIGHT_MAHALANOBIS = 0.10  # Mahalanobis multivariate deviation

# Fatigue threshold for break suggestion
FATIGUE_SCORE_THRESHOLD = 0.6  # 0 to 1 scale
FATIGUE_WINDOW_SECONDS = 60  # Time window to calculate fatigue metrics

# Cooldown period after break suggestion (seconds)
BREAK_SUGGESTION_COOLDOWN = 300  # 5 minutes

# ==================== STUDY SESSION SETTINGS ====================

# Fixed-Timer Mode (Pomodoro)
POMODORO_WORK_DURATION = 25 * 60  # 25 minutes in seconds
POMODORO_BREAK_DURATION = 5 * 60  # 5 minutes in seconds

# Adaptive Mode
ADAPTIVE_SESSION_DURATION = 45 * 60  # 45 minutes total
ADAPTIVE_MIN_WORK_TIME = 10 * 60  # Minimum 10 minutes before first break suggestion
ADAPTIVE_BREAK_DURATION = 5 * 60  # 5 minutes

# ==================== FLASHCARD SETTINGS ====================

FLASHCARDS_PER_SESSION = 30
FLASHCARD_DISPLAY_TIME = 5  # Seconds to display each flashcard
FLASHCARD_AUTO_ADVANCE = True

# ==================== TESTING SETTINGS ====================

RECALL_TEST_QUESTIONS = 20
RECALL_TEST_TIME_LIMIT = 10 * 60  # 10 minutes

# ==================== UI SETTINGS ====================

# Colors (R, G, B)
COLOR_PRIMARY = (66, 135, 245)  # Blue
COLOR_SUCCESS = (76, 175, 80)  # Green
COLOR_WARNING = (255, 152, 0)  # Orange
COLOR_DANGER = (244, 67, 54)  # Red
COLOR_BACKGROUND = (245, 245, 245)  # Light gray
COLOR_TEXT = (33, 33, 33)  # Dark gray
COLOR_WHITE = (255, 255, 255)

# Window settings
WINDOW_TITLE = "AdaptiBreak - Personalized Study Break System"
MAIN_WINDOW_WIDTH = 1000
MAIN_WINDOW_HEIGHT = 700

# Notification settings
NOTIFICATION_DURATION = 10  # Seconds
NOTIFICATION_SOUND = True

# ==================== DATA LOGGING ====================

LOG_DIRECTORY = "study_sessions"
LOG_BIOMETRIC_DATA = True  # Log fatigue scores and metrics
LOG_INTERVAL = 5  # Seconds between data points

# ==================== PRIVACY & ETHICS ====================

STORE_WEBCAM_FRAMES = False  # Never store raw webcam data
STORE_FACE_LANDMARKS = False  # Never store facial landmark coordinates
ANONYMIZE_PARTICIPANT_DATA = True
REQUIRE_CONSENT = True

# ==================== FACIAL LANDMARKS INDICES ====================
# MediaPipe Face Mesh landmark indices for specific features

# Left eye landmarks
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# Right eye landmarks  
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

# Mouth landmarks (outer lips)
MOUTH_INDICES = [61, 291, 0, 17, 39, 269, 270, 409, 375, 321, 405, 314, 17, 84, 181, 91, 146, 78]

# Mouth for MAR calculation (simpler version)
MOUTH_MAR_INDICES = {
    'top': 13,
    'bottom': 14,
    'left': 78,
    'right': 308
}

# Nose tip for head pose
NOSE_TIP_INDEX = 1

# Face oval for head pose estimation
FACE_OVAL_INDICES = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                      397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                      172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

