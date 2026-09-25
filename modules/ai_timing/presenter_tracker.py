"""
Presenter Tracker Module

Tracks presenter's face orientation, emotion, and engagement level using
DeepFace/InsightFace for real-time video feed analysis.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import cv2
import numpy as np
import logging
from typing import Optional, Dict, List
from enum import Enum

from modules.face_ai.face_analyzer import FaceAnalyzer
from modules.face_ai.head_pose_estimator import HeadPoseEstimator

logger = logging.getLogger(__name__)


class PresenterState(Enum):
    """Presenter activity states."""
    TALKING = "talking"
    ENGAGED = "engaged"
    AWAY = "away"
    DISENGAGED = "disengaged"
    UNKNOWN = "unknown"


class PresenterTracker(QObject):
    """
    Tracks presenter's face orientation, emotion, and engagement.
    
    Features:
    - Face detection and orientation tracking
    - Emotion analysis (engaged, bored, etc.)
    - Engagement state detection
    - Real-time signals for presenter activity
    """
    
    # Signals
    presenter_talking = pyqtSignal()  # Presenter is actively talking/engaged
    presenter_engaged = pyqtSignal()  # Presenter is visually engaged
    presenter_away = pyqtSignal()  # Presenter is away from camera/view
    presenter_disengaged = pyqtSignal()  # Presenter is disengaged
    presenter_state_changed = pyqtSignal(str)  # Emits state: "talking", "engaged", "away", etc.
    presenter_emotion_changed = pyqtSignal(str)  # Emits emotion: "engaged", "bored", etc.
    
    def __init__(self):
        """Initialize presenter tracker."""
        super().__init__()
        
        # Camera
        self._camera = None
        self._camera_index = 0
        self._is_tracking = False
        
        # AI components
        self._face_analyzer = FaceAnalyzer()
        self._head_pose_estimator = HeadPoseEstimator()
        
        # State tracking
        self._current_state = PresenterState.UNKNOWN
        self._current_emotion = "neutral"
        self._face_detected = False
        self._looking_at_audience = False
        self._looking_at_screen = False
        
        # Thresholds
        self._engagement_threshold = 0.5  # Face confidence threshold
        self._orientation_threshold = 30.0  # Degrees for "looking at audience"
        self._frame_counter = 0
        
        # Processing timer
        self._process_timer = QTimer()
        self._process_timer.timeout.connect(self._process_next_frame)
        
        # State history for stability
        self._state_history = []  # Last N states
        self._state_history_size = 5
    
    def start_tracking(self, camera_index: int = 0, fps: int = 10):
        """
        Start tracking presenter.
        
        Args:
            camera_index: Camera index for presenter feed
            fps: Target frames per second (default: 10, lower for presenter tracking)
        """
        if self._is_tracking:
            logger.warning("Presenter tracking already running")
            return False
        
        try:
            self._camera_index = camera_index
            self._camera = cv2.VideoCapture(camera_index)
            
            if not self._camera.isOpened():
                logger.error(f"Failed to open presenter camera at index {camera_index}")
                return False
            
            # Set camera properties
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self._is_tracking = True
            self._frame_counter = 0
            self._state_history.clear()
            
            # Start processing timer
            interval_ms = int(1000 / fps)
            self._process_timer.start(interval_ms)
            
            logger.info(f"Started presenter tracking on camera {camera_index} at {fps} FPS")
            return True
            
        except Exception as e:
            logger.error(f"Error starting presenter tracking: {e}")
            self._is_tracking = False
            return False
    
    def stop_tracking(self):
        """Stop tracking presenter."""
        if not self._is_tracking:
            return
        
        self._is_tracking = False
        self._process_timer.stop()
        
        if self._camera:
            self._camera.release()
            self._camera = None
        
        self._current_state = PresenterState.UNKNOWN
        self._face_detected = False
        logger.info("Stopped presenter tracking")
    
    def _process_next_frame(self):
        """Process next frame from camera."""
        if not self._is_tracking or not self._camera:
            return
        
        ret, frame = self._camera.read()
        if not ret:
            logger.warning("Failed to read frame from presenter camera")
            return
        
        self._frame_counter += 1
        
        # Process every frame for presenter tracking (more critical)
        try:
            self._analyze_presenter_frame(frame)
        except Exception as e:
            logger.error(f"Error analyzing presenter frame: {e}")
    
    def _analyze_presenter_frame(self, frame: np.ndarray):
        """
        Analyze presenter frame for face, orientation, and emotion.
        
        Args:
            frame: BGR frame from camera
        """
        # Detect faces
        faces = self._face_analyzer.analyze_frame(frame)
        
        if not faces:
            # No face detected - presenter is away
            self._update_state(PresenterState.AWAY)
            self._face_detected = False
            return
        
        # Use first detected face (assumed to be presenter)
        face = faces[0]
        self._face_detected = True
        
        # Get face region for pose estimation
        face_region = face.get('region', (0, 0, 0, 0))
        if face_region and len(face_region) == 4:
            pose = self._head_pose_estimator.estimate_pose(frame, face_region)
        else:
            pose = None
        
        # Analyze orientation
        if pose:
            yaw = pose.get('yaw', 0)
            pitch = pose.get('pitch', 0)
            
            # Determine if looking at audience (yaw close to 0, pitch reasonable)
            # Looking at audience: yaw between -30 and +30 degrees
            # Looking at screen: yaw outside this range or pitch too high/low
            if abs(yaw) <= self._orientation_threshold and abs(pitch) <= 20:
                self._looking_at_audience = True
                self._looking_at_screen = False
            else:
                self._looking_at_audience = False
                self._looking_at_screen = True
        else:
            # Default to engaged if pose unavailable
            self._looking_at_audience = True
            self._looking_at_screen = False
        
        # Analyze emotion
        emotion = face.get('emotion', 'neutral').lower()
        self._current_emotion = emotion
        
        # Map emotion to engagement state
        engaged_emotions = ['happy', 'surprise', 'neutral']
        disengaged_emotions = ['sad', 'angry', 'fear']
        
        # Determine state
        if self._looking_at_audience:
            if emotion in engaged_emotions:
                new_state = PresenterState.ENGAGED
            elif emotion in disengaged_emotions:
                new_state = PresenterState.DISENGAGED
            else:
                new_state = PresenterState.ENGAGED  # Default to engaged if looking at audience
        elif self._looking_at_screen:
            # Looking at screen - could be reading slides, less engagement
            new_state = PresenterState.DISENGAGED
        else:
            new_state = PresenterState.UNKNOWN
        
        # Update state with stability check
        self._update_state(new_state)
        
        # Emit emotion signal if changed
        emotion_label = "engaged" if emotion in engaged_emotions else ("bored" if emotion in disengaged_emotions else "neutral")
        self.presenter_emotion_changed.emit(emotion_label)
    
    def _update_state(self, new_state: PresenterState):
        """Update presenter state with stability check."""
        # Add to history
        self._state_history.append(new_state)
        if len(self._state_history) > self._state_history_size:
            self._state_history.pop(0)
        
        # Use most common state in history for stability
        state_counts = {}
        for state in self._state_history:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        stable_state = max(state_counts.items(), key=lambda x: x[1])[0]
        
        if stable_state != self._current_state:
            old_state = self._current_state
            self._current_state = stable_state
            
            # Emit state-specific signals
            if stable_state == PresenterState.TALKING or stable_state == PresenterState.ENGAGED:
                if old_state != PresenterState.TALKING and old_state != PresenterState.ENGAGED:
                    self.presenter_engaged.emit()
                    if stable_state == PresenterState.TALKING:
                        self.presenter_talking.emit()
            elif stable_state == PresenterState.AWAY:
                if old_state != PresenterState.AWAY:
                    self.presenter_away.emit()
            elif stable_state == PresenterState.DISENGAGED:
                if old_state != PresenterState.DISENGAGED:
                    self.presenter_disengaged.emit()
            
            # Emit general state changed signal
            self.presenter_state_changed.emit(stable_state.value)
    
    def get_current_state(self) -> str:
        """Get current presenter state as string."""
        return self._current_state.value
    
    def is_talking(self) -> bool:
        """Check if presenter is talking/engaged."""
        return self._current_state in [PresenterState.TALKING, PresenterState.ENGAGED]
    
    def is_away(self) -> bool:
        """Check if presenter is away."""
        return self._current_state == PresenterState.AWAY
    
    def is_disengaged(self) -> bool:
        """Check if presenter is disengaged."""
        return self._current_state == PresenterState.DISENGAGED
    
    def get_emotion(self) -> str:
        """Get current emotion label."""
        return self._current_emotion
    
    def is_face_detected(self) -> bool:
        """Check if face is currently detected."""
        return self._face_detected
    
    def is_looking_at_audience(self) -> bool:
        """Check if presenter is looking at audience."""
        return self._looking_at_audience
    
    def is_looking_at_screen(self) -> bool:
        """Check if presenter is looking at screen."""
        return self._looking_at_screen
    
    def set_engagement_threshold(self, threshold: float):
        """Set engagement confidence threshold."""
        self._engagement_threshold = max(0.0, min(1.0, threshold))
    
    def set_orientation_threshold(self, degrees: float):
        """Set orientation threshold in degrees."""
        self._orientation_threshold = max(0.0, min(90.0, degrees))

