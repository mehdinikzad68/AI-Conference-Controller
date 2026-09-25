"""
Unit Tests for Timer Controller

Tests all functionality of the TimerController class.
"""

import pytest
from PyQt6.QtCore import QTimer, QEventLoop
from modules.timer.timer_controller import TimerController


class TestTimerController:
    """Test suite for TimerController."""
    
    @pytest.fixture
    def timer(self, qapp):
        """Create a timer controller instance."""
        return TimerController()
    
    def test_initialization(self, timer):
        """Test timer initializes correctly."""
        assert not timer.is_running()
        assert not timer.is_paused()
        assert timer.get_current_time() == 0
        assert timer.get_initial_time() == 0
    
    def test_set_time(self, timer):
        """Test setting timer duration."""
        timer.set_time(300)
        assert timer.get_current_time() == 300
        assert timer.get_initial_time() == 300
    
    def test_set_time_negative(self, timer):
        """Test that negative time is rejected."""
        timer.set_time(-100)
        assert timer.get_current_time() == 0
    
    def test_start_timer(self, timer):
        """Test starting the timer."""
        timer.set_time(60)
        timer.start()
        assert timer.is_running()
        assert not timer.is_paused()
    
    def test_start_without_time(self, timer):
        """Test that timer doesn't start without time set."""
        timer.start()
        assert not timer.is_running()
    
    def test_pause_timer(self, timer):
        """Test pausing the timer."""
        timer.set_time(60)
        timer.start()
        timer.pause()
        assert not timer.is_running()
        assert timer.is_paused()
    
    def test_resume_timer(self, timer):
        """Test resuming the timer."""
        timer.set_time(60)
        timer.start()
        timer.pause()
        timer.resume()
        assert timer.is_running()
        assert not timer.is_paused()
    
    def test_stop_timer(self, timer):
        """Test stopping the timer."""
        timer.set_time(60)
        timer.start()
        timer.stop()
        assert not timer.is_running()
        assert not timer.is_paused()
    
    def test_reset_timer(self, timer):
        """Test resetting the timer."""
        timer.set_time(60)
        timer.start()
        # Simulate some time passing
        timer._current_time = 30
        timer.reset()
        assert timer.get_current_time() == 60
        assert not timer.is_running()
    
    def test_countdown_mode(self, timer):
        """Test countdown mode."""
        timer.set_mode("countdown")
        timer.set_time(5)
        timer.start()
        # Manually trigger update
        timer._update_time()
        assert timer.get_current_time() == 4
    
    def test_countup_mode(self, timer):
        """Test count-up mode."""
        timer.set_mode("countup")
        timer.set_time(0)
        timer._current_time = 0
        timer.start()
        timer._update_time()
        assert timer.get_current_time() == 1
    
    def test_get_progress(self, timer):
        """Test progress calculation."""
        timer.set_time(100)
        assert timer.get_progress() == 1.0  # 100%
        timer._current_time = 50
        assert timer.get_progress() == 0.5  # 50%
        timer._current_time = 0
        assert timer.get_progress() == 0.0  # 0%
    
    def test_get_progress_zero_initial(self, timer):
        """Test progress with zero initial time."""
        timer.set_time(0)
        assert timer.get_progress() == 0.0
    
    def test_warning_threshold_signal(self, timer, qtbot):
        """Test warning signal is emitted at 20%."""
        timer.set_time(100)
        timer.start()
        
        with qtbot.waitSignal(timer.warning_threshold, timeout=100):
            timer._current_time = 20
            timer._update_time()
    
    def test_timer_finished_signal(self, timer, qtbot):
        """Test finished signal is emitted."""
        timer.set_time(1)
        timer.start()
        
        with qtbot.waitSignal(timer.timer_finished, timeout=100):
            timer._current_time = 1
            timer._update_time()
    
    def test_time_changed_signal(self, timer, qtbot):
        """Test time changed signal is emitted."""
        timer.set_time(60)
        
        with qtbot.waitSignal(timer.time_changed, timeout=100):
            timer.set_time(120)
    
    def test_cannot_set_time_while_running(self, timer):
        """Test that time cannot be changed while timer is running."""
        timer.set_time(60)
        timer.start()
        initial_time = timer.get_initial_time()
        timer.set_time(120)
        assert timer.get_initial_time() == initial_time
    
    def test_mode_validation(self, timer):
        """Test that invalid modes are rejected."""
        timer.set_mode("invalid_mode")
        # Mode should remain at default
        timer.set_time(10)
        timer.start()
        timer._update_time()
        assert timer.get_current_time() == 9  # Countdown (default)
    
    def test_multiple_pause_resume_cycles(self, timer):
        """Test multiple pause/resume cycles."""
        timer.set_time(60)
        timer.start()
        assert timer.is_running()
        
        timer.pause()
        assert timer.is_paused()
        
        timer.resume()
        assert timer.is_running()
        
        timer.pause()
        assert timer.is_paused()
    
    def test_edge_case_timer_at_zero(self, timer):
        """Test timer behavior when reaching zero."""
        timer.set_time(1)
        timer.start()
        timer._current_time = 1
        timer._update_time()
        assert timer.get_current_time() == 0
        assert not timer.is_running()

