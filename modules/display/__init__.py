"""
Display module for AI-Symp-Controller.

Manages output to projectors, TVs, and external displays.
"""

from .display_controller import DisplayController
from .display_manager_window import DisplayManagerWindow
from .display_output import DisplayOutput

__all__ = ['DisplayController', 'DisplayManagerWindow', 'DisplayOutput']

