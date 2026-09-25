"""
Media Controller Module

Handles playback of various media types including slides, PDFs, images, and videos.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import Optional, Dict, List
import gc
import logging

logger = logging.getLogger(__name__)


class MediaController(QObject):
    """
    Controller for media playback module.
    
    Manages loading, playback, and navigation of media content.
    Features memory optimization and resource management.
    """
    
    # Signals for media events
    media_loaded = pyqtSignal(str)  # Emits file path
    media_ended = pyqtSignal()
    position_changed = pyqtSignal(float)  # Emits position as percentage (0.0-1.0)
    playback_state_changed = pyqtSignal(bool)  # True for playing, False for paused
    memory_warning = pyqtSignal(float)  # Emits RAM usage percentage
    
    def __init__(self) -> None:
        """Initialize the media controller."""
        super().__init__()
        self._current_file: Optional[str] = None
        self._is_playing: bool = False
        self._current_position: float = 0.0
        
        # Memory management
        self._loaded_files: Dict[str, object] = {}  # Cache of loaded files
        self._max_cache_size = 5  # Maximum number of files to keep in cache
        self._enable_thumbnail_mode = True  # Use thumbnails for large files
        
        # Resource monitoring callback
        self._check_ram_callback: Optional[callable] = None
        
    def load_file(self, file_path: str, force_reload: bool = False) -> None:
        """
        Load a media file with memory optimization.
        
        Args:
            file_path: Path to the media file
            force_reload: Force reload even if already cached
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")
        
        # Check RAM usage before loading
        if self._check_ram_callback:
            try:
                if self._check_ram_callback():
                    logger.warning("High RAM usage detected. Clearing cache before loading new file.")
                    self._clear_cache()
            except:
                pass
        
        # Clear old file from memory if exists
        if self._current_file and self._current_file != str(path):
            self._release_file(self._current_file)
        
        # Load new file
        self._current_file = str(path)
        
        # Manage cache size
        if len(self._loaded_files) >= self._max_cache_size:
            self._clear_oldest_cache()
        
        self.media_loaded.emit(self._current_file)
        logger.info(f"Media file loaded: {file_path}")
    
    def _release_file(self, file_path: str):
        """
        Release a file from memory.
        
        Args:
            file_path: Path to file to release
        """
        try:
            if file_path in self._loaded_files:
                del self._loaded_files[file_path]
            
            # Force garbage collection
            gc.collect()
            logger.debug(f"Released file from memory: {file_path}")
        except Exception as e:
            logger.warning(f"Error releasing file {file_path}: {e}")
    
    def _clear_cache(self):
        """Clear all cached files."""
        try:
            self._loaded_files.clear()
            gc.collect()
            logger.info("Media cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def _clear_oldest_cache(self):
        """Clear oldest cached file."""
        if self._loaded_files:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._loaded_files))
            self._release_file(oldest_key)
    
    def play(self) -> None:
        """Start or resume media playback."""
        if self._current_file:
            self._is_playing = True
            self.playback_state_changed.emit(True)
    
    def pause(self) -> None:
        """Pause media playback."""
        if self._is_playing:
            self._is_playing = False
            self.playback_state_changed.emit(False)
    
    def stop(self) -> None:
        """Stop media playback and release resources."""
        self._is_playing = False
        self._current_position = 0.0
        self.playback_state_changed.emit(False)
        
        # Release current file if not needed
        if self._current_file:
            self._release_file(self._current_file)
    
    def clear_all_cache(self) -> None:
        """Clear all cached media files to free memory."""
        self._clear_cache()
        logger.info("All media cache cleared")
    
    def set_max_cache_size(self, size: int):
        """
        Set maximum cache size.
        
        Args:
            size: Maximum number of files to cache
        """
        self._max_cache_size = max(1, size)
        logger.info(f"Max cache size set to {self._max_cache_size}")
        
        # Clear excess if needed
        while len(self._loaded_files) > self._max_cache_size:
            self._clear_oldest_cache()
    
    def set_ram_check_callback(self, callback: callable):
        """
        Set callback function to check RAM usage.
        
        Args:
            callback: Function that returns True if RAM usage is high
        """
        self._check_ram_callback = callback
    
    def next_slide(self) -> None:
        """Navigate to next slide/page."""
        pass  # Placeholder for slide navigation
    
    def previous_slide(self) -> None:
        """Navigate to previous slide/page."""
        pass  # Placeholder for slide navigation
    
    def get_current_file(self) -> str:
        """
        Get the currently loaded file path.
        
        Returns:
            Current file path or empty string
        """
        return self._current_file or ""
    
    def is_playing(self) -> bool:
        """
        Check if media is currently playing.
        
        Returns:
            True if playing, False otherwise
        """
        return self._is_playing

