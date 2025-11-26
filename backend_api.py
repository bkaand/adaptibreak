"""
FastAPI Backend for AdaptiBreak Flutter GUI
Provides REST API endpoints for fatigue detection system.
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import cv2
import uvicorn
from typing import Optional

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


def detection_loop():
    """Background thread for continuous fatigue detection"""
    global current_fatigue_score, current_metrics, running
    
    print("🎥 Detection loop started")
    
    # Create window for video preview
    cv2.namedWindow('AdaptiBreak - Webcam Preview', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('AdaptiBreak - Webcam Preview', 640, 480)
    
    while running:
        if webcam and webcam.isOpened():
            ret, frame = webcam.read()
            if ret and detector:
                # Process frame with fatigue detector (draw landmarks for preview)
                processed_frame, metrics = detector.process_frame(frame, draw_landmarks=True)
                
                # Update global state
                current_metrics = metrics
                current_fatigue_score = metrics.get('fatigue_score', 0.0)
                
                # Add text overlay with metrics
                cv2.putText(processed_frame, f"Fatigue: {current_fatigue_score:.3f}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(processed_frame, f"Blink Rate: {detector.get_blink_rate():.1f}/min", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(processed_frame, f"Yawns: {detector.yawn_counter}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show calibration status
                if detector.is_calibrating():
                    progress = detector.get_calibration_progress()
                    cv2.putText(processed_frame, f"Calibrating: {int(progress*100)}%", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
                # Display the frame
                cv2.imshow('AdaptiBreak - Webcam Preview', processed_frame)
                cv2.waitKey(1)
            else:
                print("⚠️  Failed to read frame from webcam")
                time.sleep(0.1)
        else:
            print("⚠️  Webcam not opened")
            time.sleep(0.1)
        
        # Control frame rate (~15 FPS)
        time.sleep(1.0 / 15)
    
    # Cleanup
    cv2.destroyAllWindows()
    print("🛑 Detection loop stopped")


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
        print("🔧 Initializing fatigue detector...")
        detector = FatigueDetector()
        
        # Initialize webcam
        print(f"📸 Opening webcam (device {config.WEBCAM_ID})...")
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
        
        print("✅ Session started successfully")
        
        return SessionResponse(
            status="started",
            message="Fatigue detection session started successfully"
        )
    
    except Exception as e:
        print(f"❌ Error starting session: {e}")
        running = False
        return SessionResponse(
            status="error",
            message=f"Failed to start session: {str(e)}"
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current fatigue detection status.
    Returns real-time fatigue score and metrics.
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
            calibration_progress=0.0
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
        calibration_progress=round(calibration_progress, 2)
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
        
        print("✅ Session stopped successfully")
        
        return SessionResponse(
            status="stopped",
            message="Session stopped successfully"
        )
    
    except Exception as e:
        print(f"❌ Error stopping session: {e}")
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    global running, webcam
    
    running = False
    if webcam:
        webcam.release()
    
    print("🔌 Server shutdown complete")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the FastAPI server"""
    print("=" * 60)
    print("🚀 AdaptiBreak Backend API")
    print("=" * 60)
    print(f"Server running at: http://{host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

