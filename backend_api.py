"""
FastAPI Backend for AdaptiBreak Flutter GUI
Provides REST API endpoints for fatigue detection system.
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import threading
import time
import cv2
import uvicorn
from typing import Optional
import io

from fatigue_detector import FatigueDetector
import config

# Initialize FastAPI app
app = FastAPI(title="AdaptiBreak API", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
detector: Optional[FatigueDetector] = None
webcam: Optional[cv2.VideoCapture] = None
running = False
detection_thread: Optional[threading.Thread] = None
current_fatigue_score = 0.0
current_metrics = {}
session_start_time = 0.0
current_frame = None  # Store current processed frame for video streaming
frame_lock = threading.Lock()
break_suggested = False
break_reason = ""


class SessionResponse(BaseModel):
    """Response model for session operations"""
    status: str
    message: str


class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    score: float
    blink_rate: float
    yawn_count: int
    head_tilt: float
    head_forward: float
    session_duration: float
    is_calibrating: bool
    calibration_progress: float
    # PERCLOS metrics
    perclos: float
    perclos_drowsy: bool
    perclos_severe: bool
    # Mahalanobis metrics
    mahalanobis_distance: float
    mahalanobis_warning: bool
    mahalanobis_alert: bool


def detection_loop():
    """Background thread for continuous fatigue detection"""
    global current_fatigue_score, current_metrics, running, current_frame, break_suggested, break_reason
    
    print("[INFO] Detection loop started")
    last_calibration_log = -1
    
    while running:
        if webcam and webcam.isOpened():
            ret, frame = webcam.read()
            if ret and detector:
                # Process frame with fatigue detector (draw landmarks for video preview)
                processed_frame, metrics = detector.process_frame(frame, draw_landmarks=True)
                
                # Update global state
                current_metrics = metrics
                current_fatigue_score = metrics.get('fatigue_score', 0.0)
                
                # Store processed frame for video streaming
                with frame_lock:
                    current_frame = processed_frame.copy()
                
                # Add overlay text to the frame
                overlay_frame = processed_frame.copy()
                
                # Add fatigue score overlay
                score_color = (0, 255, 0) if current_fatigue_score < 0.4 else (0, 165, 255) if current_fatigue_score < 0.6 else (0, 0, 255)
                cv2.putText(overlay_frame, f"Fatigue: {current_fatigue_score:.2f}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, score_color, 2)
                cv2.putText(overlay_frame, f"Blinks: {detector.blink_counter} | Rate: {detector.get_blink_rate():.1f}/min", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(overlay_frame, f"Yawns: {detector.yawn_counter}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Show calibration or monitoring status
                if detector.is_calibrating():
                    progress = detector.get_calibration_progress()
                    cv2.putText(overlay_frame, f"CALIBRATING: {int(progress*100)}%", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    # Draw progress bar
                    bar_width = int(200 * progress)
                    cv2.rectangle(overlay_frame, (10, 130), (210, 145), (100, 100, 100), -1)
                    cv2.rectangle(overlay_frame, (10, 130), (10 + bar_width, 145), (0, 165, 255), -1)
                    
                    # Log calibration progress
                    progress_pct = int(progress * 100)
                    if progress_pct // 20 > last_calibration_log:
                        last_calibration_log = progress_pct // 20
                        print(f"[INFO] Calibrating: {progress_pct}%")
                else:
                    cv2.putText(overlay_frame, "MONITORING ACTIVE", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Check for break suggestion
                should_break, reason = detector.should_suggest_break()
                if should_break:
                    break_suggested = True
                    break_reason = reason
                    cv2.putText(overlay_frame, "BREAK SUGGESTED!", 
                               (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.putText(overlay_frame, f"Reason: {reason}", 
                               (10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                # Update stored frame with overlay
                with frame_lock:
                    current_frame = overlay_frame.copy()
                    
            else:
                print("[WARN] Failed to read frame from webcam")
                time.sleep(0.1)
        else:
            print("[WARN] Webcam not opened")
            time.sleep(0.1)
        
        # Control frame rate (~15 FPS)
        time.sleep(1.0 / 15)
    
    print("[INFO] Detection loop stopped")


@app.post("/start", response_model=SessionResponse)
async def start_session():
    """
    Start a new fatigue detection session.
    Initializes webcam and begins monitoring.
    """
    global detector, webcam, running, detection_thread, session_start_time
    
    if running:
        return SessionResponse(
            status="already_running",
            message="Session is already active"
        )
    
    try:
        # Initialize fatigue detector
        print("[INFO] Initializing fatigue detector...")
        detector = FatigueDetector()
        
        # Initialize webcam
        print(f"[INFO] Opening webcam (device {config.WEBCAM_ID})...")
        webcam = cv2.VideoCapture(config.WEBCAM_ID)
        
        if not webcam.isOpened():
            return SessionResponse(
                status="error",
                message="Failed to open webcam. Please check camera permissions."
            )
        
        webcam.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        
        # Start detection thread
        running = True
        session_start_time = time.time()
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()
        
        print("[OK] Session started successfully")
        
        return SessionResponse(
            status="started",
            message="Fatigue detection session started successfully"
        )
    
    except Exception as e:
        print(f"[ERROR] Error starting session: {e}")
        running = False
        return SessionResponse(
            status="error",
            message=f"Failed to start session: {str(e)}"
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current fatigue detection status.
    Returns real-time fatigue score and metrics including PERCLOS and Mahalanobis.
    """
    global current_fatigue_score, current_metrics, session_start_time
    
    if not running or not detector:
        return StatusResponse(
            score=0.0,
            blink_rate=0.0,
            yawn_count=0,
            head_tilt=0.0,
            head_forward=0.0,
            session_duration=0.0,
            is_calibrating=False,
            calibration_progress=0.0,
            perclos=0.0,
            perclos_drowsy=False,
            perclos_severe=False,
            mahalanobis_distance=0.0,
            mahalanobis_warning=False,
            mahalanobis_alert=False
        )
    
    # Calculate session duration
    duration = time.time() - session_start_time if session_start_time > 0 else 0.0
    
    # Get calibration status
    is_calibrating = detector.is_calibrating()
    calibration_progress = detector.get_calibration_progress()
    
    return StatusResponse(
        score=round(current_fatigue_score, 3),
        blink_rate=round(detector.get_blink_rate(), 2),
        yawn_count=detector.yawn_counter,
        head_tilt=round(current_metrics.get('head_tilt', 0.0), 2),
        head_forward=round(current_metrics.get('head_forward', 0.0), 2),
        session_duration=round(duration, 1),
        is_calibrating=is_calibrating,
        calibration_progress=round(calibration_progress, 2),
        # PERCLOS metrics
        perclos=round(current_metrics.get('perclos', 0.0), 4),
        perclos_drowsy=current_metrics.get('perclos_drowsy', False),
        perclos_severe=current_metrics.get('perclos_severe', False),
        # Mahalanobis metrics
        mahalanobis_distance=round(current_metrics.get('mahalanobis_distance', 0.0), 3),
        mahalanobis_warning=current_metrics.get('mahalanobis_warning', False),
        mahalanobis_alert=current_metrics.get('mahalanobis_alert', False)
    )


