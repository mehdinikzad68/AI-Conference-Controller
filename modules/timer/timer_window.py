"""Timer window module with multi-timer support and responsive scrolling."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QSpinBox, QLabel, QGroupBox,
    QTabWidget, QMessageBox, QSizePolicy, QScrollArea, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtMultimedia import QMediaPlayer
from pathlib import Path
import sys
import os

from .timer_controller import TimerController
from .circular_timer_widget import CircularTimerWidget
from .ai_timer_widget import AITimerWidget
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from modules.ai_timing import AIIntegrationController
from PyQt6.QtGui import QWheelEvent
import logging

logger = logging.getLogger(__name__)


class TimerWindow(QMainWindow):
    """
    Main timer window with animated circular timer, controls, and multi-timer support.
    
    Features:
    - Large animated circular countdown timer
    - Time input controls (slider and spin box)
    - Start/Pause/Resume/Reset buttons
    - Fullscreen support
    - Multi-timer tab interface
    - Visual and audio alerts
    - OBS Studio optimized design
    - Responsive layout with mouse wheel scrolling
    """
    
    def __init__(self, parent=None):
        """Initialize the timer window."""
        super().__init__(parent)
        
        # Multi-timer support
        self._timers = []  # List of (controller, widget) tuples
        self._current_tab_index = 0
        
        # AI Timer support
        self._ai_controllers = {}  # Dict mapping timer index to AI controller
        
        # Audio alert paths
        self._assets_path = Path(__file__).parent.parent.parent / "assets"
        self._assets_path.mkdir(exist_ok=True)
        self._warning_sound_path = self._assets_path / "warning_beep.wav"
        self._finished_sound_path = self._assets_path / "finished_beep.wav"
        
        # Generate sounds if they don't exist
        self._ensure_sound_files()
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller - Smart Timer")
        self.setMinimumSize(750, 600)
        self.resize(1000, 750)
        
        # Make window responsive
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(size_policy)
        
        # Apply system theme
        self.apply_theme()
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
        
    def _ensure_sound_files(self):
        """Ensure alert sound files exist, generate them if missing."""
        try:
            from modules.timer.generate_sounds import generate_sounds
            if not self._warning_sound_path.exists() or not self._finished_sound_path.exists():
                generate_sounds()
        except Exception as e:
            # Silently fail - sounds are optional
            print(f"Note: Could not generate sound files: {e}")
            print("Timer will work without audio alerts. Run 'python modules/timer/generate_sounds.py' to create sounds.")
    
    def init_ui(self):
        """Initialize the user interface with scrollable support."""
        # Create scrollable area for responsive layout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        content_widget = QWidget()
        make_responsive(content_widget)
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Tab widget for multi-timer support
        self.tab_widget = QTabWidget()
        make_responsive(self.tab_widget)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_timer_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)
        
        # Create first timer tab
        self.add_new_timer("Speaker 1")
        
        # Control buttons at bottom
        controls_layout = QHBoxLayout()
        
        # Add new timer button
        add_timer_btn = QPushButton("+ Add Timer")
        add_timer_btn.clicked.connect(self.add_new_timer_dialog)
        add_timer_btn.setToolTip("Add a new timer for another speaker or panel")
        controls_layout.addWidget(add_timer_btn)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        # Set content widget in scroll area
        scroll_area.setWidget(content_widget)
        self.setCentralWidget(scroll_area)
        
        # Menu bar
        self.setup_menu_bar()
    
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        from PyQt6.QtGui import QAction
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_timer_action = QAction("New Timer", self)
        new_timer_action.setShortcut("Ctrl+N")
        new_timer_action.triggered.connect(self.add_new_timer_dialog)
        file_menu.addAction(new_timer_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About Timer", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_new_timer_dialog(self):
        """Show dialog to add a new timer with custom name."""
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "New Timer",
            "Enter timer name (e.g., 'Speaker 2', 'Panel Discussion'):",
            text=f"Speaker {len(self._timers) + 1}"
        )
        if ok and name:
            self.add_new_timer(name.strip() or f"Timer {len(self._timers) + 1}")
    
    def add_new_timer(self, name: str):
        """
        Add a new timer tab.
        
        Args:
            name: Name for the timer tab
        """
        # Create controller and widget
        controller = TimerController()
        timer_widget = CircularTimerWidget()
        # Set responsive sizing
        from PyQt6.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(False)
        timer_widget.setSizePolicy(size_policy)
        
        # Create tab content widget (responsive)
        tab_widget = QWidget()
        make_responsive(tab_widget)
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(15)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # Circular timer display
        tab_layout.addWidget(timer_widget, stretch=3)
        
        # Time input controls
        time_group = QGroupBox("Set Session Time")
        time_layout = QVBoxLayout()
        
        # Slider and spin box layout
        input_layout = QHBoxLayout()
        
        minutes_label = QLabel("Minutes:")
        minutes_slider = QSlider(Qt.Orientation.Horizontal)
        minutes_slider.setMinimum(0)
        minutes_slider.setMaximum(120)
        minutes_slider.setValue(5)
        minutes_slider.setToolTip("Minutes")
        
        seconds_label = QLabel("Seconds:")
        seconds_slider = QSlider(Qt.Orientation.Horizontal)
        seconds_slider.setMinimum(0)
        seconds_slider.setMaximum(59)
        seconds_slider.setValue(0)
        seconds_slider.setToolTip("Seconds")
        
        total_label = QLabel("Total Time:")
        total_spinbox = QSpinBox()
        total_spinbox.setMinimum(0)
        total_spinbox.setMaximum(7200)  # 2 hours max
        total_spinbox.setSuffix(" seconds")
        total_spinbox.setValue(300)  # Default 5 minutes
        
        # Connect sliders and spin box
        def update_from_sliders():
            total = minutes_slider.value() * 60 + seconds_slider.value()
            total_spinbox.blockSignals(True)
            total_spinbox.setValue(total)
            total_spinbox.blockSignals(False)
            if not controller.is_running():
                controller.set_time(total)
                timer_widget.set_time(controller.get_current_time(), controller.get_initial_time())
        
        def update_from_spinbox():
            total = total_spinbox.value()
            minutes = total // 60
            seconds = total % 60
            minutes_slider.blockSignals(True)
            seconds_slider.blockSignals(True)
            minutes_slider.setValue(minutes)
            seconds_slider.setValue(seconds)
            minutes_slider.blockSignals(False)
            seconds_slider.blockSignals(False)
            if not controller.is_running():
                controller.set_time(total)
                timer_widget.set_time(controller.get_current_time(), controller.get_initial_time())
        
        minutes_slider.valueChanged.connect(update_from_sliders)
        seconds_slider.valueChanged.connect(update_from_sliders)
        total_spinbox.valueChanged.connect(update_from_spinbox)
        
        # Add to layout
        input_layout.addWidget(minutes_label)
        input_layout.addWidget(minutes_slider)
        input_layout.addWidget(seconds_label)
        input_layout.addWidget(seconds_slider)
        input_layout.addWidget(total_label)
        input_layout.addWidget(total_spinbox)
        
        time_layout.addLayout(input_layout)
        time_group.setLayout(time_layout)
        tab_layout.addWidget(time_group)
        
        # Control buttons
        buttons_group = QGroupBox("Timer Controls")
        buttons_layout = QHBoxLayout()
        
        # Store button references first (before connecting)
        timer_data = {
            'controller': controller,
            'widget': timer_widget,
            'start_btn': None,
            'pause_btn': None,
            'resume_btn': None,
            'reset_btn': None
        }
        
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda: self.on_timer_start(timer_data))
        start_btn.setToolTip("Start the timer")
        buttons_layout.addWidget(start_btn)
        timer_data['start_btn'] = start_btn
        
        pause_btn = QPushButton("Pause")
        pause_btn.clicked.connect(lambda: self.on_timer_pause(timer_data))
        pause_btn.setToolTip("Pause the timer")
        buttons_layout.addWidget(pause_btn)
        timer_data['pause_btn'] = pause_btn
        
        resume_btn = QPushButton("Resume")
        resume_btn.clicked.connect(lambda: self.on_timer_resume(timer_data))
        resume_btn.setToolTip("Resume the timer")
        buttons_layout.addWidget(resume_btn)
        timer_data['resume_btn'] = resume_btn
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(lambda: self.on_timer_reset(timer_data))
        reset_btn.setToolTip("Reset the timer to initial time")
        buttons_layout.addWidget(reset_btn)
        timer_data['reset_btn'] = reset_btn
        
        buttons_group.setLayout(buttons_layout)
        tab_layout.addWidget(buttons_group)
        
        # AI Timer Widget (added below controls)
        ai_timer_widget = AITimerWidget()
        timer_data['ai_timer_widget'] = ai_timer_widget
        
        # Create AI controller for this timer
        ai_controller = AIIntegrationController(base_timer_controller=controller)
        self._ai_controllers[len(self._timers)] = ai_controller
        ai_timer_widget.set_ai_controller(ai_controller)
        
        # Connect AI widget signals
        ai_timer_widget.enable_ai_requested.connect(
            lambda enabled: self._on_enable_ai_timer(len(self._timers), enabled)
        )
        ai_timer_widget.pause_ai_requested.connect(
            lambda: self._on_pause_ai_timer(len(self._timers))
        )
        ai_timer_widget.resume_ai_requested.connect(
            lambda: self._on_resume_ai_timer(len(self._timers))
        )
        ai_timer_widget.override_ai_requested.connect(
            lambda: self._on_override_ai_timer(len(self._timers))
        )
        
        tab_layout.addWidget(ai_timer_widget)
        
        # Connect controller signals
        controller.time_changed.connect(
            lambda t: timer_widget.set_time(t, controller.get_initial_time())
        )
        controller.timer_finished.connect(
            lambda: self.on_timer_finished(timer_data)
        )
        controller.warning_threshold.connect(
            lambda: self.on_timer_warning(timer_data)
        )
        controller.timer_started.connect(
            lambda: self.on_timer_started(timer_data)
        )
        controller.timer_paused.connect(
            lambda: self.on_timer_paused(timer_data)
        )
        controller.timer_resumed.connect(
            lambda: self.on_timer_resumed(timer_data)
        )
        controller.timer_reset.connect(
            lambda: self.on_timer_reset_signal(timer_data)
        )
        
        # Connect timer state changes to AI Timer widget for button updates
        def update_ai_timer_buttons():
            ai_widget = timer_data.get('ai_timer_widget')
            if ai_widget:
                ai_widget._update_ui_state()
        
        controller.timer_started.connect(update_ai_timer_buttons)
        controller.timer_paused.connect(update_ai_timer_buttons)
        controller.timer_resumed.connect(update_ai_timer_buttons)
        controller.timer_stopped.connect(update_ai_timer_buttons)
        controller.timer_reset.connect(update_ai_timer_buttons)
        
        # Add tab
        tab_index = self.tab_widget.addTab(tab_widget, name)
        self.tab_widget.setCurrentIndex(tab_index)
        self._timers.append(timer_data)
        
        # Set initial time
        controller.set_time(300)  # 5 minutes default
        timer_widget.set_time(controller.get_current_time(), controller.get_initial_time())
    
    def close_timer_tab(self, index: int):
        """Close a timer tab."""
        if len(self._timers) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Close",
                "At least one timer must remain open.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Stop and cleanup timer
        timer_data = self._timers[index]
        controller = timer_data.get('controller')
        if controller:
            if controller.is_running():
                controller.stop()
        
        # Cleanup AI controller if exists
        if index in self._ai_controllers:
            ai_controller = self._ai_controllers.pop(index)
            ai_controller.stop_ai_timing()
        
        # Remove tab
        self.tab_widget.removeTab(index)
        self._timers.pop(index)
        
        # Update indices for remaining AI controllers
        new_controllers = {}
        for old_idx in range(len(self._timers)):
            if old_idx >= index:
                # Shift indices down
                if old_idx + 1 in self._ai_controllers:
                    new_controllers[old_idx] = self._ai_controllers[old_idx + 1]
            else:
                if old_idx in self._ai_controllers:
                    new_controllers[old_idx] = self._ai_controllers[old_idx]
        self._ai_controllers = new_controllers
        
        # Update current tab index
        if self.tab_widget.currentIndex() >= len(self._timers):
            self.tab_widget.setCurrentIndex(len(self._timers) - 1)
    
    def on_tab_changed(self, index: int):
        """Handle tab change."""
        self._current_tab_index = index
    
    def get_tab_count(self) -> int:
        """Get the number of timer tabs."""
        return len(self._timers)
    
    def on_timer_start(self, timer_data):
        """Handle timer start."""
        timer_data['controller'].start()
    
    def on_timer_pause(self, timer_data):
        """Handle timer pause."""
        timer_data['controller'].pause()
    
    def on_timer_resume(self, timer_data):
        """Handle timer resume."""
        timer_data['controller'].resume()
    
    def on_timer_reset(self, timer_data):
        """Handle timer reset button click."""
        try:
            controller = timer_data.get('controller')
            if not controller:
                return
            
            # Stop the timer first if running or paused
            if hasattr(controller, 'is_running') and controller.is_running():
                controller.stop()
            elif hasattr(controller, 'is_paused') and controller.is_paused():
                controller.stop()
            
            # Then reset (this will emit timer_reset signal which calls on_timer_reset_signal)
            controller.reset()
        except Exception as e:
            # Log error but don't crash
            print(f"Error in on_timer_reset: {e}")
            import traceback
            traceback.print_exc()
    
    def on_timer_reset_signal(self, timer_data):
        """Handle timer reset signal from controller (UI update only)."""
        # This is called when controller emits timer_reset signal
        # Only update UI, don't call reset() again to avoid recursion
        if timer_data.get('start_btn') and timer_data.get('pause_btn') and timer_data.get('resume_btn') and timer_data.get('reset_btn'):
            timer_data['start_btn'].setEnabled(True)
            timer_data['pause_btn'].setEnabled(False)
            timer_data['resume_btn'].setEnabled(False)
            timer_data['reset_btn'].setEnabled(True)
    
    def on_timer_started(self, timer_data):
        """Handle timer started signal."""
        if timer_data.get('start_btn') and timer_data.get('pause_btn') and timer_data.get('resume_btn') and timer_data.get('reset_btn'):
            timer_data['start_btn'].setEnabled(False)
            timer_data['pause_btn'].setEnabled(True)
            timer_data['resume_btn'].setEnabled(False)
            timer_data['reset_btn'].setEnabled(True)
        
        # Update AI Timer widget buttons
        ai_widget = timer_data.get('ai_timer_widget')
        if ai_widget:
            ai_widget._update_ui_state()
    
    def on_timer_paused(self, timer_data):
        """Handle timer paused signal."""
        if timer_data['start_btn'] and timer_data['pause_btn'] and timer_data['resume_btn'] and timer_data['reset_btn']:
            timer_data['start_btn'].setEnabled(False)
            timer_data['pause_btn'].setEnabled(False)
            timer_data['resume_btn'].setEnabled(True)
            timer_data['reset_btn'].setEnabled(True)
        
        # Update AI Timer widget buttons
        ai_widget = timer_data.get('ai_timer_widget')
        if ai_widget:
            ai_widget._update_ui_state()
    
    def on_timer_resumed(self, timer_data):
        """Handle timer resumed signal."""
        if timer_data['start_btn'] and timer_data['pause_btn'] and timer_data['resume_btn'] and timer_data['reset_btn']:
            timer_data['start_btn'].setEnabled(False)
            timer_data['pause_btn'].setEnabled(True)
            timer_data['resume_btn'].setEnabled(False)
            timer_data['reset_btn'].setEnabled(True)
        
        # Update AI Timer widget buttons
        ai_widget = timer_data.get('ai_timer_widget')
        if ai_widget:
            ai_widget._update_ui_state()
    
    def on_timer_finished(self, timer_data):
        """Handle timer finished signal."""
        if timer_data['start_btn'] and timer_data['pause_btn'] and timer_data['resume_btn'] and timer_data['reset_btn']:
            timer_data['start_btn'].setEnabled(True)
            timer_data['pause_btn'].setEnabled(False)
            timer_data['resume_btn'].setEnabled(False)
            timer_data['reset_btn'].setEnabled(True)
        
        # Play finished sound
        self._play_sound(self._finished_sound_path)
        
        QMessageBox.information(
            self,
            "Timer Finished",
            "The timer has reached zero!",
            QMessageBox.StandardButton.Ok
        )
    
    def on_timer_warning(self, timer_data):
        """Handle timer warning signal."""
        # Play warning sound
        self._play_sound(self._warning_sound_path)
    
    def _play_sound(self, sound_path: Path):
        """Play a sound file."""
        if sound_path.exists():
            try:
                player = QMediaPlayer()
                from PyQt6.QtCore import QUrl
                player.setSource(QUrl.fromLocalFile(str(sound_path)))
                player.play()
            except Exception as e:
                # Silently fail - sounds are optional
                pass
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def apply_theme(self):
        """Apply theme based on system settings."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for scrolling when menu is hidden."""
        central = self.centralWidget()
        if isinstance(central, QScrollArea):
            scrollbar = central.verticalScrollBar()
            if scrollbar.isVisible():
                delta = event.angleDelta().y()
                scrollbar.setValue(scrollbar.value() - delta // 8)
                event.accept()
                return
        event.ignore()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Timer",
            "<h2>AI-Symp-Controller - Smart Timer</h2>"
            "<p>Version 1.1.0</p>"
            "<p>Advanced graphical timer with:</p>"
            "<ul>"
            "<li>Animated circular countdown</li>"
            "<li>Multi-timer support</li>"
            "<li>AI-driven adaptive timing (Beta)</li>"
            "<li>Visual and audio alerts</li>"
            "<li>Fullscreen mode</li>"
            "<li>Responsive design</li>"
            "</ul>"
            "<p>Built with PyQt6</p>"
        )
    
    def _on_enable_ai_timer(self, timer_index: int, enabled: bool):
        """Handle AI timer enable/disable request."""
        try:
            if timer_index not in self._ai_controllers:
                return
            
            ai_controller = self._ai_controllers[timer_index]
            timer_data = self._timers[timer_index] if timer_index < len(self._timers) else None
            
            if not timer_data:
                return
            
            if enabled:
                # Start AI timing (use default camera indices - can be configured)
                presenter_camera = 0  # Default presenter camera
                audience_camera = 0   # Default audience camera (can be same or different)
                enable_voice = False  # Disable voice by default to avoid microphone issues
                
                try:
                    success = ai_controller.start_ai_timing(
                        presenter_camera=presenter_camera,
                        audience_camera=audience_camera,
                        enable_voice=enable_voice
                    )
                except Exception as e:
                    # Handle any exceptions during startup
                    import traceback
                    error_msg = f"Error starting AI timing system:\n{str(e)}\n\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    QMessageBox.critical(
                        self,
                        "AI Timer Error",
                        f"An error occurred while starting AI timing:\n\n{str(e)}\n\n"
                        "Please check the console for details."
                    )
                    success = False
                
                if success:
                    ai_timer_widget = timer_data.get('ai_timer_widget')
                    if ai_timer_widget:
                        ai_timer_widget._update_ui_state()
                else:
                    QMessageBox.warning(
                        self,
                        "AI Timer Start Failed",
                        "Could not start AI timing system.\n\n"
                        "This is normal if:\n"
                        "- Camera is not available\n"
                        "- Face AI dependencies are not installed\n"
                        "- Camera is being used by another application\n\n"
                        "You can still use the timer manually without AI features."
                    )
                    # Uncheck the checkbox
                    ai_timer_widget = timer_data.get('ai_timer_widget')
                    if ai_timer_widget:
                        # Block signals to prevent triggering state change handler
                        ai_timer_widget._enable_checkbox.blockSignals(True)
                        ai_timer_widget._enable_checkbox.setChecked(False)
                        ai_timer_widget._enable_checkbox.blockSignals(False)
                        ai_timer_widget._ai_enabled = False
                        ai_timer_widget._enable_checkbox.update()  # Force visual update
            else:
                # Stop AI timing
                try:
                    ai_controller.stop_ai_timing()
                except Exception as e:
                    logger.error(f"Error stopping AI timing: {e}")
                
                ai_timer_widget = timer_data.get('ai_timer_widget')
                if ai_timer_widget:
                    ai_timer_widget._update_ui_state()
        except Exception as e:
            # Catch-all for any unexpected errors
            import traceback
            error_msg = f"Unexpected error in AI timer: {str(e)}\n\n{traceback.format_exc()}"
            logger.error(error_msg)
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\n"
                "The application will continue, but AI features may not work."
            )
    
    def _on_pause_ai_timer(self, timer_index: int):
        """Handle pause AI timer request."""
        if timer_index not in self._ai_controllers:
            return
        
        timer_data = self._timers[timer_index] if timer_index < len(self._timers) else None
        if timer_data:
            controller = timer_data.get('controller')
            if controller and controller.is_running():
                controller.pause()
    
    def _on_resume_ai_timer(self, timer_index: int):
        """Handle resume AI timer request."""
        if timer_index not in self._ai_controllers:
            return
        
        timer_data = self._timers[timer_index] if timer_index < len(self._timers) else None
        if timer_data:
            controller = timer_data.get('controller')
            if controller and controller.is_paused():
                controller.resume()
    
    def _on_override_ai_timer(self, timer_index: int):
        """Handle override AI timer request."""
        if timer_index not in self._ai_controllers:
            return
        
        ai_controller = self._ai_controllers[timer_index]
        ai_controller.override_ai_adaptation()
        
        timer_data = self._timers[timer_index] if timer_index < len(self._timers) else None
        if timer_data:
            ai_timer_widget = timer_data.get('ai_timer_widget')
            if ai_timer_widget:
                ai_timer_widget._log_entry("Operator: AI adaptation overridden")
