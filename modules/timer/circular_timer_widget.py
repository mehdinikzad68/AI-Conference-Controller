"""
Circular Timer Widget Module

Custom PyQt6 widget for displaying an animated circular countdown timer
with gradient color transitions and smooth animations.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QRadialGradient
import math


class CircularTimerWidget(QWidget):
    """
    Custom widget that displays a circular countdown timer with animated progress ring.
    
    Features:
    - Smoothly animated shrinking ring (progress arc)
    - Gradient color transitions (green → yellow → red)
    - Large digital time display
    - Warning effects when time is running low
    """
    
    def __init__(self, parent=None):
        """Initialize the circular timer widget."""
        super().__init__(parent)
        self._current_time = 0  # Time in seconds
        self._initial_time = 0  # Initial time in seconds
        self._progress = 1.0  # Progress from 1.0 (start) to 0.0 (end)
        
        # Color states
        self._base_color = QColor(0, 200, 0)  # Green
        self._warning_color = QColor(255, 200, 0)  # Yellow
        self._critical_color = QColor(255, 0, 0)  # Red
        
        # Animation properties
        self._shake_offset = QPoint(0, 0)
        self._glow_intensity = 0.0
        self._show_warning = False
        self._show_finished = False
        
        # Shake animation
        self._shake_animation = QPropertyAnimation(self, b"shakeOffset")
        self._shake_animation.setDuration(500)
        self._shake_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Glow animation
        self._glow_animation = QPropertyAnimation(self, b"glowIntensity")
        self._glow_animation.setDuration(500)
        self._glow_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._glow_animation.setLoopCount(-1)  # Infinite loop
        
        # Font for time display
        self._time_font = QFont("Arial", 56, QFont.Weight.Bold)  # Reduced from 72
        self._status_font = QFont("Arial", 18, QFont.Weight.Bold)  # Reduced from 24
        
        self.setMinimumSize(350, 450)  # Reduced size for smaller display
        # Enable size policy for responsiveness
        from PyQt6.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(False)
        self.setSizePolicy(size_policy)
        
    def set_time(self, current_time: int, initial_time: int):
        """
        Update the timer display.
        
        Args:
            current_time: Current time remaining in seconds
            initial_time: Initial/total time in seconds
        """
        self._current_time = max(0, current_time)
        self._initial_time = max(1, initial_time)
        self._progress = self._current_time / self._initial_time if self._initial_time > 0 else 0.0
        self._show_finished = (self._current_time == 0 and self._initial_time > 0)
        self.update()  # Trigger repaint
        
    def set_warning_mode(self, enabled: bool):
        """
        Enable or disable warning visual effects.
        
        Args:
            enabled: True to show warning effects (red color, flashing)
        """
        self._show_warning = enabled
        if enabled:
            # Start glow animation
            self._glow_animation.setStartValue(0.0)
            self._glow_animation.setEndValue(1.0)
            if self._glow_animation.state() != QPropertyAnimation.State.Running:
                self._glow_animation.start()
            # Trigger shake effect
            self._trigger_shake()
        else:
            self._glow_animation.stop()
            self._glow_intensity = 0.0
        self.update()
        
    def set_finished_mode(self, enabled: bool):
        """
        Enable or disable finished state visual effects.
        
        Args:
            enabled: True to show finished animation
        """
        self._show_finished = enabled
        if enabled:
            self._trigger_shake(stronger=True)
        self.update()
        
    def _trigger_shake(self, stronger: bool = False):
        """Trigger a shake animation effect."""
        if self._shake_animation.state() == QPropertyAnimation.State.Running:
            return
            
        # Create shake pattern
        shake_distance = 15 if not stronger else 30
        self._shake_animation.setStartValue(QPoint(0, 0))
        self._shake_animation.setKeyValueAt(0.1, QPoint(-shake_distance, 0))
        self._shake_animation.setKeyValueAt(0.2, QPoint(shake_distance, 0))
        self._shake_animation.setKeyValueAt(0.3, QPoint(-shake_distance, 0))
        self._shake_animation.setKeyValueAt(0.4, QPoint(shake_distance, 0))
        self._shake_animation.setKeyValueAt(0.5, QPoint(-shake_distance // 2, 0))
        self._shake_animation.setKeyValueAt(0.6, QPoint(shake_distance // 2, 0))
        self._shake_animation.setEndValue(QPoint(0, 0))
        self._shake_animation.start()
        
    def get_shake_offset(self) -> QPoint:
        """Get current shake offset (for animation)."""
        return self._shake_offset
        
    def set_shake_offset(self, offset: QPoint):
        """Set shake offset (for animation)."""
        self._shake_offset = offset
        self.update()
        
    shakeOffset = pyqtProperty(QPoint, get_shake_offset, set_shake_offset)
    
    def get_glow_intensity(self) -> float:
        """Get current glow intensity (for animation)."""
        return self._glow_intensity
        
    def set_glow_intensity(self, intensity: float):
        """Set glow intensity (for animation)."""
        self._glow_intensity = max(0.0, min(1.0, intensity))
        self.update()
        
    glowIntensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)
    
    def _get_color_for_progress(self) -> QColor:
        """
        Calculate color based on progress.
        
        Returns:
            QColor interpolated between green, yellow, and red
        """
        if self._show_finished or self._progress <= 0:
            return self._critical_color
        
        # Critical threshold: last 2 minutes (< 120 seconds)
        # Assuming typical session is at least 5 minutes (300 seconds)
        critical_threshold = 120 / max(self._initial_time, 300) if self._initial_time >= 300 else 0.4
        
        if self._progress <= critical_threshold:
            # Red zone
            if self._show_warning:
                # Add glow effect
                intensity = self._glow_intensity
                alpha = int(255 * (0.7 + 0.3 * intensity))
                return QColor(255, int(50 * (1 - intensity)), int(50 * (1 - intensity)), alpha)
            return self._critical_color
        elif self._progress <= 0.5:
            # Yellow zone (middle)
            ratio = (0.5 - self._progress) / (0.5 - critical_threshold)
            return QColor(
                int(255),
                int(200 - 150 * ratio),
                int(0)
            )
        else:
            # Green zone (start)
            ratio = (1.0 - self._progress) / 0.5
            return QColor(
                int(0 + 255 * ratio),
                int(200),
                int(0)
            )
    
    def paintEvent(self, event):
        """Paint the circular timer widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Account for shake offset
        painter.translate(self._shake_offset)
        
        rect = self.rect()
        center = rect.center()
        
        # Responsive sizing: adapt to available space
        # Reserve space for warning text at bottom (100px) and status text (if shown)
        available_height = rect.height() - 100  # Reserve space for warning text
        available_width = rect.width() - 40  # Small padding
        
        # Calculate size (use 80% of smaller available dimension)
        size = min(available_width, available_height) * 0.8
        radius = size / 2
        
        # Draw background circle (subtle)
        painter.setPen(QPen(QColor(50, 50, 50, 100), 4))
        painter.setBrush(QBrush(QColor(30, 30, 30, 50)))
        painter.drawEllipse(center, int(radius), int(radius))
        
        # Draw progress arc
        if self._initial_time > 0:
            # In Qt, angles are in 1/16th of a degree
            # Start at top (90 degrees = 12 o'clock position)
            start_angle = 90 * 16
            # Span angle (negative for clockwise direction)
            span_angle = int(-360 * 16 * (1.0 - self._progress))
            
            # Get color based on progress
            color = self._get_color_for_progress()
            
            # Create pen for progress ring
            pen_width = max(15, int(radius * 0.1))  # Adaptive pen width
            pen = QPen(color, pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            # Draw the arc
            # Calculate rectangle for arc (centered at center point)
            arc_rect_size = int(radius * 2)
            arc_x = center.x() - int(radius)
            arc_y = center.y() - int(radius)
            painter.drawArc(
                arc_x,
                arc_y,
                arc_rect_size,
                arc_rect_size,
                start_angle,
                span_angle
            )
        
        # Draw time text
        minutes = self._current_time // 60
        seconds = self._current_time % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        painter.setFont(self._time_font)
        painter.setPen(QColor(255, 255, 255))
        
        # Center the text
        metrics = QFontMetrics(self._time_font)
        text_rect = metrics.boundingRect(time_text)
        text_x = center.x() - text_rect.width() // 2
        text_y = center.y() + text_rect.height() // 4
        
        painter.drawText(text_x, text_y, time_text)
        
        # Draw status text if needed
        if self._show_finished:
            painter.setFont(self._status_font)
            painter.setPen(self._critical_color)
            status_text = "END OF SPEECH"
            status_metrics = QFontMetrics(self._status_font)
            status_rect = status_metrics.boundingRect(status_text)
            status_x = center.x() - status_rect.width() // 2
            status_y = center.y() + int(radius) + 60
            painter.drawText(status_x, status_y, status_text)
        elif self._show_warning and self._current_time < 120:
            painter.setFont(self._status_font)
            glow = int(255 * self._glow_intensity)
            painter.setPen(QColor(255, glow, glow))
            status_text = "TIME ENDING SOON"
            status_metrics = QFontMetrics(self._status_font)
            status_rect = status_metrics.boundingRect(status_text)
            
            # Calculate text position ensuring it's fully visible
            # Account for widget boundaries
            status_x = max(
                status_rect.width() // 2 + 10,  # Left padding
                min(
                    center.x() - status_rect.width() // 2,  # Centered if possible
                    rect.width() - status_rect.width() - 10  # Right boundary
                )
            )
            status_y = center.y() + int(radius) + 60
            
            # Ensure text fits in widget
            if status_y + status_rect.height() > rect.height():
                status_y = rect.height() - status_rect.height() - 10
            
            # Draw text with background for better visibility
            text_x_pos = status_x - status_rect.width() // 2
            bg_x = text_x_pos - 10
            bg_y = status_y - status_rect.height() - 5
            bg_width = status_rect.width() + 20
            bg_height = status_rect.height() + 10
            painter.fillRect(bg_x, bg_y, bg_width, bg_height, QColor(0, 0, 0, 180))  # Semi-transparent black background
            
            painter.drawText(text_x_pos, status_y, status_text)

