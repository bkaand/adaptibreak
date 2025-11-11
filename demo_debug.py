#!/usr/bin/env python3
"""
Debug version of fatigue detector - shows real-time values and calibration info.
"""

import cv2
import time
from fatigue_detector import FatigueDetector
import config


def main():
    print("=" * 70)
    print("AdaptiBreak - DEBUG MODE (Calibration Helper)")
    print("=" * 70)
    print()
    print("This shows REAL-TIME values to help calibrate thresholds.")
    print()
    print("OPTIMAL CAMERA POSITION:")
    print("  • Distance: 50-80 cm (arm's length)")
    print("  • Eye level with camera")
    print("  • Good lighting on your face (not backlit)")
    print("  • Face centered in frame")
    print()
    print("WHAT YOU'LL SEE:")
    print("  • Green landmarks on your face")
    print("  • Real-time EAR value (normal: 0.25-0.35)")
    print("  • Real-time MAR value (normal: 0.2-0.5, yawn: >0.85)")
    print("  • Threshold lines to see when detection triggers")
    print()
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Initialize
    detector = FatigueDetector()
    
    # Try camera
    webcam = None
    for cam_idx in [0, 1]:
        test_cam = cv2.VideoCapture(cam_idx)
        if test_cam.isOpened():
            ret, frame = test_cam.read()
            if ret and frame is not None:
                webcam = test_cam
                print(f"✓ Camera {cam_idx} working!")
                break
            test_cam.release()
    
    if webcam is None:
        print("❌ ERROR: Could not open webcam!")
        return
    
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("✓ Debug mode active")
    print("  Press 'q' to quit")
    print()
    print("CURRENT THRESHOLDS:")
    print(f"  EAR (blink): < {config.EAR_THRESHOLD:.3f}")
    print(f"  MAR (yawn):  > {config.MAR_THRESHOLD:.3f}")
    print()
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = webcam.read()
            if not ret:
                continue
            
            # Process with MediaPipe
            processed_frame, metrics = detector.process_frame(frame, draw_landmarks=True)
            
            # Mirror for natural view
            display_frame = cv2.flip(processed_frame, 1)
            h, w = display_frame.shape[:2]
            
            # Create info panel
            panel_height = 200
            panel = display_frame[0:panel_height, :].copy()
            cv2.rectangle(display_frame, (0, 0), (w, panel_height), (0, 0, 0), -1)
            cv2.rectangle(display_frame, (0, 0), (w, panel_height), (255, 255, 255), 2)
            
            y_pos = 30
            line_height = 25
            
            # Title
            cv2.putText(display_frame, "DEBUG MODE - Real-time Values", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_pos += line_height + 10
            
            if metrics['face_detected']:
                # EAR
                ear = metrics['ear']
                ear_color = (0, 0, 255) if ear < config.EAR_THRESHOLD else (0, 255, 0)
                cv2.putText(display_frame, f"EAR: {ear:.3f} (blink < {config.EAR_THRESHOLD:.3f})", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, ear_color, 2)
                
                # Draw EAR bar
                bar_width = 200
                bar_x = w - bar_width - 10
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + bar_width, y_pos + 5), (100, 100, 100), 1)
                fill_width = int(bar_width * min(ear, 0.5) / 0.5)
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + fill_width, y_pos + 5), ear_color, -1)
                
                y_pos += line_height
                
                # MAR
                mar = metrics['mar']
                mar_color = (0, 0, 255) if mar > config.MAR_THRESHOLD else (0, 255, 0)
                cv2.putText(display_frame, f"MAR: {mar:.3f} (yawn > {config.MAR_THRESHOLD:.3f})", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mar_color, 2)
                
                # Draw MAR bar
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + bar_width, y_pos + 5), (100, 100, 100), 1)
                fill_width = int(bar_width * min(mar, 1.0))
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + fill_width, y_pos + 5), mar_color, -1)
                
                y_pos += line_height
                
                # Counts
                cv2.putText(display_frame, f"Blinks: {detector.blink_counter}  |  Yawns: {detector.yawn_counter}", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_pos += line_height
                
                # Fatigue
                fatigue = metrics['fatigue_score']
                fatigue_color = (0, 255, 0) if fatigue < 0.4 else (0, 165, 255) if fatigue < 0.6 else (0, 0, 255)
                cv2.putText(display_frame, f"Fatigue: {fatigue:.2f}", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, fatigue_color, 2)
                
                # Fatigue bar
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + bar_width, y_pos + 5), (100, 100, 100), 1)
                fill_width = int(bar_width * fatigue)
                cv2.rectangle(display_frame, (bar_x, y_pos - 15), (bar_x + fill_width, y_pos + 5), fatigue_color, -1)
            else:
                cv2.putText(display_frame, "NO FACE DETECTED", 
                           (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.putText(display_frame, "Move closer to camera (50-80cm)", 
                           (10, y_pos + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # FPS
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                cv2.putText(display_frame, f"FPS: {fps:.1f}", 
                           (w - 100, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Instructions
            cv2.putText(display_frame, "Press 'q' to quit | Try YAWNING to see MAR spike!", 
                       (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Show
            cv2.imshow('AdaptiBreak - Debug Mode (Calibration)', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    
    finally:
        webcam.release()
        cv2.destroyAllWindows()
        
        # Summary
        print("\n" + "=" * 70)
        print("Session Summary:")
        print("=" * 70)
        stats = detector.get_summary_stats()
        print(f"  Total Blinks: {stats['total_blinks']}")
        print(f"  Total Yawns: {stats['total_yawns']}")
        print(f"  Avg Blink Rate: {stats['avg_blink_rate']:.1f} per minute")
        print(f"  Avg Fatigue: {stats['avg_fatigue_score']:.3f}")
        print()
        print("CALIBRATION NOTES:")
        if stats['total_yawns'] > 10:
            print(f"  ⚠️  Yawn count seems high ({stats['total_yawns']})")
            print(f"     Current MAR threshold: {config.MAR_THRESHOLD:.3f}")
            print(f"     Suggestion: Increase MAR_THRESHOLD in config.py")
            print(f"     Try: MAR_THRESHOLD = 0.90 or 0.95")
        else:
            print(f"  ✓ Yawn count looks reasonable ({stats['total_yawns']})")
        
        if stats['total_blinks'] > 0:
            if 12 <= stats['avg_blink_rate'] <= 25:
                print(f"  ✓ Blink rate looks good ({stats['avg_blink_rate']:.1f} /min)")
            else:
                print(f"  ⚠️  Blink rate: {stats['avg_blink_rate']:.1f} /min")
                print(f"     Normal range: 12-25 per minute")
        
        print("=" * 70)


if __name__ == "__main__":
    main()

