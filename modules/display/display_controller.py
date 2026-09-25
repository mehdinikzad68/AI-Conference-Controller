"""
Display Controller Module

Manages output to external displays, projectors, and TVs for presentation purposes.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QWidget
from typing import List, Optional


class DisplayController(QObject):
    """
    Controller for display output management.
    
    Handles multi-display configuration, window placement, and fullscreen modes.
    """
    
    # Signals for display events
    display_connected = pyqtSignal(QScreen)
    display_disconnected = pyqtSignal(QScreen)
    display_mode_changed = pyqtSignal(str)  # Emits mode ("extended", "mirror", etc.)
    
    def __init__(self):
        """Initialize the display controller."""
        super().__init__()
        self._available_screens = []
        self._primary_screen = None
        self._extended_mode = True
        
    def refresh_displays(self):
        """Refresh the list of available displays."""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            self._available_screens = app.screens()
            if self._available_screens:
                self._primary_screen = self._available_screens[0]
    
    def get_available_screens(self) -> list:
        """
        Get list of available display screens.
        
        Returns:
            List of QScreen objects
        """
        return self._available_screens.copy()
    
    def get_primary_screen(self) -> QScreen:
        """Get the primary display screen."""
        return self._primary_screen
    
    def set_extended_mode(self, enabled: bool):
        """
        Enable or disable extended display mode.
        
        Args:
            enabled: True for extended mode, False for mirror mode
        """
        self._extended_mode = enabled
        mode = "extended" if enabled else "mirror"
        self.display_mode_changed.emit(mode)
    
    def move_window_to_display(self, window, screen_index: int):
        """
        Move a window to a specific display.
        
        Args:
            window: QWidget window to move
            screen_index: Index of the target screen
        """
        if 0 <= screen_index < len(self._available_screens):
            screen = self._available_screens[screen_index]
            geometry = screen.geometry()
            window.setGeometry(geometry)
    
    def setup_fullscreen_on_display(self, window, screen_index: int):
        """
        Set up fullscreen mode on a specific display.
        
        Args:
            window: QWidget window to make fullscreen
            screen_index: Index of the target screen
        """
        if 0 <= screen_index < len(self._available_screens):
            screen = self._available_screens[screen_index]
            geometry = screen.geometry()
            window.setGeometry(geometry)
            window.showFullScreen()

