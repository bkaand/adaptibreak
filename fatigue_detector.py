"""
Fatigue Detection Module using MediaPipe Face Mesh, Hands, and Pose.
Detects blinks, yawns, head pose, hand positions, shoulder posture, and drinking behavior to estimate user fatigue in real-time.
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time
import config
import os

# Try to import filterpy for Kalman filtering
try:
    from filterpy.kalman import KalmanFilter
    KALMAN_AVAILABLE = True
except ImportError:
    KALMAN_AVAILABLE = False
    print("Note: filterpy not available, using exponential moving average fallback")


class FatigueDetector:
    """
    Real-time fatigue detector using webcam and MediaPipe Face Mesh + Hands + Pose.
    Tracks blink frequency, yawning, head posture, hand positions, and shoulder posture to estimate fatigue levels.
    """
    
    def __init__(self):
        # ============================================================
        # KALMAN FILTERING FOR NOISE REDUCTION
        # ============================================================
        # Kalman filters smooth temporal noise from MediaPipe landmarks
        # This improves real-time consistency of EAR, MAR, and posture metrics
        self.kalman_available = KALMAN_AVAILABLE
        
        if self.kalman_available:
            # EAR Kalman filter (dim_x=2: state=[value, velocity], dim_z=1: measurement=value)
            self.kf_ear = KalmanFilter(dim_x=2, dim_z=1)
            self.kf_ear.x = np.array([[0.3], [0.]])  # Initial state: [EAR≈0.3, velocity=0]
            self.kf_ear.F = np.array([[1., 1.], [0., 1.]])  # State transition matrix
            self.kf_ear.H = np.array([[1., 0.]])  # Measurement function
            self.kf_ear.P *= 1000.  # Initial uncertainty
            self.kf_ear.R = 0.01  # Measurement noise
            self.kf_ear.Q = np.array([[0.0001, 0.], [0., 0.0001]])  # Process noise
            
            # MAR Kalman filter
            self.kf_mar = KalmanFilter(dim_x=2, dim_z=1)
            self.kf_mar.x = np.array([[0.2], [0.]])  # Initial state: [MAR≈0.2, velocity=0]
            self.kf_mar.F = np.array([[1., 1.], [0., 1.]])
            self.kf_mar.H = np.array([[1., 0.]])
            self.kf_mar.P *= 1000.
            self.kf_mar.R = 0.01
            self.kf_mar.Q = np.array([[0.0001, 0.], [0., 0.0001]])
            
            # Head tilt Kalman filter
            self.kf_head_tilt = KalmanFilter(dim_x=2, dim_z=1)
            self.kf_head_tilt.x = np.array([[0.], [0.]])
            self.kf_head_tilt.F = np.array([[1., 1.], [0., 1.]])
            self.kf_head_tilt.H = np.array([[1., 0.]])
            self.kf_head_tilt.P *= 1000.
            self.kf_head_tilt.R = 0.05
            self.kf_head_tilt.Q = np.array([[0.001, 0.], [0., 0.001]])
            
            # Head forward Kalman filter
            self.kf_head_forward = KalmanFilter(dim_x=2, dim_z=1)
            self.kf_head_forward.x = np.array([[0.], [0.]])
            self.kf_head_forward.F = np.array([[1., 1.], [0., 1.]])
            self.kf_head_forward.H = np.array([[1., 0.]])
            self.kf_head_forward.P *= 1000.
            self.kf_head_forward.R = 0.1
            self.kf_head_forward.Q = np.array([[0.001, 0.], [0., 0.001]])
        else:
            # Fallback to exponential moving average
            self.ema_ear = None
            self.ema_mar = None
            self.ema_head_tilt = None
            self.ema_head_forward = None
            self.ema_alpha = 0.3  # Smoothing factor
        
        # ============================================================
        # ADAPTIVE PER-USER CALIBRATION
        # ============================================================
        # Personalize thresholds based on user's baseline during first ~10 seconds
        self.calibrated = False
        self.calibration_frames_needed = 150  # ~10 seconds at 15 FPS
        self.calibration_frame_count = 0
        
        # Calibration buffers
        self.ear_buffer = deque(maxlen=200)
        self.mar_buffer = deque(maxlen=200)
        self.head_tilt_buffer = deque(maxlen=200)
        self.head_forward_buffer = deque(maxlen=200)
        
        # Adaptive thresholds (will be computed after calibration)
        self.ear_baseline = None
        self.ear_threshold = config.EAR_THRESHOLD  # Default until calibration
        self.mar_baseline = None
        self.mar_threshold = config.MAR_THRESHOLD  # Default until calibration
        self.head_tilt_baseline = None
        self.head_tilt_threshold = config.HEAD_TILT_THRESHOLD
        self.head_forward_baseline = None
        self.head_forward_threshold = config.HEAD_FORWARD_THRESHOLD
        
        # Online adaptation (gradual threshold updates)
        self.online_adaptation_enabled = True
        self.adaptation_rate = 0.001  # Very slow adaptation to avoid drift
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=config.MAX_NUM_FACES,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe Hands
        if config.DETECT_HANDS:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                max_num_hands=config.MAX_NUM_HANDS,
                min_detection_confidence=config.MIN_HAND_DETECTION_CONFIDENCE,
                min_tracking_confidence=config.MIN_HAND_TRACKING_CONFIDENCE
            )
        else:
            self.mp_hands = None
            self.hands = None
        
        # Initialize MediaPipe Pose
        if config.DETECT_SHOULDERS:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=config.MIN_POSE_DETECTION_CONFIDENCE,
                min_tracking_confidence=config.MIN_POSE_TRACKING_CONFIDENCE,
                model_complexity=1  # Balance between accuracy and speed
            )
        else:
            self.mp_pose = None
            self.pose = None
        
        # Blink detection state
        self.blink_counter = 0
        self.blink_frames = 0
        self.blink_timestamps = deque(maxlen=100)  # Store last 100 blinks
        
        # Yawn detection state
        self.yawn_counter = 0
        self.yawn_frames = 0
        self.yawn_timestamps = deque(maxlen=50)
        
        # Head pose history
        self.head_tilt_history = deque(maxlen=30)
        self.head_forward_history = deque(maxlen=30)
        
        # Hand position tracking
        self.hand_near_face_counter = 0
        self.hand_near_face_timestamps = deque(maxlen=50)
        self.hand_covering_face_counter = 0
        self.fidget_counter = 0
        self.prev_hand_positions = None
        
        # Shoulder posture tracking
        self.shoulder_tilt_history = deque(maxlen=30)
        self.shoulder_forward_history = deque(maxlen=30)
        self.shoulder_raise_history = deque(maxlen=30)
        self.baseline_shoulder_height = None  # Established during first few frames
        self.poor_posture_counter = 0
        self.poor_posture_timestamps = deque(maxlen=50)
        
        # Drinking behavior tracking
        self.drinking_counter = 0
        self.drinking_timestamps = deque(maxlen=100)
        self.hand_to_mouth_counter = 0
        self.hand_to_mouth_timestamps = deque(maxlen=100)
        self.drinking_in_progress = False
        self.drinking_start_time = None
        self.last_drinking_end_time = 0
        
        # Object detection for drinkware (optional, using simple hand-mouth gesture as proxy)
        self.object_detector = None
        if config.DETECT_DRINKING:
            # Try to load object detection model (optional)
            try:
                self._init_object_detector()
            except Exception as e:
                print(f"Note: Object detection not available, using gesture-based drinking detection: {e}")
                self.object_detector = None
        
        # Fatigue scoring
        self.fatigue_scores = deque(maxlen=60)  # Store last 60 seconds of scores
        self.last_break_suggestion_time = 0
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
        
    def _init_object_detector(self):
        """
        Initialize object detection model for drinkware detection.
        Uses MobileNet-SSD with COCO dataset (optional feature).
        """
        # This is optional - if model files are not available, we'll use gesture-based detection
        model_path = 'models/MobileNetSSD_deploy.caffemodel'
        config_path = 'models/MobileNetSSD_deploy.prototxt'
        
        if os.path.exists(model_path) and os.path.exists(config_path):
            self.object_detector = cv2.dnn.readNetFromCaffe(config_path, model_path)
            print("✓ Object detection model loaded successfully")
        else:
            raise FileNotFoundError("Object detection model files not found")
    
    # ============================================================
    # KALMAN FILTERING METHODS
    # ============================================================
    
    def kalman_update(self, kf, measurement):
        """
        Apply Kalman filter prediction and update steps.
        Returns the smoothed value.
        
        Args:
            kf: KalmanFilter object
            measurement: Raw measured value (float)
        
        Returns:
            Filtered/smoothed value (float)
        """
        if self.kalman_available:
            # Prediction step
            kf.predict()
            
            # Update step with measurement
            kf.update(np.array([[measurement]]))
            
            # Return filtered state (position component only)
            return float(kf.x[0, 0])
        else:
            # Fallback: exponential moving average
            return measurement
    
    def ema_update(self, current_ema, new_value):
        """
        Exponential moving average fallback when filterpy is unavailable.
        Provides simple temporal smoothing.
        
        Args:
            current_ema: Current EMA value (None if first call)
            new_value: New measurement
        
        Returns:
            Updated EMA value
        """
        if current_ema is None:
            return new_value
        return self.ema_alpha * new_value + (1 - self.ema_alpha) * current_ema
    
    # ============================================================
    # ADAPTIVE CALIBRATION METHODS
    # ============================================================
    
    def update_calibration(self, ear, mar, head_tilt, head_forward):
        """
        Collect data for adaptive threshold calibration.
        Called during the first ~10 seconds of detection.
        
        Args:
            ear: Current eye aspect ratio
            mar: Current mouth aspect ratio
            head_tilt: Current head tilt angle
            head_forward: Current head forward angle
        """
        if self.calibrated:
            return
        
        # Add to calibration buffers
        self.ear_buffer.append(ear)
        self.mar_buffer.append(mar)
        self.head_tilt_buffer.append(head_tilt)
        self.head_forward_buffer.append(head_forward)
        
        self.calibration_frame_count += 1
        
        # Check if we have enough frames for calibration
        if self.calibration_frame_count >= self.calibration_frames_needed:
            self.compute_adaptive_thresholds()
            self.calibrated = True
            print("\n" + "="*60)
            print("✓ CALIBRATION COMPLETE - Personalized thresholds applied")
            print("="*60)
            print(f"  EAR baseline: {self.ear_baseline:.4f}, threshold: {self.ear_threshold:.4f}")
            print(f"  MAR baseline: {self.mar_baseline:.4f}, threshold: {self.mar_threshold:.4f}")
            print(f"  Head tilt baseline: {self.head_tilt_baseline:.2f}°, threshold: {self.head_tilt_threshold:.2f}°")
            print(f"  Head forward baseline: {self.head_forward_baseline:.2f}, threshold: {self.head_forward_threshold:.2f}")
            print("="*60 + "\n")
    
    def compute_adaptive_thresholds(self):
        """
        Compute personalized thresholds based on calibration data.
        Uses mean ± k*std to set detection thresholds.
        """
        # EAR threshold (blink detection)
        # Lower EAR = closed eyes, so threshold is baseline - k*std
        if len(self.ear_buffer) > 0:
            ear_array = np.array(list(self.ear_buffer))
            self.ear_baseline = np.mean(ear_array)
            ear_std = np.std(ear_array)
            self.ear_threshold = max(self.ear_baseline - 1.5 * ear_std, 0.15)  # Min threshold 0.15
        
        # MAR threshold (yawn detection)
        # Higher MAR = open mouth, so threshold is baseline + k*std
        if len(self.mar_buffer) > 0:
            mar_array = np.array(list(self.mar_buffer))
            self.mar_baseline = np.mean(mar_array)
            mar_std = np.std(mar_array)
            self.mar_threshold = self.mar_baseline + 1.5 * mar_std
        
        # Head tilt threshold
        if len(self.head_tilt_buffer) > 0:
            tilt_array = np.array(list(self.head_tilt_buffer))
            self.head_tilt_baseline = np.mean(tilt_array)
            tilt_std = np.std(tilt_array)
            self.head_tilt_threshold = self.head_tilt_baseline + 1.2 * tilt_std
        
        # Head forward threshold
        if len(self.head_forward_buffer) > 0:
            forward_array = np.array(list(self.head_forward_buffer))
            self.head_forward_baseline = np.mean(forward_array)
            forward_std = np.std(forward_array)
            self.head_forward_threshold = self.head_forward_baseline + 1.2 * forward_std
    
    def online_adapt_baselines(self, ear, mar):
        """
        Gradually adapt baselines over time to account for changing conditions.
        Uses very slow update rate to avoid drift from fatigue states.
        
        Args:
            ear: Current (filtered) EAR value
            mar: Current (filtered) MAR value
        """
        if not self.calibrated or not self.online_adaptation_enabled:
            return
        
        # Only adapt when values are close to baseline (not in extreme state)
        if self.ear_baseline is not None:
            if abs(ear - self.ear_baseline) < 0.05:  # Only adapt if close to normal
                self.ear_baseline = (1 - self.adaptation_rate) * self.ear_baseline + self.adaptation_rate * ear
        
        if self.mar_baseline is not None:
            if abs(mar - self.mar_baseline) < 0.1:
                self.mar_baseline = (1 - self.adaptation_rate) * self.mar_baseline + self.adaptation_rate * mar
    
    def is_calibrating(self):
        """
        Check if system is currently in calibration phase.
        
        Returns:
            Boolean indicating calibration status
        """
        return not self.calibrated
    
    def get_calibration_progress(self):
        """
        Get calibration progress as percentage.
        
        Returns:
            Float between 0 and 1
        """
        return min(self.calibration_frame_count / self.calibration_frames_needed, 1.0)
    
    def calculate_eye_aspect_ratio(self, eye_landmarks):
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection.
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        # Vertical eye landmarks
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Horizontal eye landmark
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        # EAR formula
        ear = (A + B) / (2.0 * C)
        return ear
    
    def calculate_mouth_aspect_ratio(self, mouth_landmarks):
        """
        Calculate Mouth Aspect Ratio (MAR) for yawn detection.
        MAR = ||p2-p8|| / ||p1-p5||
        Larger values indicate open mouth (yawning).
        """
        # Vertical mouth distance
        A = np.linalg.norm(mouth_landmarks[1] - mouth_landmarks[7])
        
        # Horizontal mouth distance
        B = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[4])
        
        # Avoid division by zero
        if B < 0.01:
            return 0
        
        mar = A / B
        return mar
    
    def estimate_head_pose(self, landmarks, frame_shape):
        """
        Estimate head pose (tilt and forward lean) from facial landmarks.
        Returns (tilt_angle, forward_angle) in degrees.
        """
        # Get key facial points
        height, width = frame_shape[:2]
        
        # Nose tip
        nose = landmarks[config.NOSE_TIP_INDEX]
        nose_x, nose_y = int(nose.x * width), int(nose.y * height)
        
        # Left and right eye outer corners
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        left_eye_x, left_eye_y = int(left_eye.x * width), int(left_eye.y * height)
        right_eye_x, right_eye_y = int(right_eye.x * width), int(right_eye.y * height)
        
        # Calculate tilt angle (side-to-side)
        delta_y = right_eye_y - left_eye_y
        delta_x = right_eye_x - left_eye_x
        tilt_angle = np.degrees(np.arctan2(delta_y, delta_x))
        
        # Calculate forward lean (using nose position relative to eyes)
        # More forward = nose appears lower relative to eyes
        eye_center_y = (left_eye_y + right_eye_y) / 2
        nose_to_eye_ratio = (nose_y - eye_center_y) / height
        
        # Convert to approximate forward angle (heuristic)
        forward_angle = nose_to_eye_ratio * 100
        
        return abs(tilt_angle), abs(forward_angle)
    
    def get_blink_rate(self):
        """Calculate blinks per minute over the last 60 seconds."""
        if len(self.blink_timestamps) < 2:
            return 0
        
        current_time = time.time()
        recent_blinks = [t for t in self.blink_timestamps if current_time - t <= 60]
        
        if len(recent_blinks) < 2:
            return 0
        
        time_span = current_time - recent_blinks[0]
        if time_span > 0:
            return (len(recent_blinks) / time_span) * 60
        return 0
    
    def get_yawn_rate(self):
        """Calculate yawns per 10 minutes."""
        if len(self.yawn_timestamps) < 1:
            return 0
        
        current_time = time.time()
        recent_yawns = [t for t in self.yawn_timestamps if current_time - t <= 600]
        
        return len(recent_yawns)
    
    def detect_hand_positions(self, hand_landmarks, face_landmarks, frame_shape):
        """
        Detect fatigue-indicating hand positions:
        - Hands near face (head resting on hands)
        - Hands covering face (eye rubbing)
        - Hand fidgeting
        
        Returns dict with hand position indicators.
        """
        h, w = frame_shape[:2]
        
        hand_indicators = {
            'hands_near_face': False,
            'hands_covering_face': False,
            'fidgeting': False,
            'num_hands': 0
        }
        
        if not hand_landmarks or len(hand_landmarks) == 0:
            return hand_indicators
        
        hand_indicators['num_hands'] = len(hand_landmarks)
        
        # Get face center position (nose tip)
        face_center = face_landmarks[config.NOSE_TIP_INDEX]
        face_x, face_y = face_center.x, face_center.y
        
        # Get face bounds for proximity detection
        face_top_y = min([face_landmarks[i].y for i in [10, 151, 9, 8]])
        face_bottom_y = max([face_landmarks[i].y for i in [152, 200, 175]])
        face_left_x = min([face_landmarks[i].x for i in [234, 127, 162]])
        face_right_x = max([face_landmarks[i].x for i in [454, 356, 389]])
        
        current_hand_positions = []
        
        for hand in hand_landmarks:
            # Get wrist and fingertip positions
            wrist = hand.landmark[0]
            index_tip = hand.landmark[8]
            middle_tip = hand.landmark[12]
            
            # Average hand position
            hand_x = (wrist.x + index_tip.x + middle_tip.x) / 3
            hand_y = (wrist.y + index_tip.y + middle_tip.y) / 3
            
            current_hand_positions.append((hand_x, hand_y))
            
            # Check if hand is near face
            dist_to_face = np.sqrt((hand_x - face_x)**2 + (hand_y - face_y)**2)
            
            if dist_to_face < config.HAND_NEAR_FACE_THRESHOLD:
                hand_indicators['hands_near_face'] = True
                
                # Check if very close (covering face)
                if dist_to_face < config.HAND_COVERING_FACE_THRESHOLD:
                    hand_indicators['hands_covering_face'] = True
            
            # Check if hand is in face region (even if not super close to nose)
            if (face_left_x - 0.1 < hand_x < face_right_x + 0.1 and
                face_top_y - 0.1 < hand_y < face_bottom_y + 0.1):
                hand_indicators['hands_near_face'] = True
        
        # Detect fidgeting (hand movement between frames)
        if self.prev_hand_positions and len(self.prev_hand_positions) == len(current_hand_positions):
            total_movement = 0
            for prev_pos, curr_pos in zip(self.prev_hand_positions, current_hand_positions):
                movement = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                total_movement += movement
            
            avg_movement = total_movement / len(current_hand_positions)
            if avg_movement > config.FIDGET_MOVEMENT_THRESHOLD:
                hand_indicators['fidgeting'] = True
        
        self.prev_hand_positions = current_hand_positions
        
        return hand_indicators
    
    def detect_shoulder_posture(self, pose_landmarks):
        """
        Detect fatigue-indicating shoulder posture:
        - Shoulder tilt (uneven shoulders)
        - Shoulder forward position (hunching/slouching)
        - Shoulder raise (tension/stress)
        
        Returns dict with shoulder posture indicators.
        """
        shoulder_indicators = {
            'shoulders_tilted': False,
            'shoulders_forward': False,
            'shoulders_raised': False,
            'shoulder_tilt_angle': 0,
            'shoulder_forward_distance': 0,
            'shoulder_raise_amount': 0,
            'poor_posture': False
        }
        
        if not pose_landmarks:
            return shoulder_indicators
        
        # Get shoulder landmarks (MediaPipe Pose indices)
        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Also get hip landmarks for forward lean calculation
        left_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP]
        
        # === SHOULDER TILT DETECTION ===
        # Calculate angle between shoulders (side-to-side tilt)
        shoulder_slope = (right_shoulder.y - left_shoulder.y) / (right_shoulder.x - left_shoulder.x + 1e-6)
        tilt_angle = abs(np.degrees(np.arctan(shoulder_slope)))
        shoulder_indicators['shoulder_tilt_angle'] = tilt_angle
        
        if tilt_angle > config.SHOULDER_TILT_THRESHOLD:
            shoulder_indicators['shoulders_tilted'] = True
        
        # === SHOULDER FORWARD POSITION (HUNCHING) ===
        # Calculate if shoulders are forward relative to hips (z-axis)
        # In MediaPipe, lower z value means closer to camera (more forward)
        avg_shoulder_z = (left_shoulder.z + right_shoulder.z) / 2
        avg_hip_z = (left_hip.z + right_hip.z) / 2
        
        # Forward distance (negative means shoulders are behind hips, positive means forward)
        forward_distance = avg_hip_z - avg_shoulder_z
        shoulder_indicators['shoulder_forward_distance'] = forward_distance
        
        if forward_distance > config.SHOULDER_FORWARD_THRESHOLD:
            shoulder_indicators['shoulders_forward'] = True
        
        # === SHOULDER RAISE DETECTION (TENSION) ===
        # Compare current shoulder height to baseline
        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # Establish baseline (average of first 30 frames with good detection)
        if self.baseline_shoulder_height is None:
            if len(self.shoulder_raise_history) >= 30:
                self.baseline_shoulder_height = np.mean(list(self.shoulder_raise_history))
        else:
            # Lower y value means higher position (y increases downward)
            raise_amount = self.baseline_shoulder_height - avg_shoulder_y
            shoulder_indicators['shoulder_raise_amount'] = raise_amount
            
            if raise_amount > config.SHOULDER_RAISE_THRESHOLD:
                shoulder_indicators['shoulders_raised'] = True
        
        # Store shoulder height for baseline calculation
        self.shoulder_raise_history.append(avg_shoulder_y)
        
        # === OVERALL POOR POSTURE ===
        # Poor posture if any indicator is triggered
        if (shoulder_indicators['shoulders_tilted'] or 
            shoulder_indicators['shoulders_forward'] or 
            shoulder_indicators['shoulders_raised']):
            shoulder_indicators['poor_posture'] = True
        
        return shoulder_indicators
    
    def detect_drinking_behavior(self, hand_landmarks, face_landmarks, frame_shape, frame=None):
        """
        Detect drinking behavior using hand-to-mouth gestures and optional object detection.
        
        Method 1 (Primary): Hand-to-mouth gesture detection
        - Tracks when hand moves to mouth area
        - Measures duration of gesture
        - Differentiates from face-touching (longer duration, specific pattern)
        
        Method 2 (Optional): Object detection for cups/mugs
        - Detects drinkware in frame
        - Confirms drinking when object near mouth
        
        Returns dict with drinking indicators.
        """
        drinking_indicators = {
            'hand_to_mouth': False,
            'drinkware_detected': False,
            'drinking_gesture': False,
            'drinking_in_progress': False,
            'drinkware_objects': []
        }
        
        current_time = time.time()
        
        # === METHOD 1: HAND-TO-MOUTH GESTURE DETECTION ===
        if hand_landmarks and face_landmarks and len(hand_landmarks) > 0:
            h, w = frame_shape[:2]
            
            # Get mouth position (nose tip as proxy)
            mouth = face_landmarks[config.NOSE_TIP_INDEX]
            mouth_x, mouth_y = mouth.x, mouth.y
            
            # Check each hand
            for hand in hand_landmarks:
                # Get hand center (average of wrist and fingertips)
                wrist = hand.landmark[0]
                index_tip = hand.landmark[8]
                thumb_tip = hand.landmark[4]
                
                # Hand center position
                hand_x = (wrist.x + index_tip.x + thumb_tip.x) / 3
                hand_y = (wrist.y + index_tip.y + thumb_tip.y) / 3
                
                # Check if hand is near mouth (but not too close like face covering)
                dist_to_mouth = np.sqrt((hand_x - mouth_x)**2 + (hand_y - mouth_y)**2)
                
                # Drinking gesture: hand near mouth but not covering it
                # Distance sweet spot: close enough to drink, not too close (face touching)
                if 0.08 < dist_to_mouth < config.DRINK_TO_MOUTH_THRESHOLD:
                    drinking_indicators['hand_to_mouth'] = True
                    
                    # Check if this is a sustained gesture (drinking vs quick touch)
                    if not self.drinking_in_progress:
                        self.drinking_in_progress = True
                        self.drinking_start_time = current_time
                    
                    break  # Found drinking hand
            
            # Check if drinking gesture has ended
            if self.drinking_in_progress and not drinking_indicators['hand_to_mouth']:
                drinking_duration = current_time - self.drinking_start_time
                
                # Validate as drinking action if duration is reasonable
                if config.DRINKING_DURATION_MIN <= drinking_duration <= config.DRINKING_DURATION_MAX:
                    # Avoid counting same drink multiple times (cooldown)
                    if current_time - self.last_drinking_end_time > 3.0:  # 3 second cooldown
                        self.drinking_counter += 1
                        self.drinking_timestamps.append(current_time)
                        drinking_indicators['drinking_gesture'] = True
                    
                    self.last_drinking_end_time = current_time
                
                self.drinking_in_progress = False
                self.drinking_start_time = None
        
        # Update current status
        if self.drinking_in_progress:
            drinking_indicators['drinking_in_progress'] = True
        
        # === METHOD 2: OBJECT DETECTION (OPTIONAL) ===
        if self.object_detector is not None and frame is not None:
            # Detect drinkware objects in frame
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
            self.object_detector.setInput(blob)
            detections = self.object_detector.forward()
            
            h, w = frame.shape[:2]
            
            # Process detections
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > config.OBJECT_DETECTION_CONFIDENCE:
                    class_id = int(detections[0, 0, i, 1])
                    
                    # Check if it's drinkware (cup=41, bottle=39 in COCO)
                    if class_id in config.DRINKWARE_CLASS_IDS:
                        drinking_indicators['drinkware_detected'] = True
                        
                        # Get bounding box
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        startX, startY, endX, endY = box.astype("int")
                        
                        drinking_indicators['drinkware_objects'].append({
                            'class_id': class_id,
                            'confidence': float(confidence),
                            'bbox': (startX, startY, endX, endY)
                        })
        
        # Track hand-to-mouth frequency (even if not confirmed drinking)
        if drinking_indicators['hand_to_mouth']:
            self.hand_to_mouth_counter += 1
            if len(self.hand_to_mouth_timestamps) == 0 or \
               current_time - self.hand_to_mouth_timestamps[-1] > 1.0:
                self.hand_to_mouth_timestamps.append(current_time)
        
        return drinking_indicators
    
    def get_drinking_rate(self):
        """Calculate drinks per hour over the last 60 minutes."""
        if len(self.drinking_timestamps) < 1:
            return 0
        
        current_time = time.time()
        recent_drinks = [t for t in self.drinking_timestamps if current_time - t <= 3600]  # Last hour
        
        if len(recent_drinks) < 1:
            return 0
        
        time_span = current_time - recent_drinks[0]
        if time_span > 0:
            return (len(recent_drinks) / time_span) * 3600  # Convert to per hour
        return 0
    
    def calculate_fatigue_score(self):
        """
        Calculate overall fatigue score (0 to 1) based on multiple indicators.
        Higher score = more fatigued.
        """
        # Blink frequency score
        blink_rate = self.get_blink_rate()
        if blink_rate < config.FATIGUE_BLINK_MIN or blink_rate > config.FATIGUE_BLINK_MAX:
            blink_score = 1.0
        elif config.NORMAL_BLINK_MIN <= blink_rate <= config.NORMAL_BLINK_MAX:
            blink_score = 0.0
        else:
            # Gradual transition
            if blink_rate < config.NORMAL_BLINK_MIN:
                blink_score = (config.NORMAL_BLINK_MIN - blink_rate) / (config.NORMAL_BLINK_MIN - config.FATIGUE_BLINK_MIN)
            else:
                blink_score = (blink_rate - config.NORMAL_BLINK_MAX) / (config.FATIGUE_BLINK_MAX - config.NORMAL_BLINK_MAX)
            blink_score = np.clip(blink_score, 0, 1)
        
        # Yawn score
        yawn_rate = self.get_yawn_rate()
        yawn_score = min(yawn_rate / 3.0, 1.0)  # 3+ yawns in 10 min = max score
        
        # Head pose score
        if len(self.head_tilt_history) > 0 and len(self.head_forward_history) > 0:
            avg_tilt = np.mean(list(self.head_tilt_history))
            avg_forward = np.mean(list(self.head_forward_history))
            
            tilt_score = min(max(avg_tilt - config.HEAD_TILT_THRESHOLD, 0) / 15, 1.0)
            forward_score = min(max(avg_forward - config.HEAD_FORWARD_THRESHOLD, 0) / 20, 1.0)
            head_pose_score = (tilt_score + forward_score) / 2
        else:
            head_pose_score = 0
        
        # Hand position score
        hand_score = 0.0
        if config.DETECT_HANDS and len(self.hand_near_face_timestamps) > 0:
            # Hand near face frequency (over last 30 seconds)
            current_time = time.time()
            recent_hand_near_face = [t for t in self.hand_near_face_timestamps if current_time - t <= 30]
            hand_near_face_rate = len(recent_hand_near_face) / 30.0  # Frequency
            
            # Score increases with frequency of hand-near-face events
            hand_score = min(hand_near_face_rate * 2.0, 1.0)  # 0.5+ rate = max score
        
        # Shoulder posture score
        shoulder_score = 0.0
        if config.DETECT_SHOULDERS:
            # Score based on shoulder tilt
            tilt_score = 0
            if len(self.shoulder_tilt_history) > 0:
                avg_tilt = np.mean(list(self.shoulder_tilt_history))
                tilt_score = min(max(avg_tilt - config.SHOULDER_TILT_THRESHOLD, 0) / 15, 1.0)
            
            # Score based on forward hunching
            forward_score = 0
            if len(self.shoulder_forward_history) > 0:
                avg_forward = np.mean(list(self.shoulder_forward_history))
                forward_score = min(max(avg_forward - config.SHOULDER_FORWARD_THRESHOLD, 0) / 0.1, 1.0)
            
            # Score based on shoulder tension (raised shoulders)
            raise_score = 0
            if len(self.shoulder_raise_history) > 0 and self.baseline_shoulder_height is not None:
                recent_raises = [r for r in list(self.shoulder_raise_history)[-10:]]
                if recent_raises:
                    avg_raise = np.mean([self.baseline_shoulder_height - r for r in recent_raises])
                    raise_score = min(max(avg_raise - config.SHOULDER_RAISE_THRESHOLD, 0) / 0.05, 1.0)
            
            # Poor posture frequency (over last 30 seconds)
            if len(self.poor_posture_timestamps) > 0:
                current_time = time.time()
                recent_poor_posture = [t for t in self.poor_posture_timestamps if current_time - t <= 30]
                posture_frequency_score = min(len(recent_poor_posture) / 30.0, 1.0)
                
                # Combine shoulder metrics
                shoulder_score = max(tilt_score, forward_score, raise_score, posture_frequency_score * 0.5)
            else:
                shoulder_score = max(tilt_score, forward_score, raise_score)
        
        # Weighted combination
        fatigue_score = (
            config.WEIGHT_BLINK * blink_score +
            config.WEIGHT_YAWN * yawn_score +
            config.WEIGHT_HEAD_POSE * head_pose_score +
            config.WEIGHT_HAND_POSITION * hand_score +
            config.WEIGHT_SHOULDER_POSTURE * shoulder_score
        )
        
        return np.clip(fatigue_score, 0, 1)
    
    def should_suggest_break(self):
        """
        Determine if a break should be suggested based on fatigue score.
        Returns (should_break, reason).
        """
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_break_suggestion_time < config.BREAK_SUGGESTION_COOLDOWN:
            return False, ""
        
        # Calculate current fatigue
        fatigue_score = self.calculate_fatigue_score()
        self.fatigue_scores.append(fatigue_score)
        
        # Check if sustained high fatigue
        if len(self.fatigue_scores) >= 10:
            recent_avg = np.mean(list(self.fatigue_scores)[-10:])
            
            if recent_avg >= config.FATIGUE_SCORE_THRESHOLD:
                # Determine primary reason
                blink_rate = self.get_blink_rate()
                yawn_rate = self.get_yawn_rate()
                
                reasons = []
                if blink_rate < config.FATIGUE_BLINK_MIN:
                    reasons.append("reduced blinking")
                elif blink_rate > config.FATIGUE_BLINK_MAX:
                    reasons.append("increased blinking")
                
                if yawn_rate >= 2:
                    reasons.append("yawning detected")
                
                if len(self.head_forward_history) > 0:
                    if np.mean(list(self.head_forward_history)) > config.HEAD_FORWARD_THRESHOLD:
                        reasons.append("forward posture")
                
                if config.DETECT_HANDS and len(self.hand_near_face_timestamps) > 0:
                    recent_hand_events = [t for t in self.hand_near_face_timestamps if current_time - t <= 30]
                    if len(recent_hand_events) >= 10:  # 10+ events in 30 seconds
                        reasons.append("hands near face")
                
                if config.DETECT_SHOULDERS and len(self.poor_posture_timestamps) > 0:
                    recent_posture_events = [t for t in self.poor_posture_timestamps if current_time - t <= 30]
                    if len(recent_posture_events) >= 15:  # 15+ events in 30 seconds
                        if len(self.shoulder_forward_history) > 0 and np.mean(list(self.shoulder_forward_history)) > config.SHOULDER_FORWARD_THRESHOLD:
                            reasons.append("poor posture (slouching)")
                        else:
                            reasons.append("poor posture")
                
                reason = " and ".join(reasons) if reasons else "fatigue indicators"
                
                self.last_break_suggestion_time = current_time
                return True, reason
        
        return False, ""
    
    def process_frame(self, frame, draw_landmarks=True):
        """
        Process a single video frame and extract fatigue indicators.
        Returns (processed_frame, metrics_dict).
        """
        self.frame_count += 1
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.face_mesh.process(rgb_frame)
        
        metrics = {
            'face_detected': False,
            'blink_rate': 0,
            'yawn_count': self.yawn_counter,
            'fatigue_score': 0,
            'ear': 0,
            'mar': 0,
            'head_tilt': 0,
            'head_forward': 0,
            'hands_detected': 0,
            'hands_near_face': False,
            'hands_covering_face': False,
            'fidgeting': False,
            'shoulders_detected': False,
            'shoulders_tilted': False,
            'shoulders_forward': False,
            'shoulders_raised': False,
            'poor_posture': False,
            'shoulder_tilt_angle': 0,
            'shoulder_forward_distance': 0,
            'drinking_detected': False,
            'hand_to_mouth': False,
            'drinking_in_progress': False,
            'drinkware_detected': False,
            'drinking_count': self.drinking_counter,
            'drinking_rate': 0
        }
        
        if results.multi_face_landmarks:
            metrics['face_detected'] = True
            face_landmarks = results.multi_face_landmarks[0]
            
            # Draw landmarks if requested
            if draw_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=1, circle_radius=1
                    )
                )
            
            # Extract landmark coordinates
            landmarks = face_landmarks.landmark
            h, w = frame.shape[:2]
            
            # === BLINK DETECTION ===
            left_eye = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                 for i in config.LEFT_EYE_INDICES])
            right_eye = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                  for i in config.RIGHT_EYE_INDICES])
            
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            ear_raw = (left_ear + right_ear) / 2.0
            
            # Apply Kalman filtering to reduce noise
            if self.kalman_available:
                ear = self.kalman_update(self.kf_ear, ear_raw)
            else:
                # Fallback to exponential moving average
                self.ema_ear = self.ema_update(self.ema_ear, ear_raw)
                ear = self.ema_ear
            
            metrics['ear'] = ear
            
            # Detect blink using adaptive threshold (or default during calibration)
            ear_threshold = self.ear_threshold if self.calibrated else config.EAR_THRESHOLD
            if ear < ear_threshold:
                self.blink_frames += 1
            else:
                if self.blink_frames >= config.BLINK_CONSEC_FRAMES:
                    self.blink_counter += 1
                    self.blink_timestamps.append(time.time())
                self.blink_frames = 0
            
            # === YAWN DETECTION ===
            mouth_points = np.array([
                [landmarks[61].x * w, landmarks[61].y * h],   # top
                [landmarks[291].x * w, landmarks[291].y * h], # bottom
                [landmarks[78].x * w, landmarks[78].y * h],   # left
                [landmarks[308].x * w, landmarks[308].y * h], # right
                [landmarks[13].x * w, landmarks[13].y * h],   # top center
                [landmarks[14].x * w, landmarks[14].y * h],   # bottom center
                [landmarks[0].x * w, landmarks[0].y * h],     # center
                [landmarks[17].x * w, landmarks[17].y * h]    # bottom-top
            ])
            
            mar_raw = self.calculate_mouth_aspect_ratio(mouth_points)
            
            # Apply Kalman filtering to reduce noise
            if self.kalman_available:
                mar = self.kalman_update(self.kf_mar, mar_raw)
            else:
                # Fallback to exponential moving average
                self.ema_mar = self.ema_update(self.ema_mar, mar_raw)
                mar = self.ema_mar
            
            metrics['mar'] = mar
            
            # Detect yawn using adaptive threshold (or default during calibration)
            current_time = time.time()
            mar_threshold = self.mar_threshold if self.calibrated else config.MAR_THRESHOLD
            if mar > mar_threshold:
                self.yawn_frames += 1
                if self.yawn_frames >= config.YAWN_CONSEC_FRAMES:
                    # Check if enough time has passed since last yawn (cooldown: 2 seconds)
                    if len(self.yawn_timestamps) == 0 or (current_time - self.yawn_timestamps[-1]) > 2.0:
                        self.yawn_counter += 1
                        self.yawn_timestamps.append(current_time)
                    self.yawn_frames = 0  # Reset to avoid multiple counts
            else:
                self.yawn_frames = 0
            
            # === HEAD POSE ESTIMATION ===
            tilt_raw, forward_raw = self.estimate_head_pose(landmarks, frame.shape)
            
            # Apply Kalman filtering to head pose
            if self.kalman_available:
                tilt = self.kalman_update(self.kf_head_tilt, tilt_raw)
                forward = self.kalman_update(self.kf_head_forward, forward_raw)
            else:
                # Fallback to exponential moving average
                self.ema_head_tilt = self.ema_update(self.ema_head_tilt, tilt_raw)
                self.ema_head_forward = self.ema_update(self.ema_head_forward, forward_raw)
                tilt = self.ema_head_tilt
                forward = self.ema_head_forward
            
            self.head_tilt_history.append(tilt)
            self.head_forward_history.append(forward)
            metrics['head_tilt'] = tilt
            metrics['head_forward'] = forward
            
            # === ADAPTIVE CALIBRATION ===
            # Collect calibration data during first ~10 seconds
            if not self.calibrated:
                self.update_calibration(ear, mar, tilt, forward)
            else:
                # Optional: online adaptation for gradual baseline updates
                self.online_adapt_baselines(ear, mar)
            
            # === HAND POSITION DETECTION ===
            if config.DETECT_HANDS and self.hands:
                hand_results = self.hands.process(rgb_frame)
                
                if hand_results.multi_hand_landmarks:
                    hand_indicators = self.detect_hand_positions(
                        hand_results.multi_hand_landmarks,
                        landmarks,
                        frame.shape
                    )
                    
                    metrics['hands_detected'] = hand_indicators['num_hands']
                    metrics['hands_near_face'] = hand_indicators['hands_near_face']
                    metrics['hands_covering_face'] = hand_indicators['hands_covering_face']
                    metrics['fidgeting'] = hand_indicators['fidgeting']
                    
                    # Update counters
                    if hand_indicators['hands_near_face']:
                        self.hand_near_face_counter += 1
                        self.hand_near_face_timestamps.append(time.time())
                    
                    if hand_indicators['hands_covering_face']:
                        self.hand_covering_face_counter += 1
                    
                    if hand_indicators['fidgeting']:
                        self.fidget_counter += 1
                    
                    # Draw hand landmarks
                    if draw_landmarks:
                        for hand_landmarks in hand_results.multi_hand_landmarks:
                            self.mp_drawing.draw_landmarks(
                                frame,
                                hand_landmarks,
                                self.mp_hands.HAND_CONNECTIONS,
                                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                                    color=(255, 0, 255), thickness=2, circle_radius=2
                                ),
                                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                                    color=(255, 0, 255), thickness=2
                                )
                            )
                    
                    # === DRINKING BEHAVIOR DETECTION ===
                    if config.DETECT_DRINKING:
                        drinking_indicators = self.detect_drinking_behavior(
                            hand_results.multi_hand_landmarks,
                            landmarks,
                            frame.shape,
                            frame if self.object_detector else None
                        )
                        
                        metrics['hand_to_mouth'] = drinking_indicators['hand_to_mouth']
                        metrics['drinking_in_progress'] = drinking_indicators['drinking_in_progress']
                        metrics['drinkware_detected'] = drinking_indicators['drinkware_detected']
                        metrics['drinking_detected'] = drinking_indicators['drinking_gesture']
                        metrics['drinking_rate'] = self.get_drinking_rate()
                        
                        # Draw drinkware bounding boxes if detected
                        if draw_landmarks and drinking_indicators['drinkware_detected']:
                            for obj in drinking_indicators['drinkware_objects']:
                                startX, startY, endX, endY = obj['bbox']
                                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                                label = f"Cup: {obj['confidence']:.2f}"
                                cv2.putText(frame, label, (startX, startY - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # === SHOULDER POSTURE DETECTION ===
            if config.DETECT_SHOULDERS and self.pose:
                pose_results = self.pose.process(rgb_frame)
                
                if pose_results.pose_landmarks:
                    shoulder_indicators = self.detect_shoulder_posture(pose_results.pose_landmarks)
                    
                    metrics['shoulders_detected'] = True
                    metrics['shoulders_tilted'] = shoulder_indicators['shoulders_tilted']
                    metrics['shoulders_forward'] = shoulder_indicators['shoulders_forward']
                    metrics['shoulders_raised'] = shoulder_indicators['shoulders_raised']
                    metrics['poor_posture'] = shoulder_indicators['poor_posture']
                    metrics['shoulder_tilt_angle'] = shoulder_indicators['shoulder_tilt_angle']
                    metrics['shoulder_forward_distance'] = shoulder_indicators['shoulder_forward_distance']
                    
                    # Update histories
                    self.shoulder_tilt_history.append(shoulder_indicators['shoulder_tilt_angle'])
                    self.shoulder_forward_history.append(shoulder_indicators['shoulder_forward_distance'])
                    
                    # Update counters
                    if shoulder_indicators['poor_posture']:
                        self.poor_posture_counter += 1
                        self.poor_posture_timestamps.append(time.time())
                    
                    # Draw pose landmarks (shoulders and upper body only for less clutter)
                    if draw_landmarks:
                        # Draw only upper body connections
                        connections_to_draw = [
                            (self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_SHOULDER),
                            (self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.LEFT_ELBOW),
                            (self.mp_pose.PoseLandmark.RIGHT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_ELBOW),
                            (self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.LEFT_HIP),
                            (self.mp_pose.PoseLandmark.RIGHT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_HIP),
                        ]
                        
                        landmarks = pose_results.pose_landmarks.landmark
                        h, w = frame.shape[:2]
                        
                        # Draw shoulder points
                        for landmark_idx in [self.mp_pose.PoseLandmark.LEFT_SHOULDER, 
                                            self.mp_pose.PoseLandmark.RIGHT_SHOULDER]:
                            lm = landmarks[landmark_idx]
                            if lm.visibility > 0.5:  # Only draw if visible
                                cx, cy = int(lm.x * w), int(lm.y * h)
                                cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)  # Yellow circles
                        
                        # Draw connections
                        for connection in connections_to_draw:
                            start_lm = landmarks[connection[0]]
                            end_lm = landmarks[connection[1]]
                            
                            if start_lm.visibility > 0.5 and end_lm.visibility > 0.5:
                                start_point = (int(start_lm.x * w), int(start_lm.y * h))
                                end_point = (int(end_lm.x * w), int(end_lm.y * h))
                                cv2.line(frame, start_point, end_point, (0, 255, 255), 2)  # Yellow lines
            
            # === FATIGUE CALCULATION ===
            metrics['blink_rate'] = self.get_blink_rate()
            metrics['fatigue_score'] = self.calculate_fatigue_score()
        
        # Calculate FPS
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
        
        return frame, metrics
    
    def reset(self):
        """Reset all detection states (e.g., for new session)."""
        # Reset calibration
        self.calibrated = False
        self.calibration_frame_count = 0
        self.ear_buffer.clear()
        self.mar_buffer.clear()
        self.head_tilt_buffer.clear()
        self.head_forward_buffer.clear()
        self.ear_baseline = None
        self.ear_threshold = config.EAR_THRESHOLD
        self.mar_baseline = None
        self.mar_threshold = config.MAR_THRESHOLD
        self.head_tilt_baseline = None
        self.head_tilt_threshold = config.HEAD_TILT_THRESHOLD
        self.head_forward_baseline = None
        self.head_forward_threshold = config.HEAD_FORWARD_THRESHOLD
        
        # Reset Kalman filters or EMA
        if self.kalman_available:
            self.kf_ear.x = np.array([[0.3], [0.]])
            self.kf_mar.x = np.array([[0.2], [0.]])
            self.kf_head_tilt.x = np.array([[0.], [0.]])
            self.kf_head_forward.x = np.array([[0.], [0.]])
        else:
            self.ema_ear = None
            self.ema_mar = None
            self.ema_head_tilt = None
            self.ema_head_forward = None
        
        # Reset detection counters
        self.blink_counter = 0
        self.blink_frames = 0
        self.blink_timestamps.clear()
        self.yawn_counter = 0
        self.yawn_frames = 0
        self.yawn_timestamps.clear()
        self.head_tilt_history.clear()
        self.head_forward_history.clear()
        self.hand_near_face_counter = 0
        self.hand_near_face_timestamps.clear()
        self.hand_covering_face_counter = 0
        self.fidget_counter = 0
        self.prev_hand_positions = None
        self.shoulder_tilt_history.clear()
        self.shoulder_forward_history.clear()
        self.shoulder_raise_history.clear()
        self.baseline_shoulder_height = None
        self.poor_posture_counter = 0
        self.poor_posture_timestamps.clear()
        self.drinking_counter = 0
        self.drinking_timestamps.clear()
        self.hand_to_mouth_counter = 0
        self.hand_to_mouth_timestamps.clear()
        self.drinking_in_progress = False
        self.drinking_start_time = None
        self.last_drinking_end_time = 0
        self.fatigue_scores.clear()
        self.last_break_suggestion_time = 0
    
    def get_summary_stats(self):
        """Get summary statistics for the session."""
        stats = {
            'total_blinks': self.blink_counter,
            'total_yawns': self.yawn_counter,
            'avg_blink_rate': self.get_blink_rate(),
            'avg_fatigue_score': np.mean(list(self.fatigue_scores)) if self.fatigue_scores else 0,
            'max_fatigue_score': np.max(list(self.fatigue_scores)) if self.fatigue_scores else 0
        }
        
        if config.DETECT_HANDS:
            stats['hand_near_face_events'] = self.hand_near_face_counter
            stats['hand_covering_face_events'] = self.hand_covering_face_counter
            stats['fidget_events'] = self.fidget_counter
        
        if config.DETECT_SHOULDERS:
            stats['poor_posture_events'] = self.poor_posture_counter
            stats['avg_shoulder_tilt'] = np.mean(list(self.shoulder_tilt_history)) if self.shoulder_tilt_history else 0
            stats['avg_shoulder_forward'] = np.mean(list(self.shoulder_forward_history)) if self.shoulder_forward_history else 0
        
        if config.DETECT_DRINKING:
            stats['total_drinks'] = self.drinking_counter
            stats['avg_drinking_rate'] = self.get_drinking_rate()
            stats['hand_to_mouth_events'] = self.hand_to_mouth_counter
        
        return stats
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()
        if hasattr(self, 'pose') and self.pose:
            self.pose.close()

