"""
Operator Dashboard Module

Live dashboard showing AI metrics, timer status, and override controls
for AI-driven adaptive timing system.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QGridLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Optional
import logging

from .ai_integration_controller import AIIntegrationController

logger = logging.getLogger(__name__)


class OperatorDashboard(QWidget):
    """
    Operator dashboard for AI-driven timing system.
    
    Features:
    - Live AI metrics display
    - Timer adaptation status
    - Override controls
    - Event log
    - Extension/reduction confirmation dialogs
    """
    
    # Signals
    override_requested = pyqtSignal()  # Operator requests override
    
    def __init__(self, ai_controller: Optional[AIIntegrationController] = None, parent=None):
        """
        Initialize operator dashboard.
        
        Args:
            ai_controller: AIIntegrationController instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._ai_controller = ai_controller
        
        # UI components
        self._metrics_labels = {}
        self._log_text = None
        self._override_btn = None
        
        self.setup_ui()
        
        # Connect to AI controller if provided
        if self._ai_controller:
            self._connect_signals()
            self.update_metrics()
    
    def setup_ui(self):
        """Setup dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("AI Timing Dashboard")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Scroll area for dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        
        # Metrics section
        metrics_group = self.create_metrics_section()
        content_layout.addWidget(metrics_group)
        
        # Controls section
        controls_group = self.create_controls_section()
        content_layout.addWidget(controls_group)
        
        # Event log section
        log_group = self.create_log_section()
        content_layout.addWidget(log_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def create_metrics_section(self) -> QGroupBox:
        """Create metrics display section."""
        group = QGroupBox("Live AI Metrics")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # Presenter state
        layout.addWidget(QLabel("Presenter State:"), 0, 0)
        self._metrics_labels['presenter_state'] = QLabel("Unknown")
        self._metrics_labels['presenter_state'].setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(self._metrics_labels['presenter_state'], 0, 1)
        
        # Audience engagement
        layout.addWidget(QLabel("Audience Engagement:"), 1, 0)
        self._metrics_labels['audience_engagement'] = QLabel("Unknown")
        self._metrics_labels['audience_engagement'].setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(self._metrics_labels['audience_engagement'], 1, 1)
        
        # Attention percentage
        layout.addWidget(QLabel("Attention Level:"), 2, 0)
        self._metrics_labels['attention_level'] = QLabel("0%")
        self._metrics_labels['attention_level'].setStyleSheet("font-weight: bold;")
        layout.addWidget(self._metrics_labels['attention_level'], 2, 1)
        
        # Timer adaptation mode
        layout.addWidget(QLabel("Timer Adaptation:"), 3, 0)
        self._metrics_labels['adaptation_mode'] = QLabel("Normal")
        self._metrics_labels['adaptation_mode'].setStyleSheet("font-weight: bold; color: #FF9800;")
        layout.addWidget(self._metrics_labels['adaptation_mode'], 3, 1)
        
        # Timer time
        layout.addWidget(QLabel("Timer Time:"), 4, 0)
        self._metrics_labels['timer_time'] = QLabel("00:00")
        self._metrics_labels['timer_time'].setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._metrics_labels['timer_time'], 4, 1)
        
        return group
    
    def create_controls_section(self) -> QGroupBox:
        """Create control buttons section."""
        group = QGroupBox("Controls")
        layout = QVBoxLayout(group)
        
        # Override button
        self._override_btn = QPushButton("Override AI Adaptation")
        self._override_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self._override_btn.clicked.connect(self._on_override_clicked)
        layout.addWidget(self._override_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Metrics")
        refresh_btn.clicked.connect(self.update_metrics)
        layout.addWidget(refresh_btn)
        
        return group
    
    def create_log_section(self) -> QGroupBox:
        """Create event log section."""
        group = QGroupBox("Event Log")
        layout = QVBoxLayout(group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(200)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self._log_text)
        
        return group
    
    def _connect_signals(self):
        """Connect to AI controller signals."""
        if not self._ai_controller:
            return
        
        self._ai_controller.presenter_state_changed.connect(self._on_presenter_state_changed)
        self._ai_controller.audience_engagement_changed.connect(self._on_engagement_changed)
        self._ai_controller.timer_adaptation_changed.connect(self._on_adaptation_changed)
        self._ai_controller.extension_requested.connect(self._on_extension_requested)
        self._ai_controller.reduction_requested.connect(self._on_reduction_requested)
        
        # Connect adaptive timer log signals
        adaptive_timer = self._ai_controller.get_adaptive_timer()
        adaptive_timer.ai_adjustment_logged.connect(self._on_log_entry)
    
    def _on_presenter_state_changed(self, state: str):
        """Handle presenter state change."""
        label = self._metrics_labels.get('presenter_state')
        if label:
            label.setText(state.title())
            
            # Update color based on state
            if state in ["talking", "engaged"]:
                label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            elif state == "away":
                label.setStyleSheet("font-weight: bold; color: #f44336;")
            else:
                label.setStyleSheet("font-weight: bold; color: #FF9800;")
    
    def _on_engagement_changed(self, level: str):
        """Handle engagement level change."""
        label = self._metrics_labels.get('audience_engagement')
        if label:
            label.setText(level.title())
            
            # Update color
            if level == "high":
                label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            elif level == "medium":
                label.setStyleSheet("font-weight: bold; color: #FF9800;")
            else:
                label.setStyleSheet("font-weight: bold; color: #f44336;")
    
    def _on_adaptation_changed(self, mode: str):
        """Handle adaptation mode change."""
        label = self._metrics_labels.get('adaptation_mode')
        if label:
            mode_display = {
                "normal": "Normal",
                "paused_ai": "Paused (AI)",
                "slowed_ai": "Slowed (AI)",
                "extended": "Extended",
                "reduced": "Reduced"
            }
            label.setText(mode_display.get(mode, mode.title()))
    
    def _on_extension_requested(self, seconds: int):
        """Handle extension request."""
        reply = QMessageBox.question(
            self,
            "Timer Extension Request",
            f"AI detected high engagement. Extend timer by {seconds} seconds?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._ai_controller.confirm_extension(seconds)
            self._log_text.append(f"[Extension] Approved: +{seconds} seconds")
        else:
            self._ai_controller.reject_extension(seconds)
            self._log_text.append(f"[Extension] Rejected: +{seconds} seconds")
    
    def _on_reduction_requested(self, seconds: int):
        """Handle reduction request."""
        reply = QMessageBox.question(
            self,
            "Timer Reduction Request",
            f"AI detected low engagement. Reduce timer by {seconds} seconds?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._ai_controller.confirm_reduction(seconds)
            self._log_text.append(f"[Reduction] Approved: -{seconds} seconds")
        else:
            self._ai_controller.reject_reduction(seconds)
            self._log_text.append(f"[Reduction] Rejected: -{seconds} seconds")
    
    def _on_log_entry(self, message: str):
        """Handle log entry from AI system."""
        if self._log_text:
            self._log_text.append(message)
            # Auto-scroll to bottom
            scrollbar = self._log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _on_override_clicked(self):
        """Handle override button click."""
        reply = QMessageBox.question(
            self,
            "Override AI Adaptation",
            "Disable AI-driven timer adaptation and return to normal operation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._ai_controller:
                self._ai_controller.override_ai_adaptation()
            self.override_requested.emit()
            self._log_text.append("[Override] AI adaptation disabled by operator")
    
    def update_metrics(self):
        """Update all metrics from AI controller."""
        if not self._ai_controller:
            return
        
        # Update presenter state
        presenter_state = self._ai_controller.get_presenter_state()
        self._on_presenter_state_changed(presenter_state)
        
        # Update engagement
        engagement = self._ai_controller.get_audience_engagement()
        self._on_engagement_changed(engagement)
        
        # Update adaptation mode
        adaptation = self._ai_controller.get_timer_adaptation_mode()
        self._on_adaptation_changed(adaptation)
        
        # Update timer time
        timer = self._ai_controller.get_base_timer()
        current = timer.get_current_time()
        minutes = current // 60
        seconds = current % 60
        time_label = self._metrics_labels.get('timer_time')
        if time_label:
            time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Update attention level
        analyzer = self._ai_controller._engagement_analyzer
        attention = analyzer.get_attention_percentage()
        attention_label = self._metrics_labels.get('attention_level')
        if attention_label:
            attention_label.setText(f"{int(attention * 100)}%")
    
    def set_ai_controller(self, controller: AIIntegrationController):
        """Set AI integration controller."""
        # Disconnect old signals
        if self._ai_controller:
            try:
                self._ai_controller.presenter_state_changed.disconnect()
                self._ai_controller.audience_engagement_changed.disconnect()
                self._ai_controller.timer_adaptation_changed.disconnect()
                self._ai_controller.extension_requested.disconnect()
                self._ai_controller.reduction_requested.disconnect()
            except:
                pass
        
        self._ai_controller = controller
        self._connect_signals()
        self.update_metrics()

