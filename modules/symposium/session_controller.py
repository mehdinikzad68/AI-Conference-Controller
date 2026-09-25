"""
Session Controller Module

Controls session lifecycle, timer synchronization, and media playback for symposium.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Optional
from pathlib import Path

from .agenda_manager import AgendaItem
from modules.timer.timer_controller import TimerController


class SessionController(QObject):
    """
    Controls individual session lifecycle and timing.
    
    Features:
    - Session start/end management
    - Timer synchronization with session duration
    - Media file detection and loading
    - Auto-transition handling
    - Warning threshold management
    """
    
    # Signals
    session_started = pyqtSignal(str)  # Emits session_id
    session_ended = pyqtSignal(str)  # Emits session_id
    media_found = pyqtSignal(str)  # Emits media_path
    media_not_found = pyqtSignal()  # No media available
    warning_threshold_reached = pyqtSignal()  # 20% time remaining
    
    def __init__(self, timer_controller: Optional[TimerController] = None):
        """
        Initialize session controller.
        
        Args:
            timer_controller: TimerController instance (creates new if None)
        """
        super().__init__()
        
        if timer_controller:
            self._timer_controller = timer_controller
        else:
            self._timer_controller = TimerController()
        
        self._current_session: Optional[AgendaItem] = None
        self._session_running = False
        self._warning_threshold_pct = 0.20  # 20%
        self._warning_emitted = False
        
        # Connect timer signals
        self._timer_controller.time_changed.connect(self._on_timer_changed)
        self._timer_controller.timer_finished.connect(self._on_timer_finished)
    
    def get_timer_controller(self) -> TimerController:
        """Get timer controller."""
        return self._timer_controller
    
    def start_session(self, session: AgendaItem) -> bool:
        """
        Start a session.
        
        Args:
            session: AgendaItem to start
            
        Returns:
            True if started successfully
        """
        if self._session_running:
            self.end_session()
        
        self._current_session = session
        self._session_running = True
        self._warning_emitted = False
        
        # Set timer duration
        duration_seconds = session.speaker.duration_minutes * 60
        self._timer_controller.set_time(duration_seconds)
        
        # Check for media file
        media_path = session.speaker.media_path
        if media_path and Path(media_path).exists():
            self.media_found.emit(media_path)
        else:
            self.media_not_found.emit()
        
        # Start timer
        self._timer_controller.start()
        
        # Emit session started
        self.session_started.emit(session.session_id)
        
        return True
    
    def end_session(self):
        """End current session."""
        if not self._session_running:
            return
        
        session_id = self._current_session.session_id if self._current_session else ""
        
        # Stop timer
        self._timer_controller.stop()
        
        self._session_running = False
        self._current_session = None
        self._warning_emitted = False
        
        # Emit session ended
        if session_id:
            self.session_ended.emit(session_id)
    
    def pause_session(self):
        """Pause current session."""
        if self._session_running:
            self._timer_controller.pause()
    
    def resume_session(self):
        """Resume current session."""
        if self._session_running:
            self._timer_controller.resume()
    
    def get_current_session(self) -> Optional[AgendaItem]:
        """Get current session."""
        return self._current_session
    
    def is_session_running(self) -> bool:
        """Check if session is running."""
        return self._session_running
    
    def _on_timer_changed(self, seconds: int):
        """Handle timer time change."""
        if not self._current_session or not self._session_running:
            return
        
        initial_time = self._timer_controller.get_initial_time()
        if initial_time > 0:
            progress = seconds / initial_time
            
            # Check for 20% warning threshold
            if progress <= self._warning_threshold_pct and not self._warning_emitted:
                self._warning_emitted = True
                self.warning_threshold_reached.emit()
    
    def _on_timer_finished(self):
        """Handle timer finished."""
        # Auto-end session when timer finishes
        if self._session_running:
            self.end_session()
    
    def set_warning_threshold(self, percentage: float):
        """
        Set warning threshold percentage.
        
        Args:
            percentage: Warning threshold (0.0 to 1.0), default 0.20 (20%)
        """
        self._warning_threshold_pct = max(0.0, min(1.0, percentage))

