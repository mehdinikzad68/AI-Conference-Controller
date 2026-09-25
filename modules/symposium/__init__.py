"""
Symposium Display & Smart Timing Module

Comprehensive symposium presentation system with agenda display, speaker introductions,
smart timer overlays, progress bars, and seamless scene switching.
"""

from .symposium_window import SymposiumWindow
from .agenda_manager import AgendaManager, AgendaItem, SpeakerInfo
from .session_controller import SessionController
from .smart_timer_overlay import SmartTimerOverlay
from .scene_manager import SceneManager, SceneType

__all__ = [
    'SymposiumWindow',
    'AgendaManager',
    'AgendaItem',
    'SpeakerInfo',
    'SessionController',
    'SmartTimerOverlay',
    'SceneManager',
    'SceneType'
]

