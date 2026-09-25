"""Sync Coordinator - Real-time Synchronization"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from ..models import SyncState, SyncStatus, PlaybackState, PlatformType
from ..sync.event_bus import Event, EventType, get_event_bus

logger = logging.getLogger(__name__)

class SyncCoordinator:
    """Manages real-time synchronization across platforms."""
    
    def __init__(self, tolerance_ms: float = 500.0):
        self._tolerance_ms = tolerance_ms
        self._sync_states: Dict[str, SyncState] = {}
        self._event_bus = get_event_bus()
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
    
    async def start(self):
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("SyncCoordinator started")
    
    async def stop(self):
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
    
    async def monitor_sync(self, schedule_id: str, playback_states: Dict[PlatformType, PlaybackState]):
        """Monitor synchronization for a playback."""
        sync_state = SyncState(
            schedule_id=schedule_id,
            platforms=playback_states
        )
        self._sync_states[schedule_id] = sync_state
    
    async def _sync_loop(self):
        """Check sync status periodically."""
        while self._running:
            try:
                await asyncio.sleep(1.0)
                await self._check_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
    
    async def _check_sync(self):
        """Check synchronization of all active playbacks."""
        for schedule_id, sync_state in self._sync_states.items():
            # Calculate offset between platforms
            progress_times = [
                s.progress_seconds for s in sync_state.platforms.values()
                if s.status == PlaybackStatus.PLAYING
            ]
            
            if len(progress_times) < 2:
                continue
            
            max_offset_ms = (max(progress_times) - min(progress_times)) * 1000
            sync_state.sync_offset_ms = max_offset_ms
            
            # Update sync status
            if max_offset_ms > self._tolerance_ms:
                sync_state.sync_status = SyncStatus.OUT_OF_SYNC
                self._event_bus.publish(Event(
                    event_type=EventType.SYNC_OFFSET_DETECTED,
                    data={
                        'schedule_id': schedule_id,
                        'offset_ms': max_offset_ms
                    }
                ))
            else:
                sync_state.sync_status = SyncStatus.SYNCED

