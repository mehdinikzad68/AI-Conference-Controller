"""
AI Timer Widget Module

UI component for displaying AI-driven timer status, metrics, and controls.
Integrates with AIIntegrationController to show live AI state and allow operator overrides.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QGroupBox, QProgressBar, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from modules.ai_timing import AIIntegrationController
from modules.utils.theme_manager import ThemeManager


class AITimerWidget(QWidget):
    """
    Widget for AI-driven timer control and status display.
    
    Features:
    - Enable/disable AI Timer toggle
    - Live AI status indicators
    - Presenter and audience metrics
    - Manual override controls
    - Event log with scrollable history
    - Visual alerts for warnings
    """
    
    # Signals
    enable_ai_requested = pyqtSignal(bool)  # Request to enable/disable AI
    pause_ai_requested = pyqtSignal()  # Request to pause AI timer
    resume_ai_requested = pyqtSignal()  # Request to resume AI timer
    extend_time_requested = pyqtSignal(int)  # Request to extend time (seconds)
    override_ai_requested = pyqtSignal()  # Request to override AI adaptation
    
    def __init__(self, parent=None):
        """Initialize AI Timer widget."""
        super().__init__(parent)
        
        # Theme manager for dynamic text colors
        self._theme_manager = ThemeManager()
        
        # AI controller (set via set_ai_controller)
        self._ai_controller: Optional[AIIntegrationController] = None
        
        # UI state
        self._ai_enabled = False
        self._alert_blink_timer = QTimer()
        self._alert_blink_timer.timeout.connect(self._toggle_alert_blink)
        self._alert_blinking = False
        
        # Pulse animation for alerts
        # Use a timer-based approach instead of QPropertyAnimation for simpler implementation
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.setInterval(50)  # Update every 50ms for smooth animation
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self._update_text_colors)
        
        # Setup UI
        self.setup_ui()
        
        # Update initial state
        self._update_ui_state()
        
        # Apply dynamic text colors
        self._update_text_colors()
    
    def setup_ui(self):
        """Setup the AI Timer UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # AI Timer Control Group
        control_group = QGroupBox("AI Timer / Smart Timing (Beta)")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(8)
        
        # Enable AI Timer checkbox
        enable_layout = QHBoxLayout()
        self._enable_checkbox = QCheckBox("Enable AI Timer")
        self._enable_checkbox.setToolTip("Enable AI-driven adaptive timing based on presenter and audience engagement")
        # Style will be applied globally via ThemeManager
        # Ensure text is visible
        self._enable_checkbox.setText("Enable AI Timer")
        self._enable_checkbox.stateChanged.connect(self._on_enable_changed)
        enable_layout.addWidget(self._enable_checkbox)
        enable_layout.addStretch()
        control_layout.addLayout(enable_layout)
        
        # Status labels layout
        status_layout = QHBoxLayout()
        
        # AI Status
        ai_status_label = QLabel("AI Status:")
        self._ai_status_value = QLabel("Inactive")
        # Text color will be updated dynamically in _update_text_colors
        status_layout.addWidget(ai_status_label)
        status_layout.addWidget(self._ai_status_value)
        status_layout.addStretch()
        
        control_layout.addLayout(status_layout)
        
        # Presenter State
        presenter_layout = QHBoxLayout()
        presenter_label = QLabel("Presenter:")
        self._presenter_state_value = QLabel("Unknown")
        # Color will be updated dynamically based on state (orange for unknown is fine)
        self._presenter_state_value.setStyleSheet("font-weight: bold; color: #FF9800;")
        presenter_layout.addWidget(presenter_label)
        presenter_layout.addWidget(self._presenter_state_value)
        presenter_layout.addStretch()
        
        control_layout.addLayout(presenter_layout)
        
        # Audience Attention
        audience_layout = QVBoxLayout()
        audience_label_layout = QHBoxLayout()
        audience_label_layout.addWidget(QLabel("Audience Focus:"))
        self._audience_attention_value = QLabel("0%")
        # Color will be updated dynamically (blue for attention value is fine)
        self._audience_attention_value.setStyleSheet("font-weight: bold; color: #2196F3;")
        audience_label_layout.addWidget(self._audience_attention_value)
        audience_label_layout.addStretch()
        
        self._audience_progress = QProgressBar()
        self._audience_progress.setMinimum(0)
        self._audience_progress.setMaximum(100)
        self._audience_progress.setValue(0)
        self._audience_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 2px;
            }
        """)
        
        audience_layout.addLayout(audience_label_layout)
        audience_layout.addWidget(self._audience_progress)
        
        control_layout.addLayout(audience_layout)
        
        # AI Actions/Alerts
        self._ai_alert_label = QLabel("")
        self._ai_alert_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                border-radius: 3px;
                background-color: transparent;
                color: #FF9800;
                font-weight: bold;
            }
        """)
        self._ai_alert_label.setWordWrap(True)
        control_layout.addWidget(self._ai_alert_label)
        
        # Extension/Reduction Confirmation Buttons
        self._extension_layout = QHBoxLayout()
        self._extension_approve_btn = QPushButton("✓ Approve Extension")
        self._extension_approve_btn.setEnabled(False)
        self._extension_approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self._extension_approve_btn.clicked.connect(self._on_approve_extension)
        
        self._extension_reject_btn = QPushButton("✗ Reject Extension")
        self._extension_reject_btn.setEnabled(False)
        self._extension_reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self._extension_reject_btn.clicked.connect(self._on_reject_extension)
        
        self._extension_layout.addWidget(self._extension_approve_btn)
        self._extension_layout.addWidget(self._extension_reject_btn)
        self._extension_layout.addStretch()
        
        self._extension_requested_seconds = 0
        control_layout.addLayout(self._extension_layout)
        
        # Manual Override Controls
        override_layout = QHBoxLayout()
        
        self._pause_ai_btn = QPushButton("Pause AI Timer")
        self._pause_ai_btn.setEnabled(False)
        self._pause_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #aaaaaa;
            }
        """)
        self._pause_ai_btn.clicked.connect(self._on_pause_ai_clicked)
        override_layout.addWidget(self._pause_ai_btn)
        
        self._resume_ai_btn = QPushButton("Resume AI Timer")
        self._resume_ai_btn.setEnabled(False)
        self._resume_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #aaaaaa;
            }
        """)
        self._resume_ai_btn.clicked.connect(self._on_resume_ai_clicked)
        override_layout.addWidget(self._resume_ai_btn)
        
        self._override_btn = QPushButton("Override AI")
        self._override_btn.setEnabled(False)
        self._override_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #aaaaaa;
            }
        """)
        self._override_btn.clicked.connect(self._on_override_clicked)
        override_layout.addWidget(self._override_btn)
        
        # Session Summary Save Button
        self._save_report_btn = QPushButton("Save Session Report")
        self._save_report_btn.setEnabled(False)
        self._save_report_btn.setToolTip("Save AI-driven session summary and event log")
        self._save_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #aaaaaa;
            }
        """)
        self._save_report_btn.clicked.connect(self._on_save_report)
        override_layout.addWidget(self._save_report_btn)
        
        control_layout.addLayout(override_layout)
        
        main_layout.addWidget(control_group)
        
        # Event Log Group
        log_group = QGroupBox("AI Event Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scrollable log area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(150)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        # Text color will be updated dynamically in _update_text_colors
        scroll_area.setWidget(self._log_text)
        
        log_layout.addWidget(scroll_area)
        main_layout.addWidget(log_group)
        
        # Advanced Settings Button
        settings_btn_layout = QHBoxLayout()
        self._settings_btn = QPushButton("⚙ Advanced Settings")
        self._settings_btn.setToolTip("Configure AI thresholds and sensitivity")
        self._settings_btn.clicked.connect(self._show_advanced_settings)
        settings_btn_layout.addWidget(self._settings_btn)
        settings_btn_layout.addStretch()
        main_layout.addLayout(settings_btn_layout)
        
        main_layout.addStretch()
    
    def set_ai_controller(self, controller: Optional[AIIntegrationController]):
        """Set the AI integration controller and connect signals."""
        # Disconnect old controller
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
        
        # Connect new controller
        if self._ai_controller:
            self._ai_controller.presenter_state_changed.connect(self._on_presenter_state_changed)
            self._ai_controller.audience_engagement_changed.connect(self._on_engagement_changed)
            self._ai_controller.timer_adaptation_changed.connect(self._on_adaptation_changed)
            self._ai_controller.extension_requested.connect(self._on_extension_requested)
            self._ai_controller.reduction_requested.connect(self._on_reduction_requested)
            
            # Connect adaptive timer log signals
            adaptive_timer = self._ai_controller.get_adaptive_timer()
            adaptive_timer.ai_adjustment_logged.connect(self._on_log_entry)
            
            # Connect base timer signals for warning threshold
            base_timer = self._ai_controller.get_base_timer()
            if base_timer:
                base_timer.warning_threshold.connect(self._on_warning_threshold)
                base_timer.time_changed.connect(self._on_timer_time_changed)
        
        self._update_ui_state()
    
    def _on_enable_changed(self, state: int):
        """Handle enable checkbox state change."""
        try:
            # Use proper CheckState enum comparison
            # state can be int (0=Unchecked, 2=Checked) or CheckState enum
            # Qt.CheckState.Checked.value is 2
            enabled = (state == Qt.CheckState.Checked.value or state == 2 or state == Qt.CheckState.Checked)
            self._ai_enabled = enabled
            
            # Force visual update of checkbox
            self._enable_checkbox.update()
            self._enable_checkbox.repaint()
            
            if enabled and self._ai_controller:
                # Check if AI timing can be started
                # Note: This requires camera indices - will be set by parent
                self.enable_ai_requested.emit(True)
                self._log_entry("AI Timer enabled")
                # Update UI immediately to enable Override button
                self._update_ui_state()
            else:
                if self._ai_controller:
                    try:
                        self._ai_controller.stop_ai_timing()
                    except Exception as e:
                        self._log_entry(f"Error stopping AI timing: {str(e)}")
                self._log_entry("AI Timer disabled")
                self._update_ui_state()
        except Exception as e:
            # Catch any exceptions to prevent crash
            import traceback
            error_msg = f"Error in enable checkbox handler: {str(e)}"
            self._log_entry(error_msg)
            # Reset checkbox state to prevent inconsistent state
            try:
                self._enable_checkbox.blockSignals(True)
                self._enable_checkbox.setChecked(False)
                self._enable_checkbox.blockSignals(False)
                self._ai_enabled = False
            except:
                pass
            # Log full traceback for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Checkbox handler error: {traceback.format_exc()}")
    
    def _on_presenter_state_changed(self, state: str):
        """Handle presenter state change."""
        self._presenter_state_value.setText(state.title())
        
        # Update color based on state
        if state in ["talking", "engaged"]:
            self._presenter_state_value.setStyleSheet("font-weight: bold; color: #4CAF50;")
        elif state == "away":
            self._presenter_state_value.setStyleSheet("font-weight: bold; color: #f44336;")
        else:
            self._presenter_state_value.setStyleSheet("font-weight: bold; color: #FF9800;")
        
        self._log_entry(f"Presenter: {state}")
    
    def _on_engagement_changed(self, level: str):
        """Handle audience engagement level change."""
        # Update attention percentage (convert level to percentage)
        attention_map = {
            "high": 75,
            "medium": 50,
            "low": 25
        }
        
        attention = attention_map.get(level, 0)
        self._audience_attention_value.setText(f"{attention}%")
        self._audience_progress.setValue(attention)
        
        # Update progress bar color
        if level == "high":
            self._audience_progress.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #4CAF50;
                }
            """)
        elif level == "medium":
            self._audience_progress.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #FF9800;
                }
            """)
        else:
            self._audience_progress.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #f44336;
                }
            """)
    
    def _on_adaptation_changed(self, mode: str):
        """Handle timer adaptation mode change."""
        mode_display = {
            "normal": "Normal",
            "paused_ai": "Paused (AI)",
            "slowed_ai": "Slowed (AI)",
            "extended": "Extended",
            "reduced": "Reduced"
        }
        
        display_text = mode_display.get(mode, mode.title())
        
        # Update alert message
        if mode == "paused_ai":
            self._show_alert("AI Pause: Timer paused due to low engagement")
        elif mode == "slowed_ai":
            self._show_alert("AI Slow: Timer slowed due to low engagement")
        elif mode == "extended":
            self._show_alert("AI Extension: Timer extended due to high engagement")
        elif mode == "reduced":
            self._show_alert("AI Reduction: Timer reduced due to low engagement")
        else:
            self._hide_alert()
    
    def _on_extension_requested(self, seconds: int):
        """Handle extension request from AI."""
        self._extension_requested_seconds = seconds
        minutes = seconds // 60
        secs = seconds % 60
        time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
        self._show_alert(f"Extension Request: +{time_str} (High engagement detected) - Approve or Reject")
        
        # Enable extension buttons
        self._extension_approve_btn.setEnabled(True)
        self._extension_reject_btn.setEnabled(True)
        
        self._log_entry(f"Extension requested: +{time_str} (High audience engagement)")
    
    def _on_approve_extension(self):
        """Approve and apply timer extension."""
        if not self._extension_approve_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        # Check if this is for reduction (button text changed)
        if "Reduction" in self._extension_approve_btn.text():
            self._on_confirm_reduction()
            return
        
        if self._ai_controller and self._extension_requested_seconds > 0:
            try:
                self._ai_controller.confirm_extension(self._extension_requested_seconds)
                minutes = self._extension_requested_seconds // 60
                secs = self._extension_requested_seconds % 60
                time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
                self._log_entry(f"✓ Extension approved: +{time_str}")
                
                # Reset warning logged flag so 20% warning can show again if needed
                self._warning_logged = False
                
                # Hide alert and reset buttons
                self._hide_alert()
                self._extension_approve_btn.setEnabled(False)
                self._extension_reject_btn.setEnabled(False)
                self._extension_approve_btn.setText("✓ Approve Extension")
                self._extension_reject_btn.setText("✗ Reject Extension")
                self._extension_requested_seconds = 0
            except Exception as e:
                self._log_entry(f"✗ Error approving extension: {str(e)}")
                logger.error(f"Error approving extension: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ No extension request to approve")
    
    def _on_reject_extension(self):
        """Reject timer extension request."""
        if not self._extension_reject_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        # Check if this is for reduction (button text changed)
        if "Reduction" in self._extension_reject_btn.text():
            self._on_cancel_reduction()
            return
        
        if self._ai_controller and self._extension_requested_seconds > 0:
            try:
                self._ai_controller.reject_extension(self._extension_requested_seconds)
                minutes = self._extension_requested_seconds // 60
                secs = self._extension_requested_seconds % 60
                time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
                self._log_entry(f"✗ Extension rejected: +{time_str}")
                
                # Hide alert and reset buttons
                self._hide_alert()
                self._extension_approve_btn.setEnabled(False)
                self._extension_reject_btn.setEnabled(False)
                self._extension_approve_btn.setText("✓ Approve Extension")
                self._extension_reject_btn.setText("✗ Reject Extension")
                self._extension_requested_seconds = 0
            except Exception as e:
                self._log_entry(f"✗ Error rejecting extension: {str(e)}")
                logger.error(f"Error rejecting extension: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ No extension request to reject")
    
    def _on_reduction_requested(self, seconds: int):
        """Handle reduction request from AI."""
        self._reduction_requested_seconds = seconds
        minutes = seconds // 60
        secs = seconds % 60
        time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
        self._show_alert(f"Reduction Request: -{time_str} (Low engagement detected) - Confirm to apply")
        
        # Enable reduction confirmation (using extension buttons)
        # Note: We reuse the same buttons, and check button text in handlers to determine action
        self._extension_approve_btn.setText("✓ Confirm Reduction")
        self._extension_reject_btn.setText("✗ Cancel Reduction")
        self._extension_approve_btn.setEnabled(True)
        self._extension_reject_btn.setEnabled(True)
        
        self._log_entry(f"Reduction requested: -{time_str} (Low audience engagement)")
    
    def _on_confirm_reduction(self):
        """Confirm and apply timer reduction."""
        if self._ai_controller and self._reduction_requested_seconds > 0:
            try:
                self._ai_controller.confirm_reduction(self._reduction_requested_seconds)
                minutes = self._reduction_requested_seconds // 60
                secs = self._reduction_requested_seconds % 60
                time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
                self._log_entry(f"✓ Reduction confirmed: -{time_str}")
                
                # Reset buttons
                self._hide_alert()
                self._extension_approve_btn.setText("✓ Approve Extension")
                self._extension_reject_btn.setText("✗ Reject Extension")
                self._extension_approve_btn.setEnabled(False)
                self._extension_reject_btn.setEnabled(False)
                self._reduction_requested_seconds = 0
            except Exception as e:
                self._log_entry(f"✗ Error confirming reduction: {str(e)}")
                logger.error(f"Error confirming reduction: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ No reduction request to confirm")
    
    def _on_cancel_reduction(self):
        """Cancel timer reduction request."""
        if self._ai_controller and self._reduction_requested_seconds > 0:
            try:
                self._ai_controller.reject_reduction(self._reduction_requested_seconds)
                minutes = self._reduction_requested_seconds // 60
                secs = self._reduction_requested_seconds % 60
                time_str = f"{minutes}:{secs:02d}" if minutes > 0 else f"{secs}s"
                self._log_entry(f"✗ Reduction cancelled: -{time_str}")
                
                # Reset buttons
                self._hide_alert()
                self._extension_approve_btn.setText("✓ Approve Extension")
                self._extension_reject_btn.setText("✗ Reject Extension")
                self._extension_approve_btn.setEnabled(False)
                self._extension_reject_btn.setEnabled(False)
                self._reduction_requested_seconds = 0
            except Exception as e:
                self._log_entry(f"✗ Error cancelling reduction: {str(e)}")
                logger.error(f"Error cancelling reduction: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ No reduction request to cancel")
    
    def _on_save_report(self):
        """Save session summary report."""
        if not self._save_report_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        if not self._ai_controller:
            self._log_entry("⚠️ AI controller not available")
            QMessageBox.warning(
                self, "Cannot Save Report",
                "AI Timer must be enabled and have collected data before saving a report."
            )
            return
        
        try:
            from modules.ai_timing import SessionReportGenerator
            from PyQt6.QtWidgets import QFileDialog
            import json
            from pathlib import Path
            
            # Generate report
            report_gen = SessionReportGenerator()
            
            # Collect session data from AI controller
            # Start session tracking if not started
            if not hasattr(report_gen, '_session_started'):
                report_gen.start_session()
                report_gen._session_started = True
            
            # Get AI state
            presenter_state = self._ai_controller.get_presenter_state() if self._ai_controller else "unknown"
            audience_engagement = self._ai_controller.get_audience_engagement() if self._ai_controller else "unknown"
            
            # Record current state
            report_gen.record_presenter_state(presenter_state)
            try:
                analyzer = self._ai_controller._engagement_analyzer
                attention = analyzer.get_attention_percentage()
                report_gen.record_engagement(audience_engagement, attention)
            except:
                report_gen.record_engagement(audience_engagement, 0.0)
            
            # End session
            report_gen.end_session()
            
            # Generate report
            report = report_gen.generate_report()
            
            # Get save location
            default_filename = f"ai_timer_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Save Session Report",
                str(Path.home() / default_filename),
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                self._log_entry(f"✓ Session report saved: {Path(filepath).name}")
                self._show_alert("Session report saved successfully!")
        except Exception as e:
            self._log_entry(f"✗ Error saving report: {str(e)}")
            logger.error(f"Error saving session report: {e}", exc_info=True)
    
    def _show_advanced_settings(self):
        """Show advanced settings dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Timer Advanced Settings")
        dialog.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(dialog)
        
        if not self._ai_controller:
            layout.addWidget(QLabel("AI Timer must be enabled first."))
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            dialog.exec()
            return
        
        # Get adaptive timer for configuration
        adaptive_timer = self._ai_controller.get_adaptive_timer()
        engagement_analyzer = self._ai_controller._engagement_analyzer
        
        # Engagement Thresholds
        engagement_group = QGroupBox("Engagement Thresholds")
        engagement_layout = QVBoxLayout(engagement_group)
        
        high_layout = QHBoxLayout()
        high_layout.addWidget(QLabel("High Engagement Threshold (%):"))
        high_spinbox = QDoubleSpinBox()
        high_spinbox.setRange(0, 100)
        high_spinbox.setValue(engagement_analyzer._high_threshold * 100 if hasattr(engagement_analyzer, '_high_threshold') else 70.0)
        high_layout.addWidget(high_spinbox)
        engagement_layout.addLayout(high_layout)
        
        medium_layout = QHBoxLayout()
        medium_layout.addWidget(QLabel("Medium Engagement Threshold (%):"))
        medium_spinbox = QDoubleSpinBox()
        medium_spinbox.setRange(0, 100)
        medium_spinbox.setValue(engagement_analyzer._medium_threshold * 100 if hasattr(engagement_analyzer, '_medium_threshold') else 40.0)
        medium_layout.addWidget(medium_spinbox)
        engagement_layout.addLayout(medium_layout)
        
        layout.addWidget(engagement_group)
        
        # Timer Adaptation Settings
        adaptation_group = QGroupBox("Timer Adaptation")
        adaptation_layout = QVBoxLayout(adaptation_group)
        
        max_extension_layout = QHBoxLayout()
        max_extension_layout.addWidget(QLabel("Max Extension (%):"))
        max_extension_spinbox = QSpinBox()
        max_extension_spinbox.setRange(0, 50)
        max_extension_spinbox.setValue(int(adaptive_timer._max_extension_percent) if hasattr(adaptive_timer, '_max_extension_percent') else 10)
        max_extension_layout.addWidget(max_extension_spinbox)
        adaptation_layout.addLayout(max_extension_layout)
        
        layout.addWidget(adaptation_group)
        
        # Presenter Tracking Settings
        presenter_group = QGroupBox("Presenter Tracking")
        presenter_layout = QVBoxLayout(presenter_group)
        
        presenter_engagement_layout = QHBoxLayout()
        presenter_engagement_layout.addWidget(QLabel("Engagement Threshold (%):"))
        presenter_engagement_spinbox = QDoubleSpinBox()
        presenter_engagement_spinbox.setRange(0, 100)
        presenter_engagement_spinbox.setValue(50.0)  # Default
        presenter_engagement_layout.addWidget(presenter_engagement_spinbox)
        presenter_layout.addLayout(presenter_engagement_layout)
        
        layout.addWidget(presenter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self._save_settings(
            dialog, 
            high_spinbox.value() / 100,
            medium_spinbox.value() / 100,
            max_extension_spinbox.value(),
            presenter_engagement_spinbox.value() / 100
        ))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _save_settings(self, dialog, high_threshold, medium_threshold, max_extension, presenter_threshold):
        """Save advanced settings."""
        if not self._ai_controller:
            return
        
        try:
            adaptive_timer = self._ai_controller.get_adaptive_timer()
            engagement_analyzer = self._ai_controller._engagement_analyzer
            
            # Apply settings
            engagement_analyzer.set_high_threshold(high_threshold)
            engagement_analyzer.set_medium_threshold(medium_threshold)
            adaptive_timer._max_extension_percent = max_extension
            
            if hasattr(self._ai_controller, '_presenter_tracker'):
                self._ai_controller._presenter_tracker.set_engagement_threshold(presenter_threshold)
            
            self._log_entry(f"✓ Settings saved: High={int(high_threshold*100)}%, Medium={int(medium_threshold*100)}%, Max Extension={max_extension}%")
            dialog.accept()
        except Exception as e:
            self._log_entry(f"✗ Error saving settings: {str(e)}")
            logger.error(f"Error saving settings: {e}", exc_info=True)
    
    def _on_pause_ai_clicked(self):
        """Handle pause AI timer button click."""
        if not self._pause_ai_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        if self._ai_controller:
            try:
                # Pause the base timer
                base_timer = self._ai_controller.get_base_timer()
                if base_timer and base_timer.is_running():
                    base_timer.pause()
                    self._log_entry("Operator: Timer paused manually")
                    # Update button states immediately
                    self._update_ui_state()
                else:
                    self._log_entry("Operator: Cannot pause - timer not running")
            except Exception as e:
                self._log_entry(f"✗ Error pausing timer: {str(e)}")
                logger.error(f"Error pausing timer: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ AI controller not available")
        self.pause_ai_requested.emit()
    
    def _on_resume_ai_clicked(self):
        """Handle resume AI timer button click."""
        if not self._resume_ai_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        if self._ai_controller:
            try:
                # Resume the base timer
                base_timer = self._ai_controller.get_base_timer()
                if base_timer and base_timer.is_paused():
                    base_timer.resume()
                    self._log_entry("Operator: Timer resumed manually")
                    # Update button states immediately
                    self._update_ui_state()
                else:
                    self._log_entry("Operator: Cannot resume - timer not paused")
            except Exception as e:
                self._log_entry(f"✗ Error resuming timer: {str(e)}")
                logger.error(f"Error resuming timer: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ AI controller not available")
        self.resume_ai_requested.emit()
    
    def _on_override_clicked(self):
        """Handle override AI button click."""
        if not self._override_btn.isEnabled():
            # Button is disabled, do nothing
            return
        
        if self._ai_controller:
            try:
                self._ai_controller.override_ai_adaptation()
                self._log_entry("Operator: AI adaptation overridden - Manual control enabled")
                # Update UI state after override
                self._update_ui_state()
                
                # Hide extension buttons if visible
                self._extension_approve_btn.setEnabled(False)
                self._extension_reject_btn.setEnabled(False)
                self._extension_approve_btn.setText("✓ Approve Extension")
                self._extension_reject_btn.setText("✗ Reject Extension")
            except Exception as e:
                self._log_entry(f"✗ Error overriding AI: {str(e)}")
                logger.error(f"Error overriding AI: {e}", exc_info=True)
        else:
            self._log_entry("⚠️ AI controller not available")
        self.override_ai_requested.emit()
    
    def _on_log_entry(self, message: str):
        """Handle log entry from AI system."""
        self._log_entry(message)
    
    def _log_entry(self, message: str):
        """Add entry to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {message}"
        self._log_text.append(log_text)
        
        # Auto-scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Limit log size (keep last 50 entries)
        lines = self._log_text.toPlainText().split('\n')
        if len(lines) > 50:
            self._log_text.setPlainText('\n'.join(lines[-50:]))
    
    def _show_alert(self, message: str):
        """Show alert message with blinking effect."""
        self._ai_alert_label.setText(message)
        self._ai_alert_label.setVisible(True)
        
        # Start blinking animation
        if not self._alert_blink_timer.isActive():
            self._alert_blink_timer.start(500)  # Blink every 500ms
        
        # Start pulse animation
        if not self._pulse_timer.isActive():
            self._pulse_timer.start()
    
    def _hide_alert(self):
        """Hide alert message."""
        self._ai_alert_label.setText("")
        self._ai_alert_label.setVisible(False)
        
        # Stop animations
        self._alert_blink_timer.stop()
        self._pulse_timer.stop()
    
    def _toggle_alert_blink(self):
        """Toggle alert label visibility for blinking effect."""
        self._alert_blinking = not self._alert_blinking
        opacity = 0.3 if self._alert_blinking else 1.0
        self._ai_alert_label.setStyleSheet(f"""
            QLabel {{
                padding: 5px;
                border-radius: 3px;
                background-color: rgba(255, 152, 0, {0.2 * opacity});
                color: #FF9800;
                font-weight: bold;
            }}
        """)
    
    def _update_ui_state(self):
        """Update UI state based on AI controller status."""
        if not self._ai_controller:
            self._ai_status_value.setText("Inactive")
            self._ai_status_value.setStyleSheet("font-weight: bold; color: #888888;")
            self._enable_checkbox.setEnabled(False)
            # Disable all buttons when no controller
            self._pause_ai_btn.setEnabled(False)
            self._resume_ai_btn.setEnabled(False)
            self._override_btn.setEnabled(False)
            return
        
        is_active = self._ai_controller.is_active()
        
        if is_active and self._ai_enabled:
            self._ai_status_value.setText("Active")
            self._ai_status_value.setStyleSheet("font-weight: bold; color: #4CAF50;")
        elif self._ai_enabled:
            self._ai_status_value.setText("Waiting")
            self._ai_status_value.setStyleSheet("font-weight: bold; color: #FF9800;")
        else:
            self._ai_status_value.setText("Inactive")
            self._ai_status_value.setStyleSheet("font-weight: bold; color: #888888;")
        
        # Enable controls based on state
        # Override button: Always enabled if AI is enabled (can override even when not fully active)
        self._override_btn.setEnabled(self._ai_enabled)
        
        # Save Report button: Enabled if AI Timer was enabled (has data or session to save)
        # Should be enabled whenever AI Timer is enabled, even if currently stopped
        self._save_report_btn.setEnabled(self._ai_enabled)
        
        # Pause/Resume buttons: Enabled if timer exists and AI is enabled
        # Check timer state from base timer
        base_timer = self._ai_controller.get_base_timer() if self._ai_controller else None
        
        if base_timer is None:
            # No timer available
            self._pause_ai_btn.setEnabled(False)
            self._resume_ai_btn.setEnabled(False)
        else:
            timer_running = base_timer.is_running()
            timer_paused = base_timer.is_paused()
            
            # Enable buttons if AI is enabled (checkbox checked) and timer controller exists
            # Buttons should work even if AI timing system is not fully active yet
            buttons_enabled = self._ai_enabled
            
            # Pause button: enable if timer is running and buttons are enabled
            self._pause_ai_btn.setEnabled(buttons_enabled and timer_running)
            
            # Resume button: enable if timer is paused and buttons are enabled
            self._resume_ai_btn.setEnabled(buttons_enabled and timer_paused)
        
        self._enable_checkbox.setEnabled(True)
        
        # Update metrics if active
        if is_active:
            presenter_state = self._ai_controller.get_presenter_state()
            self._on_presenter_state_changed(presenter_state)
            
            engagement = self._ai_controller.get_audience_engagement()
            self._on_engagement_changed(engagement)
    
    def _update_text_colors(self):
        """Update all text colors based on current theme."""
        text_color = self._theme_manager.get_text_color()
        colors = self._theme_manager.get_color_scheme()
        text_secondary_color = colors['text_secondary']
        text_secondary_str = f"rgb({text_secondary_color.red()}, {text_secondary_color.green()}, {text_secondary_color.blue()})"
        
        # Checkbox styling is handled globally by ThemeManager
        # Text color is automatically applied through ThemeManager stylesheet
        
        # Update log text color
        log_bg = colors['background_alt']
        log_bg_str = f"rgb({log_bg.red()}, {log_bg.green()}, {log_bg.blue()})"
        self._log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {log_bg_str};
                color: {text_color};
                border: 1px solid #444;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                padding: 5px;
            }}
        """)
        
        # Update AI Status color based on current state
        current_status = self._ai_status_value.text()
        if current_status == "Inactive":
            self._ai_status_value.setStyleSheet(f"font-weight: bold; color: {text_secondary_str};")
        # Active/Waiting states use their own colors (green/orange) - these are fine
    
    def update_metrics(self):
        """Manually update all metrics from AI controller."""
        self._update_ui_state()
        
        if self._ai_controller and self._ai_controller.is_active():
            # Get attention percentage from engagement analyzer
            try:
                analyzer = self._ai_controller._engagement_analyzer
                attention = analyzer.get_attention_percentage()
                attention_percent = int(attention * 100)
                self._audience_attention_value.setText(f"{attention_percent}%")
                self._audience_progress.setValue(attention_percent)
            except:
                pass
    
    def _on_warning_threshold(self):
        """Handle timer warning threshold (< 20% remaining)."""
        base_timer = self._ai_controller.get_base_timer() if self._ai_controller else None
        if base_timer:
            self._check_warning_threshold(base_timer)
    
    def _on_timer_time_changed(self, time_remaining: int):
        """Handle timer time change to check warning threshold."""
        if self._ai_controller:
            base_timer = self._ai_controller.get_base_timer()
            if base_timer:
                self._check_warning_threshold(base_timer)
    
    def _check_warning_threshold(self, base_timer):
        """Check if timer is in last 20% and show AI-contextual warning."""
        try:
            current_time = base_timer.get_current_time()
            initial_time = base_timer.get_initial_time()
            
            if initial_time <= 0:
                return
            
            percent_remaining = (current_time / initial_time) * 100
            
            if percent_remaining <= 20 and percent_remaining > 0:
                # Get AI context
                presenter_state = "Unknown"
                audience_engagement = "Unknown"
                attention_percent = 0
                
                if self._ai_controller and self._ai_controller.is_active():
                    presenter_state = self._ai_controller.get_presenter_state()
                    audience_engagement = self._ai_controller.get_audience_engagement()
                    try:
                        analyzer = self._ai_controller._engagement_analyzer
                        attention_percent = int(analyzer.get_attention_percentage() * 100)
                    except:
                        pass
                
                # Generate contextual warning message
                warning_parts = [f"⚠️ Last 20% Time Remaining ({int(percent_remaining)}%)"]
                
                if presenter_state in ["away", "disengaged", "silent"]:
                    warning_parts.append("Presenter inactive - Consider wrapping up")
                elif presenter_state in ["talking", "engaged"]:
                    warning_parts.append("Presenter active")
                
                if audience_engagement == "low" or attention_percent < 30:
                    warning_parts.append(f"Audience attention low ({attention_percent}%) - Summarize soon")
                elif audience_engagement == "high" and attention_percent > 70:
                    warning_parts.append(f"Audience engaged ({attention_percent}%) - Extension possible")
                
                warning_msg = " | ".join(warning_parts)
                self._show_alert(warning_msg)
                
                if not hasattr(self, '_warning_logged'):
                    self._warning_logged = False
                
                if not self._warning_logged:
                    self._log_entry(f"⚠️ Warning threshold reached ({int(percent_remaining)}%) - AI Context: Presenter={presenter_state}, Engagement={audience_engagement}, Attention={attention_percent}%")
                    self._warning_logged = True
        except Exception as e:
            logger.error(f"Error checking warning threshold: {e}")
    
    def _update_pulse(self):
        """Update pulse animation for alerts."""
        if not self._ai_alert_label.isVisible():
            return
        
        import math
        # Use sine wave for smooth pulse effect
        current_time = datetime.now().timestamp() * 1000  # milliseconds
        pulse_speed = 2.0  # pulses per second
        pulse_value = (math.sin(current_time * pulse_speed * 0.001) + 1.0) / 2.0  # 0.0 to 1.0
        
        intensity = 0.5 + 0.5 * pulse_value
        self._ai_alert_label.setStyleSheet(f"""
            QLabel {{
                padding: 5px;
                border: 2px solid rgba(255, 152, 0, {intensity});
                border-radius: 3px;
                background-color: rgba(255, 152, 0, {0.1 * intensity});
                color: #FF9800;
                font-weight: bold;
            }}
        """)

