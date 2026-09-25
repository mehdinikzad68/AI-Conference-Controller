"""
AI Integration Controller Module

Coordinates presenter tracking, audience analysis, and adaptive timer control.
Main integration point for AI-driven timing system.
"""

from PyQt6.QtCore import QObject, pyqtSignal
import logging
from typing import Optional

from .presenter_tracker import PresenterTracker
from .voice_activity_detector import VoiceActivityDetector
from .engagement_analyzer import EngagementAnalyzer
from .adaptive_timer_controller import AdaptiveTimerController
from modules.face_ai.face_ai_controller import FaceAIController
from modules.timer.timer_controller import TimerController

logger = logging.getLogger(__name__)


class AIIntegrationController(QObject):
    """
    Main controller that integrates all AI components for adaptive timing.
    
    Features:
    - Coordinates presenter tracking (video + voice)
    - Coordinates audience analysis
    - Manages adaptive timer
    - Provides unified signals and state
    """
    
    # Unified signals
    presenter_state_changed = pyqtSignal(str)  # Emits: "talking", "engaged", "away", "disengaged"
    audience_engagement_changed = pyqtSignal(str)  # Emits: "high", "medium", "low"
    timer_adaptation_changed = pyqtSignal(str)  # Emits: "normal", "paused_ai", "slowed_ai", "extended", "reduced"
    extension_requested = pyqtSignal(int)  # Requests operator confirmation
    reduction_requested = pyqtSignal(int)  # Requests operator confirmation
    
    def __init__(self, base_timer_controller: Optional[TimerController] = None):
        """
        Initialize AI integration controller.
        
        Args:
            base_timer_controller: Base timer controller (creates new if None)
        """
        super().__init__()
        
        # Base timer
        if base_timer_controller:
            self._base_timer = base_timer_controller
        else:
            self._base_timer = TimerController()
        
        # AI components
        self._presenter_tracker = PresenterTracker()
        self._voice_detector = VoiceActivityDetector()
        self._audience_analyzer = FaceAIController()  # Reuse existing audience controller
        self._engagement_analyzer = EngagementAnalyzer()
        self._adaptive_timer = AdaptiveTimerController(self._base_timer)
        
        # State
        self._is_active = False
        self._presenter_camera_index = 0
        self._audience_camera_index = 0
        
        # Setup signal connections
        self._setup_connections()
    
    def _setup_connections(self):
        """Setup signal connections between components."""
        # Presenter tracker signals
        self._presenter_tracker.presenter_talking.connect(self._on_presenter_talking)
        self._presenter_tracker.presenter_engaged.connect(self._on_presenter_engaged)
        self._presenter_tracker.presenter_away.connect(self._on_presenter_away)
        self._presenter_tracker.presenter_disengaged.connect(self._on_presenter_disengaged)
        self._presenter_tracker.presenter_state_changed.connect(self._on_presenter_state_changed)
        
        # Voice detector signals
        self._voice_detector.presenter_speaking.connect(self._on_presenter_speaking)
        self._voice_detector.presenter_silent.connect(self._on_presenter_silent)
        
        # Audience analyzer signals
        self._audience_analyzer.attention_level_changed.connect(self._on_audience_attention_changed)
        self._audience_analyzer.statistics_updated.connect(self._on_audience_statistics_updated)
        
        # Engagement analyzer signals
        self._engagement_analyzer.engagement_level_changed.connect(self._on_engagement_level_changed)
        
        # Adaptive timer signals
        self._adaptive_timer.extension_requested.connect(self._on_extension_requested)
        self._adaptive_timer.reduction_requested.connect(self._on_reduction_requested)
        self._adaptive_timer.adaptation_changed.connect(self._on_adaptation_changed)
    
    def start_ai_timing(self, presenter_camera: int = 0, audience_camera: int = 0, 
                        enable_voice: bool = True):
        """
        Start AI-driven timing system.
        
        Args:
            presenter_camera: Camera index for presenter tracking
            audience_camera: Camera index for audience analysis
            enable_voice: Enable voice activity detection
            
        Returns:
            True if started successfully
        """
        if self._is_active:
            logger.warning("AI timing already active")
            return False
        
        try:
            # Start presenter tracking
            if not self._presenter_tracker.start_tracking(presenter_camera):
                logger.error("Failed to start presenter tracking")
                return False
            
            self._presenter_camera_index = presenter_camera
            
            # Start voice detection (optional)
            if enable_voice:
                if not self._voice_detector.start_detection():
                    logger.warning("Voice detection failed, continuing without it")
            
            # Start audience analysis
            if not self._audience_analyzer.start_analysis(audience_camera):
                logger.error("Failed to start audience analysis")
                self._presenter_tracker.stop_tracking()
                return False
            
            self._audience_camera_index = audience_camera
            self._is_active = True
            
            logger.info("AI-driven timing system started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting AI timing: {e}")
            self.stop_ai_timing()
            return False
    
    def stop_ai_timing(self):
        """Stop AI-driven timing system."""
        if not self._is_active:
            return
        
        self._is_active = False
        
        self._presenter_tracker.stop_tracking()
        self._voice_detector.stop_detection()
        self._audience_analyzer.stop_analysis()
        
        logger.info("AI-driven timing system stopped")
    
    def _on_presenter_talking(self):
        """Handle presenter talking signal."""
        self._adaptive_timer.set_presenter_active(True, "Talking")
        self.presenter_state_changed.emit("talking")
    
    def _on_presenter_engaged(self):
        """Handle presenter engaged signal."""
        self._adaptive_timer.set_presenter_active(True, "Engaged")
        self.presenter_state_changed.emit("engaged")
    
    def _on_presenter_away(self):
        """Handle presenter away signal."""
        self._adaptive_timer.set_presenter_active(False, "Away")
        self.presenter_state_changed.emit("away")
    
    def _on_presenter_disengaged(self):
        """Handle presenter disengaged signal."""
        self._adaptive_timer.set_presenter_active(False, "Disengaged")
        self.presenter_state_changed.emit("disengaged")
    
    def _on_presenter_state_changed(self, state: str):
        """Handle presenter state change."""
        # Combined with voice activity for better detection
        if state in ["talking", "engaged"]:
            self._adaptive_timer.set_presenter_active(True, f"State: {state}")
        else:
            self._adaptive_timer.set_presenter_active(False, f"State: {state}")
    
    def _on_presenter_speaking(self):
        """Handle voice activity detected."""
        # Voice speaking confirms presenter is active
        self._adaptive_timer.set_presenter_active(True, "Voice detected")
    
    def _on_presenter_silent(self, seconds: int):
        """Handle silence detected."""
        # Long silence might indicate disengagement
        if seconds >= 5:  # 5+ seconds of silence
            # Don't immediately set inactive, but reduce confidence
            pass  # Could implement a confidence score
    
    def _on_audience_attention_changed(self, attention: float):
        """Handle audience attention level change."""
        # Pass to engagement analyzer
        # Get emotion counts from statistics (will come via statistics_updated)
        pass
    
    def _on_audience_statistics_updated(self, statistics: dict):
        """Handle audience statistics update."""
        # Extract attention and emotions
        attention = statistics.get('average_attention', 0.0)
        emotion_counts = statistics.get('emotion_counts', {})
        face_count = statistics.get('total_faces', 0)
        
        # Update engagement analyzer
        self._engagement_analyzer.analyze_frame(attention, emotion_counts, face_count)
    
    def _on_engagement_level_changed(self, level: str):
        """Handle engagement level change."""
        self._adaptive_timer.set_audience_engagement(level)
        self.audience_engagement_changed.emit(level)
    
    def _on_adaptation_changed(self, mode: str):
        """Handle timer adaptation change."""
        self.timer_adaptation_changed.emit(mode)
    
    def _on_extension_requested(self, seconds: int):
        """Handle extension request."""
        self.extension_requested.emit(seconds)
    
    def _on_reduction_requested(self, seconds: int):
        """Handle reduction request."""
        self.reduction_requested.emit(seconds)
    
    def confirm_extension(self, seconds: int):
        """Confirm and apply timer extension."""
        self._adaptive_timer.extend_timer(seconds, confirmed=True)
    
    def reject_extension(self, seconds: int):
        """Reject timer extension request."""
        pass  # Just don't apply
    
    def confirm_reduction(self, seconds: int):
        """Confirm and apply timer reduction."""
        self._adaptive_timer.reduce_timer(seconds, confirmed=True)
    
    def reject_reduction(self, seconds: int):
        """Reject timer reduction request."""
        pass  # Just don't apply
    
    def override_ai_adaptation(self):
        """Override AI adaptation (operator control)."""
        self._adaptive_timer.override_adaptation()
    
    def get_presenter_state(self) -> str:
        """Get current presenter state."""
        return self._presenter_tracker.get_current_state()
    
    def get_audience_engagement(self) -> str:
        """Get current audience engagement level."""
        return self._engagement_analyzer.get_current_level()
    
    def get_timer_adaptation_mode(self) -> str:
        """Get current timer adaptation mode."""
        return self._adaptive_timer.get_adaptation_mode()
    
    def get_base_timer(self) -> TimerController:
        """Get base timer controller."""
        return self._base_timer
    
    def get_adaptive_timer(self) -> AdaptiveTimerController:
        """Get adaptive timer controller."""
        return self._adaptive_timer
    
    def configure(self, **kwargs):
        """Configure AI timing system."""
        # Forward to adaptive timer
        if 'adaptive_timer' in kwargs:
            self._adaptive_timer.configure(**kwargs['adaptive_timer'])
        
        # Configure presenter tracker
        if 'presenter_tracker' in kwargs:
            pt_config = kwargs['presenter_tracker']
            if 'engagement_threshold' in pt_config:
                self._presenter_tracker.set_engagement_threshold(pt_config['engagement_threshold'])
            if 'orientation_threshold' in pt_config:
                self._presenter_tracker.set_orientation_threshold(pt_config['orientation_threshold'])
        
        # Configure voice detector
        if 'voice_detector' in kwargs:
            vd_config = kwargs['voice_detector']
            if 'silence_threshold' in vd_config:
                self._voice_detector.set_silence_threshold(vd_config['silence_threshold'])
            if 'energy_threshold' in vd_config:
                self._voice_detector.set_energy_threshold(vd_config['energy_threshold'])
        
        # Configure engagement analyzer
        if 'engagement_analyzer' in kwargs:
            ea_config = kwargs['engagement_analyzer']
            if 'high_threshold' in ea_config:
                self._engagement_analyzer.set_high_threshold(ea_config['high_threshold'])
            if 'medium_threshold' in ea_config:
                self._engagement_analyzer.set_medium_threshold(ea_config['medium_threshold'])
    
    def is_active(self) -> bool:
        """Check if AI timing is active."""
        return self._is_active

