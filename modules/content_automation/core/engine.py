"""
Main Content Automation Engine - Orchestration Layer

Coordinates all components and provides unified API.
"""

import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime

from ..models import ContentItem, ContentType, ContentMetadata, ScheduleItem, Priority, PlatformType
from .content_manager import ContentManager
from .schedule_engine import ScheduleEngine
from .playback_controller import PlaybackController
from .validation_service import ValidationService
from ..sync.coordinator import SyncCoordinator
from ..sync.event_bus import get_event_bus, Event, EventType
from ..platforms.local_hall_adapter import LocalHallAdapter
from ..platforms.skyroom_adapter import SkyroomAdapter

logger = logging.getLogger(__name__)


class ContentAutomationEngine:
    """
    Main orchestration engine.
    
    Unified interface for content automation system.
    
    Example:
        >>> engine = ContentAutomationEngine()
        >>> await engine.start()
        >>> 
        >>> # Add content
        >>> content_id = await engine.add_content(
        ...     path='/media/video.mp4',
        ...     content_type=ContentType.VIDEO,
        ...     metadata=ContentMetadata(title='Opening')
        ... )
        >>> 
        >>> # Schedule
        >>> await engine.schedule_content(
        ...     content_id=content_id,
        ...     start_time=datetime(2025, 11, 4, 9, 0),
        ...     platforms=['hall', 'skyroom']
        ... )
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize engine.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        
        # Core components
        self._validation_service = ValidationService()
        self._content_manager = ContentManager(
            storage_path=self._config.get('storage_path'),
            validation_service=self._validation_service
        )
        self._schedule_engine = ScheduleEngine()
        self._playback_controller = PlaybackController()
        self._sync_coordinator = SyncCoordinator()
        
        # Event bus
        self._event_bus = get_event_bus()
        
        # State
        self._running = False
        
        # Connect schedule engine to playback
        self._schedule_engine.on_trigger(self._on_schedule_triggered)
        
        logger.info("ContentAutomationEngine initialized")
    
    async def start(self):
        """Start all services."""
        if self._running:
            return
        
        logger.info("Starting ContentAutomationEngine...")
        
        # Start services
        await self._validation_service.start()
        await self._schedule_engine.start()
        await self._sync_coordinator.start()
        
        self._running = True
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SYSTEM_STARTED,
            source='ContentAutomationEngine'
        ))
        
        logger.info("ContentAutomationEngine started")
    
    async def stop(self):
        """Stop all services."""
        if not self._running:
            return
        
        logger.info("Stopping ContentAutomationEngine...")
        
        # Emergency stop all playbacks
        await self._playback_controller.emergency_stop_all()
        
        # Stop services
        await self._sync_coordinator.stop()
        await self._schedule_engine.stop()
        await self._validation_service.stop()
        
        self._running = False
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SYSTEM_STOPPED,
            source='ContentAutomationEngine'
        ))
        
        logger.info("ContentAutomationEngine stopped")
    
    # ========== Content Management ==========
    
    async def add_content(
        self,
        path: str,
        content_type: ContentType,
        metadata: ContentMetadata
    ) -> str:
        """
        Add content to library.
        
        Returns content_id
        """
        content = await self._content_manager.add_content(path, content_type, metadata)
        return content.content_id
    
    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Get content by ID."""
        return self._content_manager.get_content(content_id)
    
    def search_content(self, **filters) -> List[ContentItem]:
        """Search content with filters."""
        return self._content_manager.search_content(**filters)
    
    # ========== Scheduling ==========
    
    async def schedule_content(
        self,
        content_id: str,
        start_time: datetime,
        platforms: List[str],  # ['hall', 'skyroom']
        priority: str = 'normal',
        **kwargs
    ) -> str:
        """
        Schedule content playback.
        
        Returns schedule_id
        """
        # Convert platform strings to enums
        platform_types = []
        for p in platforms:
            if p == 'hall':
                platform_types.append(PlatformType.LOCAL_HALL)
            elif p == 'skyroom':
                platform_types.append(PlatformType.SKYROOM)
        
        # Convert priority
        priority_map = {
            'low': Priority.LOW,
            'normal': Priority.NORMAL,
            'high': Priority.HIGH,
            'emergency': Priority.EMERGENCY
        }
        priority_enum = priority_map.get(priority.lower(), Priority.NORMAL)
        
        # Create schedule
        schedule = await self._schedule_engine.create_schedule(
            content_id=content_id,
            start_time=start_time,
            platforms=platform_types,
            priority=priority_enum,
            **kwargs
        )
        
        return schedule.schedule_id
    
    async def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel scheduled playback."""
        return await self._schedule_engine.cancel_schedule(schedule_id)
    
    def get_upcoming_schedules(self, limit: int = 10) -> List[ScheduleItem]:
        """Get upcoming schedules."""
        return self._schedule_engine.get_upcoming_schedules(limit)
    
    # ========== Platform Management ==========
    
    def register_platform(self, platform_name: str, adapter):
        """Register platform adapter."""
        platform_map = {
            'hall': PlatformType.LOCAL_HALL,
            'skyroom': PlatformType.SKYROOM
        }
        platform_type = platform_map.get(platform_name.lower())
        if platform_type:
            self._playback_controller.register_adapter(platform_type, adapter)
    
    # ========== Emergency Controls ==========
    
    async def emergency_stop(self):
        """Emergency stop everything."""
        logger.warning("EMERGENCY STOP triggered")
        await self._schedule_engine.emergency_stop_all()
        await self._playback_controller.emergency_stop_all()
    
    # ========== Statistics ==========
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        return {
            'content': self._content_manager.get_stats(),
            'schedule': self._schedule_engine.get_stats(),
            'playback': self._playback_controller.get_stats(),
            'validation': self._validation_service.get_stats(),
            'running': self._running
        }
    
    # ========== Internal Handlers ==========
    
    async def _on_schedule_triggered(self, schedule: ScheduleItem):
        """Handle schedule trigger."""
        logger.info(f"Schedule triggered: {schedule.schedule_id}")
        
        # Get content
        content = self._content_manager.get_content(schedule.content_id)
        if not content:
            logger.error(f"Content not found: {schedule.content_id}")
            return
        
        # Check validation
        if not content.is_valid():
            logger.error(f"Content not validated: {schedule.content_id}")
            return
        
        # Start playback
        playback_states = await self._playback_controller.start_playback(schedule, content)
        
        # Monitor sync
        await self._sync_coordinator.monitor_sync(schedule.schedule_id, playback_states)

