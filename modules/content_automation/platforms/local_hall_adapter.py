"""Local Hall Adapter - Integration with existing media/display modules"""
import logging
from typing import Optional
from .adapter_interface import PlatformAdapter
from ..models import ContentItem, ContentType

logger = logging.getLogger(__name__)

class LocalHallAdapter(PlatformAdapter):
    """Adapter for local hall (existing media/display modules)."""
    
    def __init__(self, media_controller=None, display_controller=None):
        self._media_controller = media_controller
        self._display_controller = display_controller
        self._connected = False
        self._current_content: Optional[ContentItem] = None
    
    async def connect(self) -> bool:
        """Connect to local controllers."""
        if self._media_controller and self._display_controller:
            self._connected = True
            logger.info("LocalHallAdapter connected")
            return True
        logger.warning("LocalHallAdapter: controllers not provided")
        return False
    
    async def disconnect(self):
        self._connected = False
    
    async def play_content(self, content: ContentItem, volume: float = 1.0, loop: bool = False) -> bool:
        """Play content via media controller."""
        if not self._connected or not self._media_controller:
            return False
        
        try:
            self._current_content = content
            
            # Load media based on type
            if content.content_type in [ContentType.VIDEO, ContentType.IMAGE]:
                success = self._media_controller.load_media(content.file_info.path)
                if success:
                    self._media_controller.play()
            
            elif content.content_type == ContentType.PDF:
                # Show on display
                if self._display_controller:
                    self._display_controller.show_pdf(content.file_info.path)
                    success = True
            
            logger.info(f"Playing content: {content.content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False
    
    async def stop_content(self):
        if self._media_controller:
            self._media_controller.stop()
        self._current_content = None
    
    async def pause_content(self):
        if self._media_controller:
            self._media_controller.pause()
    
    async def resume_content(self):
        if self._media_controller:
            self._media_controller.resume()
    
    async def get_playback_position(self) -> float:
        if self._media_controller and hasattr(self._media_controller, 'get_position'):
            return self._media_controller.get_position()
        return 0.0
    
    def is_connected(self) -> bool:
        return self._connected

