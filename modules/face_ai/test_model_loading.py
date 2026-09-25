"""
Test Script for dlib Shape Predictor Model Loading

Verifies that the shape predictor model can be loaded correctly
and provides diagnostic information.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_dlib_installation():
    """Test if dlib is installed and importable."""
    print("="*70)
    print("Testing dlib Installation")
    print("="*70)
    
    try:
        import dlib
        print("[OK] dlib imported successfully")
        print(f"  dlib version: {dlib.__version__ if hasattr(dlib, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print("[FAIL] dlib import failed")
        print(f"  Error: {e}")
        print("\nInstallation options:")
        print("  1. pip install dlib")
        print("  2. conda install -c conda-forge dlib")
        print("  3. Download pre-built wheel from: https://github.com/sachadee/Dlib")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error importing dlib: {e}")
        return False


def test_model_paths():
    """Test all possible model file paths."""
    print("\n" + "="*70)
    print("Testing Model File Paths")
    print("="*70)
    
    # Get paths
    current_file_dir = Path(__file__).parent.resolve()
    project_root = current_file_dir.parent.parent.resolve()
    
    # Define search paths in priority order
    test_paths = [
        ("Absolute (Windows)", r"D:\AI-Studio\My-Win-App\AI-Symp-Controler\assets\models\shape_predictor_68_face_landmarks.dat"),
        ("Relative from root", str(project_root / "assets" / "models" / "shape_predictor_68_face_landmarks.dat")),
        ("Module relative", str(current_file_dir / ".." / ".." / "assets" / "models" / "shape_predictor_68_face_landmarks.dat")),
        ("Legacy assets", str(project_root / "assets" / "shape_predictor_68_face_landmarks.dat")),
        ("Module directory", str(current_file_dir / "shape_predictor_68_face_landmarks.dat")),
    ]
    
    found_paths = []
    
    for name, path_str in test_paths:
        path = Path(path_str).resolve()
        exists = path.exists()
        is_file = path.is_file() if exists else False
        
        status = "[OK]" if exists and is_file else "[NOT FOUND]"
        print(f"{status} {name}:")
        print(f"    Path: {path}")
        print(f"    Exists: {exists}")
        if exists:
            print(f"    Is File: {is_file}")
            print(f"    Size: {path.stat().st_size / (1024*1024):.2f} MB")
            found_paths.append(str(path))
        print()
    
    if found_paths:
        print("="*70)
        print(f"Found {len(found_paths)} model file(s):")
        for i, path in enumerate(found_paths, 1):
            print(f"  {i}. {path}")
        print("="*70)
        return found_paths[0]  # Return first found
    else:
        print("="*70)
        print("✗ No model file found in any tested location")
        print("="*70)
        return None


def test_model_loading(model_path: str):
    """Test loading the model file."""
    print("\n" + "="*70)
    print("Testing Model Loading")
    print("="*70)
    
    try:
        import dlib
    except ImportError:
        print("✗ dlib not available - cannot test model loading")
        return False
    
    if not model_path:
        print("[FAIL] No model path provided")
        return False
    
    path = Path(model_path)
    if not path.exists():
        print(f"[FAIL] Model file does not exist: {model_path}")
        return False
    
    print(f"Loading model from: {model_path}")
    
    try:
        predictor = dlib.shape_predictor(str(path))
        print("[OK] Model loaded successfully!")
        print(f"  Model file size: {path.stat().st_size / (1024*1024):.2f} MB")
        return True
    except dlib.error as e:
        print(f"[FAIL] dlib error loading model: {e}")
        print("  The model file may be corrupted or incompatible.")
        print("  Please re-download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error loading model: {e}")
        return False


def test_head_pose_estimator():
    """Test HeadPoseEstimator initialization."""
    print("\n" + "="*70)
    print("Testing HeadPoseEstimator Class")
    print("="*70)
    
    try:
        from modules.face_ai.head_pose_estimator import HeadPoseEstimator
    except ImportError as e:
        print(f"[FAIL] Failed to import HeadPoseEstimator: {e}")
        return False
    
    print("Initializing HeadPoseEstimator...")
    try:
        estimator = HeadPoseEstimator()
        
        if estimator.is_available():
            print("[OK] HeadPoseEstimator initialized successfully!")
            model_path = estimator.get_model_path()
            if model_path:
                print(f"  Model loaded from: {model_path}")
            return True
        else:
            print("[WARN] HeadPoseEstimator initialized but model not available")
            print("  (This is expected if model file is missing)")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error initializing HeadPoseEstimator: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("dlib Shape Predictor Model Loading Test")
    print("="*70)
    print("\nThis script tests:")
    print("  1. dlib library installation")
    print("  2. Model file path detection")
    print("  3. Model file loading")
    print("  4. HeadPoseEstimator initialization")
    print("\n" + "="*70 + "\n")
    
    # Test 1: dlib installation
    dlib_available = test_dlib_installation()
    
    if not dlib_available:
        print("\n" + "="*70)
        print("STOPPING: dlib not available")
        print("="*70)
        print("\nPlease install dlib first, then run this test again.")
        return
    
    # Test 2: Find model paths
    model_path = test_model_paths()
    
    # Test 3: Load model
    if model_path:
        model_loaded = test_model_loading(model_path)
    else:
        model_loaded = False
        print("\n[WARNING] Model file not found - cannot test loading")
        print("   Head pose estimation will not work until model is placed in correct location")
    
    # Test 4: Test HeadPoseEstimator
    estimator_works = test_head_pose_estimator()
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"dlib Installed:     {'[OK]' if dlib_available else '[FAIL]'}")
    print(f"Model File Found:   {'[OK]' if model_path else '[NOT FOUND]'}")
    print(f"Model Loads:         {'[OK]' if model_loaded else '[FAIL]'}")
    print(f"Estimator Works:     {'[OK]' if estimator_works else '[FAIL]'}")
    print("="*70)
    
    if dlib_available and model_path and model_loaded and estimator_works:
        print("\n[SUCCESS] All tests passed! Head pose estimation is ready to use.")
    elif dlib_available and not model_path:
        print("\n[WARNING] dlib is installed but model file is missing.")
        print("   Head pose estimation will not work until model is placed.")
    elif not dlib_available:
        print("\n[FAIL] dlib is not installed. Install dlib to use head pose estimation.")
    else:
        print("\n[WARNING] Some issues detected. Review the test output above.")


if __name__ == "__main__":
    main()

