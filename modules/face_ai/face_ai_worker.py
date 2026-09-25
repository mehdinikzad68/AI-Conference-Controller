"""
Face AI Worker Thread

QThread worker for processing face AI analysis in background thread.
Keeps UI responsive during heavy AI computations.
"""

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
import cv2
import numpy as np
import logging
from typing import Optional, Dict, List
import time
import gc

from .face_analyzer import FaceAnalyzer
from .head_pose_estimator import HeadPoseEstimator

logger = logging.getLogger(__name__)


class FaceAIWorker(QThread):
    """
    Worker thread for Face AI processing.
    
    Runs face detection, emotion analysis, and head pose estimation
    in a separate thread to prevent UI blocking.
    
    Signals:
        frame_processed: Emitted when a frame is processed (frame, faces, poses)
        statistics_updated: Emitted with updated statistics
        error_occurred: Emitted when an error occurs
        fps_updated: Emitted with current FPS
    """
    
    # Signals
    frame_processed = pyqtSignal(np.ndarray, list, list)  # frame, faces, poses
    statistics_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    fps_updated = pyqtSignal(float)
    
    def __init__(self, camera_index: int = 0, target_fps: int = 15):
        """
        Initialize Face AI worker.
        
        Args:
            camera_index: Camera device index
            target_fps: Target frames per second
        """
        super().__init__()
        
        self._camera_index = camera_index
        self._target_fps = target_fps
        self._running = False
        self._paused = False
        self._process_every_n = 2  # Process every 2nd frame for performance
        self._adaptive_skipping = True  # Enable adaptive frame skipping based on RAM
        
        # Memory optimization
        self._max_resolution = (640, 480)  # Maximum frame resolution for processing
        self._downscale_factor = 1.0  # Downscale factor (1.0 = no downscale)
        
        # Thread-safe access
        self._mutex = QMutex()
        
        # AI components
        self._face_analyzer: Optional[FaceAnalyzer] = None
        self._head_pose_estimator: Optional[HeadPoseEstimator] = None
        
        # Camera
        self._camera: Optional[cv2.VideoCapture] = None
        
        # Statistics
        self._frame_count = 0
        self._stats = {
            'total_faces': 0,
            'focused_count': 0,
            'distracted_count': 0,
            'emotions': {},
            'attention_level': 0.0
        }
        
        # Performance monitoring
        self._last_fps_update = time.time()
        self._fps_counter = 0
        self._current_fps = 0.0
        
        # Resource monitoring callback
        self._check_ram_callback: Optional[callable] = None
    
    def run(self):
        """Main thread execution loop."""
        try:
            logger.info(f"Face AI Worker starting (camera: {self._camera_index}, fps: {self._target_fps})")
            
            # Initialize AI components
            self._face_analyzer = FaceAnalyzer()
            self._head_pose_estimator = HeadPoseEstimator()
            
            # Initialize camera
            self._camera = cv2.VideoCapture(self._camera_index)
            if not self._camera.isOpened():
                error_msg = f"Failed to open camera {self._camera_index}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # Set camera properties
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self._running = True
            frame_delay = 1.0 / self._target_fps
            
            logger.info("Face AI Worker started successfully")
            
            while self._running:
                if self._paused:
                    # Sleep briefly when paused
                    time.sleep(0.1)
                    continue
                
                loop_start = time.time()
                
                # Read frame
                ret, frame = self._camera.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Adaptive frame skipping based on RAM usage
                if self._adaptive_skipping and self._check_ram_callback:
                    try:
                        is_high_ram = self._check_ram_callback()
                        if is_high_ram:
                            # Increase skipping when RAM is high
                            adaptive_skip = min(self._process_every_n * 2, 8)
                        else:
                            adaptive_skip = self._process_every_n
                    except:
                        adaptive_skip = self._process_every_n
                else:
                    adaptive_skip = self._process_every_n
                
                # Process frame (every N frames with adaptive skipping)
                self._frame_count += 1
                if self._frame_count % adaptive_skip == 0:
                    # Downscale frame for processing if needed
                    processed_frame = self._optimize_frame_resolution(frame)
                    self._process_frame(processed_frame)
                
                # Update FPS
                self._update_fps()
                
                # Maintain target FPS
                elapsed = time.time() - loop_start
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            logger.info("Face AI Worker stopped")
            
        except Exception as e:
            error_msg = f"Face AI Worker error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
        
        finally:
            # Cleanup
            self._cleanup()
    
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
    
    def _process_frame(self, frame: np.ndarray):
        """
        Process a single frame.
        
        Args:
            frame: Camera frame (BGR)
        """
        try:
            # Analyze faces
            faces = self._face_analyzer.analyze_frame(frame)
            
            # Estimate head poses
            head_poses = []
            for face in faces:
                face_box = face.get('region', (0, 0, 0, 0))
                pose = self._head_pose_estimator.estimate_pose(frame, face_box)
                head_poses.append(pose)
            
            # Calculate statistics
            self._update_statistics(faces, head_poses)
            
            # Emit results (use original frame for display if needed)
            self.frame_processed.emit(frame.copy(), faces, head_poses)
            
            # Emit statistics periodically (every 30 processed frames)
            if (self._frame_count // self._process_every_n) % 30 == 0:
                with QMutexLocker(self._mutex):
                    self.statistics_updated.emit(self._stats.copy())
            
            # Periodic memory cleanup
            if self._frame_count % 100 == 0:
                gc.collect()
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
    
    def _update_statistics(self, faces: List[Dict], head_poses: List[Dict]):
        """
        Update statistics based on analysis results.
        
        Args:
            faces: List of face analysis results
            head_poses: List of head pose results
        """
        with QMutexLocker(self._mutex):
            self._stats['total_faces'] = len(faces)
            
            focused = 0
            distracted = 0
            
            for i, pose in enumerate(head_poses):
                if pose and 'attention_direction' in pose:
                    direction = pose['attention_direction']
                    if direction == 'focused':
                        focused += 1
                    elif direction == 'distracted':
                        distracted += 1
            
            self._stats['focused_count'] = focused
            self._stats['distracted_count'] = distracted
            
            # Calculate attention level
            total = focused + distracted
            if total > 0:
                self._stats['attention_level'] = focused / total
            else:
                self._stats['attention_level'] = 0.0
            
            # Update emotions
            emotions = {}
            for face in faces:
                emotion = face.get('emotion', 'neutral')
                emotions[emotion] = emotions.get(emotion, 0) + 1
            
            self._stats['emotions'] = emotions
    
    def _update_fps(self):
        """Update FPS counter."""
        self._fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self._last_fps_update
        
        if elapsed >= 1.0:  # Update every second
            self._current_fps = self._fps_counter / elapsed
            self.fps_updated.emit(self._current_fps)
            
            self._fps_counter = 0
            self._last_fps_update = current_time
    
    def _cleanup(self):
        """Cleanup resources."""
        if self._camera is not None:
            try:
                if self._camera.isOpened():
                    self._camera.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            self._camera = None
        
        logger.info("Face AI Worker cleaned up")
    
    def stop(self):
        """Stop the worker thread."""
        logger.info("Stopping Face AI Worker...")
        self._running = False
    
    def pause(self):
        """Pause processing."""
        with QMutexLocker(self._mutex):
            self._paused = True
        logger.info("Face AI Worker paused")
    
    def resume(self):
        """Resume processing."""
        with QMutexLocker(self._mutex):
            self._paused = False
        logger.info("Face AI Worker resumed")
    
    def set_processing_rate(self, process_every_n: int):
        """
        Set processing rate (process every Nth frame).
        
        Args:
            process_every_n: Process every N frames (1 = every frame, 2 = every other, etc)
        """
        with QMutexLocker(self._mutex):
            self._process_every_n = max(1, process_every_n)
        logger.info(f"Processing rate set to every {self._process_every_n} frames")
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics (thread-safe).
        
        Returns:
            Statistics dictionary
        """
        with QMutexLocker(self._mutex):
            return self._stats.copy()
    
    def get_current_fps(self) -> float:
        """
        Get current FPS (thread-safe).
        
        Returns:
            Current FPS
        """
        with QMutexLocker(self._mutex):
            return self._current_fps
    
    def set_max_resolution(self, width: int, height: int):
        """
        Set maximum frame resolution for processing.
        
        Args:
            width: Maximum width
            height: Maximum height
        """
        with QMutexLocker(self._mutex):
            self._max_resolution = (width, height)
        logger.info(f"Max resolution set to {width}x{height}")
    
    def set_adaptive_skipping(self, enabled: bool):
        """
        Enable/disable adaptive frame skipping based on RAM usage.
        
        Args:
            enabled: True to enable adaptive skipping
        """
        with QMutexLocker(self._mutex):
            self._adaptive_skipping = enabled
        logger.info(f"Adaptive skipping: {enabled}")
    
    def set_ram_check_callback(self, callback: callable):
        """
        Set callback function to check RAM usage.
        
        Args:
            callback: Function that returns True if RAM usage is high
        """
        with QMutexLocker(self._mutex):
            self._check_ram_callback = callback

