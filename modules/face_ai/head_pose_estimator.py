"""
Head Pose Estimator Module

Estimates head pose (yaw, pitch, roll) using dlib facial landmarks
and OpenCV solvePnP for 3D pose estimation.

Requires pre-trained dlib shape predictor model:
shape_predictor_68_face_landmarks.dat

Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

Model File Location:
- Primary (Windows): D:\\AI-Studio\\My-Win-App\\AI-Symp-Controler\\assets\\models\\shape_predictor_68_face_landmarks.dat
- Fallback: Relative paths from module directory or assets/
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Try importing dlib
try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    logger.warning("dlib not available. Install with: pip install dlib")


class HeadPoseEstimator:
    """
    Estimates head pose (yaw, pitch, roll) from facial landmarks.
    
    Uses dlib's 68-point facial landmark detector and OpenCV's solvePnP
    for 3D pose estimation.
    """
    
    # 3D model points for a standard face (in mm)
    # Based on average human face proportions
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),              # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left mouth corner
        (150.0, -150.0, -125.0),     # Right mouth corner
    ], dtype=np.float64)
    
    # 2D landmark indices in dlib's 68-point model
    LANDMARK_INDICES = {
        'nose_tip': 30,
        'chin': 8,
        'left_eye_left': 36,
        'right_eye_right': 45,
        'left_mouth': 48,
        'right_mouth': 54,
    }
    
    def __init__(self, predictor_path: Optional[str] = None):
        """
        Initialize head pose estimator.
        
        Loads dlib shape predictor model with robust path handling:
        1. Uses provided predictor_path if given
        2. Tries absolute path: D:\\AI-Studio\\My-Win-App\\AI-Symp-Controler\\assets\\models\\shape_predictor_68_face_landmarks.dat
        3. Falls back to relative paths from module directory
        4. Provides clear error messages if model not found
        
        Args:
            predictor_path: Explicit path to dlib shape predictor model file.
                          If None, searches in standard locations.
        """
        self._dlib_available = DLIB_AVAILABLE
        self._detector = None
        self._predictor = None
        self._model_path = None
        
        if not DLIB_AVAILABLE:
            error_msg = (
                "dlib library not available. Head pose estimation disabled.\n"
                "Install with: pip install dlib\n"
                "Note: On Windows, you may need C++ Build Tools or use pre-built wheels:\n"
                "  - Download from: https://github.com/sachadee/Dlib\n"
                "  - Or install via conda: conda install -c conda-forge dlib"
            )
            logger.error(error_msg)
            print(f"\n{'='*60}")
            print("ERROR: dlib not available")
            print("="*60)
            print(error_msg)
            print("="*60 + "\n")
            return
        
        # Initialize dlib face detector
        try:
            self._detector = dlib.get_frontal_face_detector()
            logger.info("dlib face detector initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize dlib detector: {e}"
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n")
            self._dlib_available = False
            return
        
        # Load shape predictor with robust path handling
        if predictor_path is None:
            predictor_path = self._find_predictor_model()
        
        if predictor_path:
            success = self._load_predictor(predictor_path)
            if not success:
                # Try fallback paths
                self._try_fallback_paths()
        else:
            logger.warning("No predictor path provided and automatic search failed.")
            self._print_model_not_found_help()
    
    def _find_predictor_model(self) -> Optional[str]:
        """
        Find shape predictor model in common locations.
        
        Search order:
        1. Absolute path (Windows): D:\\AI-Studio\\My-Win-App\\AI-Symp-Controler\\assets\\models\\shape_predictor_68_face_landmarks.dat
        2. Relative from project root: assets/models/shape_predictor_68_face_landmarks.dat
        3. Relative from module: ../assets/models/shape_predictor_68_face_landmarks.dat
        4. Other common locations
        
        Returns:
            Path to model file if found, None otherwise
        """
        # Get current file directory for relative path calculations
        current_file_dir = Path(__file__).parent.resolve()
        project_root = current_file_dir.parent.parent.resolve()
        
        # Define search paths in priority order
        possible_paths = [
            # 1. Absolute path (Windows - primary deployment location)
            r"D:\AI-Studio\My-Win-App\AI-Symp-Controler\assets\models\shape_predictor_68_face_landmarks.dat",
            
            # 2. Relative from project root (portable deployment)
            str(project_root / "assets" / "models" / "shape_predictor_68_face_landmarks.dat"),
            
            # 3. Relative from module directory (if assets is at project root)
            str(current_file_dir / ".." / ".." / "assets" / "models" / "shape_predictor_68_face_landmarks.dat"),
            
            # 4. Legacy locations (for backward compatibility)
            str(project_root / "assets" / "shape_predictor_68_face_landmarks.dat"),
            str(current_file_dir / "shape_predictor_68_face_landmarks.dat"),
            str(project_root / "shape_predictor_68_face_landmarks.dat"),
            str(Path.home() / ".dlib" / "shape_predictor_68_face_landmarks.dat"),
        ]
        
        # Try each path
        for path_str in possible_paths:
            path = Path(path_str).resolve()
            if path.exists() and path.is_file():
                logger.info(f"Found shape predictor model: {path}")
                return str(path)
        
        logger.warning("Shape predictor model not found in any standard location.")
        return None
    
    def _load_predictor(self, predictor_path: str) -> bool:
        """
        Load shape predictor model from file.
        
        Args:
            predictor_path: Path to model file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        path = Path(predictor_path)
        
        # Verify file exists
        if not path.exists():
            logger.error(f"Model file not found: {predictor_path}")
            return False
        
        if not path.is_file():
            logger.error(f"Path is not a file: {predictor_path}")
            return False
        
        # Check file permissions (readable)
        if not os.access(predictor_path, os.R_OK):
            error_msg = (
                f"Cannot read model file: {predictor_path}\n"
                "Please check file permissions. Ensure you have read access to the file."
            )
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n")
            return False
        
        # Try to load the predictor
        try:
            logger.info(f"Loading shape predictor from: {predictor_path}")
            self._predictor = dlib.shape_predictor(str(predictor_path))
            self._model_path = str(path.resolve())
            logger.info(f"[OK] Shape predictor loaded successfully from: {self._model_path}")
            print(f"\n[OK] Shape predictor loaded: {self._model_path}\n")
            return True
            
        except dlib.error as e:
            error_msg = (
                f"dlib error loading shape predictor: {e}\n"
                "The model file may be corrupted or incompatible.\n"
                "Please re-download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
            )
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n")
            self._predictor = None
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error loading shape predictor: {e}"
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n")
            self._predictor = None
            return False
    
    def _try_fallback_paths(self):
        """Try loading from additional fallback paths."""
        fallback_paths = [
            "assets/models/shape_predictor_68_face_landmarks.dat",
            "modules/face_ai/shape_predictor_68_face_landmarks.dat",
        ]
        
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        
        for rel_path in fallback_paths:
            abs_path = (project_root / rel_path).resolve()
            if abs_path.exists():
                logger.info(f"Trying fallback path: {abs_path}")
                if self._load_predictor(str(abs_path)):
                    return
        
        self._print_model_not_found_help()
    
    def _print_model_not_found_help(self):
        """Print helpful error message when model not found."""
        help_text = f"""
{'='*70}
ERROR: dlib Shape Predictor Model Not Found
{'='*70}

The head pose estimation feature requires the dlib shape predictor model file:
  shape_predictor_68_face_landmarks.dat

EXPECTED LOCATION (Primary - Windows):
  D:\\AI-Studio\\My-Win-App\\AI-Symp-Controler\\assets\\models\\shape_predictor_68_face_landmarks.dat

ALTERNATIVE LOCATIONS (will be checked automatically):
  - assets/models/shape_predictor_68_face_landmarks.dat (relative to project root)
  - modules/face_ai/shape_predictor_68_face_landmarks.dat
  - assets/shape_predictor_68_face_landmarks.dat

DOWNLOAD INSTRUCTIONS:
  1. Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
  2. Extract the .dat file from the .bz2 archive
  3. Place in: assets/models/shape_predictor_68_face_landmarks.dat
  4. Ensure the file is readable (not corrupted)

NOTE: Head pose estimation will be disabled until the model file is available.
      Face detection and emotion analysis will still work.
{'='*70}
"""
        logger.error(help_text)
        print(help_text)
    
    def detect_landmarks(self, frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Detect facial landmarks for a face region.
        
        Args:
            frame: Input frame (BGR)
            face_box: (x, y, w, h) bounding box
            
        Returns:
            68x2 numpy array of landmark coordinates, or None if detection fails
        """
        if not self._dlib_available or self._predictor is None:
            return None
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Convert (x, y, w, h) to dlib rectangle
            x, y, w, h = face_box
            rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
            
            # Detect landmarks
            landmarks = self._predictor(gray, rect)
            
            # Convert to numpy array
            points = np.array([(p.x, p.y) for p in landmarks.parts()], dtype=np.float32)
            
            return points
            
        except Exception as e:
            logger.error(f"Landmark detection error: {e}")
            return None
    
    def estimate_pose(
        self, 
        frame: np.ndarray, 
        face_box: Tuple[int, int, int, int],
        landmarks: Optional[np.ndarray] = None
    ) -> Optional[Dict]:
        """
        Estimate head pose (yaw, pitch, roll) for a detected face.
        
        Args:
            frame: Input frame (BGR)
            face_box: (x, y, w, h) face bounding box
            landmarks: Optional pre-detected landmarks (68x2 array)
            
        Returns:
            Dictionary with:
            - yaw: Rotation around vertical axis (degrees, negative = left, positive = right)
            - pitch: Rotation around horizontal axis (degrees, negative = up, positive = down)
            - roll: Rotation around depth axis (degrees, negative = clockwise, positive = counter-clockwise)
            - attention_direction: 'focused', 'left', 'right', 'up', 'down', 'distracted'
            - landmarks: 2D landmark points used for estimation
        """
        if not self._dlib_available or self._predictor is None:
            return None
        
        # Get landmarks if not provided
        if landmarks is None:
            landmarks = self.detect_landmarks(frame, face_box)
        
        if landmarks is None or len(landmarks) < 68:
            return None
        
        try:
            # Extract specific landmark points for pose estimation
            image_points = np.array([
                landmarks[self.LANDMARK_INDICES['nose_tip']],      # Nose tip
                landmarks[self.LANDMARK_INDICES['chin']],          # Chin
                landmarks[self.LANDMARK_INDICES['left_eye_left']], # Left eye left corner
                landmarks[self.LANDMARK_INDICES['right_eye_right']], # Right eye right corner
                landmarks[self.LANDMARK_INDICES['left_mouth']],   # Left mouth corner
                landmarks[self.LANDMARK_INDICES['right_mouth']],  # Right mouth corner
            ], dtype=np.float64)
            
            # Camera internals (assume typical webcam parameters)
            # These can be calibrated for better accuracy
            height, width = frame.shape[:2]
            focal_length = width
            center = (width / 2, height / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Distortion coefficients (assume no distortion for webcam)
            dist_coeffs = np.zeros((4, 1), dtype=np.float64)
            
            # Solve PnP to estimate pose
            success, rotation_vector, translation_vector = cv2.solvePnP(
                self.MODEL_POINTS,
                image_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return None
            
            # Convert rotation vector to rotation matrix
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            
            # Extract Euler angles (yaw, pitch, roll)
            # Using ZYX convention
            sy = np.sqrt(rotation_matrix[0, 0]**2 + rotation_matrix[1, 0]**2)
            singular = sy < 1e-6
            
            if not singular:
                yaw = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
                pitch = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            else:
                yaw = np.arctan2(-rotation_matrix[0, 1], rotation_matrix[1, 1])
                pitch = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = 0
            
            # Convert to degrees
            yaw = np.degrees(yaw)
            pitch = np.degrees(pitch)
            roll = np.degrees(roll)
            
            # Determine attention direction
            attention_direction = self._classify_attention(yaw, pitch, roll)
            
            return {
                'yaw': float(yaw),
                'pitch': float(pitch),
                'roll': float(roll),
                'attention_direction': attention_direction,
                'landmarks': landmarks.tolist(),
                'rotation_vector': rotation_vector.tolist(),
                'translation_vector': translation_vector.tolist(),
            }
            
        except Exception as e:
            logger.error(f"Pose estimation error: {e}")
            return None
    
    def _classify_attention(self, yaw: float, pitch: float, roll: float) -> str:
        """
        Classify attention direction based on head pose angles.
        
        Args:
            yaw: Head rotation left/right (degrees)
            pitch: Head rotation up/down (degrees)
            roll: Head tilt (degrees)
            
        Returns:
            Attention direction string
        """
        # Thresholds in degrees
        YAW_THRESHOLD = 15.0  # Left/right
        PITCH_THRESHOLD = 15.0  # Up/down
        ROLL_THRESHOLD = 15.0  # Tilt
        
        # Check for large movements (distracted)
        if abs(yaw) > 30 or abs(pitch) > 25 or abs(roll) > 20:
            return 'distracted'
        
        # Check yaw (left/right)
        if yaw < -YAW_THRESHOLD:
            return 'left'
        elif yaw > YAW_THRESHOLD:
            return 'right'
        
        # Check pitch (up/down)
        if pitch < -PITCH_THRESHOLD:
            return 'up'
        elif pitch > PITCH_THRESHOLD:
            return 'down'
        
        # Check roll (tilted)
        if abs(roll) > ROLL_THRESHOLD:
            return 'tilted'
        
        # Otherwise focused (looking forward)
        return 'focused'
    
    def is_available(self) -> bool:
        """
        Check if head pose estimation is available.
        
        Returns:
            True if dlib is available and predictor model is loaded, False otherwise
        """
        return self._dlib_available and self._predictor is not None
    
    def get_model_path(self) -> Optional[str]:
        """
        Get the path of the loaded model file.
        
        Returns:
            Path to model file if loaded, None otherwise
        """
        return self._model_path
    
    def draw_pose_arrow(
        self, 
        frame: np.ndarray, 
        face_box: Tuple[int, int, int, int],
        pose: Dict,
        scale: float = 50.0
    ) -> np.ndarray:
        """
        Draw arrow indicating head pose direction on frame.
        
        Args:
            frame: Input frame
            face_box: (x, y, w, h) face bounding box
            pose: Pose dictionary with yaw, pitch, roll
            scale: Arrow length scale
            
        Returns:
            Frame with pose arrow drawn
        """
        if pose is None:
            return frame
        
        # Get face center
        x, y, w, h = face_box
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Calculate arrow direction from yaw and pitch
        yaw_rad = np.radians(pose['yaw'])
        pitch_rad = np.radians(pose['pitch'])
        
        # Arrow endpoint
        end_x = int(center_x + scale * np.sin(yaw_rad))
        end_y = int(center_y + scale * np.sin(pitch_rad))
        
        # Draw arrow
        cv2.arrowedLine(
            frame,
            (center_x, center_y),
            (end_x, end_y),
            (0, 255, 0),
            2,
            tipLength=0.3
        )
        
        return frame

