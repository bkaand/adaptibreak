"""
Demo script for testing the fatigue detection system.
Useful for quick testing without going through the full study protocol.
"""

import cv2
import time
from fatigue_detector import FatigueDetector
import config


def main():
    print("=" * 60)
    print("AdaptiBreak - Fatigue Detection Demo")
    print("=" * 60)
    print("\nThis demo shows real-time fatigue detection using your webcam.")
    print("\nInstructions:")
    print("  - Sit comfortably in front of your webcam")
    print("  - Ensure good lighting on your face")
    print("  - The system will detect blinks, yawns, head posture, shoulders, and drinking")
    print("  - Make sure your shoulders are visible in the frame")
    print("  - Try drinking from a cup/mug to test drinking detection")
    print("  - Press 'q' to quit")
    print("\nStarting in 3 seconds...")
    print("=" * 60)
    time.sleep(3)
    
    # Initialize components
    detector = FatigueDetector()
    
    # Try multiple camera indices
    webcam = None
    for cam_idx in [0, 1]:
        print(f"Trying camera index {cam_idx}...")
        test_cam = cv2.VideoCapture(cam_idx)
        if test_cam.isOpened():
            # Test if we can actually read a frame
            ret, frame = test_cam.read()
            if ret and frame is not None:
                webcam = test_cam
                print(f"✓ Camera {cam_idx} working!")
                break
            test_cam.release()
    
    if webcam is None:
        print("\n❌ ERROR: Could not open webcam!")
        print("   Troubleshooting steps:")
        print("   1. Close other apps using camera (Zoom, FaceTime, etc.)")
        print("   2. Grant camera permissions to Terminal in System Settings")
        print("   3. Run: killall VDCAssistant (restarts camera)")
        print("   4. Disconnect iPhone if using Continuity Camera")
        return
    
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    print("\n✓ Webcam initialized successfully")
    print("  Press 'q' to quit\n")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = webcam.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Process frame
            processed_frame, metrics = detector.process_frame(frame, draw_landmarks=True)
            
            # Flip frame for mirror effect
            display_frame = cv2.flip(processed_frame, 1)
            
            # Add text overlay with metrics
            y_offset = 30
            line_height = 30
            
            if metrics['face_detected']:
                cv2.putText(display_frame, "Face: Detected", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                y_offset += line_height
                cv2.putText(display_frame, f"Blink Rate: {metrics['blink_rate']:.1f} /min", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_offset += line_height
                cv2.putText(display_frame, f"Yawns: {metrics['yawn_count']}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_offset += line_height
                cv2.putText(display_frame, f"EAR: {metrics['ear']:.3f}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_offset += line_height
                cv2.putText(display_frame, f"MAR: {metrics['mar']:.3f}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                y_offset += line_height
                # Hand position indicators
                if config.DETECT_HANDS:
                    hand_text = f"Hands: {metrics['hands_detected']}"
                    if metrics['hands_near_face']:
                        hand_text += " [NEAR FACE]"
                    if metrics['hands_covering_face']:
                        hand_text += " [COVERING]"
                    if metrics['fidgeting']:
                        hand_text += " [FIDGETING]"
                    
                    hand_color = (0, 165, 255) if metrics['hands_near_face'] else (255, 255, 255)
                    cv2.putText(display_frame, hand_text, 
                               (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, hand_color, 2)
                    y_offset += line_height
                
                # Shoulder posture indicators
                if config.DETECT_SHOULDERS:
                    shoulder_text = "Posture: "
                    if metrics['shoulders_detected']:
                        if metrics['poor_posture']:
                            shoulder_text += "POOR"
                            if metrics['shoulders_forward']:
                                shoulder_text += " [SLOUCHING]"
                            if metrics['shoulders_tilted']:
                                shoulder_text += " [TILTED]"
                            if metrics['shoulders_raised']:
                                shoulder_text += " [TENSE]"
                            shoulder_color = (0, 0, 255)  # Red for poor posture
                        else:
                            shoulder_text += "Good"
                            shoulder_color = (0, 255, 0)  # Green for good posture
                    else:
                        shoulder_text += "Not detected"
                        shoulder_color = (128, 128, 128)  # Gray when not detected
                    
                    cv2.putText(display_frame, shoulder_text, 
                               (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, shoulder_color, 2)
                    y_offset += line_height
                
                # Drinking behavior indicators
                if config.DETECT_DRINKING:
                    drinking_text = f"Drinks: {metrics['drinking_count']}"
                    if metrics['drinking_in_progress']:
                        drinking_text += " [DRINKING NOW]"
                        drinking_color = (0, 255, 255)  # Cyan when drinking
                    elif metrics['hand_to_mouth']:
                        drinking_text += " [HAND TO MOUTH]"
                        drinking_color = (0, 165, 255)  # Orange for gesture
                    else:
                        drinking_color = (255, 255, 255)  # White
                    
                    cv2.putText(display_frame, drinking_text, 
                               (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, drinking_color, 2)
                    y_offset += line_height
                    
                    # Drinking rate
                    rate_text = f"Rate: {metrics['drinking_rate']:.1f} /hr"
                    cv2.putText(display_frame, rate_text, 
                               (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
                    y_offset += line_height
                
                fatigue_score = metrics['fatigue_score']
                color = (0, 255, 0) if fatigue_score < 0.4 else (0, 165, 255) if fatigue_score < 0.6 else (0, 0, 255)
                cv2.putText(display_frame, f"Fatigue: {fatigue_score:.2f}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Fatigue bar
                bar_width = 200
                bar_height = 20
                bar_x = 10
                bar_y = y_offset + 10
                
                cv2.rectangle(display_frame, (bar_x, bar_y), 
                            (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), 2)
                
                fill_width = int(bar_width * fatigue_score)
                cv2.rectangle(display_frame, (bar_x + 2, bar_y + 2), 
                            (bar_x + fill_width, bar_y + bar_height - 2), color, -1)
                
                # Check if should suggest break
                should_break, reason = detector.should_suggest_break()
                if should_break:
                    cv2.putText(display_frame, f"BREAK SUGGESTED: {reason}", 
                               (10, display_frame.shape[0] - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    print(f"\n⚠️  Break suggested: {reason}")
            else:
                cv2.putText(display_frame, "Face: Not Detected", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # FPS counter
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                cv2.putText(display_frame, f"FPS: {fps:.1f}", 
                           (display_frame.shape[1] - 120, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display
            cv2.imshow('AdaptiBreak - Fatigue Detection Demo', display_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        webcam.release()
        cv2.destroyAllWindows()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Session Summary:")
        print("=" * 60)
        stats = detector.get_summary_stats()
        print(f"  Total Blinks: {stats['total_blinks']}")
        print(f"  Total Yawns: {stats['total_yawns']}")
        print(f"  Avg Blink Rate: {stats['avg_blink_rate']:.1f} per minute")
        print(f"  Avg Fatigue Score: {stats['avg_fatigue_score']:.3f}")
        print(f"  Max Fatigue Score: {stats['max_fatigue_score']:.3f}")
        
        if 'hand_near_face_events' in stats:
            print(f"  Hand Near Face Events: {stats['hand_near_face_events']}")
        
        if 'poor_posture_events' in stats:
            print(f"  Poor Posture Events: {stats['poor_posture_events']}")
            print(f"  Avg Shoulder Tilt: {stats['avg_shoulder_tilt']:.2f}°")
            print(f"  Avg Shoulder Forward: {stats['avg_shoulder_forward']:.3f}")
        
        if 'total_drinks' in stats:
            print(f"  Total Drinks Detected: {stats['total_drinks']}")
            print(f"  Avg Drinking Rate: {stats['avg_drinking_rate']:.1f} per hour")
            print(f"  Hand-to-Mouth Gestures: {stats['hand_to_mouth_events']}")
        
        print("=" * 60)
        print("\nThank you for testing!")


if __name__ == "__main__":
    main()

