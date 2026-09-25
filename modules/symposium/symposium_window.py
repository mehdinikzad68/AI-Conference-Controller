"""
Symposium Window Module

Main window for symposium display with agenda, speaker intros, session management,
smart timer overlays, and scene switching.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QGroupBox, QFileDialog, QMessageBox, QComboBox,
    QSpinBox, QCheckBox, QSlider, QDialog, QDialogButtonBox, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QFont, QKeySequence, QShortcut, QColor
from pathlib import Path
from typing import Optional

from .agenda_manager import AgendaManager, AgendaItem, SpeakerInfo
from .session_controller import SessionController
from .smart_timer_overlay import SmartTimerOverlay
from .scene_manager import SceneManager, SceneType
from .agenda_display_widget import AgendaDisplayWidget
from .speaker_intro_widget import SpeakerIntroWidget

from modules.media.media_display_widget import MediaDisplayWidget
from modules.timer.timer_controller import TimerController
from modules.utils.theme_manager import ThemeManager


class SymposiumWindow(QMainWindow):
    """
    Main symposium display window.
    
    Features:
    - Agenda display
    - Speaker introduction slides
    - Session management with timer
    - Smart timer overlay with progress bar
    - Scene switching (agenda, intro, session, logo)
    - Media playback integration
    - Logo slide display
    - OBS Studio optimized
    """
    
    def __init__(self, parent=None):
        """Initialize symposium window."""
        super().__init__(parent)
        
        # Managers and controllers
        self._agenda_manager = AgendaManager()
        self._scene_manager = SceneManager()
        self._timer_controller = TimerController()
        self._session_controller = SessionController(self._timer_controller)
        
        # Theme manager
        self._theme_manager = ThemeManager()
        
        # Current state
        self._current_session: Optional[AgendaItem] = None
        self._logo_pixmap: Optional[QPixmap] = None
        
        # UI components
        self._stacked_widget: Optional[QStackedWidget] = None
        self._agenda_widget: Optional[AgendaDisplayWidget] = None
        self._intro_widget: Optional[SpeakerIntroWidget] = None
        self._media_display: Optional[MediaDisplayWidget] = None
        self._logo_widget: Optional[QWidget] = None
        self._smart_timer_overlay: Optional[SmartTimerOverlay] = None
        
        # Overlay settings
        self._overlay_position = SmartTimerOverlay.POSITION_BOTTOM_CENTER
        self._overlay_opacity = 0.85
        self._overlay_width_ratio = 0.4
        
        # Setup
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller - Symposium Display [OBS]")
        self.setMinimumSize(1280, 720)
        self.resize(1920, 1080)
        
        # Apply theme
        self.apply_theme()
    
    def setup_ui(self):
        """Setup main UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #1a1a1a;")
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Stacked widget for scene switching
        self._stacked_widget = QStackedWidget()
        main_layout.addWidget(self._stacked_widget)
        
        # Create scene widgets
        self.create_agenda_scene()
        self.create_intro_scene()
        self.create_session_scene()
        self.create_logo_scene()
        
        # Control panel (minimized by default, can be shown/hidden)
        self.create_control_panel()
        
        # Start with logo scene
        self._scene_manager.switch_to_logo()
        self.update_scene_display()
    
    def create_agenda_scene(self):
        """Create agenda display scene."""
        agenda_widget = QWidget()
        agenda_widget.setStyleSheet("background-color: #1a1a1a;")
        agenda_layout = QVBoxLayout(agenda_widget)
        agenda_layout.setContentsMargins(0, 0, 0, 0)
        
        self._agenda_widget = AgendaDisplayWidget(self._agenda_manager, agenda_widget)
        agenda_layout.addWidget(self._agenda_widget)
        
        self._stacked_widget.addWidget(agenda_widget)
    
    def create_intro_scene(self):
        """Create speaker intro scene."""
        intro_widget = QWidget()
        intro_widget.setStyleSheet("background-color: #1a1a1a;")
        intro_layout = QVBoxLayout(intro_widget)
        intro_layout.setContentsMargins(0, 0, 0, 0)
        
        self._intro_widget = SpeakerIntroWidget(intro_widget)
        intro_layout.addWidget(self._intro_widget)
        
        self._stacked_widget.addWidget(intro_widget)
    
    def create_session_scene(self):
        """Create session scene with media display."""
        session_widget = QWidget()
        session_widget.setStyleSheet("background-color: #000000;")
        session_layout = QVBoxLayout(session_widget)
        session_layout.setContentsMargins(0, 0, 0, 0)
        
        # Media display widget
        self._media_display = MediaDisplayWidget(session_widget)
        session_layout.addWidget(self._media_display)
        
        self._stacked_widget.addWidget(session_widget)
    
    def create_logo_scene(self):
        """Create logo/branded slide scene."""
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background-color: #1a1a1a;")
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo label (centered)
        self._logo_label = QLabel()
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("background-color: transparent;")
        logo_layout.addWidget(self._logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Symposium title label
        self._logo_title_label = QLabel()
        self._logo_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_title_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #ffffff;
                padding: 20px;
            }
        """)
        logo_layout.addWidget(self._logo_title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._logo_widget = logo_widget
        self._stacked_widget.addWidget(logo_widget)
        
        # Load logo if available
        self.update_logo_display()
    
    def create_control_panel(self):
        """Create control panel (can be toggled)."""
        # Control panel as a floating widget (can be made into dock widget)
        # For now, integrate into menu or make toggleable
        pass
    
    def setup_connections(self):
        """Setup signal connections."""
        # Scene manager signals
        self._scene_manager.scene_changed.connect(self.update_scene_display)
        
        # Session controller signals
        self._session_controller.session_started.connect(self.on_session_started)
        self._session_controller.session_ended.connect(self.on_session_ended)
        self._session_controller.media_found.connect(self.on_media_found)
        self._session_controller.media_not_found.connect(self.on_media_not_found)
        self._session_controller.warning_threshold_reached.connect(self.on_warning_threshold)
        
        # Agenda manager signals
        self._agenda_manager.agenda_loaded.connect(self.on_agenda_loaded)
        self._agenda_manager.current_session_changed.connect(self.on_current_session_changed)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Scene switching shortcuts
        QShortcut(QKeySequence("F1"), self, self._scene_manager.switch_to_agenda)
        QShortcut(QKeySequence("F2"), self, self._scene_manager.switch_to_speaker_intro)
        QShortcut(QKeySequence("F3"), self, self._scene_manager.switch_to_session)
        QShortcut(QKeySequence("F4"), self, self._scene_manager.switch_to_logo)
        QShortcut(QKeySequence("F5"), self, self._scene_manager.switch_to_break)
        
        # Session control shortcuts
        QShortcut(QKeySequence("Space"), self, self.toggle_session_pause)
        QShortcut(QKeySequence("Ctrl+N"), self, self.next_session)
        QShortcut(QKeySequence("Ctrl+P"), self, self.previous_session)
    
    def update_scene_display(self):
        """Update display based on current scene."""
        scene = self._scene_manager.get_current_scene()
        
        if scene == SceneType.AGENDA:
            self._stacked_widget.setCurrentIndex(0)  # Agenda
            if self._agenda_widget:
                self._agenda_widget.refresh()
        elif scene == SceneType.SPEAKER_INTRO:
            self._stacked_widget.setCurrentIndex(1)  # Intro
        elif scene == SceneType.SESSION:
            self._stacked_widget.setCurrentIndex(2)  # Session
        elif scene == SceneType.LOGO or scene == SceneType.BREAK:
            self._stacked_widget.setCurrentIndex(3)  # Logo
        
        # Update timer overlay visibility
        if scene == SceneType.SESSION:
            if self._smart_timer_overlay:
                self._smart_timer_overlay.show_overlay()
        else:
            if self._smart_timer_overlay:
                self._smart_timer_overlay.hide_overlay()
    
    def on_session_started(self, session_id: str):
        """Handle session started."""
        session = self._agenda_manager.get_agenda_item(session_id)
        if session:
            self._current_session = session
            
            # Switch to session scene
            self._scene_manager.switch_to_session()
            
            # Setup smart timer overlay
            self.setup_smart_timer_overlay()
    
    def on_session_ended(self, session_id: str):
        """Handle session ended."""
        # Hide timer overlay
        if self._smart_timer_overlay:
            self._smart_timer_overlay.hide_overlay()
        
        # Clear media
        if self._media_display:
            self._media_display.clear_display()
        
        # Return to logo scene
        self._scene_manager.switch_to_logo()
    
    def on_media_found(self, media_path: str):
        """Handle media file found."""
        if self._media_display:
            self._media_display.load_media(media_path)
    
    def on_media_not_found(self):
        """Handle no media file."""
        # Keep logo scene or branded slide visible
        # Timer overlay will still show
        pass
    
    def on_warning_threshold(self):
        """Handle 20% warning threshold."""
        # Trigger visual effects (already handled by SmartTimerOverlay)
        # Play audio chime if enabled
        self.play_warning_chime()
    
    def play_warning_chime(self):
        """Play warning chime sound."""
        try:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PyQt6.QtCore import QUrl
            
            player = QMediaPlayer(self)
            audio_output = QAudioOutput(self)
            player.setAudioOutput(audio_output)
            
            # Try to load warning sound (if available)
            sound_path = Path("assets/sounds/warning_chime.mp3")
            if sound_path.exists():
                player.setSource(QUrl.fromLocalFile(str(sound_path)))
                player.play()
        except Exception as e:
            print(f"Could not play warning chime: {e}")
    
    def setup_smart_timer_overlay(self):
        """Setup smart timer overlay."""
        if not self._media_display:
            return
        
        # Create overlay if it doesn't exist
        if not self._smart_timer_overlay:
            self._smart_timer_overlay = SmartTimerOverlay(
                self._media_display,
                self._timer_controller
            )
            self._smart_timer_overlay.set_position(self._overlay_position)
            self._smart_timer_overlay.set_width_ratio(self._overlay_width_ratio)
            self._smart_timer_overlay.set_opacity(self._overlay_opacity)
        else:
            # Update timer controller
            self._smart_timer_overlay.set_timer_controller(self._timer_controller)
        
        self._smart_timer_overlay.show_overlay()
    
    def start_session(self):
        """Start current session."""
        session = self._agenda_manager.get_current_session()
        if session:
            # Show speaker intro first
            self._intro_widget.set_speaker_info(session.speaker)
            self._scene_manager.switch_to_speaker_intro()
            
            # Auto-advance to session after 3 seconds (or manual)
            QTimer.singleShot(3000, lambda: self._session_controller.start_session(session))
    
    def next_session(self):
        """Move to next session."""
        if self._agenda_manager.move_to_next_session():
            session = self._agenda_manager.get_current_session()
            if session:
                self.start_session()
    
    def previous_session(self):
        """Move to previous session."""
        if self._agenda_manager.move_to_previous_session():
            session = self._agenda_manager.get_current_session()
            if session:
                self.start_session()
    
    def toggle_session_pause(self):
        """Toggle session pause/resume."""
        if self._session_controller.is_session_running():
            if self._timer_controller.is_paused():
                self._session_controller.resume_session()
            else:
                self._session_controller.pause_session()
    
    def load_agenda_from_file(self, file_path: str) -> bool:
        """Load agenda from JSON file."""
        return self._agenda_manager.load_from_file(file_path)
    
    def save_agenda_to_file(self, file_path: str) -> bool:
        """Save agenda to JSON file."""
        return self._agenda_manager.save_to_file(file_path)
    
    def update_logo_display(self):
        """Update logo display."""
        logo_path = self._agenda_manager.get_logo_path()
        if logo_path and Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    400, 300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._logo_label.setPixmap(scaled)
        
        title = self._agenda_manager.get_symposium_title()
        self._logo_title_label.setText(title)
    
    def on_agenda_loaded(self):
        """Handle agenda loaded."""
        if self._agenda_widget:
            self._agenda_widget.refresh()
        self.update_logo_display()
    
    def on_current_session_changed(self, session_id: str):
        """Handle current session changed."""
        pass
    
    def set_overlay_position(self, position: str):
        """Set overlay position."""
        self._overlay_position = position
        if self._smart_timer_overlay:
            self._smart_timer_overlay.set_position(position)
    
    def set_overlay_opacity(self, opacity: float):
        """Set overlay opacity."""
        self._overlay_opacity = opacity
        if self._smart_timer_overlay:
            self._smart_timer_overlay.set_opacity(opacity)
    
    def set_overlay_width_ratio(self, ratio: float):
        """Set overlay width ratio."""
        self._overlay_width_ratio = ratio
        if self._smart_timer_overlay:
            self._smart_timer_overlay.set_width_ratio(ratio)
    
    def apply_theme(self):
        """Apply theme."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def get_agenda_manager(self) -> AgendaManager:
        """Get agenda manager."""
        return self._agenda_manager
    
    def get_session_controller(self) -> SessionController:
        """Get session controller."""
        return self._session_controller
    
    def get_scene_manager(self) -> SceneManager:
        """Get scene manager."""
        return self._scene_manager

