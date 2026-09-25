"""
Scene Manager Module

Manages scene switching for symposium display (agenda, intro, session, logo).
"""

from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional


class SceneType(Enum):
    """Scene types for symposium display."""
    AGENDA = "agenda"  # Full agenda display
    SPEAKER_INTRO = "speaker_intro"  # Speaker introduction slide
    SESSION = "session"  # Active session with media
    LOGO = "logo"  # Branded logo slide
    BREAK = "break"  # Break/intermission screen


class SceneManager(QObject):
    """
    Manages scene switching for symposium presentations.
    
    Features:
    - Seamless transitions between scenes
    - State management
    - Event signals for scene changes
    """
    
    # Signals
    scene_changed = pyqtSignal(SceneType)  # Emits new scene type
    scene_transition_started = pyqtSignal(SceneType, SceneType)  # Emits (from, to)
    scene_transition_completed = pyqtSignal(SceneType)  # Emits new scene type
    
    def __init__(self):
        """Initialize scene manager."""
        super().__init__()
        self._current_scene = SceneType.LOGO
        self._previous_scene: Optional[SceneType] = None
        self._is_transitioning = False
    
    def get_current_scene(self) -> SceneType:
        """Get current scene type."""
        return self._current_scene
    
    def get_previous_scene(self) -> Optional[SceneType]:
        """Get previous scene type."""
        return self._previous_scene
    
    def is_transitioning(self) -> bool:
        """Check if currently transitioning."""
        return self._is_transitioning
    
    def switch_to_agenda(self):
        """Switch to agenda scene."""
        self._transition_to(SceneType.AGENDA)
    
    def switch_to_speaker_intro(self):
        """Switch to speaker intro scene."""
        self._transition_to(SceneType.SPEAKER_INTRO)
    
    def switch_to_session(self):
        """Switch to session scene."""
        self._transition_to(SceneType.SESSION)
    
    def switch_to_logo(self):
        """Switch to logo scene."""
        self._transition_to(SceneType.LOGO)
    
    def switch_to_break(self):
        """Switch to break scene."""
        self._transition_to(SceneType.BREAK)
    
    def _transition_to(self, new_scene: SceneType):
        """
        Transition to a new scene.
        
        Args:
            new_scene: Target scene type
        """
        if self._is_transitioning:
            return
        
        if new_scene == self._current_scene:
            return
        
        self._is_transitioning = True
        
        # Emit transition started
        self.scene_transition_started.emit(self._current_scene, new_scene)
        
        # Update state
        self._previous_scene = self._current_scene
        self._current_scene = new_scene
        
        # Emit scene changed
        self.scene_changed.emit(new_scene)
        
        # Mark transition as complete
        self._is_transitioning = False
        self.scene_transition_completed.emit(new_scene)
    
    def go_back(self) -> bool:
        """
        Go back to previous scene.
        
        Returns:
            True if went back, False if no previous scene
        """
        if self._previous_scene:
            self._transition_to(self._previous_scene)
            return True
        return False

