"""
Face Analyzer Module

Handles face detection and emotion analysis using DeepFace and FER.
Provides high-accuracy face detection with RetinaFace backend and
dual emotion analysis for cross-validation.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try importing required libraries
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError as e:
    DEEPFACE_AVAILABLE = False
    logger.warning(f"DeepFace not available. Install with: pip install deepface. Error: {e}")
except Exception as e:
    # DeepFace might be installed but have initialization issues
    # Still mark as available if import succeeds
    try:
        from deepface import DeepFace
        DEEPFACE_AVAILABLE = True
        logger.info(f"DeepFace available (with warnings during import)")
    except:
        DEEPFACE_AVAILABLE = False
        logger.warning(f"DeepFace import failed: {e}")

try:
    # Try different import paths for different FER versions
    try:
        from fer import FER
    except ImportError:
        # FER v25+ uses fer.fer module
        from fer.fer import FER
    FER_AVAILABLE = True
except ImportError:
    FER_AVAILABLE = False
    logger.warning("FER not available. Install with: pip install fer")

try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    logger.warning("dlib not available. Install with: pip install dlib")


class FaceAnalyzer:
    """
    Analyzes faces in video frames using DeepFace and FER.
    
    Uses RetinaFace for high-accuracy detection and dual emotion analysis
    for cross-validation.
    """
    
    def __init__(self):
        """Initialize face analyzer with DeepFace and FER."""
        # Use dynamic check instead of cached flags to handle runtime installations
        self._deepface_available = self._check_deepface_dynamic()
        self._fer_available = self._check_fer_dynamic()
        
        # Store imported modules for later use
        self._DeepFace = None
        self._FER_Class = None
        self._fer_detector = None
        
        # Initialize DeepFace reference if available
        if self._deepface_available:
            try:
                from deepface import DeepFace
                self._DeepFace = DeepFace
            except Exception as e:
                logger.warning(f"Failed to import DeepFace: {e}")
                self._deepface_available = False
        
        # Initialize FER detector (using MTCNN for better accuracy)
        if self._fer_available:
            try:
                try:
                    from fer import FER as FER_Class
                except ImportError:
                    from fer.fer import FER as FER_Class
                self._FER_Class = FER_Class
                self._fer_detector = FER_Class(mtcnn=True)
                logger.info("FER detector initialized with MTCNN")
            except Exception as e:
                logger.warning(f"Failed to initialize FER: {e}")
                self._fer_available = False
        
        # Configuration
        self._detector_backend = 'retinaface'  # Best accuracy
        self._model_name = 'VGG-Face'  # Best for emotion/age/gender
        self._enforce_detection = False  # Don't fail if no face found
    
    def _check_deepface_dynamic(self) -> bool:
        """Dynamically check if DeepFace is available at runtime."""
        try:
            from deepface import DeepFace
            return True
        except (ImportError, Exception) as e:
            # Also check the global flag as fallback
            return DEEPFACE_AVAILABLE if 'DEEPFACE_AVAILABLE' in globals() else False
    
    def _check_fer_dynamic(self) -> bool:
        """Dynamically check if FER is available at runtime."""
        try:
            try:
                from fer import FER
            except ImportError:
                from fer.fer import FER
            return True
        except (ImportError, Exception) as e:
            # Also check the global flag as fallback
            return FER_AVAILABLE if 'FER_AVAILABLE' in globals() else False
        
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for better detection accuracy.
        
        Applies:
        - Histogram equalization for better contrast
        - Optional denoising
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Preprocessed frame
        """
        # Convert to LAB color space for better contrast adjustment
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge back and convert to BGR
        lab = cv2.merge([l, a, b])
        processed = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return processed
    
    def detect_faces_deepface(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces and analyze emotion/age/gender using DeepFace with RetinaFace.
        
        Args:
            frame: Input BGR frame
            
        Returns:
            List of face analysis dictionaries, each containing:
            - region: (x, y, w, h) bounding box
            - emotion: dominant emotion with confidence
            - age: estimated age
            - gender: predicted gender
            - emotion_confidence: confidence scores for all emotions
        """
        # Dynamic check - recheck if needed
        if not self._deepface_available:
            self._deepface_available = self._check_deepface_dynamic()
            if self._deepface_available and self._DeepFace is None:
                try:
                    from deepface import DeepFace
                    self._DeepFace = DeepFace
                except:
                    return []
        
        if not self._deepface_available or self._DeepFace is None:
            return []
        
        try:
            # Analyze frame with DeepFace
            # Using RetinaFace for best detection accuracy
            result = self._DeepFace.analyze(
                frame,
                actions=['emotion', 'age', 'gender'],
                detector_backend=self._detector_backend,
                enforce_detection=self._enforce_detection,
                model_name=self._model_name,
                silent=True  # Suppress progress output
            )
            
            # Handle both single face and multiple faces
            if isinstance(result, dict):
                result = [result]
            
            faces = []
            for face_data in result:
                if 'region' not in face_data:
                    continue
                
                # Extract region (x, y, w, h)
                region = face_data['region']
                x = region.get('x', 0)
                y = region.get('y', 0)
                w = region.get('w', 0)
                h = region.get('h', 0)
                
                # Get dominant emotion
                emotion_data = face_data.get('emotion', {})
                if isinstance(emotion_data, dict):
                    dominant_emotion = max(emotion_data.items(), key=lambda x: x[1])[0]
                    emotion_confidence = emotion_data.get(dominant_emotion, 0.0)
                else:
                    dominant_emotion = "neutral"
                    emotion_confidence = 0.0
                
                faces.append({
                    'region': (x, y, w, h),
                    'emotion': dominant_emotion,
                    'emotion_confidence': emotion_confidence,
                    'emotion_scores': emotion_data if isinstance(emotion_data, dict) else {},
                    'age': face_data.get('age', 0),
                    'gender': face_data.get('dominant_gender', 'unknown'),
                    'gender_confidence': face_data.get('gender', {}).get(
                        face_data.get('dominant_gender', ''), 0.0
                    ) if isinstance(face_data.get('gender'), dict) else 0.0,
                    'source': 'deepface'
                })
            
            return faces
            
        except Exception as e:
            logger.error(f"DeepFace analysis error: {e}")
            return []
    
    def detect_emotions_fer(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect emotions using FER for cross-validation.
        
        Args:
            frame: Input BGR frame
            
        Returns:
            List of emotion detection results with bounding boxes
        """
        if not self._fer_available or self._fer_detector is None:
            return []
        
        try:
            # FER expects RGB, so convert
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect emotions
            fer_results = self._fer_detector.detect_emotions(frame_rgb)
            
            faces = []
            for result in fer_results:
                box = result['box']  # (x, y, w, h)
                emotions = result['emotions']
                
                # Get dominant emotion
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                emotion_confidence = emotions[dominant_emotion]
                
                faces.append({
                    'region': (box[0], box[1], box[2], box[3]),
                    'emotion': dominant_emotion,
                    'emotion_confidence': emotion_confidence,
                    'emotion_scores': emotions,
                    'source': 'fer'
                })
            
            return faces
            
        except Exception as e:
            logger.error(f"FER analysis error: {e}")
            return []
    
    def merge_analysis_results(
        self, 
        deepface_results: List[Dict], 
        fer_results: List[Dict],
        frame: np.ndarray
    ) -> List[Dict]:
        """
        Merge DeepFace and FER results for each detected face.
        
        Matches faces by bounding box overlap and aggregates results.
        
        Args:
            deepface_results: Results from DeepFace
            fer_results: Results from FER
            frame: Original frame for reference
            
        Returns:
            Merged list of face analysis results
        """
        if not deepface_results and not fer_results:
            return []
        
        # If only one source available, return that
        if not deepface_results:
            return fer_results
        if not fer_results:
            return deepface_results
        
        # Calculate IoU (Intersection over Union) for matching
        merged_faces = []
        
        for df_face in deepface_results:
            df_box = df_face['region']
            best_fer_match = None
            best_iou = 0.0
            
            # Find best matching FER face
            for fer_face in fer_results:
                fer_box = fer_face['region']
                iou = self._calculate_iou(df_box, fer_box)
                if iou > best_iou and iou > 0.3:  # Minimum overlap threshold
                    best_iou = iou
                    best_fer_match = fer_face
            
            # Merge results
            merged_face = df_face.copy()
            
            if best_fer_match:
                # Average emotion confidence if both detected similar emotions
                df_emotion = df_face['emotion']
                fer_emotion = best_fer_match['emotion']
                
                if df_emotion == fer_emotion:
                    # Both agree - average confidence
                    merged_face['emotion_confidence'] = (
                        df_face['emotion_confidence'] + best_fer_match['emotion_confidence']
                    ) / 2.0
                    merged_face['emotion_scores_fer'] = best_fer_match['emotion_scores']
                else:
                    # Disagreement - use higher confidence source
                    if df_face['emotion_confidence'] > best_fer_match['emotion_confidence']:
                        merged_face['emotion'] = df_emotion
                        merged_face['emotion_confidence'] = df_face['emotion_confidence']
                    else:
                        merged_face['emotion'] = fer_emotion
                        merged_face['emotion_confidence'] = best_fer_match['emotion_confidence']
                    merged_face['emotion_scores_fer'] = best_fer_match['emotion_scores']
                
                merged_face['merged'] = True
            else:
                merged_face['merged'] = False
            
            merged_faces.append(merged_face)
        
        # Add unmatched FER faces
        for fer_face in fer_results:
            fer_box = fer_face['region']
            matched = False
            
            for merged_face in merged_faces:
                df_box = merged_face['region']
                iou = self._calculate_iou(df_box, fer_box)
                if iou > 0.3:
                    matched = True
                    break
            
            if not matched:
                # Add as standalone FER result
                merged_face = fer_face.copy()
                merged_face['merged'] = False
                merged_faces.append(merged_face)
        
        return merged_faces
    
    def _calculate_iou(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """
        Calculate Intersection over Union (IoU) of two bounding boxes.
        
        Args:
            box1: (x, y, w, h)
            box2: (x, y, w, h)
            
        Returns:
            IoU value between 0.0 and 1.0
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        inter_area = (xi2 - xi1) * (yi2 - yi1)
        
        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def analyze_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Complete face analysis pipeline: preprocessing, detection, and merging.
        
        Args:
            frame: Input BGR frame
            
        Returns:
            List of merged face analysis results
        """
        # Preprocess frame
        processed_frame = self.preprocess_frame(frame)
        
        # Detect with DeepFace
        deepface_results = self.detect_faces_deepface(processed_frame)
        
        # Detect with FER
        fer_results = self.detect_emotions_fer(frame)  # Use original for FER
        
        # Merge results
        merged_results = self.merge_analysis_results(deepface_results, fer_results, frame)
        
        return merged_results

