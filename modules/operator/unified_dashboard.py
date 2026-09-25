"""
Unified Dashboard - Master Control Panel

Dashboard یکپارچه برای کنترل و نظارت بر همه ماژول‌ها
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QProgressBar, QComboBox, QSpinBox, QCheckBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
from typing import Optional
import asyncio

from .unified_controller import UnifiedController
from ..utils.device_manager import get_device_manager


class UnifiedDashboard(QMainWindow):
    """
    Unified Dashboard for all modules.
    
    Features:
    - Module status overview
    - Centralized controls
    - Unified statistics
    - Session management
    - Emergency controls
    """
    
    def __init__(self, unified_controller: UnifiedController, parent=None):
        super().__init__(parent)
        
        try:
            self.unified_controller = unified_controller
            self.device_manager = get_device_manager()
            
            self._init_ui()
            self._start_monitoring()
            
            self.setWindowTitle("Unified Control Dashboard")
            self.setMinimumSize(1400, 900)
        except Exception as e:
            print(f"Error initializing Unified Dashboard: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _init_ui(self):
        """Initialize UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main tabs
        tabs = QTabWidget()
        
        # Tab 1: Overview
        overview_tab = self._create_overview_tab()
        tabs.addTab(overview_tab, "Overview")
        
        # Tab 2: Module Control
        control_tab = self._create_control_tab()
        tabs.addTab(control_tab, "Control")
        
        # Tab 3: Statistics
        stats_tab = self._create_stats_tab()
        tabs.addTab(stats_tab, "Statistics")
        
        # Tab 4: Devices
        devices_tab = self._create_devices_tab()
        tabs.addTab(devices_tab, "Devices")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background: #e8f5e9; border-radius: 3px;")
        layout.addWidget(self.status_label)
    
    def _create_header(self) -> QWidget:
        """Create header with quick actions."""
        header = QGroupBox("Unified Control Panel")
        layout = QHBoxLayout(header)
        
        # Quick start button
        self.btn_start_session = QPushButton("Start Full Session")
        self.btn_start_session.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_start_session.clicked.connect(self._on_start_session)
        layout.addWidget(self.btn_start_session)
        
        # Stop button
        self.btn_stop_session = QPushButton("Stop Session")
        self.btn_stop_session.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.btn_stop_session.clicked.connect(self._on_stop_session)
        self.btn_stop_session.setEnabled(False)
        layout.addWidget(self.btn_stop_session)
        
        # Emergency stop
        self.btn_emergency = QPushButton("EMERGENCY STOP")
        self.btn_emergency.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.btn_emergency.clicked.connect(self._on_emergency)
        layout.addWidget(self.btn_emergency)
        
        layout.addStretch()
        
        # Session info
        self.session_label = QLabel("Session: None")
        self.session_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.session_label)
        
        return header
    
    def _create_overview_tab(self) -> QWidget:
        """Create overview tab."""
        # Scroll area for overview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Module status table
        status_group = QGroupBox("Module Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_table = QTableWidget(0, 4)
        self.status_table.setHorizontalHeaderLabels([
            "Module", "Status", "Details", "Actions"
        ])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.setMinimumHeight(200)
        status_layout.addWidget(self.status_table)
        
        layout.addWidget(status_group)
        
        # Quick stats
        stats_group = QGroupBox("Quick Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        self.stat_engagement = QLabel("Engagement: --")
        self.stat_faces = QLabel("Faces: --")
        self.stat_timer = QLabel("Timer: --")
        self.stat_content = QLabel("Content: --")
        
        for label in [self.stat_engagement, self.stat_faces, self.stat_timer, self.stat_content]:
            label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_group)
        
        # Set content widget to scroll area
        scroll.setWidget(widget)
        
        return scroll
    
    def _create_control_tab(self) -> QWidget:
        """Create control tab with individual module controls."""
        # Main widget with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Device selection
        devices_group = QGroupBox("Device Configuration")
        devices_layout = QVBoxLayout(devices_group)
        devices_layout.setSpacing(10)
        
        # Camera selection
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(QLabel("Presenter Camera:"))
        self.combo_presenter_cam = QComboBox()
        self._populate_cameras(self.combo_presenter_cam)
        cam_layout.addWidget(self.combo_presenter_cam)
        devices_layout.addLayout(cam_layout)
        
        cam_layout2 = QHBoxLayout()
        cam_layout2.addWidget(QLabel("Audience Camera:"))
        self.combo_audience_cam = QComboBox()
        self._populate_cameras(self.combo_audience_cam)
        cam_layout2.addWidget(self.combo_audience_cam)
        devices_layout.addLayout(cam_layout2)
        
        # Microphone selection
        mic_layout = QHBoxLayout()
        mic_layout.addWidget(QLabel("Laptop Microphone:"))
        self.combo_microphone = QComboBox()
        self._populate_microphones(self.combo_microphone)
        mic_layout.addWidget(self.combo_microphone)
        devices_layout.addLayout(mic_layout)
        
        layout.addWidget(devices_group)
        
        # Individual Module Controls
        modules_group = QGroupBox("Individual Module Controls")
        modules_layout = QVBoxLayout(modules_group)
        modules_layout.setSpacing(10)
        
        # Timer Module
        timer_group = self._create_module_control_group(
            "Timer",
            "timer",
            [
                ("Start", self._start_timer),
                ("Stop", self._stop_timer),
                ("Pause", self._pause_timer),
                ("Resume", self._resume_timer)
            ]
        )
        modules_layout.addWidget(timer_group)
        
        # Face AI Module
        face_ai_group = self._create_module_control_group(
            "Face AI",
            "face_ai",
            [
                ("Start", self._start_face_ai),
                ("Stop", self._stop_face_ai)
            ],
            extra_controls=[
                ("FPS", QSpinBox, {"minimum": 5, "maximum": 30, "value": 15, "suffix": " fps"})
            ]
        )
        modules_layout.addWidget(face_ai_group)
        
        # AI Timing Module
        ai_timing_group = self._create_module_control_group(
            "AI Timing",
            "ai_timing",
            [
                ("Start", self._start_ai_timing),
                ("Stop", self._stop_ai_timing)
            ],
            extra_controls=[
                ("Voice Detection", "checkbox", {"checked": True})
            ]
        )
        modules_layout.addWidget(ai_timing_group)
        
        # Content Automation Module
        content_group = self._create_module_control_group(
            "Content Automation",
            "content_automation",
            [
                ("Start", self._start_content_automation),
                ("Stop", self._stop_content_automation)
            ]
        )
        modules_layout.addWidget(content_group)
        
        # Display Module
        display_group = self._create_module_control_group(
            "Display",
            "display",
            [
                ("Refresh", self._refresh_display),
                ("Stop", self._stop_display)
            ]
        )
        modules_layout.addWidget(display_group)
        
        # Media Module
        media_group = self._create_module_control_group(
            "Media",
            "media",
            [
                ("Start", self._start_media),
                ("Stop", self._stop_media),
                ("Pause", self._pause_media),
                ("Resume", self._resume_media)
            ]
        )
        modules_layout.addWidget(media_group)
        
        layout.addWidget(modules_group)
        
        # Set content widget to scroll area
        scroll.setWidget(content_widget)
        
        # Return scroll area as the tab widget
        return scroll
    
    def _create_module_control_group(
        self,
        module_name: str,
        module_id: str,
        buttons: list,
        extra_controls: Optional[list] = None
    ) -> QGroupBox:
        """Create a control group for a specific module."""
        group = QGroupBox(module_name)
        layout = QVBoxLayout(group)
        
        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        status_label = QLabel("Inactive")
        status_label.setStyleSheet("color: red; font-weight: bold;")
        status_label.setObjectName(f"{module_id}_status")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        for btn_text, btn_handler in buttons:
            btn = QPushButton(btn_text)
            btn.clicked.connect(lambda checked, h=btn_handler: h())
            btn.setObjectName(f"{module_id}_{btn_text.lower()}")
            buttons_layout.addWidget(btn)
        layout.addLayout(buttons_layout)
        
        # Extra controls
        if extra_controls:
            extra_layout = QHBoxLayout()
            for control_name, control_type, control_params in extra_controls:
                extra_layout.addWidget(QLabel(f"{control_name}:"))
                if control_type == QSpinBox:
                    control = QSpinBox()
                    for key, value in control_params.items():
                        setattr(control, key, value)
                    control.setObjectName(f"{module_id}_{control_name.lower().replace(' ', '_')}")
                elif control_type == "checkbox":
                    control = QCheckBox()
                    if "checked" in control_params:
                        control.setChecked(control_params["checked"])
                    control.setObjectName(f"{module_id}_{control_name.lower().replace(' ', '_')}")
                else:
                    control = QLabel("N/A")
                extra_layout.addWidget(control)
            layout.addLayout(extra_layout)
        
        return group
    
    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab."""
        # Stats display (QTextEdit has built-in scroll)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.stats_text)
        
        return widget
    
    def _create_devices_tab(self) -> QWidget:
        """Create devices tab."""
        # Scroll area for devices
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Cameras
        cameras_group = QGroupBox("Available Cameras")
        cameras_layout = QVBoxLayout(cameras_group)
        
        self.cameras_table = QTableWidget(0, 3)
        self.cameras_table.setHorizontalHeaderLabels(["Index", "Name", "Status"])
        self.cameras_table.setMinimumHeight(150)
        cameras_layout.addWidget(self.cameras_table)
        
        layout.addWidget(cameras_group)
        
        # Microphones
        mics_group = QGroupBox("Available Microphones")
        mics_layout = QVBoxLayout(mics_group)
        
        self.mics_table = QTableWidget(0, 3)
        self.mics_table.setHorizontalHeaderLabels(["Index", "Name", "Status"])
        self.mics_table.setMinimumHeight(150)
        mics_layout.addWidget(self.mics_table)
        
        layout.addWidget(mics_group)
        
        # Refresh button
        btn_refresh = QPushButton("Refresh Devices")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_refresh.clicked.connect(self._refresh_devices)
        layout.addWidget(btn_refresh)
        
        # Set content widget to scroll area
        scroll.setWidget(widget)
        
        # Initial load
        self._refresh_devices()
        
        return scroll
    
    def _populate_cameras(self, combo: QComboBox):
        """Populate camera combo box."""
        try:
            cameras = self.device_manager.get_available_cameras(test=True)
            for cam in cameras:
                if cam.get('available', False):
                    name = cam.get('name', f'Camera {cam["index"]}')
                    combo.addItem(f"Camera {cam['index']}: {name}", cam['index'])
            # Add default if no cameras
            if combo.count() == 0:
                combo.addItem("Camera 0 (Default)", 0)
        except Exception as e:
            print(f"Error populating cameras: {e}")
            combo.addItem("Camera 0 (Default)", 0)
    
    def _populate_microphones(self, combo: QComboBox):
        """Populate microphone combo box."""
        try:
            microphones = self.device_manager.get_available_microphones()
            for mic in microphones:
                mic_index = mic.get('index')
                mic_name = mic.get('name', f'Microphone {mic_index}')
                combo.addItem(f"Mic {mic_index}: {mic_name}", mic_index)
            # Add default if no microphones
            if combo.count() == 0:
                combo.addItem("Microphone 0 (Default)", 0)
        except Exception as e:
            print(f"Error populating microphones: {e}")
            combo.addItem("Microphone 0 (Default)", 0)
    
    def _start_monitoring(self):
        """Start periodic UI updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)  # Update every second
    
    def _update_ui(self):
        """Update UI with current state."""
        # Update module status
        self._update_module_status()
        
        # Update statistics
        self._update_statistics()
        
        # Update session info
        session_id = self.unified_controller.get_current_session_id()
        if session_id:
            self.session_label.setText(f"Session: {session_id}")
            self.btn_start_session.setEnabled(False)
            self.btn_stop_session.setEnabled(True)
        else:
            self.session_label.setText("Session: None")
            self.btn_start_session.setEnabled(True)
            self.btn_stop_session.setEnabled(False)
    
    def _update_module_status(self):
        """Update module status table and individual module status labels."""
        try:
            if not self.unified_controller:
                return
            
            status = self.unified_controller.get_module_status()
            
            if not status:
                return
            
            modules = [
                ('Timer', 'timer', status.get('timer', {})),
                ('Face AI', 'face_ai', status.get('face_ai', {})),
                ('AI Timing', 'ai_timing', status.get('ai_timing', {})),
                ('Content Automation', 'content_automation', status.get('content_automation', {})),
                ('Display', 'display', status.get('display', {})),
                ('Session', 'session', status.get('session', {}))
            ]
        except Exception as e:
            print(f"Error updating module status: {e}")
            return
        
        self.status_table.setRowCount(len(modules))
        
        for row, (name, module_id, state) in enumerate(modules):
            # Module name
            self.status_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Status
            is_active = state.get('active', False)
            status_item = QTableWidgetItem("Active" if is_active else "Inactive")
            if is_active:
                status_item.setBackground(QColor("#c8e6c9"))
            else:
                status_item.setBackground(QColor("#ffcdd2"))
            self.status_table.setItem(row, 1, status_item)
            
            # Details
            details = []
            if name == 'Timer' and state.get('running'):
                details.append("Running")
                time_remaining = state.get('time_remaining')
                if time_remaining:
                    details.append(f"{time_remaining}s")
            if name == 'Face AI' and state.get('analyzing'):
                details.append("Analyzing")
            if name == 'AI Timing' and state.get('is_active'):
                details.append("Active")
            if name == 'Content Automation' and state.get('running'):
                details.append("Running")
            if name == 'Display':
                screens = state.get('screens', 0)
                details.append(f"{screens} screens")
            details_text = ", ".join(details) if details else "Ready"
            self.status_table.setItem(row, 2, QTableWidgetItem(details_text))
            
            # Actions
            self.status_table.setItem(row, 3, QTableWidgetItem("--"))
            
            # Update individual module status labels
            if module_id != 'session':
                self._update_module_status_label(module_id, is_active)
    
    def _update_statistics(self):
        """Update statistics display."""
        try:
            if not self.unified_controller:
                return
            
            stats = self.unified_controller.get_unified_stats()
            
            if not stats:
                return
            
            # Quick stats
            ai_timing_stats = stats.get('ai_timing', {})
            engagement = ai_timing_stats.get('engagement', 0) if isinstance(ai_timing_stats, dict) else 0
            self.stat_engagement.setText(f"Engagement: {engagement:.1f}%")
            
            face_ai_stats = stats.get('face_ai', {})
            faces = face_ai_stats.get('faces_detected', 0) if isinstance(face_ai_stats, dict) else 0
            self.stat_faces.setText(f"Faces: {faces}")
            
            modules_stats = stats.get('modules', {})
            timer_stats = modules_stats.get('timer', {}) if isinstance(modules_stats, dict) else {}
            timer_remaining = timer_stats.get('time_remaining') if isinstance(timer_stats, dict) else None
            timer_text = f"{timer_remaining}s" if timer_remaining else "Stopped"
            self.stat_timer.setText(f"Timer: {timer_text}")
            
            content_stats = modules_stats.get('content_automation', {}) if isinstance(modules_stats, dict) else {}
            content_count = content_stats.get('active', 0) if isinstance(content_stats, dict) else 0
            self.stat_content.setText(f"Content: {content_count}")
        
            # Detailed stats
            session_stats = stats.get('session', {})
            modules_stats = stats.get('modules', {})
            devices_stats = stats.get('devices', {})
            
            stats_text = f"""
=== Unified Statistics ===
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Session:
  Active: {session_stats.get('active', False) if isinstance(session_stats, dict) else False}
  ID: {session_stats.get('session_id', 'None') if isinstance(session_stats, dict) else 'None'}

Modules:
  Timer: {modules_stats.get('timer', {}).get('active', False) if isinstance(modules_stats.get('timer'), dict) else False}
  Face AI: {modules_stats.get('face_ai', {}).get('active', False) if isinstance(modules_stats.get('face_ai'), dict) else False}
  AI Timing: {modules_stats.get('ai_timing', {}).get('active', False) if isinstance(modules_stats.get('ai_timing'), dict) else False}
  Content Automation: {modules_stats.get('content_automation', {}).get('active', False) if isinstance(modules_stats.get('content_automation'), dict) else False}

AI Timing:
  Engagement: {engagement:.1f}%
  Presenter Tracking: {ai_timing_stats.get('presenter_tracking', False) if isinstance(ai_timing_stats, dict) else False}
  Voice Active: {ai_timing_stats.get('voice_active', False) if isinstance(ai_timing_stats, dict) else False}

Face AI:
  Faces Detected: {faces}
  Analyzing: {modules_stats.get('face_ai', {}).get('analyzing', False) if isinstance(modules_stats.get('face_ai'), dict) else False}

Devices:
  Cameras: {devices_stats.get('cameras', 0) if isinstance(devices_stats, dict) else 0}
  Microphones: {devices_stats.get('microphones', 0) if isinstance(devices_stats, dict) else 0}
"""
            self.stats_text.setText(stats_text)
        except Exception as e:
            print(f"Error updating statistics: {e}")
            # Don't crash, just log the error
    
    def _refresh_devices(self):
        """Refresh device lists."""
        try:
            # Cameras
            cameras = self.device_manager.get_available_cameras(test=True)
            available_cameras = [c for c in cameras if c.get('available', False)]
            self.cameras_table.setRowCount(len(available_cameras))
            
            for row, cam in enumerate(available_cameras):
                self.cameras_table.setItem(row, 0, QTableWidgetItem(str(cam.get('index', 0))))
                self.cameras_table.setItem(row, 1, QTableWidgetItem(cam.get('name', f'Camera {cam.get("index", 0)}')))
                status_item = QTableWidgetItem("[OK] Working")
                status_item.setBackground(QColor("#c8e6c9"))
                self.cameras_table.setItem(row, 2, status_item)
            
            # Microphones
            microphones = self.device_manager.get_available_microphones()
            self.mics_table.setRowCount(len(microphones))
            
            for row, mic in enumerate(microphones):
                self.mics_table.setItem(row, 0, QTableWidgetItem(str(mic.get('index', 0))))
                self.mics_table.setItem(row, 1, QTableWidgetItem(mic.get('name', f'Microphone {mic.get("index", 0)}')))
                status_item = QTableWidgetItem("[OK] Available")
                status_item.setBackground(QColor("#c8e6c9"))
                self.mics_table.setItem(row, 2, status_item)
        except Exception as e:
            print(f"Error refreshing devices: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== Event Handlers ==========
    
    def _on_start_session(self):
        """Start full session."""
        presenter_cam = self.combo_presenter_cam.currentData()
        audience_cam = self.combo_audience_cam.currentData()
        mic = self.combo_microphone.currentData()
        
        if presenter_cam is None:
            presenter_cam = 0
        if audience_cam is None:
            audience_cam = 1
        if mic is None:
            mic = self.device_manager.get_laptop_microphone()
        
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self._run_async(self._async_start_session(
            session_id, presenter_cam, audience_cam, mic
        ))
    
    async def _async_start_session(self, session_id, presenter_cam, audience_cam, mic):
        """Start session asynchronously."""
        try:
            success = await self.unified_controller.start_full_session(
                session_id=session_id,
                presenter_camera=presenter_cam,
                audience_camera=audience_cam,
                laptop_microphone=mic,
                enable_ai_timing=True,
                enable_content_automation=True
            )
            
            if success:
                self.status_label.setText(f"✅ Session started: {session_id}")
                self.status_label.setStyleSheet("padding: 5px; background: #c8e6c9; border-radius: 3px;")
            else:
                self.status_label.setText("❌ Failed to start session")
                self.status_label.setStyleSheet("padding: 5px; background: #ffcdd2; border-radius: 3px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("padding: 5px; background: #ffcdd2; border-radius: 3px;")
    
    def _on_stop_session(self):
        """Stop session."""
        self._run_async(self._async_stop_session())
    
    async def _async_stop_session(self):
        """Stop session asynchronously."""
        try:
            await self.unified_controller.stop_full_session()
            self.status_label.setText("✅ Session stopped")
            self.status_label.setStyleSheet("padding: 5px; background: #fff3e0; border-radius: 3px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
    
    def _on_emergency(self):
        """Emergency stop all."""
        self._run_async(self._async_emergency())
    
    async def _async_emergency(self):
        """Emergency stop asynchronously."""
        try:
            # Stop all modules
            await self.unified_controller.stop_full_session()
            
            # Emergency stop content automation
            if self.unified_controller.content_automation:
                await self.unified_controller.content_automation.emergency_stop()
            
            self.status_label.setText("🚨 EMERGENCY STOP")
            self.status_label.setStyleSheet("padding: 5px; background: #ffcdd2; border-radius: 3px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
    
    def _toggle_ai_timing(self):
        """Toggle AI Timing."""
        # Implementation here
        pass
    
    def _toggle_content_automation(self):
        """Toggle Content Automation."""
        # Implementation here
        pass
    
    # ========== Individual Module Handlers ==========
    
    def _start_timer(self):
        """Start timer module."""
        try:
            success = self.unified_controller.start_module("timer")
            self._update_module_status_label("timer", success)
        except Exception as e:
            print(f"Error starting timer: {e}")
            self._update_module_status_label("timer", False)
    
    def _stop_timer(self):
        """Stop timer module."""
        try:
            success = self.unified_controller.stop_module("timer")
            self._update_module_status_label("timer", not success)  # Inactive if stopped
        except Exception as e:
            print(f"Error stopping timer: {e}")
    
    def _pause_timer(self):
        """Pause timer module."""
        try:
            if self.unified_controller.timer_controller:
                self.unified_controller.timer_controller.pause()
                self.status_label.setText("Timer paused")
        except Exception as e:
            print(f"Error pausing timer: {e}")
    
    def _resume_timer(self):
        """Resume timer module."""
        try:
            if self.unified_controller.timer_controller:
                self.unified_controller.timer_controller.resume()
                self.status_label.setText("Timer resumed")
        except Exception as e:
            print(f"Error resuming timer: {e}")
    
    def _start_face_ai(self):
        """Start Face AI module."""
        try:
            # Get FPS from spinbox if exists
            fps = 15
            fps_control = self.findChild(QSpinBox, "face_ai_fps")
            if fps_control:
                fps = fps_control.value()
            
            # Get camera index from combo
            camera_index = self.combo_audience_cam.currentData() or 0
            
            success = self.unified_controller.start_module(
                "face_ai",
                camera_index=camera_index,
                fps=fps
            )
            self._update_module_status_label("face_ai", success)
        except Exception as e:
            print(f"Error starting Face AI: {e}")
            self._update_module_status_label("face_ai", False)
    
    def _stop_face_ai(self):
        """Stop Face AI module."""
        try:
            success = self.unified_controller.stop_module("face_ai")
            self._update_module_status_label("face_ai", not success)
        except Exception as e:
            print(f"Error stopping Face AI: {e}")
    
    def _start_ai_timing(self):
        """Start AI Timing module."""
        try:
            # Get voice detection checkbox
            enable_voice = True
            voice_check = self.findChild(QCheckBox, "ai_timing_voice_detection")
            if voice_check:
                enable_voice = voice_check.isChecked()
            
            # Get camera indices
            presenter_cam = self.combo_presenter_cam.currentData() or 0
            audience_cam = self.combo_audience_cam.currentData() or 1
            mic = self.combo_microphone.currentData()
            
            success = self.unified_controller.start_module(
                "ai_timing",
                presenter_camera=presenter_cam,
                audience_camera=audience_cam,
                enable_voice=enable_voice,
                laptop_microphone=mic
            )
            self._update_module_status_label("ai_timing", success)
        except Exception as e:
            print(f"Error starting AI Timing: {e}")
            self._update_module_status_label("ai_timing", False)
    
    def _stop_ai_timing(self):
        """Stop AI Timing module."""
        try:
            if self.unified_controller:
                success = self.unified_controller.stop_module("ai_timing")
                self._update_module_status_label("ai_timing", not success)
            else:
                print("Unified controller not available")
        except Exception as e:
            print(f"Error stopping AI Timing: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_content_automation(self):
        """Start Content Automation module."""
        try:
            success = self.unified_controller.start_module("content_automation")
            self._update_module_status_label("content_automation", success)
        except Exception as e:
            print(f"Error starting Content Automation: {e}")
            self._update_module_status_label("content_automation", False)
    
    def _stop_content_automation(self):
        """Stop Content Automation module."""
        try:
            success = self.unified_controller.stop_module("content_automation")
            self._update_module_status_label("content_automation", not success)
        except Exception as e:
            print(f"Error stopping Content Automation: {e}")
    
    def _refresh_display(self):
        """Refresh Display module."""
        try:
            success = self.unified_controller.start_module("display")
            self._update_module_status_label("display", success)
            self.status_label.setText("Display refreshed")
        except Exception as e:
            print(f"Error refreshing display: {e}")
    
    def _stop_display(self):
        """Stop Display module."""
        try:
            success = self.unified_controller.stop_module("display")
            self._update_module_status_label("display", not success)
        except Exception as e:
            print(f"Error stopping display: {e}")
    
    def _start_media(self):
        """Start Media module."""
        try:
            success = self.unified_controller.start_module("media")
            self._update_module_status_label("media", success)
        except Exception as e:
            print(f"Error starting media: {e}")
            self._update_module_status_label("media", False)
    
    def _stop_media(self):
        """Stop Media module."""
        try:
            success = self.unified_controller.stop_module("media")
            self._update_module_status_label("media", not success)
        except Exception as e:
            print(f"Error stopping media: {e}")
    
    def _pause_media(self):
        """Pause Media module."""
        try:
            if self.unified_controller and hasattr(self.unified_controller, 'media_controller'):
                if self.unified_controller.media_controller:
                    if hasattr(self.unified_controller.media_controller, 'pause'):
                        self.unified_controller.media_controller.pause()
                        self.status_label.setText("Media paused")
                    else:
                        print("Media controller doesn't have pause method")
        except Exception as e:
            print(f"Error pausing media: {e}")
            import traceback
            traceback.print_exc()
    
    def _resume_media(self):
        """Resume Media module."""
        try:
            if self.unified_controller and hasattr(self.unified_controller, 'media_controller'):
                if self.unified_controller.media_controller:
                    if hasattr(self.unified_controller.media_controller, 'resume'):
                        self.unified_controller.media_controller.resume()
                        self.status_label.setText("Media resumed")
                    else:
                        print("Media controller doesn't have resume method")
        except Exception as e:
            print(f"Error resuming media: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_module_status_label(self, module_id: str, is_active: bool):
        """Update status label for a module."""
        try:
            status_label = self.findChild(QLabel, f"{module_id}_status")
            if status_label:
                if is_active:
                    status_label.setText("Active")
                    status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    status_label.setText("Inactive")
                    status_label.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            print(f"Error updating status label: {e}")
    
    def _run_async(self, coro):
        """Safely run async coroutine."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(coro)
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(coro)
                else:
                    asyncio.run(coro)
            except RuntimeError:
                asyncio.run(coro)
