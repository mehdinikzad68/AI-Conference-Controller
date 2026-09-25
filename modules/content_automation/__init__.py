"""
Content Automation Module

Automated multimedia content scheduling, validation, playback,
and synchronization for hybrid conferences.

Main Components:
- ContentAutomationEngine: Core engine
- ContentAutomationDashboard: Operator UI
- SymposiumBridge: Integration with symposium module
- EmergencyManager: Crisis management
- Notifier: Event notifications
- ReportingAnalytics: Execution reports

Quick Start:
    >>> from modules.content_automation import ContentAutomationEngine
    >>> engine = ContentAutomationEngine()
    >>> await engine.start()
"""

from .core.engine import ContentAutomationEngine
from .models import (
    ContentType, ContentMetadata, ContentItem,
    ScheduleItem, Priority, PlatformType,
    ValidationStatus, PlaybackStatus
)
from .sync.event_bus import get_event_bus, EventType, Event

__version__ = "1.0.0"
__all__ = [
    'ContentAutomationEngine',
    'ContentType',
    'ContentMetadata',
    'ContentItem',
    'ScheduleItem',
    'Priority',
    'PlatformType',
    'ValidationStatus',
    'PlaybackStatus',
    'get_event_bus',
    'EventType',
    'Event'
]
