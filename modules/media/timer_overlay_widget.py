"""
Timer Overlay Widget Module

Overlay widget that displays the smart animated timer on top of media content.
Designed for seamless integration with video, PDF, and image displays.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont, QPen
from typing import Optional

# Import timer components
from modules.timer.circular_timer_widget import CircularTimerWidget
from modules.timer.timer_controller import TimerController


class TimerOverlayWidget(QWidget):
    """
    Overlay widget that displays animated timer on top of media content.
    
    Features:
    - Transparent background
    - Animated timer display
    - Draggable positioning
    - Fade in/out animations
    - Multiple position presets
    """
    
    # Position presets
    POSITION_TOP_LEFT = "top_left"
    POSITION_TOP_RIGHT = "top_right"
    POSITION_BOTTOM_LEFT = "bottom_left"
    POSITION_BOTTOM_RIGHT = "bottom_right"
    POSITION_CENTER = "center"
    POSITION_TOP_CENTER = "top_center"
    
    # Signals
    overlay_closed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None, timer_controller: Optional[TimerController] = None):
        """
        Initialize timer overlay widget.
        
        Args:
            parent: Parent widget (typically MediaWindow or MediaDisplayWidget)
            timer_controller: TimerController instance to use (creates new if None)
        """
        super().__init__(parent)
        
        # Timer controller
        if timer_controller:
            self._timer_controller = timer_controller
        else:
            self._timer_controller = TimerController()
        
        # Position
        self._position = self.POSITION_TOP_RIGHT
        self._custom_position = QPoint(0, 0)
        self._is_dragging = False
        self._drag_offset = QPoint(0, 0)
        
        # Visibility
        self._is_visible = True
        self._opacity = 1.0
        self._fade_animation = None
        
        # Timer widget
        self._timer_widget = None
        
        # Setup UI
        self.init_ui()
        
        # Connect timer signals
        self._connect_timer_signals()
        
        # Window flags for overlay
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        # Make draggable
        self.setMouseTracking(True)
        
    def init_ui(self):
        """Initialize the overlay UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container widget with semi-transparent background
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title bar (for dragging)
        title_bar = QWidget()
        title_bar.setFixedHeight(25)
        title_bar.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        
        title_label = QLabel("Timer")
        title_label.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 150);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
            }
        """)
        close_btn.clicked.connect(self.hide_overlay)
        title_layout.addWidget(close_btn)
        
        container_layout.addWidget(title_bar)
        
        # Circular timer widget
        self._timer_widget = CircularTimerWidget(container)
        self._timer_widget.setMinimumSize(200, 200)
        self._timer_widget.setMaximumSize(250, 250)
        container_layout.addWidget(self._timer_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(container)
        
        # Update timer display
        self._update_timer_display()
        
    def _connect_timer_signals(self):
        """Connect timer controller signals."""
        self._timer_controller.time_changed.connect(self._on_timer_changed)
        self._timer_controller.warning_threshold.connect(self._on_warning_threshold)
        self._timer_controller.timer_finished.connect(self._on_timer_finished)
        
    def _on_timer_changed(self, seconds: int):
        """Handle timer time change."""
        initial_time = self._timer_controller.get_initial_time()
        if self._timer_widget:
            self._timer_widget.set_time(seconds, initial_time)
    
    def _on_warning_threshold(self):
        """Handle warning threshold."""
        if self._timer_widget:
            self._timer_widget.set_warning_mode(True)
    
    def _on_timer_finished(self):
        """Handle timer finished."""
        if self._timer_widget:
            self._timer_widget.set_finished_mode(True)
            # Auto-hide after 3 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, self.hide_overlay)
    
    def _update_timer_display(self):
        """Update timer display with current values."""
        if self._timer_widget:
            current_time = self._timer_controller.get_current_time()
            initial_time = self._timer_controller.get_initial_time()
            if initial_time == 0:
                initial_time = 300  # Default 5 minutes if not set
                current_time = initial_time
            self._timer_widget.set_time(current_time, initial_time)
    
    def set_timer_controller(self, controller: TimerController):
        """
        Set timer controller.
        
        Args:
            controller: TimerController instance
        """
        # Disconnect old signals
        if self._timer_controller:
            self._timer_controller.time_changed.disconnect()
            self._timer_controller.warning_threshold.disconnect()
            self._timer_controller.timer_finished.disconnect()
        
        self._timer_controller = controller
        self._connect_timer_signals()
        self._update_timer_display()
    
    def get_timer_controller(self) -> TimerController:
        """Get current timer controller."""
        return self._timer_controller
    
    def set_position(self, position: str):
        """
        Set overlay position preset.
        
        Args:
            position: Position preset (top_left, top_right, center, etc.)
        """
        self._position = position
        self._update_position()
    
    def set_custom_position(self, point: QPoint):
        """
        Set custom overlay position.
        
        Args:
            point: Custom position point
        """
        self._custom_position = point
        self._position = "custom"
        self._update_position()
    
    def _update_position(self):
        """Update widget position based on current position setting."""
        if not self.parent():
            return
        
        parent = self.parent()
        if isinstance(parent, QWidget):
            parent_rect = parent.rect()
        else:
            parent_rect = parent.geometry()
        
        widget_size = self.sizeHint()
        margin = 20
        
        if self._position == self.POSITION_TOP_LEFT:
            x = margin
            y = margin
        elif self._position == self.POSITION_TOP_RIGHT:
            x = parent_rect.width() - widget_size.width() - margin
            y = margin
        elif self._position == self.POSITION_BOTTOM_LEFT:
            x = margin
            y = parent_rect.height() - widget_size.height() - margin
        elif self._position == self.POSITION_BOTTOM_RIGHT:
            x = parent_rect.width() - widget_size.width() - margin
            y = parent_rect.height() - widget_size.height() - margin
        elif self._position == self.POSITION_CENTER:
            x = (parent_rect.width() - widget_size.width()) // 2
            y = (parent_rect.height() - widget_size.height()) // 2
        elif self._position == self.POSITION_TOP_CENTER:
            x = (parent_rect.width() - widget_size.width()) // 2
            y = margin
        else:  # custom
            x = self._custom_position.x()
            y = self._custom_position.y()
        
        self.move(x, y)
    
    def show_overlay(self, fade_in: bool = True, duration: int = 300):
        """
        Show overlay with optional fade-in animation.
        
        Args:
            fade_in: Enable fade-in animation
            duration: Animation duration in milliseconds
        """
        self._is_visible = True
        
        if fade_in:
            self._opacity = 0.0
            self._fade_animation = QPropertyAnimation(self, b"opacity")
            self._fade_animation.setDuration(duration)
            self._fade_animation.setStartValue(0.0)
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._fade_animation.start()
        else:
            self._opacity = 1.0
        
        self.show()
        self.raise_()
        self._update_timer_display()
    
    def hide_overlay(self, fade_out: bool = True, duration: int = 300):
        """
        Hide overlay with optional fade-out animation.
        
        Args:
            fade_out: Enable fade-out animation
            duration: Animation duration in milliseconds
        """
        if fade_out:
            if self._fade_animation:
                self._fade_animation.stop()
            
            self._fade_animation = QPropertyAnimation(self, b"opacity")
            self._fade_animation.setDuration(duration)
            self._fade_animation.setStartValue(1.0)
            self._fade_animation.setEndValue(0.0)
            self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._fade_animation.finished.connect(lambda: self.setVisible(False))
            self._fade_animation.start()
        else:
            self._is_visible = False
            self.hide()
        
        self.overlay_closed.emit()
    
    def get_opacity(self) -> float:
        """Get current opacity (for animation)."""
        return self._opacity
    
    def set_opacity(self, opacity: float):
        """Set opacity (for animation)."""
        self._opacity = max(0.0, min(1.0, opacity))
        self.update()
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_offset = event.pos()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = self.mapToParent(event.pos() - self._drag_offset)
            self.move(new_pos)
            self._position = "custom"
            self._custom_position = new_pos
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
    
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        # Adjust position if needed
        if self._position != "custom":
            self._update_position()
    
    def paintEvent(self, event):
        """Paint overlay with opacity support."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # Fill with transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Paint children (timer widget)
        super().paintEvent(event)
    
    def set_timer_time(self, seconds: int):
        """
        Set timer time.
        
        Args:
            seconds: Time in seconds
        """
        self._timer_controller.set_time(seconds)
        self._update_timer_display()
    
    def start_timer(self):
        """Start the timer."""
        if self._timer_controller.get_current_time() == 0:
            # Set default time if not set
            self._timer_controller.set_time(300)  # 5 minutes
        self._timer_controller.start()
    
    def pause_timer(self):
        """Pause the timer."""
        self._timer_controller.pause()
    
    def resume_timer(self):
        """Resume the timer."""
        self._timer_controller.resume()
    
    def reset_timer(self):
        """Reset the timer."""
        self._timer_controller.reset()
        if self._timer_widget:
            self._timer_widget.set_warning_mode(False)
            self._timer_widget.set_finished_mode(False)
        self._update_timer_display()

