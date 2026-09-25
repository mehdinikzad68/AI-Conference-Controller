"""
Scrollable Widget Utility

Provides a scrollable wrapper widget with mouse wheel support for responsive layouts.
"""

from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QWheelEvent


class ScrollableWidget(QWidget):
    """
    A scrollable widget wrapper that enables mouse wheel scrolling.
    
    This widget automatically handles scroll events even when menu bar is hidden
    (e.g., in fullscreen mode).
    """
    
    def __init__(self, parent=None):
        """Initialize scrollable widget."""
        super().__init__(parent)
        self.setup_scroll()
    
    def setup_scroll(self):
        """Setup scroll area and layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Create content widget
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.MinimumExpanding
        )
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # Enable mouse wheel events
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def get_content_widget(self) -> QWidget:
        """Get the content widget where child widgets should be added."""
        return self.content_widget
    
    def wheelEvent(self, event: QWheelEvent):
        """
        Handle mouse wheel events for scrolling.
        
        Works even when menu bar is hidden.
        """
        # Forward wheel event to scroll area
        if self.scroll_area.verticalScrollBar().isVisible():
            # Calculate scroll delta
            delta = event.angleDelta().y()
            scrollbar = self.scroll_area.verticalScrollBar()
            
            # Scroll with smooth behavior
            current_value = scrollbar.value()
            scrollbar.setValue(current_value - delta // 8)
            
            event.accept()
        else:
            event.ignore()
    
    def enable_wheel_scroll(self, enabled: bool = True):
        """Enable or disable wheel scrolling."""
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded if enabled 
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )


def make_responsive(widget: QWidget):
    """
    Make a widget responsive with proper size policy.
    
    Args:
        widget: Widget to make responsive
    """
    size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    size_policy.setHeightForWidth(False)
    widget.setSizePolicy(size_policy)

