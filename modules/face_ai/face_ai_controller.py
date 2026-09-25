"""
Face AI Controller Module

Handles audience attention analysis and reaction detection using computer vision.
Integrates DeepFace, FER, and dlib for comprehensive face analysis.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import cv2
import numpy as np
import logging
from typing import Optional, List, Dict
import gc

from .face_analyzer import FaceAnalyzer
from .head_pose_estimator import HeadPoseEstimator
from .statistics_aggregator import StatisticsAggregator

logger = logging.getLogger(__name__)


class FaceAIController(QObject):
    """
    Controller for face AI and audience analysis module.
    
    Manages camera input, face detection, attention tracking, and reaction analysis.
    Uses DeepFace (RetinaFace) for detection, FER for emotion validation,
    and dlib for head pose estimation.
    """
    
    # Signals for AI analysis events
    attention_level_changed = pyqtSignal(float)  # Emits attention level (0.0-1.0)
    reaction_detected = pyqtSignal(str)  # Emits reaction type (e.g., "positive", "negative", "neutral")
    faces_detected = pyqtSignal(int)  # Emits number of detected faces
    frame_analyzed = pyqtSignal(np.ndarray, list, list)  # Emits (frame, faces, poses)
    statistics_updated = pyqtSignal(dict)  # Emits statistics dictionary
    
    def __init__(self):
        """Initialize the face AI controller."""
        super().__init__()
        
        # State
        self._is_analyzing = False
        self._is_paused = False
        self._camera_index = 0
        self._attention_threshold = 0.5
        self._camera = None
        self._age_filter = None  # (min, max) tuple or None
        self._gender_filter = None  # "Male" or "Female" or None
        
        # AI components
        self._face_analyzer = FaceAnalyzer()
        self._head_pose_estimator = HeadPoseEstimator()
        self._statistics_aggregator = StatisticsAggregator()
        
        # Processing settings
        self._process_every_n_frames = 2  # Process every 2nd frame for performance
        self._frame_counter = 0
        self._adaptive_skipping = True  # Enable adaptive frame skipping
        self._max_resolution = (640, 480)  # Maximum frame resolution
        
        # Resource monitoring callback
        self._check_ram_callback: Optional[callable] = None
        
        # Timer for frame processing
        self._process_timer = QTimer()
        self._process_timer.timeout.connect(self._process_next_frame)
        
    def start_analysis(self, camera_index: int = 0, fps: int = 15):
        """
        Start analyzing audience attention and reactions.
        
        Args:
            camera_index: Index of the camera to use (default: 0)
            fps: Target frames per second for processing (default: 15)
        """
        if self._is_analyzing:
            logger.warning("Analysis already running. Stop first before starting again.")
            return False
        
        try:
            self._camera_index = camera_index
            self._camera = cv2.VideoCapture(camera_index)
            
            if not self._camera.isOpened():
                logger.error(f"Failed to open camera at index {camera_index}")
                return False
            
            # Set camera properties
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self._is_analyzing = True
            self._frame_counter = 0
            
            # Start statistics aggregation
            self._statistics_aggregator.start_session()
            
            # Start processing timer
            interval_ms = int(1000 / fps)  # Convert fps to milliseconds
            self._process_timer.start(interval_ms)
            
            logger.info(f"Started face AI analysis on camera {camera_index} at {fps} FPS")
            return True
            
        except Exception as e:
            logger.error(f"Error starting analysis: {e}", exc_info=True)
            self._is_analyzing = False
            # Clean up camera if opened but failed
            if self._camera is not None:
                try:
                    if self._camera.isOpened():
                        self._camera.release()
                except:
                    pass
                self._camera = None
            return False
    
    def stop_analysis(self):
        """Stop analyzing audience and release camera."""
        self._is_analyzing = False
        self._process_timer.stop()
        
        # Properly release camera and cleanup resources
        if self._camera is not None:
            try:
                if self._camera.isOpened():
                    self._camera.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            self._camera = None
        
        # Clear OpenCV windows (only if GUI support is available)
        # Note: Some OpenCV builds don't include GUI support, so we wrap this in try-except
        try:
            import cv2
            # Only call destroyAllWindows if we're actually using OpenCV windows
            # Since we use PyQt for display, this is usually not needed
            # But we'll keep it safe with try-except for compatibility
            if hasattr(cv2, 'destroyAllWindows'):
                cv2.destroyAllWindows()
        except Exception as e:
            # OpenCV may not have GUI support compiled in - this is normal
            # and not a critical error since we use PyQt for display
            logger.debug(f"OpenCV window cleanup not available (GUI support may not be compiled): {e}")
        
        logger.info("Stopped face AI analysis and released resources")
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame for face detection and analysis.
        
        Args:
            frame: NumPy array representing the video frame (BGR)
            
        Returns:
            Dictionary with analysis results:
            - faces_count: Number of faces detected
            - faces: List of face analysis results
            - head_poses: List of head pose results
            - attention_level: Overall attention level (0.0-1.0)
            - reactions: List of reaction classifications
        """
        if frame is None or frame.size == 0:
            return {
                "faces_count": 0,
                "faces": [],
                "head_poses": [],
                "attention_level": 0.0,
                "reactions": []
            }
        
        try:
            # Analyze faces
            faces = self._face_analyzer.analyze_frame(frame)
            
            # Estimate head poses for each face
            head_poses = []
            for face in faces:
                face_box = face.get('region', (0, 0, 0, 0))
                pose = self._head_pose_estimator.estimate_pose(frame, face_box)
                head_poses.append(pose)
            
            # Calculate overall attention level
            attention_level = self._calculate_attention_level(faces, head_poses)
            
            # Classify reactions
            reactions = self._classify_reactions(faces, head_poses)
            
            # Update statistics
            self._statistics_aggregator.add_frame_results(faces, head_poses)
            
            # Emit signals
            num_faces = len(faces)
            self.faces_detected.emit(num_faces)
            self.attention_level_changed.emit(attention_level)
            
            # Emit frame analysis results for UI display
            self.frame_analyzed.emit(frame, faces, head_poses)
            
            # Emit statistics periodically
            if self._frame_counter % 30 == 0:  # Every 30 frames
                stats = self._statistics_aggregator.get_statistics()
                self.statistics_updated.emit(stats)
            
            return {
                "faces_count": num_faces,
                "faces": faces,
                "head_poses": head_poses,
                "attention_level": attention_level,
                "reactions": reactions
            }
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {
                "faces_count": 0,
                "faces": [],
                "head_poses": [],
                "attention_level": 0.0,
                "reactions": []
            }
    
    def _process_next_frame(self):
        """Process next frame from camera (called by timer)."""
        if not self._is_analyzing or self._camera is None:
            return
        
        ret, frame = self._camera.read()
        if not ret:
            logger.warning("Failed to read frame from camera")
            return
        
        # Adaptive frame skipping based on RAM usage
        if self._adaptive_skipping and self._check_ram_callback:
            try:
                is_high_ram = self._check_ram_callback()
                if is_high_ram:
                    # Increase skipping when RAM is high
                    adaptive_skip = min(self._process_every_n_frames * 2, 8)
                else:
                    adaptive_skip = self._process_every_n_frames
            except:
                adaptive_skip = self._process_every_n_frames
        else:
            adaptive_skip = self._process_every_n_frames
        
        # Process every Nth frame for performance
        self._frame_counter += 1
        if self._frame_counter % adaptive_skip == 0:
            # Optimize frame resolution
            optimized_frame = self._optimize_frame_resolution(frame)
            self.process_frame(optimized_frame)
        
        # Periodic memory cleanup
        if self._frame_counter % 100 == 0:
            gc.collect()
    
    def _optimize_frame_resolution(self, frame: np.ndarray) -> np.ndarray:
        """
        Optimize frame resolution for processing to reduce memory usage.
        
        Args:
            frame: Original frame (BGR)
        
        Returns:
            Optimized frame with reduced resolution if needed
        """
        try:
            h, w = frame.shape[:2]
            max_w, max_h = self._max_resolution
            
            # Check if downscaling is needed
            if w > max_w or h > max_h:
                # Calculate scale factor
                scale_w = max_w / w
                scale_h = max_h / h
                scale = min(scale_w, scale_h)
                
                # Downscale frame
                new_w = int(w * scale)
                new_h = int(h * scale)
                optimized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                
                logger.debug(f"Frame downscaled: {w}x{h} -> {new_w}x{new_h}")
                return optimized_frame
            
            return frame
        
        except Exception as e:
            logger.warning(f"Error optimizing frame resolution: {e}")
            return frame
    
    def _calculate_attention_level(self, faces: List[Dict], head_poses: List[Dict]) -> float:
        """
        Calculate overall attention level from faces and head poses.
        
        Args:
            faces: List of face analysis results
            head_poses: List of head pose results
            
        Returns:
            Attention level between 0.0 (distracted) and 1.0 (focused)
        """
        if not faces:
            return 0.0
        
        attention_sum = 0.0
        valid_count = 0
        
        for i, face in enumerate(faces):
            if i < len(head_poses) and head_poses[i] is not None:
                pose = head_poses[i]
                direction = pose.get('attention_direction', 'unknown')
                
                if direction == 'focused':
                    attention_sum += 1.0
                elif direction == 'distracted':
                    attention_sum += 0.0
                else:
                    # Partial attention
                    attention_sum += 0.5
                
                valid_count += 1
        
        if valid_count == 0:
            return 0.0
        
        return attention_sum / valid_count
    
    def _classify_reactions(self, faces: List[Dict], head_poses: List[Dict]) -> List[str]:
        """
        Classify reactions based on emotions and head poses.
        
        Args:
            faces: List of face analysis results
            head_poses: List of head pose results
            
        Returns:
            List of reaction classifications ("positive", "negative", "neutral")
        """
        reactions = []
        
        for i, face in enumerate(faces):
            emotion = face.get('emotion', 'neutral').lower()
            emotion_confidence = face.get('emotion_confidence', 0.0)
            
            # Only classify if confidence is reasonable
            if emotion_confidence < 0.3:
                reactions.append("neutral")
                continue
            
            # Positive reactions
            if emotion in ['happy', 'surprise']:
                reactions.append("positive")
            # Negative reactions
            elif emotion in ['sad', 'angry', 'fear', 'disgust']:
                reactions.append("negative")
            else:
                reactions.append("neutral")
        
        return reactions
    
    def set_attention_threshold(self, threshold: float):
        """
        Set the threshold for attention level detection.
        
        Args:
            threshold: Attention threshold between 0.0 and 1.0
        """
        if 0.0 <= threshold <= 1.0:
            self._attention_threshold = threshold
    
    def set_processing_rate(self, process_every_n: int):
        """
        Set how often to process frames (for performance tuning).
        
        Args:
            process_every_n: Process every Nth frame (1 = every frame, 2 = every other, etc.)
        """
        if process_every_n >= 1:
            self._process_every_n_frames = process_every_n
            logger.info(f"Processing rate set to every {self._process_every_n_frames} frames")
    
    def set_max_resolution(self, width: int, height: int):
        """
        Set maximum frame resolution for processing.
        
        Args:
            width: Maximum width
            height: Maximum height
        """
        self._max_resolution = (width, height)
        logger.info(f"Max resolution set to {width}x{height}")
    
    def set_adaptive_skipping(self, enabled: bool):
        """
        Enable/disable adaptive frame skipping based on RAM usage.
        
        Args:
            enabled: True to enable adaptive skipping
        """
        self._adaptive_skipping = enabled
        logger.info(f"Adaptive skipping: {enabled}")
    
    def set_ram_check_callback(self, callback: callable):
        """
        Set callback function to check RAM usage.
        
        Args:
            callback: Function that returns True if RAM usage is high
        """
        self._check_ram_callback = callback
    
    def is_analyzing(self) -> bool:
        """Check if analysis is currently running."""
        return self._is_analyzing
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics about audience analysis.
        
        Returns:
            Dictionary with statistics
        """
        return self._statistics_aggregator.get_statistics()
    
    def generate_report_charts(self, output_dir: str = "assets/reports") -> List[str]:
        """
        Generate visualization charts for analysis results.
        
        Args:
            output_dir: Directory to save chart images
            
        Returns:
            List of paths to generated chart files
        """
        return self._statistics_aggregator.generate_charts(output_dir)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current frame from camera without processing.
        
        Returns:
            Current camera frame or None
        """
        if self._camera is None or not self._is_analyzing:
            return None
        
        ret, frame = self._camera.read()
        if ret:
            return frame
        return None
