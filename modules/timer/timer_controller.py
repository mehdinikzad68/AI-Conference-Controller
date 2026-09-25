"""
Timer Controller Module

Provides smart graphical timer functionality with visual feedback.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from typing import Literal


class TimerController(QObject):
    """
    Controller for the smart graphical timer module.
    
    Manages timer state, countdown/countup functionality, and visual updates.
    """
    
    # Signals for timer events
    timer_started = pyqtSignal()
    timer_stopped = pyqtSignal()
    timer_paused = pyqtSignal()
    timer_resumed = pyqtSignal()
    timer_reset = pyqtSignal()
    time_changed = pyqtSignal(int)  # Emits remaining/elapsed time in seconds
    timer_finished = pyqtSignal()  # Emits when countdown reaches zero
    warning_threshold = pyqtSignal()  # Emits when < 2 minutes remaining
    
    def __init__(self):
        """Initialize the timer controller."""
        super().__init__()
        self._is_running = False
        self._is_paused = False
        self._current_time = 0
        self._initial_time = 0
        self._mode = "countdown"  # "countdown" or "countup"
        
        # QTimer for updating every second
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_time)
        self._update_timer.setInterval(1000)  # Update every second
        
        # Track if warning has been emitted
        self._warning_emitted = False
        
    def start(self) -> None:
        """Start the timer."""
        if not self._is_running and self._current_time > 0:
            self._is_running = True
            self._is_paused = False
            self._warning_emitted = False
            self._update_timer.start()
            self.timer_started.emit()
    
    def pause(self) -> None:
        """Pause the timer."""
        if self._is_running:
            self._is_running = False
            self._is_paused = True
            self._update_timer.stop()
            self.timer_paused.emit()
    
    def resume(self) -> None:
        """Resume the timer."""
        if self._is_paused and self._current_time > 0:
            self._is_running = True
            self._is_paused = False
            self._update_timer.start()
            self.timer_resumed.emit()
    
    def stop(self) -> None:
        """Stop the timer."""
        if self._is_running or self._is_paused:
            self._is_running = False
            self._is_paused = False
            self._update_timer.stop()
            self.timer_stopped.emit()
    
    def reset(self) -> None:
        """Reset the timer to initial state."""
        self.stop()
        self._current_time = self._initial_time
        self._warning_emitted = False
        self.time_changed.emit(self._current_time)
        self.timer_reset.emit()
    
    def set_time(self, seconds: int) -> None:
        """Set the timer value in seconds."""
        if not self._is_running:
            self._initial_time = max(0, seconds)
            self._current_time = self._initial_time
            self._warning_emitted = False
            self.time_changed.emit(self._current_time)
    
    def set_mode(self, mode: Literal["countdown", "countup"]) -> None:
        """
        Set timer mode.
        
        Args:
            mode: Either "countdown" or "countup"
        """
        if mode in ["countdown", "countup"]:
            self._mode = mode
    
    def _update_time(self) -> None:
        """Internal method to update timer every second."""
        if self._mode == "countdown":
            if self._current_time > 0:
                self._current_time -= 1
                self.time_changed.emit(self._current_time)
                
                # Check for warning threshold (last 20% of time)
                if self._initial_time > 0:
                    percent_remaining = (self._current_time / self._initial_time) * 100
                    if percent_remaining <= 20 and percent_remaining > 0 and not self._warning_emitted:
                        self._warning_emitted = True
                        self.warning_threshold.emit()
                
                # Check if timer finished
                if self._current_time == 0:
                    self.stop()
                    self.timer_finished.emit()
            else:
                self.stop()
                self.timer_finished.emit()
        else:  # countup mode
            self._current_time += 1
            self.time_changed.emit(self._current_time)
    
    def get_current_time(self) -> int:
        """Get current timer value in seconds."""
        return self._current_time
    
    def get_initial_time(self) -> int:
        """Get initial timer value in seconds."""
        return self._initial_time
    
    def get_progress(self) -> float:
        """
        Get timer progress as a percentage (0.0 to 1.0).
        
        Returns:
            Progress percentage (1.0 = started, 0.0 = finished)
        """
        if self._initial_time == 0:
            return 0.0
        return self._current_time / self._initial_time
    
    def is_running(self) -> bool:
        """Check if timer is currently running."""
        return self._is_running
    
    def is_paused(self) -> bool:
        """Check if timer is currently paused."""
        return self._is_paused

