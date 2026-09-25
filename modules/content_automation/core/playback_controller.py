"""
Playback Controller - Multi-Platform Playback Coordination

Coordinates content playback across multiple platforms simultaneously.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models import ScheduleItem, PlaybackState, PlaybackStatus, PlatformType
from ..sync.event_bus import Event, EventType, get_event_bus
from ..platforms.adapter_interface import PlatformAdapter

logger = logging.getLogger(__name__)


class PlaybackController:
    """Coordinates playback across platforms."""
    
    def __init__(self):
        self._adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._active_playbacks: Dict[str, Dict[PlatformType, PlaybackState]] = {}
        self._event_bus = get_event_bus()
        self._lock = asyncio.Lock()
        logger.info("PlaybackController initialized")
    
    def register_adapter(self, platform: PlatformType, adapter: PlatformAdapter):
        """Register platform adapter."""
        self._adapters[platform] = adapter
        logger.info(f"Registered adapter: {platform.value}")
    
    async def start_playback(
        self,
        schedule: ScheduleItem,
        content_item
    ) -> Dict[PlatformType, PlaybackState]:
        """
        Start playback on all scheduled platforms.
        
        Returns dict of PlaybackState per platform.
        """
        schedule_id = schedule.schedule_id
        results = {}
        
        for platform in schedule.platforms:
            if platform not in self._adapters:
                logger.error(f"No adapter for {platform.value}")
                results[platform] = PlaybackState(
                    schedule_id=schedule_id,
                    content_id=schedule.content_id,
                    status=PlaybackStatus.FAILED,
                    platform=platform,
                    error_message=f"No adapter for {platform.value}"
                )
                continue
            
            adapter = self._adapters[platform]
            
            try:
                # Start playback
                success = await adapter.play_content(
                    content_item,
                    volume=schedule.volume,
                    loop=schedule.loop
                )
                
                state = PlaybackState(
                    schedule_id=schedule_id,
                    content_id=schedule.content_id,
                    status=PlaybackStatus.PLAYING if success else PlaybackStatus.FAILED,
                    platform=platform,
                    started_at=datetime.now() if success else None,
                    duration_seconds=content_item.get_duration(),
                    error_message=None if success else "Failed to start playback"
                )
                
                results[platform] = state
                
            except Exception as e:
                logger.error(f"Playback error on {platform.value}: {e}", exc_info=True)
                results[platform] = PlaybackState(
                    schedule_id=schedule_id,
                    content_id=schedule.content_id,
                    status=PlaybackStatus.FAILED,
                    platform=platform,
                    error_message=str(e)
                )
        
        # Store active playbacks
        async with self._lock:
            self._active_playbacks[schedule_id] = results
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.PLAYBACK_STARTED,
            data={
                'schedule_id': schedule_id,
                'platforms': [p.value for p in results.keys()],
                'success_count': sum(1 for s in results.values() if s.status == PlaybackStatus.PLAYING)
            },
            source='PlaybackController'
        ))
        
        return results
    
    async def stop_playback(self, schedule_id: str):
        """Stop playback on all platforms."""
        async with self._lock:
            if schedule_id not in self._active_playbacks:
                return
            
            states = self._active_playbacks[schedule_id]
        
        for platform, state in states.items():
            if state.status == PlaybackStatus.PLAYING:
                adapter = self._adapters.get(platform)
                if adapter:
                    try:
                        await adapter.stop_content()
                    except Exception as e:
                        logger.error(f"Stop error on {platform.value}: {e}")
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.PLAYBACK_COMPLETED,
            data={'schedule_id': schedule_id},
            source='PlaybackController'
        ))
    
    async def emergency_stop_all(self):
        """Emergency stop all playbacks."""
        async with self._lock:
            schedule_ids = list(self._active_playbacks.keys())
        
        for schedule_id in schedule_ids:
            await self.stop_playback(schedule_id)
        
        logger.warning("EMERGENCY STOP - All playbacks stopped")
    
    def get_playback_state(self, schedule_id: str) -> Optional[Dict[PlatformType, PlaybackState]]:
        """Get playback states."""
        return self._active_playbacks.get(schedule_id)
    
    def get_stats(self) -> Dict:
        """Get playback statistics."""
        return {
            'active_playbacks': len(self._active_playbacks),
            'registered_adapters': len(self._adapters),
            'adapter_types': [p.value for p in self._adapters.keys()]
        }

