"""
Smart Timer Overlay Module

Enhanced timer overlay with horizontal progress bar, color transitions,
20% warning threshold, and visual effects for symposium presentations.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont, QPen, QLinearGradient
from typing import Optional
from pathlib import Path

from modules.timer.timer_controller import TimerController


class SmartTimerOverlay(QWidget):
    """
    Smart timer overlay with horizontal progress bar.
    
    Features:
    - Horizontal progress bar (fills/shrinks based on time)
    - Color transitions (green → yellow → red)
    - Time remaining display (mm:ss)
    - 20% warning threshold with visual effects
    - Pulsing border and blinking animations
    - Warning message display
    - Adjustable position, size, and transparency
    - OBS Studio compatible
    """
    
    # Position presets
    POSITION_BOTTOM_LEFT = "bottom_left"
    POSITION_BOTTOM_RIGHT = "bottom_right"
    POSITION_BOTTOM_CENTER = "bottom_center"
    POSITION_TOP_LEFT = "top_left"
    POSITION_TOP_RIGHT = "top_right"
    POSITION_TOP_CENTER = "top_center"
    
    # Signals
    overlay_closed = pyqtSignal()
    warning_triggered = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None, timer_controller: Optional[TimerController] = None):
        """
        Initialize smart timer overlay.
        
        Args:
            parent: Parent widget (typically MediaDisplayWidget or SymposiumWindow)
            timer_controller: TimerController instance
        """
        super().__init__(parent)
        
        # Timer controller
        if timer_controller:
            self._timer_controller = timer_controller
        else:
            self._timer_controller = TimerController()
        
        # Position and size
        self._position = self.POSITION_BOTTOM_CENTER
        self._custom_position = QPoint(0, 0)
        self._width_ratio = 0.4  # 40% of parent width
        self._height = 60  # Fixed height in pixels
        
        # Transparency
        self._opacity = 0.85
        self._background_opacity = 200  # 0-255
        
        # Progress and colors
        self._progress = 1.0  # 1.0 = start, 0.0 = end
        self._current_time = 0
        self._initial_time = 0
        
        # Warning state
        self._is_warning = False
        self._warning_threshold = 0.20  # 20% remaining
        self._pulse_animation_value = 0.0
        self._blink_animation_value = 1.0
        
        # Warning message
        self._warning_message = ""
        self._show_warning_message = False
        
        # Animations
        self._pulse_animation = QPropertyAnimation(self, b"pulseValue")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)
        
        self._blink_animation = QPropertyAnimation(self, b"blinkValue")
        self._blink_animation.setDuration(500)
        self._blink_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._blink_animation.setLoopCount(-1)
        
        # Setup
        self.setup_ui()
        self._connect_timer_signals()
        
        # Window flags for overlay (only if standalone window)
        # If parent is provided, we're a child widget overlay
        if parent:
            # Child widget overlay - no window flags needed
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
            # Raise above parent content
            self.raise_()
        else:
            # Standalone window overlay
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    
    def setup_ui(self):
        """Setup overlay UI."""
        # Widget will be drawn in paintEvent, no child widgets needed
        pass
    
    def _connect_timer_signals(self):
        """Connect timer controller signals."""
        self._timer_controller.time_changed.connect(self._on_time_changed)
        self._timer_controller.timer_finished.connect(self._on_timer_finished)
        self._timer_controller.warning_threshold.connect(self._on_warning_threshold)
    
    def _on_time_changed(self, seconds: int):
        """Handle timer time change."""
        self._current_time = seconds
        self._initial_time = self._timer_controller.get_initial_time()
        
        if self._initial_time > 0:
            self._progress = seconds / self._initial_time
            
            # Check for 20% warning threshold
            if self._progress <= self._warning_threshold and not self._is_warning:
                self._trigger_warning()
        
        self.update()
    
    def _on_timer_finished(self):
        """Handle timer finished."""
        self._progress = 0.0
        self._current_time = 0
        self._is_warning = False
        self._stop_animations()
        self.update()
    
    def _on_warning_threshold(self):
        """Handle warning threshold (legacy 2-minute threshold)."""
        # This is called by TimerController at < 2 minutes
        # We use 20% threshold instead, so this is a backup
        if self._progress > 0:
            self._trigger_warning()
    
    def _trigger_warning(self):
        """Trigger warning state."""
        if not self._is_warning:
            self._is_warning = True
            self._show_warning_message = True
            
            # Calculate remaining minutes
            minutes_left = max(0, self._current_time // 60)
            if minutes_left > 0:
                self._warning_message = f"{minutes_left} minute{'s' if minutes_left > 1 else ''} left!"
            else:
                self._warning_message = "Time ending soon!"
            
            # Start animations
            self._pulse_animation.setStartValue(0.0)
            self._pulse_animation.setEndValue(1.0)
            self._pulse_animation.start()
            
            self._blink_animation.setStartValue(1.0)
            self._blink_animation.setEndValue(0.3)
            self._blink_animation.start()
            
            self.warning_triggered.emit()
            self.update()
    
    def _stop_animations(self):
        """Stop all animations."""
        if self._pulse_animation.state() == QPropertyAnimation.State.Running:
            self._pulse_animation.stop()
        if self._blink_animation.state() == QPropertyAnimation.State.Running:
            self._blink_animation.stop()
        self._pulse_animation_value = 0.0
        self._blink_animation_value = 1.0
    
    def set_timer_controller(self, controller: TimerController):
        """Set timer controller."""
        # Disconnect old signals
        if self._timer_controller:
            try:
                self._timer_controller.time_changed.disconnect(self._on_time_changed)
                self._timer_controller.timer_finished.disconnect(self._on_timer_finished)
                self._timer_controller.warning_threshold.disconnect(self._on_warning_threshold)
            except:
                pass
        
        self._timer_controller = controller
        self._connect_timer_signals()
        self._update_from_controller()
    
    def _update_from_controller(self):
        """Update display from controller state."""
        self._current_time = self._timer_controller.get_current_time()
        self._initial_time = self._timer_controller.get_initial_time()
        
        if self._initial_time > 0:
            self._progress = self._current_time / self._initial_time
        
        # Check warning state
        if self._progress <= self._warning_threshold and self._progress > 0:
            if not self._is_warning:
                self._trigger_warning()
        else:
            self._is_warning = False
            self._show_warning_message = False
            self._stop_animations()
        
        self.update()
    
    def set_position(self, position: str):
        """Set overlay position preset."""
        self._position = position
        self._update_position()
    
    def set_custom_position(self, point: QPoint):
        """Set custom position."""
        self._custom_position = point
        self._position = "custom"
        self._update_position()
    
    def set_width_ratio(self, ratio: float):
        """
        Set overlay width as ratio of parent width.
        
        Args:
            ratio: Width ratio (0.0 to 1.0)
        """
        self._width_ratio = max(0.1, min(1.0, ratio))
        self._update_position()
    
    def set_height(self, height: int):
        """Set overlay height in pixels."""
        self._height = max(30, min(200, height))
        self._update_position()
    
    def set_opacity(self, opacity: float):
        """
        Set overlay opacity.
        
        Args:
            opacity: Opacity (0.0 to 1.0)
        """
        self._opacity = max(0.0, min(1.0, opacity))
        self._background_opacity = int(255 * opacity * 0.8)
        self.update()
    
    def get_opacity(self) -> float:
        """Get current opacity."""
        return self._opacity
    
    def _update_position(self):
        """Update widget position based on settings."""
        if not self.parent():
            return
        
        parent = self.parent()
        if isinstance(parent, QWidget):
            parent_rect = parent.rect()
        else:
            parent_rect = parent.geometry()
        
        # Calculate size
        width = int(parent_rect.width() * self._width_ratio)
        height = self._height
        self.setFixedSize(width, height)
        
        # Calculate position
        margin = 20
        
        if self._position == self.POSITION_BOTTOM_LEFT:
            x = margin
            y = parent_rect.height() - height - margin
        elif self._position == self.POSITION_BOTTOM_RIGHT:
            x = parent_rect.width() - width - margin
            y = parent_rect.height() - height - margin
        elif self._position == self.POSITION_BOTTOM_CENTER:
            x = (parent_rect.width() - width) // 2
            y = parent_rect.height() - height - margin
        elif self._position == self.POSITION_TOP_LEFT:
            x = margin
            y = margin
        elif self._position == self.POSITION_TOP_RIGHT:
            x = parent_rect.width() - width - margin
            y = margin
        elif self._position == self.POSITION_TOP_CENTER:
            x = (parent_rect.width() - width) // 2
            y = margin
        else:  # custom
            x = self._custom_position.x()
            y = self._custom_position.y()
        
        self.move(x, y)
    
    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        if self._position != "custom":
            self._update_position()
    
    def paintEvent(self, event):
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        rect = self.rect()
        
        # Background with rounded corners
        bg_color = QColor(0, 0, 0, self._background_opacity)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Border (pulsing if warning)
        border_width = 2
        if self._is_warning:
            border_width = int(2 + 3 * self._pulse_animation_value)
            border_color = QColor(255, int(100 * (1 - self._blink_animation_value)), 0)
        else:
            border_color = QColor(255, 255, 255, 100)
        
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Progress bar
        bar_margin = 10
        bar_rect = QRect(
            bar_margin,
            bar_margin,
            rect.width() - 2 * bar_margin,
            rect.height() - 2 * bar_margin - 20  # Space for time label
        )
        
        # Progress bar background
        bg_bar_rect = bar_rect
        painter.setBrush(QBrush(QColor(60, 60, 60, 180)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_bar_rect, 4, 4)
        
        # Progress fill
        fill_width = int(bar_rect.width() * self._progress)
        if fill_width > 0:
            fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_width, bar_rect.height())
            
            # Color gradient based on progress
            gradient = QLinearGradient(bar_rect.x(), 0, bar_rect.x() + bar_rect.width(), 0)
            
            if self._progress <= self._warning_threshold:
                # Red zone
                if self._is_warning:
                    # Pulsing red
                    intensity = self._blink_animation_value
                    gradient.setColorAt(0, QColor(255, int(50 * intensity), int(50 * intensity)))
                    gradient.setColorAt(1, QColor(200, int(30 * intensity), int(30 * intensity)))
                else:
                    gradient.setColorAt(0, QColor(255, 50, 50))
                    gradient.setColorAt(1, QColor(200, 30, 30))
            elif self._progress <= 0.5:
                # Yellow zone
                ratio = (0.5 - self._progress) / 0.3
                gradient.setColorAt(0, QColor(255, int(200 - 150 * ratio), 0))
                gradient.setColorAt(1, QColor(255, int(150 - 120 * ratio), 0))
            else:
                # Green zone
                ratio = (1.0 - self._progress) / 0.5
                gradient.setColorAt(0, QColor(0, 255, 0))
                gradient.setColorAt(1, QColor(0, int(200 - 50 * ratio), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(fill_rect, 4, 4)
        
        # Time label
        minutes = self._current_time // 60
        seconds = self._current_time % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Text color (white normally, red if warning)
        if self._is_warning:
            text_color = QColor(255, int(100 * self._blink_animation_value), 0)
        else:
            text_color = QColor(255, 255, 255)
        
        painter.setPen(QPen(text_color))
        text_rect = QRect(bar_margin, bar_rect.bottom() + 2, rect.width() - 2 * bar_margin, 18)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
        
        # Warning message (top right corner)
        if self._show_warning_message and self._is_warning:
            warning_font = QFont("Arial", 11, QFont.Weight.Bold)
            painter.setFont(warning_font)
            
            # Pulsing warning text
            warning_opacity = self._blink_animation_value
            warning_color = QColor(255, int(200 * warning_opacity), 0)
            painter.setPen(QPen(warning_color))
            
            warning_rect = QRect(rect.width() - 150, 5, 145, 20)
            painter.drawText(warning_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, self._warning_message)
    
    def get_pulse_value(self) -> float:
        """Get pulse animation value."""
        return self._pulse_animation_value
    
    def set_pulse_value(self, value: float):
        """Set pulse animation value."""
        self._pulse_animation_value = max(0.0, min(1.0, value))
        self.update()
    
    pulseValue = pyqtProperty(float, get_pulse_value, set_pulse_value)
    
    def get_blink_value(self) -> float:
        """Get blink animation value."""
        return self._blink_animation_value
    
    def set_blink_value(self, value: float):
        """Set blink animation value."""
        self._blink_animation_value = max(0.0, min(1.0, value))
        self.update()
    
    blinkValue = pyqtProperty(float, get_blink_value, set_blink_value)
    
    def show_overlay(self, fade_in: bool = True):
        """Show overlay."""
        if fade_in:
            from PyQt6.QtCore import QPropertyAnimation
            self.setWindowOpacity(0.0)
            fade = QPropertyAnimation(self, b"windowOpacity")
            fade.setDuration(300)
            fade.setStartValue(0.0)
            fade.setEndValue(self._opacity)
            fade.start()
        self.show()
        self.raise_()
        self._update_from_controller()
    
    def hide_overlay(self, fade_out: bool = True):
        """Hide overlay."""
        if fade_out:
            from PyQt6.QtCore import QPropertyAnimation
            fade = QPropertyAnimation(self, b"windowOpacity")
            fade.setDuration(300)
            fade.setStartValue(self._opacity)
            fade.setEndValue(0.0)
            fade.finished.connect(lambda: self.setVisible(False))
            fade.start()
        else:
            self.hide()
        self._stop_animations()
        self.overlay_closed.emit()

