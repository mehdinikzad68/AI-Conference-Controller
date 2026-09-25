"""
Display Output Module

Manages individual display output windows with OBS Studio compatibility.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QScreen, QPixmap, QPainter, QColor, QFont
from pathlib import Path
from typing import Optional


class DisplayOutput(QWidget):
    """
    Individual display output window that can show content from different modules.
    
    Features:
    - OBS Studio compatible window capture
    - Fullscreen support
    - Auto-scaling and centering
    - Preview mode
    """
    
    # Signals
    output_ready = pyqtSignal(str)  # Emits display name when ready
    content_changed = pyqtSignal(str)  # Emits content type when changed
    
    # Content types
    CONTENT_NONE = "none"
    CONTENT_TIMER = "timer"
    CONTENT_MEDIA = "media"
    CONTENT_FACE_AI = "face_ai"
    CONTENT_CUSTOM = "custom"
    
    def __init__(self, screen: QScreen, display_name: str, parent=None):
        """
        Initialize display output.
        
        Args:
            screen: QScreen object for this display
            display_name: User-friendly name for the display
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._screen = screen
        self._display_name = display_name
        self._content_type = self.CONTENT_NONE
        self._content_widget = None
        self._is_preview_mode = False
        self._target_resolution = None
        
        # Setup window
        self.setWindowTitle(f"Display Output - {display_name}")
        self.setup_ui()
        
        # Move to target screen
        self.move_to_screen()
        
    def setup_ui(self):
        """Setup the display output UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background (black for projector)
        self.setStyleSheet("background-color: #000000;")
        
        # Content area (will be populated by routed content)
        self._content_label = QLabel("No content assigned")
        self._content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 24px;
                padding: 50px;
            }
        """)
        layout.addWidget(self._content_label)
        
    def move_to_screen(self):
        """Move window to the target screen."""
        if self._screen:
            geometry = self._screen.geometry()
            self.setGeometry(geometry)
    
    def set_content(self, content_type: str, content_widget: Optional[QWidget] = None):
        """
        Set content to display.
        
        Args:
            content_type: Type of content (timer, media, face_ai, none)
            content_widget: Optional widget to display (will be reparented)
            
        Returns:
            bool: True if content was set successfully, False otherwise
        """
        # Validate widget if provided
        if content_widget is not None:
            # Check if widget is valid (not None and is a QWidget)
            if not isinstance(content_widget, QWidget):
                return False
            
            # Check if widget is still valid (not deleted)
            try:
                if content_widget.isHidden() is None:
                    return False  # Widget has been deleted
            except RuntimeError:
                return False  # Widget is no longer valid
        
        # Remove existing content
        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget = None
        
        self._content_type = content_type
        
        if content_widget:
            # Validate widget before assignment
            try:
                # Reparent and add content widget
                content_widget.setParent(self)
                layout = self.layout()
                if layout.count() > 0:
                    layout.removeWidget(self._content_label)
                    self._content_label.setParent(None)
                layout.addWidget(content_widget)
                content_widget.show()
                self._content_widget = content_widget
                self._content_label.hide()
            except Exception as e:
                # Widget assignment failed
                print(f"Error setting content widget: {e}")
                return False
        else:
            # Show placeholder
            if self.layout().count() == 0 or not self._content_label:
                layout = self.layout()
                self._content_label = QLabel(f"Content: {content_type}")
                self._content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._content_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 24px;
                        padding: 50px;
                    }
                """)
                layout.addWidget(self._content_label)
            else:
                self._content_label.setText(f"Content: {content_type}")
                self._content_label.show()
        
        self.content_changed.emit(content_type)
        self.update()
        return True
    
    def validate_widget(self) -> tuple[bool, str]:
        """
        Validate that content widget is present and valid.
        
        Returns:
            tuple: (is_valid, error_message)
            - is_valid: True if widget is valid, False otherwise
            - error_message: Description of validation issue (empty if valid)
        """
        # Check if content type requires a widget
        if self._content_type == self.CONTENT_NONE:
            return (True, "")  # No widget required for none
        
        # Check if widget is assigned
        if self._content_widget is None:
            return (False, f"No widget assigned for content type '{self._content_type}'")
        
        # Check if widget is a valid QWidget instance
        if not isinstance(self._content_widget, QWidget):
            return (False, f"Assigned widget is not a valid QWidget instance")
        
        # Check if widget is still valid (not deleted)
        try:
            # Try to access widget properties
            _ = self._content_widget.isVisible()
            _ = self._content_widget.isEnabled()
        except RuntimeError:
            return (False, f"Widget has been deleted or is no longer valid")
        except Exception as e:
            return (False, f"Widget validation error: {str(e)}")
        
        # Widget is valid
        return (True, "")
    
    def get_content_widget(self) -> Optional[QWidget]:
        """Get current content widget (if any)."""
        return self._content_widget
    
    def set_preview_mode(self, enabled: bool):
        """
        Enable or disable preview mode.
        
        Args:
            enabled: True for preview mode (shows test pattern)
        """
        self._is_preview_mode = enabled
        
        if enabled:
            # Show test pattern
            if self._content_widget:
                self._content_widget.hide()
            
            # Create preview widget
            preview = QWidget()
            preview.setStyleSheet("background-color: #1a1a1a;")
            preview_layout = QVBoxLayout(preview)
            
            preview_label = QLabel(f"Preview Mode\n{self._display_name}")
            preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_label.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-size: 32px;
                    font-weight: bold;
                    padding: 100px;
                }
            """)
            preview_layout.addWidget(preview_label)
            
            # Test pattern
            pattern_label = QLabel("Test Pattern\n\nRed\nGreen\nBlue\nWhite")
            pattern_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pattern_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 24px;
                    padding: 50px;
                }
            """)
            preview_layout.addWidget(pattern_label)
            
            # Replace content with preview
            layout = self.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            
            layout.addWidget(preview)
            preview.show()
        else:
            # Restore normal content
            if self._content_widget:
                self._content_widget.show()
    
    def enable_fullscreen(self):
        """Enable fullscreen mode on this display."""
        self.showFullScreen()
        self.move_to_screen()
    
    def disable_fullscreen(self):
        """Disable fullscreen mode."""
        self.showNormal()
        self.move_to_screen()
    
    def set_target_resolution(self, width: int, height: int):
        """
        Set target resolution for content scaling.
        
        Args:
            width: Target width in pixels
            height: Target height in pixels
        """
        self._target_resolution = (width, height)
        if self._content_widget:
            # Resize content widget to target resolution
            # (content will scale to fit while maintaining aspect ratio)
            pass
    
    def get_display_name(self) -> str:
        """Get display name."""
        return self._display_name
    
    def get_screen(self) -> QScreen:
        """Get associated QScreen object."""
        return self._screen
    
    def get_content_type(self) -> str:
        """Get current content type."""
        return self._content_type
    
    def is_preview_mode(self) -> bool:
        """Check if in preview mode."""
        return self._is_preview_mode
    
    def get_screen_info(self) -> dict:
        """Get information about this display."""
        if self._screen:
            geometry = self._screen.geometry()
            return {
                'name': self._display_name,
                'geometry': {
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'width': geometry.width(),
                    'height': geometry.height()
                },
                'physical_size': self._screen.physicalSize(),
                'dpi': (self._screen.physicalDotsPerInchX(), self._screen.physicalDotsPerInchY()),
                'content_type': self._content_type,
                'is_preview': self._is_preview_mode
            }
        return {}
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        
        # Auto-scale content if needed
        if self._content_widget and self._target_resolution:
            # Calculate scaling to maintain aspect ratio
            target_w, target_h = self._target_resolution
            current_w = self.width()
            current_h = self.height()
            
            scale_w = current_w / target_w
            scale_h = current_h / target_h
            scale = min(scale_w, scale_h)
            
            # Apply scaling (content widget will handle this)
            pass

