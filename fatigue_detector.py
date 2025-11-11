"""
Fatigue Detection Module using MediaPipe Face Mesh.
Detects blinks, yawns, and head pose to estimate user fatigue in real-time.
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time
import config


class FatigueDetector:
    """
    Real-time fatigue detector using webcam and MediaPipe Face Mesh.
    Tracks blink frequency, yawning, and head posture to estimate fatigue levels.
    """
    
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=config.MAX_NUM_FACES,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
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
        
        # Fatigue scoring
        self.fatigue_scores = deque(maxlen=60)  # Store last 60 seconds of scores
        self.last_break_suggestion_time = 0
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
        
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
        
        # Weighted combination
        fatigue_score = (
            config.WEIGHT_BLINK * blink_score +
            config.WEIGHT_YAWN * yawn_score +
            config.WEIGHT_HEAD_POSE * head_pose_score
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
            'head_forward': 0
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
            ear = (left_ear + right_ear) / 2.0
            metrics['ear'] = ear
            
            # Detect blink
            if ear < config.EAR_THRESHOLD:
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
            
            mar = self.calculate_mouth_aspect_ratio(mouth_points)
            metrics['mar'] = mar
            
            # Detect yawn (with cooldown to avoid multiple detections of same yawn)
            current_time = time.time()
            if mar > config.MAR_THRESHOLD:
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
            tilt, forward = self.estimate_head_pose(landmarks, frame.shape)
            self.head_tilt_history.append(tilt)
            self.head_forward_history.append(forward)
            metrics['head_tilt'] = tilt
            metrics['head_forward'] = forward
            
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
        self.blink_counter = 0
        self.blink_frames = 0
        self.blink_timestamps.clear()
        self.yawn_counter = 0
        self.yawn_frames = 0
        self.yawn_timestamps.clear()
        self.head_tilt_history.clear()
        self.head_forward_history.clear()
        self.fatigue_scores.clear()
        self.last_break_suggestion_time = 0
    
    def get_summary_stats(self):
        """Get summary statistics for the session."""
        return {
            'total_blinks': self.blink_counter,
            'total_yawns': self.yawn_counter,
            'avg_blink_rate': self.get_blink_rate(),
            'avg_fatigue_score': np.mean(list(self.fatigue_scores)) if self.fatigue_scores else 0,
            'max_fatigue_score': np.max(list(self.fatigue_scores)) if self.fatigue_scores else 0
        }
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()

