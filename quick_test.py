#!/usr/bin/env python3
"""Quick test of new features"""

print("Testing imports...")
try:
    import sys
    print(f"Python: {sys.version.split()[0]}")
    
    import numpy as np
    print(f"NumPy: OK")
    
    try:
        from filterpy.kalman import KalmanFilter
        print("filterpy: INSTALLED ✓")
        KALMAN_OK = True
    except ImportError:
        print("filterpy: NOT INSTALLED (will use fallback)")
        KALMAN_OK = False
    
    from fatigue_detector import FatigueDetector
    print("FatigueDetector: Imported ✓")
    
    detector = FatigueDetector()
    print(f"Calibration state: {detector.calibrated}")
    print(f"Kalman available: {detector.kalman_available}")
    
    if hasattr(detector, 'is_calibrating'):
        print("New methods: OK ✓")
    
    print("\n✅ All basic tests passed!")
    print("\nTo fully test, run: python3 main.py")
    print("Then select 'Adaptive Mode' and watch for calibration!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