@app.post("/stop", response_model=SessionResponse)
async def stop_session():
    """
    Stop the current fatigue detection session.
    Releases webcam and stops monitoring.
    """
    global running, webcam, detector, detection_thread
    
    if not running:
        return SessionResponse(
            status="not_running",
            message="No active session to stop"
        )
    
    try:
        # Stop detection loop
        running = False
        
        # Wait for thread to finish (with timeout)
        if detection_thread:
            detection_thread.join(timeout=2.0)
        
        # Release webcam
        if webcam:
            webcam.release()
            webcam = None
        
        # Clean up detector
        if detector:
            detector.reset()
            detector = None
        
        print("[OK] Session stopped successfully")
        
        return SessionResponse(
            status="stopped",
            message="Session stopped successfully"
        )
    
    except Exception as e:
        print(f"[ERROR] Error stopping session: {e}")
        return SessionResponse(
            status="error",
            message=f"Failed to stop session: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "running": running,
        "version": "1.0.0"
    }


@app.get("/break_status")
async def get_break_status():
    """Get break suggestion status"""
    global break_suggested, break_reason
    
    result = {
        "break_suggested": break_suggested,
        "break_reason": break_reason,
        "fatigue_score": current_fatigue_score
    }
    
    # Reset after reading
    if break_suggested:
        break_suggested = False
        break_reason = ""
    
    return result


@app.post("/acknowledge_break")
async def acknowledge_break():
    """Acknowledge that user is taking a break"""
    global break_suggested, break_reason
    break_suggested = False
    break_reason = ""
    return {"status": "acknowledged", "message": "Break acknowledged. Take a rest!"}


def generate_video_frames():
    """Generator function for video streaming"""
    global current_frame
    
    while running:
        with frame_lock:
            if current_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(1.0 / 15)  # ~15 FPS


@app.get("/video_feed")
async def video_feed():
    """
    Video streaming endpoint for camera preview.
    Returns MJPEG stream with face detection overlay.
    """
    if not running:
        return {"error": "Session not running"}
    
    return StreamingResponse(
        generate_video_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/frame")
async def get_frame():
    """
    Get a single frame as JPEG image.
    Useful for periodic updates in Flutter.
    """
    global current_frame
    
    if not running or current_frame is None:
        return {"error": "No frame available"}
    
    with frame_lock:
        ret, buffer = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            return StreamingResponse(
                io.BytesIO(buffer.tobytes()),
                media_type="image/jpeg"
            )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    global running, webcam
    
    running = False
    if webcam:
        webcam.release()
    
    print("[INFO] Server shutdown complete")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the FastAPI server"""
    print("=" * 60)
    print("AdaptiBreak Backend API")
    print("=" * 60)
    print(f"Server running at: http://{host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

