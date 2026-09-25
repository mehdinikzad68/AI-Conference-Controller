"""
Adaptive Timer Controller Module

Timer that adapts in real-time based on AI-driven presenter and audience engagement.
Pauses/slows when engagement drops, extends when engagement is high.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging
from typing import Optional
from enum import Enum
from datetime import datetime

from modules.timer.timer_controller import TimerController

logger = logging.getLogger(__name__)


class TimerAdaptationMode(Enum):
    """Timer adaptation modes."""
    NORMAL = "normal"  # Standard countdown
    PAUSED_AI = "paused_ai"  # Paused due to low engagement
    SLOWED_AI = "slowed_ai"  # Slowed due to low engagement
    EXTENDED = "extended"  # Extended due to high engagement
    REDUCED = "reduced"  # Reduced due to low engagement


class AdaptiveTimerController(QObject):
    """
    Adaptive timer controller that responds to AI engagement signals.
    
    Features:
    - Pauses/slows timer when engagement drops
    - Extends timer when engagement is high (with confirmation)
    - Logs all AI-driven adjustments
    - Operator override support
    """
    
    # Signals
    timer_paused_ai = pyqtSignal(str)  # Emits reason for pause
    timer_slowed_ai = pyqtSignal(float)  # Emits slow factor (0.0-1.0)
    timer_extended = pyqtSignal(int)  # Emits extension seconds (requires confirmation)
    timer_reduced = pyqtSignal(int)  # Emits reduction seconds (requires confirmation)
    extension_requested = pyqtSignal(int)  # Requests operator confirmation for extension
    reduction_requested = pyqtSignal(int)  # Requests operator confirmation for reduction
    adaptation_changed = pyqtSignal(str)  # Emits adaptation mode
    ai_adjustment_logged = pyqtSignal(str)  # Emits log message for UI
    
    def __init__(self, base_timer_controller: TimerController):
        """
        Initialize adaptive timer controller.
        
        Args:
            base_timer_controller: Base TimerController instance to wrap
        """
        super().__init__()
        
        self._base_timer = base_timer_controller
        
        # AI state
        self._presenter_active = True  # Default to active
        self._audience_engagement = "medium"  # Default to medium
        self._adaptation_mode = TimerAdaptationMode.NORMAL
        
        # Configuration
        self._pause_on_low_engagement = True
        self._slow_on_low_engagement = False  # Alternative to pause
        self._slow_factor = 0.5  # If slowing, reduce speed by this factor
        self._allow_extensions = True
        self._allow_reductions = False  # Usually not allowed by default
        self._max_extension_percent = 10  # Max 10% extension
        self._extension_confirmation_required = True
        
        # Timer adjustment
        self._original_time = 0
        self._extended_time = 0
        self._slow_timer = None
        self._slow_counter = 0  # Count ticks for slow mode
        
        # Engagement history for extension decisions
        self._high_engagement_duration = 0  # Seconds of continuous high engagement
        self._low_engagement_duration = 0  # Seconds of continuous low engagement
        self._last_engagement_check = datetime.now()
        
        # Logging
        self._adjustment_log = []
        
        # Setup slow timer if using slow mode
        self._setup_slow_timer()
    
    def _setup_slow_timer(self):
        """Setup timer for slow mode (counts slower)."""
        self._slow_timer = QTimer()
        self._slow_timer.timeout.connect(self._slow_tick)
        # Will be started/stopped as needed
    
    def set_presenter_active(self, active: bool, reason: str = ""):
        """
        Update presenter activity state.
        
        Args:
            active: True if presenter is talking/engaged
            reason: Reason for state change (for logging)
        """
        self._presenter_active = active
        
        if not active and reason:
            self._log_adjustment(f"Presenter inactive: {reason}")
        
        self._update_adaptation()
    
    def set_audience_engagement(self, level: str):
        """
        Update audience engagement level.
        
        Args:
            level: "high", "medium", or "low"
        """
        old_level = self._audience_engagement
        self._audience_engagement = level
        
        # Track duration of engagement levels
        now = datetime.now()
        if old_level != level:
            elapsed = (now - self._last_engagement_check).total_seconds()
            
            if old_level == "high":
                self._high_engagement_duration += elapsed
            elif old_level == "low":
                self._low_engagement_duration += elapsed
            
            self._high_engagement_duration = 0 if level != "high" else self._high_engagement_duration
            self._low_engagement_duration = 0 if level != "low" else self._low_engagement_duration
            
            self._last_engagement_check = now
        
        self._update_adaptation()
    
    def _update_adaptation(self):
        """Update timer adaptation based on current AI state."""
        # Determine if timer should run
        should_run = True
        reason = ""
        
        # Check conditions for pausing/slowing
        if self._pause_on_low_engagement or self._slow_on_low_engagement:
            if not self._presenter_active:
                should_run = False
                reason = "Presenter inactive"
            elif self._audience_engagement == "low":
                should_run = False
                reason = "Low audience engagement"
        
        # Apply adaptation
        if not should_run:
            if self._pause_on_low_engagement:
                if self._adaptation_mode != TimerAdaptationMode.PAUSED_AI:
                    self._pause_timer(reason)
            elif self._slow_on_low_engagement:
                if self._adaptation_mode != TimerAdaptationMode.SLOWED_AI:
                    self._slow_timer_reason(reason)
        else:
            # Resume normal operation if paused/slowed
            if self._adaptation_mode in [TimerAdaptationMode.PAUSED_AI, TimerAdaptationMode.SLOWED_AI]:
                self._resume_normal()
            
            # Check for extension opportunity
            if self._allow_extensions and self._audience_engagement == "high" and self._presenter_active:
                self._consider_extension()
            
            # Check for reduction (if allowed)
            if self._allow_reductions and self._audience_engagement == "low" and not self._presenter_active:
                self._consider_reduction()
    
    def _pause_timer(self, reason: str):
        """Pause timer due to AI detection."""
        if self._base_timer.is_running() and not self._base_timer.is_paused():
            self._base_timer.pause()
            self._adaptation_mode = TimerAdaptationMode.PAUSED_AI
            self.timer_paused_ai.emit(reason)
            self.adaptation_changed.emit("paused_ai")
            self._log_adjustment(f"Timer paused: {reason}")
    
    def _slow_timer_reason(self, reason: str):
        """Slow timer due to AI detection."""
        if self._base_timer.is_running() and not self._base_timer.is_paused():
            self._adaptation_mode = TimerAdaptationMode.SLOWED_AI
            self._slow_counter = 0
            self._slow_timer.start(int(1000 / self._slow_factor))  # Slower interval
            self.timer_slowed_ai.emit(self._slow_factor)
            self.adaptation_changed.emit("slowed_ai")
            self._log_adjustment(f"Timer slowed ({self._slow_factor}x): {reason}")
    
    def _slow_tick(self):
        """Handle slow mode tick (only counts every Nth tick)."""
        if self._adaptation_mode == TimerAdaptationMode.SLOWED_AI:
            self._slow_counter += 1
            # Only tick base timer every 1/slow_factor ticks
            if self._slow_counter >= int(1 / self._slow_factor):
                # Manually decrement base timer
                current = self._base_timer.get_current_time()
                if current > 0:
                    self._base_timer.set_time(current - 1)
                    self._base_timer.time_changed.emit(current - 1)
                self._slow_counter = 0
        else:
            self._slow_timer.stop()
    
    def _resume_normal(self):
        """Resume normal timer operation."""
        if self._adaptation_mode == TimerAdaptationMode.PAUSED_AI:
            if self._base_timer.is_paused():
                self._base_timer.resume()
        elif self._adaptation_mode == TimerAdaptationMode.SLOWED_AI:
            self._slow_timer.stop()
        
        self._adaptation_mode = TimerAdaptationMode.NORMAL
        self.adaptation_changed.emit("normal")
        self._log_adjustment("Timer resumed to normal operation")
    
    def _consider_extension(self):
        """Consider extending timer based on high engagement duration."""
        # Only consider if high engagement sustained
        if self._high_engagement_duration >= 60:  # 1 minute of high engagement
            max_extension = int(self._base_timer.get_initial_time() * (self._max_extension_percent / 100))
            
            if max_extension > 0:
                if self._extension_confirmation_required:
                    # Request operator confirmation
                    self.extension_requested.emit(max_extension)
                else:
                    # Auto-extend
                    self.extend_timer(max_extension)
    
    def _consider_reduction(self):
        """Consider reducing timer based on low engagement duration."""
        # Only consider if low engagement sustained for extended period
        if self._allow_reductions and self._low_engagement_duration >= 120:  # 2 minutes
            max_reduction = int(self._base_timer.get_initial_time() * 0.1)  # 10% max
            
            if max_reduction > 0:
                self.reduction_requested.emit(max_reduction)
    
    def extend_timer(self, seconds: int, confirmed: bool = True):
        """
        Extend timer by specified seconds.
        
        Args:
            seconds: Seconds to extend
            confirmed: If True, apply extension (operator confirmed)
        """
        if not confirmed:
            return
        
        current = self._base_timer.get_current_time()
        new_time = current + seconds
        
        # Don't exceed max extension
        max_allowed = self._base_timer.get_initial_time() * (1 + self._max_extension_percent / 100)
        new_time = min(new_time, int(max_allowed))
        
        extension = new_time - current
        if extension > 0:
            self._base_timer.set_time(new_time)
            self._adaptation_mode = TimerAdaptationMode.EXTENDED
            self.adaptation_changed.emit("extended")
            self.timer_extended.emit(extension)
            self._log_adjustment(f"Timer extended by {extension} seconds (AI-driven)")
    
    def reduce_timer(self, seconds: int, confirmed: bool = True):
        """
        Reduce timer by specified seconds.
        
        Args:
            seconds: Seconds to reduce
            confirmed: If True, apply reduction (operator confirmed)
        """
        if not confirmed:
            return
        
        current = self._base_timer.get_current_time()
        new_time = max(0, current - seconds)
        
        reduction = current - new_time
        if reduction > 0:
            self._base_timer.set_time(new_time)
            self._adaptation_mode = TimerAdaptationMode.REDUCED
            self.adaptation_changed.emit("reduced")
            self.timer_reduced.emit(reduction)
            self._log_adjustment(f"Timer reduced by {reduction} seconds (AI-driven)")
    
    def override_adaptation(self):
        """Override AI adaptation and return to normal operation."""
        self._resume_normal()
        self._log_adjustment("Operator override: AI adaptation disabled")
    
    def _log_adjustment(self, message: str):
        """Log AI-driven adjustment."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._adjustment_log.append(log_entry)
        
        # Keep log size manageable
        if len(self._adjustment_log) > 100:
            self._adjustment_log.pop(0)
        
        self.ai_adjustment_logged.emit(log_entry)
        logger.info(log_entry)
    
    def get_adjustment_log(self) -> list:
        """Get all adjustment log entries."""
        return self._adjustment_log.copy()
    
    def get_adaptation_mode(self) -> str:
        """Get current adaptation mode."""
        return self._adaptation_mode.value
    
    def get_base_timer(self) -> TimerController:
        """Get underlying base timer controller."""
        return self._base_timer
    
    def configure(self, **kwargs):
        """
        Configure adaptive timer settings.
        
        Args:
            pause_on_low_engagement: Pause timer when engagement is low
            slow_on_low_engagement: Slow timer when engagement is low
            slow_factor: Slow factor (0.0-1.0)
            allow_extensions: Allow AI-driven extensions
            allow_reductions: Allow AI-driven reductions
            max_extension_percent: Maximum extension percentage
            extension_confirmation_required: Require confirmation for extensions
        """
        if 'pause_on_low_engagement' in kwargs:
            self._pause_on_low_engagement = kwargs['pause_on_low_engagement']
        if 'slow_on_low_engagement' in kwargs:
            self._slow_on_low_engagement = kwargs['slow_on_low_engagement']
        if 'slow_factor' in kwargs:
            self._slow_factor = max(0.1, min(1.0, kwargs['slow_factor']))
        if 'allow_extensions' in kwargs:
            self._allow_extensions = kwargs['allow_extensions']
        if 'allow_reductions' in kwargs:
            self._allow_reductions = kwargs['allow_reductions']
        if 'max_extension_percent' in kwargs:
            self._max_extension_percent = max(0, min(50, kwargs['max_extension_percent']))
        if 'extension_confirmation_required' in kwargs:
            self._extension_confirmation_required = kwargs['extension_confirmation_required']

