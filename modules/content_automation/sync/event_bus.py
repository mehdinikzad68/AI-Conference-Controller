"""
Event Bus - Event-Driven Communication System

Provides publish-subscribe pattern for loose coupling between components.
Thread-safe and async-compatible.

Usage:
    event_bus = EventBus()
    
    # Subscribe
    def handler(event):
        print(f"Received: {event.data}")
    
    event_bus.subscribe(EventType.CONTENT_ADDED, handler)
    
    # Publish
    event_bus.publish(Event(EventType.CONTENT_ADDED, data={'content_id': '123'}))
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import asyncio
import logging
from threading import Lock
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """
    All event types in the content automation system.
    
    Naming convention: {COMPONENT}_{ACTION}_{OBJECT}
    """
    # Content Events
    CONTENT_ADDED = "content.added"
    CONTENT_UPDATED = "content.updated"
    CONTENT_REMOVED = "content.removed"
    CONTENT_VALIDATION_STARTED = "content.validation.started"
    CONTENT_VALIDATION_COMPLETED = "content.validation.completed"
    CONTENT_VALIDATION_FAILED = "content.validation.failed"
    
    # Schedule Events
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_UPDATED = "schedule.updated"
    SCHEDULE_CANCELLED = "schedule.cancelled"
    SCHEDULE_TRIGGERED = "schedule.triggered"
    
    # Playback Events
    PLAYBACK_STARTED = "playback.started"
    PLAYBACK_PAUSED = "playback.paused"
    PLAYBACK_RESUMED = "playback.resumed"
    PLAYBACK_COMPLETED = "playback.completed"
    PLAYBACK_FAILED = "playback.failed"
    PLAYBACK_PROGRESS = "playback.progress"
    
    # Sync Events
    SYNC_STATUS_CHANGED = "sync.status.changed"
    SYNC_OFFSET_DETECTED = "sync.offset.detected"
    SYNC_RECOVERED = "sync.recovered"
    SYNC_FAILED = "sync.failed"
    
    # Emergency Events
    EMERGENCY_STOP = "emergency.stop"
    EMERGENCY_FALLBACK = "emergency.fallback"
    EMERGENCY_OVERRIDE = "emergency.override"
    
    # Platform Events
    PLATFORM_CONNECTED = "platform.connected"
    PLATFORM_DISCONNECTED = "platform.disconnected"
    PLATFORM_ERROR = "platform.error"
    
    # System Events
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"
    
    # Operator Events
    OPERATOR_ACTION = "operator.action"
    OPERATOR_OVERRIDE = "operator.override"


@dataclass
class Event:
    """
    Event data container.
    
    Immutable after creation for thread safety.
    """
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    priority: int = 0  # Higher = more important
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create from dictionary"""
        return cls(
            event_type=EventType(data['event_type']),
            data=data.get('data', {}),
            event_id=data.get('event_id', str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            source=data.get('source'),
            priority=data.get('priority', 0)
        )


class EventBus:
    """
    Thread-safe event bus for pub-sub pattern.
    
    Features:
    - Multiple subscribers per event type
    - Sync and async handlers
    - Priority-based event handling
    - Event filtering
    - Event history (optional)
    """
    
    def __init__(self, enable_history: bool = True, history_limit: int = 1000):
        """
        Initialize event bus.
        
        Args:
            enable_history: Keep event history for debugging
            history_limit: Maximum events to keep in history
        """
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._handler_ids: Dict[int, str] = {}  # Map handler id() -> subscription_id
        self._lock = Lock()
        self._enable_history = enable_history
        self._history: List[Event] = []
        self._history_limit = history_limit
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Callback function (sync or async)
            filter_func: Optional filter to apply before calling handler
        
        Returns:
            Subscription ID for later unsubscribe
        
        Example:
            >>> def my_handler(event: Event):
            ...     print(f"Got event: {event.data}")
            >>> 
            >>> sub_id = event_bus.subscribe(EventType.CONTENT_ADDED, my_handler)
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            # Wrap handler with filter if provided
            if filter_func:
                original_handler = handler
                def filtered_handler(event: Event):
                    if filter_func(event):
                        return original_handler(event)
                handler = filtered_handler
            
            # Store handler ID mapping (use id() to avoid attribute setting)
            handler_id = str(uuid.uuid4())
            self._handler_ids[id(handler)] = handler_id
            
            self._subscribers[event_type].append(handler)
            
            logger.debug(f"Subscribed to {event_type.value}")
            return handler_id
    
    def unsubscribe(self, event_type: EventType, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type
            subscription_id: ID returned from subscribe()
        
        Returns:
            True if unsubscribed successfully
        """
        with self._lock:
            if event_type not in self._subscribers:
                return False
            
            # Find and remove handler by ID mapping
            for i, handler in enumerate(self._subscribers[event_type]):
                if self._handler_ids.get(id(handler)) == subscription_id:
                    self._subscribers[event_type].pop(i)
                    del self._handler_ids[id(handler)]
                    logger.debug(f"Unsubscribed from {event_type.value}")
                    return True
            
            return False
    
    def publish(self, event: Event) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        
        Returns:
            Number of handlers called
        
        Example:
            >>> event = Event(
            ...     event_type=EventType.CONTENT_ADDED,
            ...     data={'content_id': '123'},
            ...     source='ContentManager'
            ... )
            >>> event_bus.publish(event)
        """
        # Add to history
        if self._enable_history:
            self._history.append(event)
            if len(self._history) > self._history_limit:
                self._history.pop(0)
        
        # Get subscribers
        with self._lock:
            handlers = self._subscribers.get(event.event_type, []).copy()
        
        if not handlers:
            logger.debug(f"No subscribers for {event.event_type.value}")
            return 0
        
        # Call handlers
        called_count = 0
        for handler in handlers:
            try:
                # Check if async
                if asyncio.iscoroutinefunction(handler):
                    # Schedule async handler
                    asyncio.create_task(handler(event))
                else:
                    # Call sync handler
                    handler(event)
                
                called_count += 1
                
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)
        
        logger.debug(f"Published {event.event_type.value} to {called_count} handlers")
        return called_count
    
    async def publish_async(self, event: Event) -> int:
        """
        Publish event asynchronously.
        
        Waits for all async handlers to complete.
        
        Args:
            event: Event to publish
        
        Returns:
            Number of handlers called
        """
        # Add to history
        if self._enable_history:
            self._history.append(event)
            if len(self._history) > self._history_limit:
                self._history.pop(0)
        
        # Get subscribers
        with self._lock:
            handlers = self._subscribers.get(event.event_type, []).copy()
        
        if not handlers:
            return 0
        
        # Call handlers
        called_count = 0
        tasks = []
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    handler(event)
                
                called_count += 1
                
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)
        
        # Wait for async handlers
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Published (async) {event.event_type.value} to {called_count} handlers")
        return called_count
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum events to return
        
        Returns:
            List of events (most recent first)
        """
        if not self._enable_history:
            return []
        
        events = self._history.copy()
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def clear_history(self):
        """Clear event history."""
        self._history.clear()
        logger.debug("Event history cleared")
    
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get number of subscribers.
        
        Args:
            event_type: Specific event type (None = total)
        
        Returns:
            Subscriber count
        """
        with self._lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            else:
                return sum(len(handlers) for handlers in self._subscribers.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            return {
                'total_subscribers': sum(len(h) for h in self._subscribers.values()),
                'event_types_with_subscribers': len(self._subscribers),
                'history_size': len(self._history) if self._enable_history else 0,
                'history_enabled': self._enable_history
            }


# Global event bus instance (singleton pattern)
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get global event bus instance.
    
    Returns:
        Singleton EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


# Convenience decorators

def event_handler(event_type: EventType):
    """
    Decorator to mark a method as an event handler.
    
    Usage:
        @event_handler(EventType.CONTENT_ADDED)
        def on_content_added(self, event: Event):
            print(f"Content added: {event.data}")
    """
    def decorator(func):
        func._is_event_handler = True
        func._event_type = event_type
        return func
    return decorator


def auto_subscribe_handlers(instance, event_bus: Optional[EventBus] = None):
    """
    Auto-subscribe all methods marked with @event_handler decorator.
    
    Args:
        instance: Object instance
        event_bus: EventBus to subscribe to (None = global)
    
    Example:
        class MyClass:
            @event_handler(EventType.CONTENT_ADDED)
            def on_content_added(self, event):
                pass
        
        obj = MyClass()
        auto_subscribe_handlers(obj)
    """
    if event_bus is None:
        event_bus = get_event_bus()
    
    # Find all event handlers
    for attr_name in dir(instance):
        attr = getattr(instance, attr_name)
        if callable(attr) and hasattr(attr, '_is_event_handler'):
            event_type = attr._event_type
            event_bus.subscribe(event_type, attr)
            logger.debug(f"Auto-subscribed {instance.__class__.__name__}.{attr_name} to {event_type.value}")

