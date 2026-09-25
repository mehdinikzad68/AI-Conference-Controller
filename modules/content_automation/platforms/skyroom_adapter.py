"""Skyroom API Adapter - Integration with Skyroom virtual platform"""
import asyncio
import aiohttp
import logging
from typing import Optional
from .adapter_interface import PlatformAdapter
from ..models import ContentItem

logger = logging.getLogger(__name__)

class SkyroomAdapter(PlatformAdapter):
    """Adapter for Skyroom API."""
    
    def __init__(self, api_url: str, api_key: str, room_id: str):
        self._api_url = api_url
        self._api_key = api_key
        self._room_id = room_id
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Skyroom API."""
        try:
            self._session = aiohttp.ClientSession(
                headers={'Authorization': f'Bearer {self._api_key}'}
            )
            
            # Test connection
            async with self._session.get(f"{self._api_url}/rooms/{self._room_id}/status") as resp:
                if resp.status == 200:
                    self._connected = True
                    logger.info(f"Connected to Skyroom: {self._room_id}")
                    return True
        except Exception as e:
            logger.error(f"Skyroom connection failed: {e}")
        return False
    
    async def disconnect(self):
        if self._session:
            await self._session.close()
        self._connected = False
    
    async def play_content(self, content: ContentItem, volume: float = 1.0, loop: bool = False) -> bool:
        """Play content via Skyroom API."""
        if not self._connected or not self._session:
            return False
        
        try:
            # Upload/share content via Skyroom API
            payload = {
                'room_id': self._room_id,
                'content_url': content.file_info.path,  # Or upload to Skyroom storage
                'content_type': content.content_type.value,
                'title': content.metadata.title
            }
            
            async with self._session.post(
                f"{self._api_url}/rooms/{self._room_id}/share_content",
                json=payload
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Playing on Skyroom: {content.content_id}")
                    return True
                else:
                    logger.error(f"Skyroom playback failed: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Skyroom playback error: {e}")
            return False
    
    async def stop_content(self):
        if self._connected and self._session:
            try:
                await self._session.post(f"{self._api_url}/rooms/{self._room_id}/stop_sharing")
            except Exception as e:
                logger.error(f"Stop error: {e}")
    
    async def pause_content(self):
        pass  # Implement based on Skyroom API
    
    async def resume_content(self):
        pass
    
    async def get_playback_position(self) -> float:
        return 0.0  # Implement based on Skyroom API
    
    def is_connected(self) -> bool:
        return self._connected

