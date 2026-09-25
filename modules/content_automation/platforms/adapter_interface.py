"""Platform Adapter Interface - Abstract base for platform adapters"""
from abc import ABC, abstractmethod
from typing import Optional
from ..models import ContentItem

class PlatformAdapter(ABC):
    """Abstract base class for platform adapters."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to platform."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from platform."""
        pass
    
    @abstractmethod
    async def play_content(
        self,
        content: ContentItem,
        volume: float = 1.0,
        loop: bool = False
    ) -> bool:
        """Play content on platform."""
        pass
    
    @abstractmethod
    async def stop_content(self):
        """Stop current content."""
        pass
    
    @abstractmethod
    async def pause_content(self):
        """Pause current content."""
        pass
    
    @abstractmethod
    async def resume_content(self):
        """Resume paused content."""
        pass
    
    @abstractmethod
    async def get_playback_position(self) -> float:
        """Get current playback position in seconds."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to platform."""
        pass

