"""
Test Script for Face AI Module

Standalone demo script showcasing all Face AI features:
- Real-time face detection
- Emotion analysis
- Head pose estimation
- Statistics and reporting
"""

import sys
import cv2
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication
from modules.face_ai.face_ai_window import FaceAIWindow
from modules.face_ai.face_ai_controller import FaceAIController


def main():
    """Run Face AI module demo."""
    print("="*60)
    print("AI-Symp-Controller - Face AI Module Test")
    print("="*60)
    print("\nThis demo showcases:")
    print("  - Real-time face detection using RetinaFace")
    print("  - Emotion analysis (DeepFace + FER)")
    print("  - Head pose estimation (dlib)")
    print("  - Attention tracking and statistics")
    print("  - Report generation with charts")
    print("\n" + "-"*60)
    print("\nRequirements:")
    print("  - Camera connected and accessible")
    print("  - dlib shape predictor model (shape_predictor_68_face_landmarks.dat)")
    print("  - All AI libraries installed (deepface, fer, dlib)")
    print("\n" + "-"*60)
    
    # Check for required libraries
    missing_libs = []
    
    try:
        import deepface
        print("✓ DeepFace available")
    except ImportError:
        missing_libs.append("deepface")
        print("✗ DeepFace not found - install with: pip install deepface")
    
    try:
        from fer import FER
        print("✓ FER available")
    except ImportError:
        missing_libs.append("fer")
        print("✗ FER not found - install with: pip install fer")
    
    try:
        import dlib
        print("✓ dlib available")
    except ImportError:
        missing_libs.append("dlib")
        print("✗ dlib not found - install with: pip install dlib")
    
    if missing_libs:
        print("\n" + "="*60)
        print("WARNING: Missing required libraries!")
        print("="*60)
        print(f"Please install: {', '.join(missing_libs)}")
        print("\nSome features may not work correctly.")
        print("="*60)
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Check for shape predictor model
    predictor_paths = [
        "assets/shape_predictor_68_face_landmarks.dat",
        "modules/face_ai/shape_predictor_68_face_landmarks.dat",
        "shape_predictor_68_face_landmarks.dat",
    ]
    
    predictor_found = False
    for path in predictor_paths:
        if Path(path).exists():
            print(f"✓ Shape predictor found: {path}")
            predictor_found = True
            break
    
    if not predictor_found:
        print("\n" + "="*60)
        print("WARNING: Shape predictor model not found!")
        print("="*60)
        print("Head pose estimation will not work without the model.")
        print("\nDownload from:")
        print("http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        print("\nExtract and place in assets/ or modules/face_ai/")
        print("="*60)
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Test camera
    print("\n" + "-"*60)
    print("Testing camera...")
    test_cap = cv2.VideoCapture(0)
    if not test_cap.isOpened():
        print("✗ Camera not accessible!")
        print("Please check camera connection and permissions.")
        return
    test_cap.release()
    print("✓ Camera accessible")
    
    print("\n" + "="*60)
    print("Starting Face AI Module...")
    print("="*60)
    print("\nInstructions:")
    print("  1. Click 'Start Analysis' to begin")
    print("  2. Adjust FPS and processing rate as needed")
    print("  3. Watch real-time face detection and analysis")
    print("  4. View statistics in the right panel")
    print("  5. Click 'Stop Analysis' when done")
    print("  6. Click 'Generate Report' to create charts")
    print("\nPress Ctrl+Q or close window to exit")
    print("="*60)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create controller and window
    controller = FaceAIController()
    window = FaceAIWindow(controller=controller)
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

