"""
Configuration Window Module

Main window for application configuration with tabs for all settings categories.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QSpinBox, QComboBox, QCheckBox, QSlider,
    QGroupBox, QFileDialog, QMessageBox, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QColorDialog, QFontDialog,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
from pathlib import Path
from typing import Optional
import json

from .config_manager import ConfigManager
from .config_profiles import ProfileManager, ConfigProfile
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QScrollArea


class ProfileDialog(QDialog):
    """Dialog for creating/editing configuration profiles."""
    
    def __init__(self, parent=None, profile: Optional[ConfigProfile] = None):
        """Initialize profile dialog."""
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Profile Settings" if profile else "New Profile")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(profile.name if profile else "")
        layout.addRow("Profile Name:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        if profile:
            self.desc_edit.setText(profile.description)
        layout.addRow("Description:", self.desc_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_profile_data(self):
        """Get profile name and description."""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip()
        }


class ConfigWindow(QMainWindow):
    """
    Main configuration window with tabs for all settings.
    
    Features:
    - Timer settings
    - Media settings
    - AI/Face Analysis settings
    - Display/Output configuration
    - Sound/Alert settings
    - General preferences
    - Asset management
    - Profile management
    """
    
    # Signal emitted when configuration changes
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the configuration window."""
        super().__init__(parent)
        
        # Configuration managers
        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        self.profile_manager = ProfileManager()
        
        # Current profile
        self._current_profile_name = "Default"
        
        # Preview timer for real-time updates
        self._preview_timer = QTimer()
        self._preview_timer.timeout.connect(self._update_previews)
        self._preview_timer.setSingleShot(True)
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller - Configuration")
        self.setMinimumSize(750, 600)
        self.resize(950, 700)
        
        # Make responsive
        make_responsive(self)
        
        # Load current configuration
        self.load_config_to_ui()
        
        # Apply system theme
        self.apply_theme()
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
    
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
    
    def init_ui(self):
        """Initialize the user interface with scrollable support."""
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        central_widget = QWidget()
        make_responsive(central_widget)
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Profile management bar
        profile_bar = self.create_profile_bar()
        main_layout.addWidget(profile_bar)
        
        # Tab widget for settings categories
        self.tabs = QTabWidget()
        
        # Timer settings tab
        timer_tab = self.create_timer_tab()
        self.tabs.addTab(timer_tab, "Timer")
        
        # Media settings tab
        media_tab = self.create_media_tab()
        self.tabs.addTab(media_tab, "Media")
        
        # AI/Face Analysis tab
        face_ai_tab = self.create_face_ai_tab()
        self.tabs.addTab(face_ai_tab, "Face AI")
        
        # Display settings tab
        display_tab = self.create_display_tab()
        self.tabs.addTab(display_tab, "Display")
        
        # Sound settings tab
        sound_tab = self.create_sound_tab()
        self.tabs.addTab(sound_tab, "Sound & Alerts")
        
        # General preferences tab
        general_tab = self.create_general_tab()
        self.tabs.addTab(general_tab, "General")
        
        # Assets tab
        assets_tab = self.create_assets_tab()
        self.tabs.addTab(assets_tab, "Assets")
        
        main_layout.addWidget(self.tabs)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        preview_btn = QPushButton("Preview Changes")
        preview_btn.clicked.connect(self.preview_changes)
        preview_btn.setToolTip("Preview configuration changes in real-time")
        buttons_layout.addWidget(preview_btn)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setToolTip("Save current configuration")
        buttons_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setToolTip("Reset all settings to default values")
        buttons_layout.addWidget(reset_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Menu bar
        self.setup_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_profile_bar(self) -> QWidget:
        """Create profile management bar."""
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(200)
        self.refresh_profiles()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        layout.addWidget(self.profile_combo)
        
        new_profile_btn = QPushButton("New")
        new_profile_btn.clicked.connect(self.create_new_profile)
        new_profile_btn.setToolTip("Create new configuration profile")
        layout.addWidget(new_profile_btn)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_profile)
        import_btn.setToolTip("Import profile from file")
        layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_profile)
        export_btn.setToolTip("Export current profile to file")
        layout.addWidget(export_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_profile)
        delete_btn.setToolTip("Delete selected profile")
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        return bar
    
    def create_timer_tab(self) -> QWidget:
        """Create timer settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Default duration
        duration_group = QGroupBox("Default Timer Settings")
        duration_layout = QVBoxLayout()
        
        duration_h_layout = QHBoxLayout()
        duration_h_layout.addWidget(QLabel("Default Duration (minutes):"))
        self.timer_duration_spin = QSpinBox()
        self.timer_duration_spin.setMinimum(1)
        self.timer_duration_spin.setMaximum(120)
        self.timer_duration_spin.setValue(5)
        self.timer_duration_spin.setToolTip("Default timer duration when creating new timers")
        duration_h_layout.addWidget(self.timer_duration_spin)
        duration_h_layout.addStretch()
        duration_layout.addLayout(duration_h_layout)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Timer Mode:"))
        self.timer_mode_combo = QComboBox()
        self.timer_mode_combo.addItems(["Countdown", "Count Up"])
        self.timer_mode_combo.setToolTip("Default timer counting direction")
        mode_layout.addWidget(self.timer_mode_combo)
        mode_layout.addStretch()
        duration_layout.addLayout(mode_layout)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        
        # Appearance
        appearance_group = QGroupBox("Timer Appearance")
        appearance_layout = QVBoxLayout()
        
        color_scheme_layout = QHBoxLayout()
        color_scheme_layout.addWidget(QLabel("Color Scheme:"))
        self.timer_color_combo = QComboBox()
        self.timer_color_combo.addItems(["Gradient", "Solid Green", "Solid Red", "Custom"])
        self.timer_color_combo.setToolTip("Timer ring color scheme")
        color_scheme_layout.addWidget(self.timer_color_combo)
        color_scheme_layout.addStretch()
        appearance_layout.addLayout(color_scheme_layout)
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        self.timer_font_spin = QSpinBox()
        self.timer_font_spin.setMinimum(24)
        self.timer_font_spin.setMaximum(200)
        self.timer_font_spin.setValue(72)
        self.timer_font_spin.setToolTip("Timer display font size in pixels")
        font_size_layout.addWidget(self.timer_font_spin)
        font_size_layout.addStretch()
        appearance_layout.addLayout(font_size_layout)
        
        self.timer_show_seconds_check = QCheckBox("Show Seconds")
        self.timer_show_seconds_check.setChecked(True)
        self.timer_show_seconds_check.setToolTip("Display seconds in timer (MM:SS format)")
        appearance_layout.addWidget(self.timer_show_seconds_check)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Warning settings
        warning_group = QGroupBox("Warning Settings")
        warning_layout = QVBoxLayout()
        
        self.timer_warning_enabled_check = QCheckBox("Enable Warning Alerts")
        self.timer_warning_enabled_check.setChecked(True)
        self.timer_warning_enabled_check.setToolTip("Show visual and audio warnings when time is running low")
        warning_layout.addWidget(self.timer_warning_enabled_check)
        
        warning_threshold_layout = QHBoxLayout()
        warning_threshold_layout.addWidget(QLabel("Warning Threshold (seconds):"))
        self.timer_warning_threshold_spin = QSpinBox()
        self.timer_warning_threshold_spin.setMinimum(10)
        self.timer_warning_threshold_spin.setMaximum(600)
        self.timer_warning_threshold_spin.setValue(120)
        self.timer_warning_threshold_spin.setToolTip("Time remaining when warning alerts trigger")
        warning_threshold_layout.addWidget(self.timer_warning_threshold_spin)
        warning_threshold_layout.addStretch()
        warning_layout.addLayout(warning_threshold_layout)
        
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        layout.addStretch()
        
        return tab
    
    def create_media_tab(self) -> QWidget:
        """Create media settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Playback settings
        playback_group = QGroupBox("Playback Settings")
        playback_layout = QVBoxLayout()
        
        self.media_auto_play_check = QCheckBox("Auto-Play on Load")
        self.media_auto_play_check.setToolTip("Automatically start playback when media is loaded")
        playback_layout.addWidget(self.media_auto_play_check)
        
        self.media_auto_advance_check = QCheckBox("Auto-Advance to Next")
        self.media_auto_advance_check.setToolTip("Automatically move to next media when current finishes")
        playback_layout.addWidget(self.media_auto_advance_check)
        
        self.media_fullscreen_on_play_check = QCheckBox("Fullscreen on Play")
        self.media_fullscreen_on_play_check.setToolTip("Enter fullscreen mode when starting playback")
        playback_layout.addWidget(self.media_fullscreen_on_play_check)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        
        transition_layout = QHBoxLayout()
        transition_layout.addWidget(QLabel("Default Transition:"))
        self.media_transition_combo = QComboBox()
        self.media_transition_combo.addItems(["Fade", "Slide", "Blur", "None"])
        self.media_transition_combo.setToolTip("Default transition effect between media items")
        transition_layout.addWidget(self.media_transition_combo)
        transition_layout.addStretch()
        display_layout.addLayout(transition_layout)
        
        self.media_aspect_ratio_check = QCheckBox("Maintain Aspect Ratio")
        self.media_aspect_ratio_check.setChecked(True)
        self.media_aspect_ratio_check.setToolTip("Keep media aspect ratio when scaling")
        display_layout.addWidget(self.media_aspect_ratio_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        
        return tab
    
    def create_face_ai_tab(self) -> QWidget:
        """Create Face AI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Basic settings
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QVBoxLayout()
        
        self.face_ai_enabled_check = QCheckBox("Enable Face AI Analysis")
        self.face_ai_enabled_check.setToolTip("Enable audience attention and reaction analysis")
        basic_layout.addWidget(self.face_ai_enabled_check)
        
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel("Camera Index:"))
        self.face_ai_camera_spin = QSpinBox()
        self.face_ai_camera_spin.setMinimum(0)
        self.face_ai_camera_spin.setMaximum(10)
        self.face_ai_camera_spin.setValue(0)
        self.face_ai_camera_spin.setToolTip("Camera device index (0 = first camera)")
        camera_layout.addWidget(self.face_ai_camera_spin)
        camera_layout.addStretch()
        basic_layout.addLayout(camera_layout)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Analysis settings
        analysis_group = QGroupBox("Analysis Settings")
        analysis_layout = QVBoxLayout()
        
        sampling_layout = QHBoxLayout()
        sampling_layout.addWidget(QLabel("Sampling Frequency (seconds):"))
        self.face_ai_sampling_spin = QSpinBox()
        self.face_ai_sampling_spin.setMinimum(1)
        self.face_ai_sampling_spin.setMaximum(60)
        self.face_ai_sampling_spin.setValue(2)
        self.face_ai_sampling_spin.setToolTip("Time between frame captures for analysis")
        sampling_layout.addWidget(self.face_ai_sampling_spin)
        sampling_layout.addStretch()
        analysis_layout.addLayout(sampling_layout)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Attention Threshold:"))
        self.face_ai_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.face_ai_threshold_slider.setMinimum(0)
        self.face_ai_threshold_slider.setMaximum(100)
        self.face_ai_threshold_slider.setValue(50)
        self.face_ai_threshold_slider.setToolTip("Threshold for determining if audience is attentive (0-100%)")
        threshold_layout.addWidget(self.face_ai_threshold_slider)
        self.face_ai_threshold_label = QLabel("50%")
        threshold_layout.addWidget(self.face_ai_threshold_label)
        self.face_ai_threshold_slider.valueChanged.connect(
            lambda v: self.face_ai_threshold_label.setText(f"{v}%")
        )
        analysis_layout.addLayout(threshold_layout)
        
        self.face_ai_emotion_check = QCheckBox("Enable Emotion Detection")
        self.face_ai_emotion_check.setChecked(True)
        self.face_ai_emotion_check.setToolTip("Detect audience emotions (smile, neutral, frown)")
        analysis_layout.addWidget(self.face_ai_emotion_check)
        
        self.face_ai_gaze_check = QCheckBox("Enable Gaze Tracking")
        self.face_ai_gaze_check.setToolTip("Track eye gaze direction (experimental)")
        analysis_layout.addWidget(self.face_ai_gaze_check)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Visualization settings
        viz_group = QGroupBox("Visualization Settings")
        viz_layout = QVBoxLayout()
        
        chart_layout = QHBoxLayout()
        chart_layout.addWidget(QLabel("Chart Type:"))
        self.face_ai_chart_combo = QComboBox()
        self.face_ai_chart_combo.addItems(["Bar Chart", "Pie Chart", "Line Chart"])
        self.face_ai_chart_combo.setToolTip("Chart type for displaying analysis results")
        chart_layout.addWidget(self.face_ai_chart_combo)
        chart_layout.addStretch()
        viz_layout.addLayout(chart_layout)
        
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        layout.addStretch()
        
        return tab
    
    def create_display_tab(self) -> QWidget:
        """Create display settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Display mode
        mode_group = QGroupBox("Display Mode")
        mode_layout = QVBoxLayout()
        
        mode_combo_layout = QHBoxLayout()
        mode_combo_layout.addWidget(QLabel("Display Mode:"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Extended", "Mirror"])
        self.display_mode_combo.setToolTip("Extended = different content on each display, Mirror = same content")
        mode_combo_layout.addWidget(self.display_mode_combo)
        mode_combo_layout.addStretch()
        mode_layout.addLayout(mode_combo_layout)
        
        self.display_auto_detect_check = QCheckBox("Auto-Detect Displays")
        self.display_auto_detect_check.setChecked(True)
        self.display_auto_detect_check.setToolTip("Automatically detect connected displays on startup")
        mode_layout.addWidget(self.display_auto_detect_check)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Resolution settings
        resolution_group = QGroupBox("Target Resolution")
        resolution_layout = QVBoxLayout()
        
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self.display_width_spin = QSpinBox()
        self.display_width_spin.setMinimum(640)
        self.display_width_spin.setMaximum(7680)
        self.display_width_spin.setValue(1920)
        self.display_width_spin.setToolTip("Target display width in pixels")
        width_layout.addWidget(self.display_width_spin)
        width_layout.addStretch()
        resolution_layout.addLayout(width_layout)
        
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.display_height_spin = QSpinBox()
        self.display_height_spin.setMinimum(480)
        self.display_height_spin.setMaximum(4320)
        self.display_height_spin.setValue(1080)
        self.display_height_spin.setToolTip("Target display height in pixels")
        height_layout.addWidget(self.display_height_spin)
        height_layout.addStretch()
        resolution_layout.addLayout(height_layout)
        
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        layout.addStretch()
        
        return tab
    
    def create_sound_tab(self) -> QWidget:
        """Create sound/alert settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Warning sound
        warning_group = QGroupBox("Warning Alert")
        warning_layout = QVBoxLayout()
        
        self.sound_warning_enabled_check = QCheckBox("Enable Warning Sound")
        self.sound_warning_enabled_check.setChecked(True)
        self.sound_warning_enabled_check.setToolTip("Play sound when timer warning threshold is reached")
        warning_layout.addWidget(self.sound_warning_enabled_check)
        
        warning_volume_layout = QHBoxLayout()
        warning_volume_layout.addWidget(QLabel("Volume:"))
        self.sound_warning_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sound_warning_volume_slider.setMinimum(0)
        self.sound_warning_volume_slider.setMaximum(100)
        self.sound_warning_volume_slider.setValue(80)
        warning_volume_layout.addWidget(self.sound_warning_volume_slider)
        self.sound_warning_volume_label = QLabel("80%")
        warning_volume_layout.addWidget(self.sound_warning_volume_label)
        self.sound_warning_volume_slider.valueChanged.connect(
            lambda v: self.sound_warning_volume_label.setText(f"{v}%")
        )
        warning_layout.addLayout(warning_volume_layout)
        
        warning_sound_layout = QHBoxLayout()
        warning_sound_layout.addWidget(QLabel("Custom Sound:"))
        self.sound_warning_path_edit = QLineEdit()
        self.sound_warning_path_edit.setPlaceholderText("Use default warning sound")
        warning_sound_layout.addWidget(self.sound_warning_path_edit)
        warning_browse_btn = QPushButton("Browse...")
        warning_browse_btn.clicked.connect(lambda: self.browse_sound_file(self.sound_warning_path_edit))
        warning_sound_layout.addWidget(warning_browse_btn)
        warning_layout.addLayout(warning_sound_layout)
        
        test_warning_btn = QPushButton("Test Warning Sound")
        test_warning_btn.clicked.connect(self.test_warning_sound)
        warning_layout.addWidget(test_warning_btn)
        
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        # Finished sound
        finished_group = QGroupBox("Finished Alert")
        finished_layout = QVBoxLayout()
        
        self.sound_finished_enabled_check = QCheckBox("Enable Finished Sound")
        self.sound_finished_enabled_check.setChecked(True)
        self.sound_finished_enabled_check.setToolTip("Play sound when timer reaches zero")
        finished_layout.addWidget(self.sound_finished_enabled_check)
        
        finished_volume_layout = QHBoxLayout()
        finished_volume_layout.addWidget(QLabel("Volume:"))
        self.sound_finished_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sound_finished_volume_slider.setMinimum(0)
        self.sound_finished_volume_slider.setMaximum(100)
        self.sound_finished_volume_slider.setValue(80)
        finished_volume_layout.addWidget(self.sound_finished_volume_slider)
        self.sound_finished_volume_label = QLabel("80%")
        finished_volume_layout.addWidget(self.sound_finished_volume_label)
        self.sound_finished_volume_slider.valueChanged.connect(
            lambda v: self.sound_finished_volume_label.setText(f"{v}%")
        )
        finished_layout.addLayout(finished_volume_layout)
        
        finished_sound_layout = QHBoxLayout()
        finished_sound_layout.addWidget(QLabel("Custom Sound:"))
        self.sound_finished_path_edit = QLineEdit()
        self.sound_finished_path_edit.setPlaceholderText("Use default finished sound")
        finished_sound_layout.addWidget(self.sound_finished_path_edit)
        finished_browse_btn = QPushButton("Browse...")
        finished_browse_btn.clicked.connect(lambda: self.browse_sound_file(self.sound_finished_path_edit))
        finished_sound_layout.addWidget(finished_browse_btn)
        finished_layout.addLayout(finished_sound_layout)
        
        test_finished_btn = QPushButton("Test Finished Sound")
        test_finished_btn.clicked.connect(self.test_finished_sound)
        finished_layout.addWidget(test_finished_btn)
        
        finished_group.setLayout(finished_layout)
        layout.addWidget(finished_group)
        
        layout.addStretch()
        
        return tab
    
    def create_general_tab(self) -> QWidget:
        """Create general preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Language and theme
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("Language:"))
        self.general_language_combo = QComboBox()
        self.general_language_combo.addItems(["English (en)"])
        self.general_language_combo.setToolTip("Application language (more languages coming soon)")
        language_layout.addWidget(self.general_language_combo)
        language_layout.addStretch()
        appearance_layout.addLayout(language_layout)
        
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.general_theme_combo = QComboBox()
        self.general_theme_combo.addItems(["Dark", "Light"])
        self.general_theme_combo.setToolTip("Application color theme")
        theme_layout.addWidget(self.general_theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("UI Font Size:"))
        self.general_font_spin = QSpinBox()
        self.general_font_spin.setMinimum(8)
        self.general_font_spin.setMaximum(24)
        self.general_font_spin.setValue(12)
        self.general_font_spin.setToolTip("Base font size for user interface")
        font_size_layout.addWidget(self.general_font_spin)
        font_size_layout.addStretch()
        appearance_layout.addLayout(font_size_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Accessibility
        accessibility_group = QGroupBox("Accessibility")
        accessibility_layout = QVBoxLayout()
        
        self.general_high_contrast_check = QCheckBox("High Contrast Mode")
        self.general_high_contrast_check.setToolTip("Increase contrast for better visibility")
        accessibility_layout.addWidget(self.general_high_contrast_check)
        
        self.general_projector_check = QCheckBox("Optimize for Projector Display")
        self.general_projector_check.setChecked(True)
        self.general_projector_check.setToolTip("Optimize colors and contrast for projector screens")
        accessibility_layout.addWidget(self.general_projector_check)
        
        accessibility_group.setLayout(accessibility_layout)
        layout.addWidget(accessibility_group)
        
        # Auto-save
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QVBoxLayout()
        
        self.general_autosave_check = QCheckBox("Enable Auto-Save")
        self.general_autosave_check.setChecked(True)
        self.general_autosave_check.setToolTip("Automatically save configuration changes")
        autosave_layout.addWidget(self.general_autosave_check)
        
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("Backup Interval (seconds):"))
        self.general_backup_spin = QSpinBox()
        self.general_backup_spin.setMinimum(60)
        self.general_backup_spin.setMaximum(3600)
        self.general_backup_spin.setValue(300)
        self.general_backup_spin.setToolTip("Time between automatic configuration backups")
        backup_layout.addWidget(self.general_backup_spin)
        backup_layout.addStretch()
        autosave_layout.addLayout(backup_layout)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        layout.addStretch()
        
        return tab
    
    def create_assets_tab(self) -> QWidget:
        """Create assets management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Logo
        logo_group = QGroupBox("Branding Logo")
        logo_layout = QVBoxLayout()
        
        logo_path_layout = QHBoxLayout()
        logo_path_layout.addWidget(QLabel("Logo Path:"))
        self.assets_logo_edit = QLineEdit()
        self.assets_logo_edit.setPlaceholderText("No logo selected")
        logo_path_layout.addWidget(self.assets_logo_edit)
        logo_browse_btn = QPushButton("Browse...")
        logo_browse_btn.clicked.connect(self.browse_logo)
        logo_path_layout.addWidget(logo_browse_btn)
        logo_layout.addLayout(logo_path_layout)
        
        # Logo preview
        self.logo_preview_label = QLabel("No logo")
        self.logo_preview_label.setMinimumHeight(100)
        self.logo_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview_label.setStyleSheet("border: 1px solid #3d3d3d; background-color: #2d2d2d;")
        logo_layout.addWidget(self.logo_preview_label)
        
        self.assets_branding_check = QCheckBox("Enable Branding Display")
        self.assets_branding_check.setToolTip("Show logo in presentation overlays")
        logo_layout.addWidget(self.assets_branding_check)
        
        logo_group.setLayout(logo_layout)
        layout.addWidget(logo_group)
        
        # Colors
        colors_group = QGroupBox("Custom Colors")
        colors_layout = QVBoxLayout()
        
        primary_color_layout = QHBoxLayout()
        primary_color_layout.addWidget(QLabel("Primary Color:"))
        self.assets_primary_color_btn = QPushButton("#ffffff")
        self.assets_primary_color_btn.setMaximumWidth(100)
        self.assets_primary_color_btn.clicked.connect(lambda: self.choose_color(self.assets_primary_color_btn))
        primary_color_layout.addWidget(self.assets_primary_color_btn)
        primary_color_layout.addStretch()
        colors_layout.addLayout(primary_color_layout)
        
        secondary_color_layout = QHBoxLayout()
        secondary_color_layout.addWidget(QLabel("Secondary Color:"))
        self.assets_secondary_color_btn = QPushButton("#000000")
        self.assets_secondary_color_btn.setMaximumWidth(100)
        self.assets_secondary_color_btn.clicked.connect(lambda: self.choose_color(self.assets_secondary_color_btn))
        secondary_color_layout.addWidget(self.assets_secondary_color_btn)
        secondary_color_layout.addStretch()
        colors_layout.addLayout(secondary_color_layout)
        
        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)
        
        layout.addStretch()
        
        return tab
    
    # Helper methods for file dialogs
    def browse_logo(self):
        """Browse for logo file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.svg);;All Files (*.*)"
        )
        if file:
            self.assets_logo_edit.setText(file)
            # Update preview
            pixmap = QPixmap(file)
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_preview_label.setPixmap(scaled)
    
    def browse_sound_file(self, line_edit: QLineEdit):
        """Browse for sound file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sound File",
            "",
            "Audio Files (*.wav *.mp3 *.ogg);;All Files (*.*)"
        )
        if file:
            line_edit.setText(file)
    
    def choose_color(self, button: QPushButton):
        """Choose color using color dialog."""
        current_color = QColor(button.text())
        color = QColorDialog.getColor(current_color, self, "Choose Color")
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet(f"background-color: {color.name()};")
    
    # Profile management methods
    def refresh_profiles(self):
        """Refresh profile list."""
        self.profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        if "Default" not in profiles:
            self.profile_combo.addItem("Default")
        for profile_name in profiles:
            self.profile_combo.addItem(profile_name)
        self.profile_combo.setCurrentText(self._current_profile_name)
    
    def on_profile_selected(self, profile_name: str):
        """Handle profile selection."""
        if profile_name != self._current_profile_name:
            self.save_current_profile()
            self.load_profile(profile_name)
    
    def create_new_profile(self):
        """Create new configuration profile."""
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_profile_data()
            if data['name']:
                # Create new profile with current config
                profile = ConfigProfile(
                    data['name'],
                    self.config_manager.get_all_config(),
                    data['description']
                )
                if self.profile_manager.save_profile(profile):
                    self.refresh_profiles()
                    self._current_profile_name = profile.name
                    self.profile_combo.setCurrentText(profile.name)
                    self.statusBar().showMessage(f"Created profile: {profile.name}", 3000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to create profile.")
            else:
                QMessageBox.warning(self, "Error", "Profile name cannot be empty.")
    
    def import_profile(self):
        """Import profile from file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Import Profile",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file:
            if self.profile_manager.import_profile(Path(file)):
                self.refresh_profiles()
                self.statusBar().showMessage("Profile imported successfully", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to import profile.")
    
    def export_profile(self):
        """Export current profile to file."""
        profile_name = self.profile_combo.currentText()
        if profile_name == "Default":
            # Export current config as new profile
            file, _ = QFileDialog.getSaveFileName(
                self,
                "Export Profile",
                f"{profile_name}.json",
                "JSON Files (*.json);;All Files (*.*)"
            )
            if file:
                config_data = self.config_manager.get_all_config()
                profile = ConfigProfile(profile_name, config_data)
                if self.profile_manager.export_profile(profile.name, Path(file)):
                    self.statusBar().showMessage("Profile exported successfully", 3000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to export profile.")
        else:
            file, _ = QFileDialog.getSaveFileName(
                self,
                "Export Profile",
                f"{profile_name}.json",
                "JSON Files (*.json);;All Files (*.*)"
            )
            if file:
                if self.profile_manager.export_profile(profile_name, Path(file)):
                    self.statusBar().showMessage("Profile exported successfully", 3000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to export profile.")
    
    def delete_profile(self):
        """Delete selected profile."""
        profile_name = self.profile_combo.currentText()
        if profile_name == "Default":
            QMessageBox.information(self, "Cannot Delete", "Default profile cannot be deleted.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self.refresh_profiles()
                self.load_profile("Default")
                self.statusBar().showMessage(f"Deleted profile: {profile_name}", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to delete profile.")
    
    def load_profile(self, profile_name: str):
        """Load a configuration profile."""
        if profile_name == "Default":
            # Load default config
            self.config_manager.set_all_config(self.config_manager._get_default_config())
        else:
            profile = self.profile_manager.load_profile(profile_name)
            if profile:
                self.config_manager.set_all_config(profile.config_data)
            else:
                QMessageBox.warning(self, "Error", f"Failed to load profile: {profile_name}")
                return
        
        self._current_profile_name = profile_name
        self.load_config_to_ui()
        self.statusBar().showMessage(f"Loaded profile: {profile_name}", 2000)
    
    def save_current_profile(self):
        """Save current configuration to profile."""
        self.save_ui_to_config()
        
        if self._current_profile_name == "Default":
            # Save to main config file
            self.config_manager.save_config()
        else:
            # Save to profile
            profile = ConfigProfile(
                self._current_profile_name,
                self.config_manager.get_all_config(),
                ""
            )
            self.profile_manager.save_profile(profile)
    
    # Configuration load/save methods
    def load_config_to_ui(self):
        """Load configuration from manager to UI."""
        config = self.config_manager.get_all_config()
        
        # Timer settings
        timer_config = config.get('timer', {})
        self.timer_duration_spin.setValue(timer_config.get('default_duration', 300) // 60)
        mode = timer_config.get('mode', 'countdown')
        self.timer_mode_combo.setCurrentIndex(0 if mode == 'countdown' else 1)
        color_scheme = timer_config.get('color_scheme', 'gradient')
        color_index = {'gradient': 0, 'solid': 1, 'custom': 3}.get(color_scheme, 0)
        self.timer_color_combo.setCurrentIndex(color_index)
        self.timer_font_spin.setValue(timer_config.get('font_size', 72))
        self.timer_show_seconds_check.setChecked(timer_config.get('show_seconds', True))
        self.timer_warning_enabled_check.setChecked(timer_config.get('show_warning', True))
        self.timer_warning_threshold_spin.setValue(timer_config.get('warning_threshold', 120))
        
        # Media settings
        media_config = config.get('media', {})
        self.media_auto_play_check.setChecked(media_config.get('auto_play', False))
        self.media_auto_advance_check.setChecked(media_config.get('auto_advance', False))
        self.media_fullscreen_on_play_check.setChecked(media_config.get('fullscreen_on_play', False))
        transition = media_config.get('default_transition', 'fade')
        transition_index = {'fade': 0, 'slide': 1, 'blur': 2, 'none': 3}.get(transition, 0)
        self.media_transition_combo.setCurrentIndex(transition_index)
        self.media_aspect_ratio_check.setChecked(media_config.get('maintain_aspect_ratio', True))
        
        # Face AI settings
        face_ai_config = config.get('face_ai', {})
        self.face_ai_enabled_check.setChecked(face_ai_config.get('enabled', False))
        self.face_ai_camera_spin.setValue(face_ai_config.get('camera_index', 0))
        self.face_ai_sampling_spin.setValue(face_ai_config.get('sampling_frequency', 2))
        threshold = int(face_ai_config.get('attention_threshold', 0.5) * 100)
        self.face_ai_threshold_slider.setValue(threshold)
        self.face_ai_emotion_check.setChecked(face_ai_config.get('enable_emotion_detection', True))
        self.face_ai_gaze_check.setChecked(face_ai_config.get('enable_gaze_tracking', False))
        chart = face_ai_config.get('chart_type', 'bar')
        chart_index = {'bar': 0, 'pie': 1, 'line': 2}.get(chart, 0)
        self.face_ai_chart_combo.setCurrentIndex(chart_index)
        
        # Display settings
        display_config = config.get('display', {})
        mode = display_config.get('mode', 'extended')
        self.display_mode_combo.setCurrentIndex(0 if mode == 'extended' else 1)
        self.display_auto_detect_check.setChecked(display_config.get('auto_detect', True))
        res = display_config.get('target_resolution', {})
        self.display_width_spin.setValue(res.get('width', 1920))
        self.display_height_spin.setValue(res.get('height', 1080))
        
        # Sound settings
        sound_config = config.get('sound', {})
        self.sound_warning_enabled_check.setChecked(sound_config.get('warning_enabled', True))
        self.sound_warning_volume_slider.setValue(sound_config.get('warning_volume', 80))
        self.sound_warning_path_edit.setText(sound_config.get('custom_warning_sound', ''))
        self.sound_finished_enabled_check.setChecked(sound_config.get('finished_enabled', True))
        self.sound_finished_volume_slider.setValue(sound_config.get('finished_volume', 80))
        self.sound_finished_path_edit.setText(sound_config.get('custom_finished_sound', ''))
        
        # General settings
        general_config = config.get('general', {})
        language = general_config.get('language', 'en')
        self.general_language_combo.setCurrentIndex(0)  # Only English for now
        theme = general_config.get('theme', 'dark')
        self.general_theme_combo.setCurrentIndex(0 if theme == 'dark' else 1)
        self.general_font_spin.setValue(general_config.get('font_size', 12))
        self.general_high_contrast_check.setChecked(general_config.get('high_contrast', False))
        self.general_projector_check.setChecked(general_config.get('optimize_for_projector', True))
        self.general_autosave_check.setChecked(general_config.get('auto_save', True))
        self.general_backup_spin.setValue(general_config.get('backup_interval', 300))
        
        # Assets
        assets_config = config.get('assets', {})
        self.assets_logo_edit.setText(assets_config.get('logo_path', ''))
        if self.assets_logo_edit.text():
            pixmap = QPixmap(self.assets_logo_edit.text())
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_preview_label.setPixmap(scaled)
        self.assets_branding_check.setChecked(assets_config.get('branding_enabled', False))
        colors = assets_config.get('custom_colors', {})
        self.assets_primary_color_btn.setText(colors.get('primary', '#ffffff'))
        self.assets_secondary_color_btn.setText(colors.get('secondary', '#000000'))
    
    def save_ui_to_config(self):
        """Save UI values to configuration manager."""
        config = {}
        
        # Timer settings
        config['timer'] = {
            'default_duration': self.timer_duration_spin.value() * 60,
            'mode': 'countdown' if self.timer_mode_combo.currentIndex() == 0 else 'countup',
            'show_warning': self.timer_warning_enabled_check.isChecked(),
            'warning_threshold': self.timer_warning_threshold_spin.value(),
            'color_scheme': ['gradient', 'solid', 'solid', 'custom'][self.timer_color_combo.currentIndex()],
            'font_size': self.timer_font_spin.value(),
            'show_seconds': self.timer_show_seconds_check.isChecked()
        }
        
        # Media settings
        config['media'] = {
            'auto_play': self.media_auto_play_check.isChecked(),
            'auto_advance': self.media_auto_advance_check.isChecked(),
            'fullscreen_on_play': self.media_fullscreen_on_play_check.isChecked(),
            'default_transition': ['fade', 'slide', 'blur', 'none'][self.media_transition_combo.currentIndex()],
            'maintain_aspect_ratio': self.media_aspect_ratio_check.isChecked(),
            'supported_formats': [".pdf", ".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"]
        }
        
        # Face AI settings
        config['face_ai'] = {
            'enabled': self.face_ai_enabled_check.isChecked(),
            'camera_index': self.face_ai_camera_spin.value(),
            'sampling_frequency': self.face_ai_sampling_spin.value(),
            'attention_threshold': self.face_ai_threshold_slider.value() / 100.0,
            'enable_emotion_detection': self.face_ai_emotion_check.isChecked(),
            'enable_gaze_tracking': self.face_ai_gaze_check.isChecked(),
            'chart_type': ['bar', 'pie', 'line'][self.face_ai_chart_combo.currentIndex()]
        }
        
        # Display settings
        config['display'] = {
            'mode': 'extended' if self.display_mode_combo.currentIndex() == 0 else 'mirror',
            'auto_detect': self.display_auto_detect_check.isChecked(),
            'target_resolution': {
                'width': self.display_width_spin.value(),
                'height': self.display_height_spin.value()
            }
        }
        
        # Sound settings
        config['sound'] = {
            'warning_enabled': self.sound_warning_enabled_check.isChecked(),
            'warning_volume': self.sound_warning_volume_slider.value(),
            'custom_warning_sound': self.sound_warning_path_edit.text(),
            'finished_enabled': self.sound_finished_enabled_check.isChecked(),
            'finished_volume': self.sound_finished_volume_slider.value(),
            'custom_finished_sound': self.sound_finished_path_edit.text()
        }
        
        # General settings
        config['general'] = {
            'language': 'en',
            'theme': 'dark' if self.general_theme_combo.currentIndex() == 0 else 'light',
            'font_size': self.general_font_spin.value(),
            'high_contrast': self.general_high_contrast_check.isChecked(),
            'optimize_for_projector': self.general_projector_check.isChecked(),
            'auto_save': self.general_autosave_check.isChecked(),
            'backup_interval': self.general_backup_spin.value()
        }
        
        # Assets
        config['assets'] = {
            'logo_path': self.assets_logo_edit.text(),
            'branding_enabled': self.assets_branding_check.isChecked(),
            'custom_colors': {
                'primary': self.assets_primary_color_btn.text(),
                'secondary': self.assets_secondary_color_btn.text()
            }
        }
        
        self.config_manager.set_all_config(config)
    
    def save_configuration(self):
        """Save configuration and emit signal."""
        self.save_ui_to_config()
        self.save_current_profile()
        self.config_changed.emit(self.config_manager.get_all_config())
        self.statusBar().showMessage("Configuration saved successfully", 3000)
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.set_all_config(self.config_manager._get_default_config())
            self.load_config_to_ui()
            self.statusBar().showMessage("Settings reset to defaults", 3000)
    
    def preview_changes(self):
        """Preview configuration changes."""
        self.save_ui_to_config()
        self._preview_timer.start(100)  # Small delay before preview
    
    def _update_previews(self):
        """Update preview displays (called by timer)."""
        # In full implementation, would update preview widgets
        self.statusBar().showMessage("Preview updated", 2000)
    
    def test_warning_sound(self):
        """Test warning sound."""
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtCore import QUrl
        sound_path = self.sound_warning_path_edit.text() or str(
            self.config_manager.get_asset_path("warning_beep.wav")
        )
        if Path(sound_path).exists():
            sound = QMediaPlayer()
            sound.setSource(QUrl.fromLocalFile(str(Path(sound_path).resolve())))
            sound.play()
            self.statusBar().showMessage("Playing warning sound...", 2000)
        else:
            QMessageBox.warning(self, "Error", "Warning sound file not found.")
    
    def test_finished_sound(self):
        """Test finished sound."""
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtCore import QUrl
        sound_path = self.sound_finished_path_edit.text() or str(
            self.config_manager.get_asset_path("finished_beep.wav")
        )
        if Path(sound_path).exists():
            sound = QMediaPlayer()
            sound.setSource(QUrl.fromLocalFile(str(Path(sound_path).resolve())))
            sound.play()
            self.statusBar().showMessage("Playing finished sound...", 2000)
        else:
            QMessageBox.warning(self, "Error", "Finished sound file not found.")
    
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        save_action = file_menu.addAction("Save Configuration")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_configuration)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About Configuration")
        about_action.triggered.connect(self.show_about)
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Configuration",
            "<h2>AI-Symp-Controller - Configuration</h2>"
            "<p><b>Version 1.0.0</b></p>"
            "<p>Centralized configuration management for all application modules.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Timer, Media, Face AI, Display settings</li>"
            "<li>Sound and alert configuration</li>"
            "<li>Asset management (logos, colors)</li>"
            "<li>Profile management (save/load/export)</li>"
            "<li>Real-time preview</li>"
            "</ul>"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.general_autosave_check.isChecked():
            self.save_configuration()
        event.accept()

