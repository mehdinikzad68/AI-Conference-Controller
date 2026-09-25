"""
Schedule Engine - Time-Based Content Scheduling

Manages scheduled content playback with:
- Time-based triggering
- Priority queue
- Dynamic re-scheduling
- Conflict detection
- Emergency override support

Real-time scheduling engine running in background.
"""

import asyncio
import heapq
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging
import uuid

from ..models import ScheduleItem, ContentItem, Priority, PlaybackStatus, PlatformType
from ..sync.event_bus import Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class ScheduleEngine:
    """
    Time-based scheduling engine with priority queue.
    
    Features:
    - Priority-based scheduling
    - Automatic triggering at scheduled time
    - Dynamic re-scheduling
    - Conflict detection
    - Emergency override
    """
    
    def __init__(self, check_interval_seconds: float = 1.0):
        """
        Initialize schedule engine.
        
        Args:
            check_interval_seconds: How often to check schedule
        """
        self._check_interval = check_interval_seconds
        self._schedules: Dict[str, ScheduleItem] = {}
        self._priority_queue: List[tuple] = []  # (timestamp, priority, schedule_id)
        self._event_bus = get_event_bus()
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Callbacks
        self._trigger_callbacks: List[Callable] = []
        
        logger.info("ScheduleEngine initialized")
    
    async def start(self):
        """Start schedule engine."""
        if self._running:
            logger.warning("ScheduleEngine already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("ScheduleEngine started")
    
    async def stop(self):
        """Stop schedule engine."""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ScheduleEngine stopped")
    
    async def create_schedule(
        self,
        content_id: str,
        start_time: datetime,
        platforms: List[PlatformType],
        priority: Priority = Priority.NORMAL,
        **kwargs
    ) -> ScheduleItem:
        """
        Create new schedule.
        
        Args:
            content_id: Content to play
            start_time: When to start
            platforms: Target platforms
            priority: Schedule priority
            **kwargs: Additional ScheduleItem parameters
        
        Returns:
            Created ScheduleItem
        
        Example:
            >>> schedule = await engine.create_schedule(
            ...     content_id='123',
            ...     start_time=datetime(2025, 11, 4, 9, 0),
            ...     platforms=[PlatformType.LOCAL_HALL, PlatformType.SKYROOM]
            ... )
        """
        schedule_id = kwargs.get('schedule_id', str(uuid.uuid4()))
        
        schedule_item = ScheduleItem(
            schedule_id=schedule_id,
            content_id=content_id,
            start_time=start_time,
            platforms=platforms,
            priority=priority,
            **{k: v for k, v in kwargs.items() if k != 'schedule_id'}
        )
        
        async with self._lock:
            self._schedules[schedule_id] = schedule_item
            
            # Add to priority queue
            heapq.heappush(
                self._priority_queue,
                (start_time.timestamp(), -priority.value, schedule_id)
            )
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SCHEDULE_CREATED,
            data={
                'schedule_id': schedule_id,
                'content_id': content_id,
                'start_time': start_time.isoformat(),
                'platforms': [p.value for p in platforms]
            },
            source='ScheduleEngine'
        ))
        
        logger.info(f"Created schedule: {schedule_id} at {start_time}")
        return schedule_item
    
    async def update_schedule(
        self,
        schedule_id: str,
        start_time: Optional[datetime] = None,
        priority: Optional[Priority] = None,
        platforms: Optional[List[PlatformType]] = None
    ) -> ScheduleItem:
        """
        Update existing schedule (re-scheduling).
        
        Args:
            schedule_id: Schedule to update
            start_time: New start time
            priority: New priority
            platforms: New platforms
        
        Returns:
            Updated ScheduleItem
        
        Raises:
            KeyError: If schedule not found
        """
        async with self._lock:
            if schedule_id not in self._schedules:
                raise KeyError(f"Schedule not found: {schedule_id}")
            
            schedule = self._schedules[schedule_id]
            
            # Update fields
            if start_time:
                schedule.start_time = start_time
            if priority:
                schedule.priority = priority
            if platforms:
                schedule.platforms = platforms
            
            # Rebuild priority queue
            self._rebuild_priority_queue()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SCHEDULE_UPDATED,
            data={'schedule_id': schedule_id},
            source='ScheduleEngine'
        ))
        
        logger.info(f"Updated schedule: {schedule_id}")
        return schedule
    
    async def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel schedule.
        
        Args:
            schedule_id: Schedule to cancel
        
        Returns:
            True if cancelled
        """
        async with self._lock:
            if schedule_id not in self._schedules:
                return False
            
            schedule = self._schedules[schedule_id]
            schedule.playback_status = PlaybackStatus.CANCELLED
            
            # Remove from queue
            self._rebuild_priority_queue()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SCHEDULE_CANCELLED,
            data={'schedule_id': schedule_id},
            source='ScheduleEngine'
        ))
        
        logger.info(f"Cancelled schedule: {schedule_id}")
        return True
    
    async def emergency_stop_all(self):
        """Emergency stop all schedules."""
        async with self._lock:
            for schedule in self._schedules.values():
                if schedule.playback_status in [PlaybackStatus.SCHEDULED, PlaybackStatus.QUEUED]:
                    schedule.playback_status = PlaybackStatus.EMERGENCY_STOPPED
            
            self._priority_queue.clear()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.EMERGENCY_STOP,
            data={'stopped_count': len(self._schedules)},
            source='ScheduleEngine'
        ))
        
        logger.warning("EMERGENCY STOP - All schedules stopped")
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduleItem]:
        """Get schedule by ID."""
        return self._schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[ScheduleItem]:
        """Get all schedules."""
        return list(self._schedules.values())
    
    def get_upcoming_schedules(self, limit: int = 10) -> List[ScheduleItem]:
        """
        Get upcoming schedules.
        
        Args:
            limit: Max number to return
        
        Returns:
            List of upcoming ScheduleItems (sorted by time)
        """
        now = datetime.now()
        upcoming = [
            s for s in self._schedules.values()
            if s.start_time > now and s.playback_status == PlaybackStatus.SCHEDULED
        ]
        upcoming.sort(key=lambda s: s.start_time)
        return upcoming[:limit]
    
    def get_active_schedules(self) -> List[ScheduleItem]:
        """Get currently active (playing) schedules."""
        return [
            s for s in self._schedules.values()
            if s.is_active()
        ]
    
    def on_trigger(self, callback: Callable[[ScheduleItem], None]):
        """
        Register callback for schedule trigger.
        
        Args:
            callback: Function to call when schedule triggers
        
        Example:
            >>> def on_schedule_triggered(schedule: ScheduleItem):
            ...     print(f"Triggered: {schedule.schedule_id}")
            >>> engine.on_trigger(on_schedule_triggered)
        """
        self._trigger_callbacks.append(callback)
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                await self._check_schedules()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
        
        logger.info("Scheduler loop stopped")
    
    async def _check_schedules(self):
        """Check for due schedules."""
        now = datetime.now()
        triggered = []
        
        async with self._lock:
            # Check priority queue
            while self._priority_queue:
                timestamp, _, schedule_id = self._priority_queue[0]
                
                # Check if due
                if timestamp <= now.timestamp():
                    heapq.heappop(self._priority_queue)
                    
                    schedule = self._schedules.get(schedule_id)
                    if schedule and schedule.playback_status == PlaybackStatus.SCHEDULED:
                        schedule.playback_status = PlaybackStatus.QUEUED
                        schedule.actual_start_time = now
                        triggered.append(schedule)
                else:
                    break  # Not yet due
        
        # Trigger schedules (outside lock)
        for schedule in triggered:
            await self._trigger_schedule(schedule)
    
    async def _trigger_schedule(self, schedule: ScheduleItem):
        """Trigger a schedule."""
        logger.info(f"Triggering schedule: {schedule.schedule_id}")
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.SCHEDULE_TRIGGERED,
            data={
                'schedule_id': schedule.schedule_id,
                'content_id': schedule.content_id,
                'platforms': [p.value for p in schedule.platforms]
            },
            source='ScheduleEngine'
        ))
        
        # Call callbacks
        for callback in self._trigger_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(schedule)
                else:
                    callback(schedule)
            except Exception as e:
                logger.error(f"Error in trigger callback: {e}", exc_info=True)
    
    def _rebuild_priority_queue(self):
        """Rebuild priority queue from schedules."""
        self._priority_queue.clear()
        
        for schedule_id, schedule in self._schedules.items():
            if schedule.playback_status == PlaybackStatus.SCHEDULED:
                heapq.heappush(
                    self._priority_queue,
                    (schedule.start_time.timestamp(), -schedule.priority.value, schedule_id)
                )
    
    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        total = len(self._schedules)
        by_status = {}
        
        for schedule in self._schedules.values():
            status = schedule.playback_status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_schedules': total,
            'by_status': by_status,
            'queue_size': len(self._priority_queue),
            'upcoming_next_hour': len([
                s for s in self._schedules.values()
                if s.start_time <= datetime.now() + timedelta(hours=1)
                and s.playback_status == PlaybackStatus.SCHEDULED
            ])
        }

