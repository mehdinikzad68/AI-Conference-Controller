"""
Face AI Window Module

PyQt6 UI for real-time face analysis display with overlays, statistics, and controls.
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QComboBox, QGroupBox, QMessageBox, QProgressBar,
    QTextEdit, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QPen
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .face_ai_controller import FaceAIController
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QScrollArea

logger = logging.getLogger(__name__)


class VideoDisplayWidget(QWidget):
    """Widget for displaying camera feed with face analysis overlays."""
    
    def __init__(self, parent=None):
        """Initialize video display widget."""
        super().__init__(parent)
        self._current_frame = None
        self._faces = []
        self._head_poses = []
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")
        
        # Make responsive
        from PyQt6.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(False)
        self.setSizePolicy(size_policy)
    
    def update_frame(self, frame: np.ndarray, faces: List[Dict], head_poses: List[Dict]):
        """
        Update display with new frame and analysis results.
        
        Args:
            frame: BGR frame from camera
            faces: List of face analysis results
            head_poses: List of head pose results
        """
        self._current_frame = frame.copy()
        self._faces = faces
        self._head_poses = head_poses
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Paint frame with overlays."""
        if self._current_frame is None:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Convert OpenCV frame to QPixmap
        height, width = self._current_frame.shape[:2]
        bytes_per_line = 3 * width
        q_image = QImage(
            self._current_frame.data, width, height, bytes_per_line,
            QImage.Format.Format_BGR888
        )
        
        # Scale to widget size
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        
        # Draw frame
        x_offset = (self.width() - scaled_pixmap.width()) // 2
        y_offset = (self.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        
        # Draw face overlays
        scale_x = scaled_pixmap.width() / width
        scale_y = scaled_pixmap.height() / height
        
        for i, face in enumerate(self._faces):
            region = face.get('region', (0, 0, 0, 0))
            x, y, w, h = region
            
            # Scale coordinates
            x_scaled = int(x * scale_x) + x_offset
            y_scaled = int(y * scale_y) + y_offset
            w_scaled = int(w * scale_x)
            h_scaled = int(h * scale_y)
            
            # Draw bounding box
            emotion = face.get('emotion', 'unknown')
            emotion_color = self._get_emotion_color(emotion)
            
            pen = QPen(QColor(*emotion_color), 3)
            painter.setPen(pen)
            painter.drawRect(x_scaled, y_scaled, w_scaled, h_scaled)
            
            # Draw emotion label
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            
            label = f"{emotion} ({face.get('emotion_confidence', 0):.1%})"
            if 'age' in face:
                label += f"\nAge: {face.get('age', 0):.0f}"
            if 'gender' in face:
                label += f"\n{face.get('gender', '')}"
            
            painter.drawText(x_scaled + 5, y_scaled - 5, label)
            
            # Draw head pose arrow
            if i < len(self._head_poses) and self._head_poses[i] is not None:
                pose = self._head_poses[i]
                direction = pose.get('attention_direction', 'unknown')
                
                # Arrow color based on attention
                if direction == 'focused':
                    arrow_color = QColor(0, 255, 0)  # Green
                elif direction == 'distracted':
                    arrow_color = QColor(255, 0, 0)  # Red
                else:
                    arrow_color = QColor(255, 255, 0)  # Yellow
                
                # Calculate arrow
                center_x = x_scaled + w_scaled // 2
                center_y = y_scaled + h_scaled // 2
                
                yaw = pose.get('yaw', 0)
                pitch = pose.get('pitch', 0)
                arrow_length = 30
                
                import math
                end_x = int(center_x + arrow_length * math.sin(math.radians(yaw)))
                end_y = int(center_y + arrow_length * math.sin(math.radians(pitch)))
                
                pen = QPen(arrow_color, 2)
                painter.setPen(pen)
                painter.drawLine(center_x, center_y, end_x, end_y)
                
                # Draw direction label
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                font = QFont("Arial", 10)
                painter.setFont(font)
                painter.drawText(center_x + 5, center_y - 20, direction)
    
    def _get_emotion_color(self, emotion: str) -> tuple:
        """Get RGB color for emotion."""
        colors = {
            'happy': (0, 255, 0),      # Green
            'sad': (0, 0, 255),        # Blue
            'angry': (0, 0, 255),      # Red
            'surprise': (255, 165, 0),  # Orange
            'fear': (128, 0, 128),      # Purple
            'disgust': (0, 128, 0),     # Dark green
            'neutral': (128, 128, 128), # Gray
        }
        return colors.get(emotion.lower(), (255, 255, 255))


class FaceAIWindow(QMainWindow):
    """
    Main window for Face AI analysis module.
    
    Features:
    - Real-time camera feed with face detection overlays
    - Emotion and head pose visualization
    - Statistics dashboard
    - Report generation
    """
    
    def __init__(self, parent=None, controller: Optional[FaceAIController] = None):
        """Initialize Face AI window."""
        super().__init__(parent)
        
        # Controller
        self._controller = controller or FaceAIController()
        
        # UI components
        self._video_display = None
        self._stats_text = None
        self._attention_progress = None
        
        # Timers
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(33)  # ~30 FPS for UI updates
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        
        # Connect controller signals
        self._controller.frame_analyzed.connect(self._on_frame_analyzed)
        self._controller.attention_level_changed.connect(self._on_attention_changed)
        self._controller.faces_detected.connect(self._on_faces_detected)
        self._controller.statistics_updated.connect(self._on_statistics_updated)
        
        # Window properties
        self.setWindowTitle("Face AI Analysis - AI-Symp-Controller")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Make responsive
        make_responsive(self)
        
        # Apply system theme
        self.apply_theme()
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
        
        # Check dependencies and warn user if needed (only once)
        self._dependency_warning_shown = False
        self._check_dependencies_on_first_use()
    
    def _check_dependencies_on_first_use(self):
        """Check and warn about missing dependencies on first use."""
        if self._dependency_warning_shown:
            return
        
        # Use dynamic check instead of cached flags
        # This ensures we check the actual runtime status
        missing_deps = []
        
        # Dynamic check for DeepFace
        deepface_available = False
        try:
            from deepface import DeepFace
            deepface_available = True
        except (ImportError, Exception):
            pass
        
        # Dynamic check for FER
        fer_available = False
        try:
            try:
                from fer import FER
                fer_available = True
            except ImportError:
                from fer.fer import FER
                fer_available = True
        except (ImportError, Exception):
            pass
        
        if not deepface_available:
            missing_deps.append("DeepFace")
        if not fer_available:
            missing_deps.append("FER")
        
        if missing_deps:
            deps_str = " and ".join(missing_deps)
            install_cmd = "\n".join([f"pip install {dep.lower()}" for dep in missing_deps])
            
            reply = QMessageBox.warning(
                self, "Optional Dependencies Missing",
                f"{deps_str} {'are' if len(missing_deps) > 1 else 'is'} not installed.\n\n"
                f"Face AI will work with reduced functionality.\n\n"
                f"To install:\n{install_cmd}\n\n"
                "Click 'OK' to continue or 'Cancel' to close.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Ok
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                self.close()
                return
        
        # If dependencies are now available, update controller's analyzer
        if deepface_available or fer_available:
            try:
                # Reinitialize analyzer in controller if needed
                if hasattr(self._controller, '_face_analyzer'):
                    # Create new analyzer with dynamic checks
                    from .face_analyzer import FaceAnalyzer
                    self._controller._face_analyzer = FaceAnalyzer()
                    logger.info("FaceAnalyzer reinitialized with available dependencies")
            except Exception as e:
                logger.warning(f"Could not reinitialize analyzer: {e}")
        
        self._dependency_warning_shown = True
    
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
        """Initialize user interface with scrollable support."""
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
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Top: Controls
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QVBoxLayout()
        
        # First row: Camera and Preview
        row1 = QHBoxLayout()
        camera_label = QLabel("Camera:")
        self._camera_combo = QComboBox()
        # Detect available cameras
        available_cameras = self._detect_available_cameras()
        self._camera_combo.addItems([f"Camera {i}" for i in available_cameras])
        self._camera_combo.setCurrentIndex(0)
        
        # Preview button
        self._preview_btn = QPushButton("Test Camera")
        self._preview_btn.clicked.connect(self._preview_camera)
        self._preview_btn.setToolTip("Preview camera feed before starting analysis")
        
        row1.addWidget(camera_label)
        row1.addWidget(self._camera_combo)
        row1.addWidget(self._preview_btn)
        row1.addStretch()
        controls_layout.addLayout(row1)
        
        # Second row: Start/Stop, Pause/Resume/Reset
        row2 = QHBoxLayout()
        self._start_stop_btn = QPushButton("Start Analysis")
        self._start_stop_btn.clicked.connect(self._toggle_analysis)
        self._start_stop_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #4CAF50; color: white;")
        
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.clicked.connect(self._pause_analysis)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #FF9800; color: white;")
        
        self._resume_btn = QPushButton("Resume")
        self._resume_btn.clicked.connect(self._resume_analysis)
        self._resume_btn.setEnabled(False)
        self._resume_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #2196F3; color: white;")
        
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._reset_analysis)
        self._reset_btn.setEnabled(False)
        self._reset_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #9E9E9E; color: white;")
        
        row2.addWidget(self._start_stop_btn)
        row2.addWidget(self._pause_btn)
        row2.addWidget(self._resume_btn)
        row2.addWidget(self._reset_btn)
        row2.addStretch()
        controls_layout.addLayout(row2)
        
        # Third row: FPS and Processing rate
        row3 = QHBoxLayout()
        fps_label = QLabel("FPS:")
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(5, 30)
        self._fps_spin.setValue(15)
        self._fps_spin.setSuffix(" fps")
        
        rate_label = QLabel("Process every:")
        self._rate_spin = QSpinBox()
        self._rate_spin.setRange(1, 5)
        self._rate_spin.setValue(2)
        self._rate_spin.setSuffix(" frame(s)")
        
        row3.addWidget(fps_label)
        row3.addWidget(self._fps_spin)
        row3.addWidget(rate_label)
        row3.addWidget(self._rate_spin)
        row3.addStretch()
        controls_layout.addLayout(row3)
        
        # Fourth row: Advanced Settings and Export buttons
        row4 = QHBoxLayout()
        
        # Advanced Settings button
        self._settings_btn = QPushButton("⚙ Advanced Settings")
        self._settings_btn.clicked.connect(self._show_advanced_settings)
        self._settings_btn.setToolTip("Configure model, thresholds, and filters")
        
        # Export buttons
        self._export_csv_btn = QPushButton("Export CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.setToolTip("Export statistics to CSV file")
        
        self._export_excel_btn = QPushButton("Export Excel")
        self._export_excel_btn.clicked.connect(self._export_excel)
        self._export_excel_btn.setEnabled(False)
        self._export_excel_btn.setToolTip("Export statistics to Excel file")
        
        # Generate report button
        self._report_btn = QPushButton("Generate Report")
        self._report_btn.clicked.connect(self._generate_report)
        self._report_btn.setEnabled(False)
        self._report_btn.setToolTip("Generate PDF/PNG charts and summary report")
        
        row4.addWidget(self._settings_btn)
        row4.addStretch()
        row4.addWidget(self._export_csv_btn)
        row4.addWidget(self._export_excel_btn)
        row4.addWidget(self._report_btn)
        controls_layout.addLayout(row4)
        
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # Middle: Splitter for video and stats
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Video display
        video_group = QGroupBox("Live Camera Feed")
        video_layout = QVBoxLayout()
        self._video_display = VideoDisplayWidget()
        video_layout.addWidget(self._video_display)
        video_group.setLayout(video_layout)
        
        # Right: Statistics panel with tabs
        stats_group = QGroupBox("Real-Time Statistics")
        stats_layout = QVBoxLayout()
        
        from PyQt6.QtWidgets import QTabWidget
        stats_tabs = QTabWidget()
        
        # Tab 1: Overview
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # Attention progress bar
        attention_label = QLabel("Overall Attention Level:")
        self._attention_progress = QProgressBar()
        self._attention_progress.setRange(0, 100)
        self._attention_progress.setValue(0)
        self._attention_progress.setFormat("%p%")
        self._attention_progress.setStyleSheet(
            "QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 red, stop:0.5 yellow, stop:1 green); }"
        )
        
        # Alert label for low attention
        self._alert_label = QLabel("")
        self._alert_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                border-radius: 3px;
                background-color: rgba(244, 67, 54, 0.8);
                color: white;
                font-weight: bold;
            }
        """)
        self._alert_label.setWordWrap(True)
        self._alert_label.setVisible(False)
        
        # Face count
        self._face_count_label = QLabel("Faces Detected: 0")
        self._face_count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Statistics text
        self._stats_text = QTextEdit()
        self._stats_text.setReadOnly(True)
        self._stats_text.setFont(QFont("Courier", 10))
        self._stats_text.setMaximumHeight(300)
        
        overview_layout.addWidget(attention_label)
        overview_layout.addWidget(self._attention_progress)
        overview_layout.addWidget(self._alert_label)
        overview_layout.addWidget(self._face_count_label)
        overview_layout.addWidget(QLabel("Statistics:"))
        overview_layout.addWidget(self._stats_text)
        overview_layout.addStretch()
        
        stats_tabs.addTab(overview_tab, "Overview")
        
        # Tab 2: Live Charts
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)
        
        # Live charts will be displayed here using matplotlib
        from PyQt6.QtWidgets import QLabel as QLabelChart
        self._charts_info = QLabelChart("Live charts will appear here during analysis")
        self._charts_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self._charts_info)
        
        # Emotion Pie Chart placeholder
        self._emotion_chart_label = QLabel("Emotion Distribution:")
        charts_layout.addWidget(self._emotion_chart_label)
        self._emotion_chart_pixmap = None  # Will store chart pixmap
        self._emotion_chart_display = QLabel()
        self._emotion_chart_display.setMinimumHeight(200)
        self._emotion_chart_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self._emotion_chart_display)
        
        # Attention Bar Chart placeholder
        self._attention_chart_label = QLabel("Attention Distribution:")
        charts_layout.addWidget(self._attention_chart_label)
        self._attention_chart_display = QLabel()
        self._attention_chart_display.setMinimumHeight(200)
        self._attention_chart_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self._attention_chart_display)
        
        charts_layout.addStretch()
        
        stats_tabs.addTab(charts_tab, "Live Charts")
        
        stats_layout.addWidget(stats_tabs)
        
        stats_group.setLayout(stats_layout)
        
        splitter.addWidget(video_group)
        splitter.addWidget(stats_group)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Bottom: Status bar
        self.statusBar().showMessage("Ready - Click 'Start Analysis' to begin")
    
    def _detect_available_cameras(self):
        """Detect available camera indices."""
        available = []
        for i in range(4):  # Check first 4 cameras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available if available else [0]  # Default to camera 0 if none found
    
    def _preview_camera(self):
        """Preview camera feed in a popup window."""
        camera_index = self._detect_available_cameras()[self._camera_combo.currentIndex()]
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            QMessageBox.warning(
                self, "Camera Error",
                f"Failed to open camera {camera_index}.\n\n"
                "Please check:\n"
                "- Camera is connected\n"
                "- Camera is not used by another application"
            )
            return
        
        # Show preview in a simple dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"Camera {camera_index} Preview")
        preview_dialog.setMinimumSize(640, 480)
        
        preview_layout = QVBoxLayout(preview_dialog)
        preview_label = QLabel()
        preview_layout.addWidget(preview_label)
        
        # Preview timer
        preview_timer = QTimer()
        def update_preview():
            ret, frame = cap.read()
            if ret:
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width = frame_rgb.shape[:2]
                q_image = QImage(frame_rgb.data, width, height, 3 * width, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
                preview_label.setPixmap(scaled_pixmap)
            else:
                preview_timer.stop()
                cap.release()
                preview_dialog.close()
        
        preview_timer.timeout.connect(update_preview)
        preview_timer.start(33)  # ~30 FPS
        
        def on_close():
            preview_timer.stop()
            cap.release()
        
        preview_dialog.finished.connect(on_close)
        preview_dialog.exec()
    
    @pyqtSlot()
    def _toggle_analysis(self):
        """Toggle analysis on/off."""
        if self._controller.is_analyzing():
            self._controller.stop_analysis()
            self._start_stop_btn.setText("Start Analysis")
            self._start_stop_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #4CAF50; color: white;")
            self._pause_btn.setEnabled(False)
            self._resume_btn.setEnabled(False)
            self._reset_btn.setEnabled(True)
            self._report_btn.setEnabled(True)
            self._export_csv_btn.setEnabled(True)
            self._export_excel_btn.setEnabled(True)
            self.statusBar().showMessage("Analysis stopped")
        else:
            camera_index = self._detect_available_cameras()[self._camera_combo.currentIndex()]
            fps = self._fps_spin.value()
            process_rate = self._rate_spin.value()
            
            self._controller.set_processing_rate(process_rate)
            
            try:
                if self._controller.start_analysis(camera_index, fps):
                    self._start_stop_btn.setText("Stop Analysis")
                    self._start_stop_btn.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f44336; color: white;")
                    self._pause_btn.setEnabled(True)
                    self._resume_btn.setEnabled(False)
                    self._reset_btn.setEnabled(False)
                    self._report_btn.setEnabled(False)
                    self._export_csv_btn.setEnabled(False)
                    self._export_excel_btn.setEnabled(False)
                    self.statusBar().showMessage(f"Analysis started on camera {camera_index}")
                else:
                    # Check specific error reasons
                    error_details = []
                    
                    # Check camera availability
                    import cv2
                    test_camera = cv2.VideoCapture(camera_index)
                    if not test_camera.isOpened():
                        error_details.append(f"Camera {camera_index} is not accessible")
                        error_details.append("Please check camera connection and permissions")
                    else:
                        test_camera.release()
                        error_details.append("Unknown error starting analysis")
                        error_details.append("Check console logs for details")
                    
                    QMessageBox.critical(
                        self, "Failed to Start Analysis",
                        f"Could not start face AI analysis.\n\n"
                        + "\n".join(f"• {detail}" for detail in error_details) + "\n\n"
                        "Possible solutions:\n"
                        "• Try a different camera index\n"
                        "• Close other applications using the camera\n"
                        "• Check camera permissions in system settings\n"
                        "• Restart the application"
                    )
            except Exception as e:
                logger.error(f"Error starting analysis: {e}", exc_info=True)
                QMessageBox.critical(
                    self, "Analysis Error",
                    f"An unexpected error occurred while starting analysis:\n\n"
                    f"{str(e)}\n\n"
                    "Please check the console for detailed error information."
                )
    
    @pyqtSlot()
    def _pause_analysis(self):
        """Pause analysis (keep camera running but stop processing)."""
        # Note: Currently controller doesn't have pause, so we'll simulate it
        # by stopping processing but keeping camera
        try:
            self._controller.stop_analysis()
            self._pause_btn.setEnabled(False)
            self._resume_btn.setEnabled(True)
            self.statusBar().showMessage("Analysis paused")
        except Exception as e:
            logger.error(f"Error pausing analysis: {e}")
            # Still update UI even if stop_analysis had issues
            self._pause_btn.setEnabled(False)
            self._resume_btn.setEnabled(True)
            self.statusBar().showMessage("Analysis paused (with warnings)")
    
    @pyqtSlot()
    def _resume_analysis(self):
        """Resume paused analysis."""
        try:
            camera_index = self._detect_available_cameras()[self._camera_combo.currentIndex()]
            fps = self._fps_spin.value()
            if self._controller.start_analysis(camera_index, fps):
                self._pause_btn.setEnabled(True)
                self._resume_btn.setEnabled(False)
                self.statusBar().showMessage("Analysis resumed")
            else:
                QMessageBox.warning(
                    self, "Resume Failed",
                    "Failed to resume analysis.\n\n"
                    "Please try stopping and starting again."
                )
        except Exception as e:
            logger.error(f"Error resuming analysis: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Resume Error",
                f"An error occurred while resuming analysis:\n\n{str(e)}"
            )
    
    @pyqtSlot()
    def _reset_analysis(self):
        """Reset statistics and clear data."""
        reply = QMessageBox.question(
            self, "Reset Analysis",
            "This will clear all statistics and reset the session. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._controller._statistics_aggregator.start_session()
            self._attention_progress.setValue(0)
            self._face_count_label.setText("Faces Detected: 0")
            self._stats_text.clear()
            self._alert_label.setVisible(False)
            self._emotion_chart_display.clear()
            self._attention_chart_display.clear()
            self.statusBar().showMessage("Statistics reset")
    
    @pyqtSlot()
    def _generate_report(self):
        """Generate analysis report with charts."""
        if self._controller.is_analyzing():
            QMessageBox.warning(self, "Analysis Running", "Please stop analysis before generating report.")
            return
        
        try:
            chart_paths = self._controller.generate_report_charts()
            if chart_paths:
                QMessageBox.information(
                    self, "Report Generated",
                    f"Successfully generated {len(chart_paths)} chart(s):\n\n" +
                    "\n".join(chart_paths) + "\n\n"
                    "Charts saved to the reports directory."
                )
            else:
                QMessageBox.warning(
                    self, "No Data Available",
                    "No analysis data available to generate report.\n\n"
                    "Please:\n"
                    "• Start face AI analysis\n"
                    "• Run analysis for at least a few seconds\n"
                    "• Ensure faces are being detected\n\n"
                    "Then try generating the report again."
                )
        except FileNotFoundError as e:
            QMessageBox.critical(
                self, "File Error",
                f"Failed to save report files:\n\n{str(e)}\n\n"
                "Please check that you have write permissions in the reports directory."
            )
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Report Generation Error",
                f"An unexpected error occurred while generating the report:\n\n{str(e)}\n\n"
                "Please check the console for detailed error information."
            )
    
    @pyqtSlot(np.ndarray, list, list)
    def _on_frame_analyzed(self, frame: np.ndarray, faces: List[Dict], head_poses: List[Dict]):
        """Handle frame analysis results."""
        if self._video_display:
            self._video_display.update_frame(frame, faces, head_poses)
    
    @pyqtSlot(float)
    def _on_attention_changed(self, attention: float):
        """Handle attention level change."""
        if self._attention_progress:
            attention_percent = int(attention * 100)
            self._attention_progress.setValue(attention_percent)
            
            # Check for low attention alert
            threshold = self._controller._attention_threshold
            if attention < threshold:
                self._alert_label.setText(f"⚠️ Attention Low! ({attention_percent}%)")
                self._alert_label.setVisible(True)
            else:
                self._alert_label.setVisible(False)
    
    @pyqtSlot(int)
    def _on_faces_detected(self, count: int):
        """Handle faces detected signal."""
        if self._face_count_label:
            self._face_count_label.setText(f"Faces Detected: {count}")
    
    @pyqtSlot(dict)
    def _on_statistics_updated(self, stats: Dict):
        """Update statistics display."""
        if self._stats_text:
            stats_text = f"""Session Duration: {stats.get('session_duration_seconds', 0):.1f}s
Frames Processed: {stats.get('frames_processed', 0)}
Total Faces: {stats.get('total_faces_detected', 0)}
Average Attention: {stats.get('average_attention', 0):.2%}
Focused: {stats.get('focused_count', 0)} | Distracted: {stats.get('distracted_count', 0)}
Focused Ratio: {stats.get('focused_ratio', 0):.2%}
Average Face Count: {stats.get('average_face_count', 0):.2f}
Smiling Events: {stats.get('smiling_count', 0)}
Average Age: {stats.get('average_age', 0):.1f} years

Attention Distribution:
"""
            attention_dist = stats.get('attention_distribution', {})
            for direction, count in attention_dist.items():
                stats_text += f"  {direction}: {count}\n"
            
            self._stats_text.setText(stats_text)
        
        # Update live charts
        self._update_live_charts(stats)
    
    def _update_display(self):
        """Update display with current camera frame."""
        if not self._controller.is_analyzing():
            return
        
        frame = self._controller.get_current_frame()
        if frame is not None and self._video_display:
            # Display raw frame (analysis overlays come from frame_analyzed signal)
            self._video_display.update_frame(frame, [], [])
    
    def _show_advanced_settings(self):
        """Show advanced settings dialog."""
        from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QCheckBox
        from pathlib import Path
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Face AI Advanced Settings")
        dialog.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Model Selection
        model_group = QGroupBox("AI Model Settings")
        model_layout = QVBoxLayout(model_group)
        
        backend_label = QLabel("Detection Backend:")
        backend_combo = QComboBox()
        backend_combo.addItems(["retinaface", "mtcnn", "opencv", "ssd", "dlib", "mediapipe"])
        try:
            backend_combo.setCurrentText(self._controller._face_analyzer._detector_backend)
        except:
            backend_combo.setCurrentText("retinaface")
        model_layout.addWidget(backend_label)
        model_layout.addWidget(backend_combo)
        
        model_name_label = QLabel("DeepFace Model:")
        model_name_combo = QComboBox()
        model_name_combo.addItems(["VGG-Face", "Facenet", "OpenFace", "DeepFace", "DeepID", "Dlib", "ArcFace"])
        try:
            model_name_combo.setCurrentText(self._controller._face_analyzer._model_name)
        except:
            model_name_combo.setCurrentText("VGG-Face")
        model_layout.addWidget(model_name_label)
        model_layout.addWidget(model_name_combo)
        
        layout.addWidget(model_group)
        
        # Thresholds
        threshold_group = QGroupBox("Thresholds")
        threshold_layout = QVBoxLayout(threshold_group)
        
        attention_threshold_layout = QHBoxLayout()
        attention_threshold_layout.addWidget(QLabel("Attention Threshold:"))
        attention_spinbox = QDoubleSpinBox()
        attention_spinbox.setRange(0.0, 1.0)
        attention_spinbox.setSingleStep(0.05)
        attention_spinbox.setValue(self._controller._attention_threshold)
        attention_threshold_layout.addWidget(attention_spinbox)
        threshold_layout.addLayout(attention_threshold_layout)
        
        emotion_threshold_layout = QHBoxLayout()
        emotion_threshold_layout.addWidget(QLabel("Emotion Confidence Threshold:"))
        emotion_spinbox = QDoubleSpinBox()
        emotion_spinbox.setRange(0.0, 1.0)
        emotion_spinbox.setSingleStep(0.05)
        emotion_spinbox.setValue(0.5)
        emotion_threshold_layout.addWidget(emotion_spinbox)
        threshold_layout.addLayout(emotion_threshold_layout)
        
        layout.addWidget(threshold_group)
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout(filter_group)
        
        age_filter_layout = QHBoxLayout()
        age_filter_check = QCheckBox("Filter by Age Range:")
        age_filter_min = QSpinBox()
        age_filter_min.setRange(0, 100)
        age_filter_min.setValue(0)
        age_filter_max = QSpinBox()
        age_filter_max.setRange(0, 100)
        age_filter_max.setValue(100)
        age_filter_layout.addWidget(age_filter_check)
        age_filter_layout.addWidget(QLabel("Min:"))
        age_filter_layout.addWidget(age_filter_min)
        age_filter_layout.addWidget(QLabel("Max:"))
        age_filter_layout.addWidget(age_filter_max)
        filter_layout.addLayout(age_filter_layout)
        
        gender_filter_layout = QHBoxLayout()
        gender_filter_check = QCheckBox("Filter by Gender:")
        gender_filter_combo = QComboBox()
        gender_filter_combo.addItems(["All", "Male", "Female"])
        gender_filter_layout.addWidget(gender_filter_check)
        gender_filter_layout.addWidget(gender_filter_combo)
        filter_layout.addLayout(gender_filter_layout)
        
        layout.addWidget(filter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self._save_advanced_settings(
            dialog, backend_combo.currentText(), model_name_combo.currentText(),
            attention_spinbox.value(), emotion_spinbox.value(),
            age_filter_check.isChecked(), age_filter_min.value(), age_filter_max.value(),
            gender_filter_check.isChecked(), gender_filter_combo.currentText()
        ))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _save_advanced_settings(self, dialog, backend, model_name, attention_threshold,
                                emotion_threshold, age_filter_enabled, age_min, age_max,
                                gender_filter_enabled, gender):
        """Save advanced settings."""
        try:
            self._controller._face_analyzer._detector_backend = backend
            self._controller._face_analyzer._model_name = model_name
            self._controller.set_attention_threshold(attention_threshold)
            # Store filters in controller for later use
            self._controller._age_filter = (age_min, age_max) if age_filter_enabled else None
            self._controller._gender_filter = gender if gender_filter_enabled and gender != "All" else None
            
            self.statusBar().showMessage("Settings saved successfully")
            dialog.accept()
            QMessageBox.information(
                self, "Settings Saved",
                "Advanced settings have been saved successfully.\n\n"
                "Changes will take effect on the next analysis session."
            )
        except ValueError as e:
            QMessageBox.warning(
                self, "Invalid Settings",
                f"Invalid setting value:\n\n{str(e)}\n\n"
                "Please check your input and try again."
            )
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Settings Error",
                f"Failed to save settings:\n\n{str(e)}\n\n"
                "Some settings may not have been applied.\n"
                "Please check the console for details."
            )
    
    def _export_csv(self):
        """Export statistics to CSV file."""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        from pathlib import Path
        
        stats = self._controller.get_statistics()
        default_filename = f"face_ai_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV",
            str(Path.home() / default_filename),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Metric', 'Value'])
                    writer.writerow(['Session Duration (s)', stats.get('session_duration_seconds', 0)])
                    writer.writerow(['Frames Processed', stats.get('frames_processed', 0)])
                    writer.writerow(['Total Faces Detected', stats.get('total_faces_detected', 0)])
                    writer.writerow(['Average Attention', f"{stats.get('average_attention', 0):.4f}"])
                    writer.writerow(['Focused Count', stats.get('focused_count', 0)])
                    writer.writerow(['Distracted Count', stats.get('distracted_count', 0)])
                    writer.writerow(['Focused Ratio', f"{stats.get('focused_ratio', 0):.4f}"])
                    writer.writerow(['Average Face Count', f"{stats.get('average_face_count', 0):.2f}"])
                    writer.writerow(['Smiling Events', stats.get('smiling_count', 0)])
                    writer.writerow(['Average Age', f"{stats.get('average_age', 0):.1f}"])
                    
                    writer.writerow([])
                    writer.writerow(['Emotion Distribution'])
                    for emotion, count in stats.get('emotion_distribution', {}).items():
                        writer.writerow([emotion, count])
                    
                    writer.writerow([])
                    writer.writerow(['Attention Distribution'])
                    for direction, count in stats.get('attention_distribution', {}).items():
                        writer.writerow([direction, count])
                
                QMessageBox.information(
                    self, "Export Successful",
                    f"Statistics successfully exported to CSV:\n\n{filepath}\n\n"
                    "The file contains all analysis data including:\n"
                    "• Session statistics\n"
                    "• Emotion distribution\n"
                    "• Attention distribution"
                )
            except PermissionError as e:
                QMessageBox.critical(
                    self, "Permission Error",
                    f"Cannot write to the selected location:\n\n{str(e)}\n\n"
                    "Please select a different location or check file permissions."
                )
            except Exception as e:
                logger.error(f"Error exporting CSV: {e}", exc_info=True)
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export CSV file:\n\n{str(e)}\n\n"
                    "Please check the console for detailed error information."
                )
    
    def _export_excel(self):
        """Export statistics to Excel file."""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.warning(
                self, "Export Error",
                "pandas is required for Excel export.\n\n"
                "Install with: pip install pandas openpyxl"
            )
            return
        
        stats = self._controller.get_statistics()
        default_filename = f"face_ai_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel",
            str(Path.home() / default_filename),
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filepath:
            try:
                # Create DataFrame with statistics
                data = {
                    'Metric': [
                        'Session Duration (s)', 'Frames Processed', 'Total Faces Detected',
                        'Average Attention', 'Focused Count', 'Distracted Count',
                        'Focused Ratio', 'Average Face Count', 'Smiling Events', 'Average Age'
                    ],
                    'Value': [
                        stats.get('session_duration_seconds', 0),
                        stats.get('frames_processed', 0),
                        stats.get('total_faces_detected', 0),
                        f"{stats.get('average_attention', 0):.4f}",
                        stats.get('focused_count', 0),
                        stats.get('distracted_count', 0),
                        f"{stats.get('focused_ratio', 0):.4f}",
                        f"{stats.get('average_face_count', 0):.2f}",
                        stats.get('smiling_count', 0),
                        f"{stats.get('average_age', 0):.1f}"
                    ]
                }
                df_main = pd.DataFrame(data)
                
                df_emotion = pd.DataFrame({
                    'Emotion': list(stats.get('emotion_distribution', {}).keys()),
                    'Count': list(stats.get('emotion_distribution', {}).values())
                })
                
                df_attention = pd.DataFrame({
                    'Direction': list(stats.get('attention_distribution', {}).keys()),
                    'Count': list(stats.get('attention_distribution', {}).values())
                })
                
                # Write to Excel with multiple sheets
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df_main.to_excel(writer, sheet_name='Summary', index=False)
                    df_emotion.to_excel(writer, sheet_name='Emotion Distribution', index=False)
                    df_attention.to_excel(writer, sheet_name='Attention Distribution', index=False)
                
                QMessageBox.information(
                    self, "Export Successful",
                    f"Statistics successfully exported to Excel:\n\n{filepath}\n\n"
                    "The file contains multiple sheets:\n"
                    "• Summary - Overall statistics\n"
                    "• Emotion Distribution - Emotion analysis\n"
                    "• Attention Distribution - Attention tracking"
                )
            except PermissionError as e:
                QMessageBox.critical(
                    self, "Permission Error",
                    f"Cannot write to the selected location:\n\n{str(e)}\n\n"
                    "Please select a different location or check file permissions."
                )
            except Exception as e:
                logger.error(f"Error exporting Excel: {e}", exc_info=True)
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export Excel file:\n\n{str(e)}\n\n"
                    "Please check the console for detailed error information.\n\n"
                    "Note: Excel export requires 'pandas' and 'openpyxl' packages."
                )
    
    def _update_live_charts(self, stats: Dict):
        """Update live charts with current statistics."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from io import BytesIO
            
            # Emotion Pie Chart
            if stats.get('emotion_distribution'):
                fig = plt.Figure(figsize=(4, 3))
                ax = fig.add_subplot(111)
                emotions = list(stats['emotion_distribution'].keys())
                counts = list(stats['emotion_distribution'].values())
                if counts and sum(counts) > 0:
                    colors = plt.cm.Set3(range(len(emotions)))
                    ax.pie(counts, labels=emotions, autopct='%1.1f%%', colors=colors, startangle=90)
                    ax.set_title('Emotion Distribution', fontsize=10)
                    
                    # Convert to pixmap
                    buf = BytesIO()
                    fig.savefig(buf, format='png', dpi=80, bbox_inches='tight')
                    buf.seek(0)
                    q_image = QImage.fromData(buf.read())
                    pixmap = QPixmap.fromImage(q_image)
                    self._emotion_chart_display.setPixmap(pixmap)
                    plt.close(fig)
            
            # Attention Bar Chart
            if stats.get('attention_distribution'):
                fig = plt.Figure(figsize=(4, 3))
                ax = fig.add_subplot(111)
                directions = list(stats['attention_distribution'].keys())
                counts = list(stats['attention_distribution'].values())
                if counts and sum(counts) > 0:
                    colors = ['green' if d == 'focused' else 'orange' if d == 'distracted' else 'gray' 
                             for d in directions]
                    ax.bar(directions, counts, color=colors)
                    ax.set_title('Attention Distribution', fontsize=10)
                    ax.tick_params(axis='x', rotation=45)
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                    
                    # Convert to pixmap
                    buf = BytesIO()
                    fig.savefig(buf, format='png', dpi=80, bbox_inches='tight')
                    buf.seek(0)
                    q_image = QImage.fromData(buf.read())
                    pixmap = QPixmap.fromImage(q_image)
                    self._attention_chart_display.setPixmap(pixmap)
                    plt.close(fig)
        except Exception as e:
            logger.error(f"Error updating live charts: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self._controller.is_analyzing():
            self._controller.stop_analysis()
        event.accept()

