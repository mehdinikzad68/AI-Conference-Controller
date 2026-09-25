# 🔌 Content Automation Module - Integration Guide

## Quick Start Integration

### 1. Initialize Engine

```python
from modules.content_automation import ContentAutomationEngine
from modules.content_automation.models import ContentType, ContentMetadata
from datetime import datetime, timedelta

# Create engine
engine = ContentAutomationEngine(config={
    'storage_path': 'content_automation_library.json'
})

# Start
await engine.start()
```

### 2. Register Platform Adapters

```python
from modules.content_automation.platforms import LocalHallAdapter, SkyroomAdapter

# Local hall (integrate with existing modules)
hall_adapter = LocalHallAdapter(
    media_controller=your_media_controller,
    display_controller=your_display_controller
)
await hall_adapter.connect()
engine.register_platform('hall', hall_adapter)

# Skyroom
skyroom_adapter = SkyroomAdapter(
    api_url='https://api.skyroom.ir',
    api_key='your_api_key',
    room_id='your_room_id'
)
await skyroom_adapter.connect()
engine.register_platform('skyroom', skyroom_adapter)
```

### 3. Add Content

```python
# Add video
content_id = await engine.add_content(
    path='/media/opening_video.mp4',
    content_type=ContentType.VIDEO,
    metadata=ContentMetadata(
        title='Opening Video',
        description='Conference opening',
        duration_seconds=120,
        tags=['opening', 'intro']
    )
)
```

### 4. Schedule Playback

```python
# Schedule for both platforms
schedule_id = await engine.schedule_content(
    content_id=content_id,
    start_time=datetime.now() + timedelta(minutes=5),
    platforms=['hall', 'skyroom'],
    priority='high'
)
```

### 5. Monitor Events

```python
from modules.content_automation.sync.event_bus import get_event_bus, EventType

event_bus = get_event_bus()

def on_playback_started(event):
    print(f"Playback started: {event.data}")

event_bus.subscribe(EventType.PLAYBACK_STARTED, on_playback_started)
```

---

## Integration with Main Application

### In main.py

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... existing code ...
        
        # Initialize Content Automation
        self.content_automation = None
        self._init_content_automation()
    
    def _init_content_automation(self):
        """Initialize content automation module."""
        from modules.content_automation import ContentAutomationEngine
        from modules.content_automation.platforms import LocalHallAdapter
        
        # Create engine
        self.content_automation = ContentAutomationEngine()
        
        # Register local hall adapter
        hall_adapter = LocalHallAdapter(
            media_controller=self.media_controller,
            display_controller=self.display_controller
        )
        
        # Start in event loop
        asyncio.create_task(self._start_content_automation(hall_adapter))
    
    async def _start_content_automation(self, hall_adapter):
        """Start content automation."""
        await hall_adapter.connect()
        self.content_automation.register_platform('hall', hall_adapter)
        await self.content_automation.start()
        print("✅ Content Automation started")
```

---

## Error Scenarios & Recovery

### Scenario 1: File Not Found

```python
# ERROR: Content file doesn't exist
try:
    content_id = await engine.add_content(
        path='/nonexistent/file.mp4',
        content_type=ContentType.VIDEO,
        metadata=ContentMetadata(title='Test')
    )
except FileNotFoundError as e:
    # RECOVERY: Show error to operator
    print(f"❌ Error: {e}")
    # Operator can browse for correct file
    correct_path = operator_dashboard.browse_file()
    content_id = await engine.add_content(correct_path, ...)
```

**Module Response**:
- Validation fails immediately
- Event: `CONTENT_VALIDATION_FAILED`
- Error message: "File not found: /nonexistent/file.mp4"
- Status: `ValidationStatus.INVALID`

### Scenario 2: Platform Connection Lost

```python
# ERROR: Skyroom connection drops during playback
# Automatic handling by adapter:
class SkyroomAdapter:
    async def play_content(self, content, ...):
        try:
            # Attempt playback
            response = await self._session.post(...)
        except aiohttp.ClientError as e:
            # CONNECTION LOST
            logger.error(f"Skyroom connection lost: {e}")
            
            # Emit error event
            event_bus.publish(Event(
                event_type=EventType.PLATFORM_ERROR,
                data={
                    'platform': 'skyroom',
                    'error': str(e),
                    'severity': 'high'
                }
            ))
            
            # Return failure
            return False

# RECOVERY in PlaybackController:
playback_states = await controller.start_playback(schedule, content)

# Check for failures
failed_platforms = [
    p for p, state in playback_states.items()
    if state.status == PlaybackStatus.FAILED
]

if failed_platforms:
    # Notify operator
    operator_dashboard.show_alert(
        f"⚠️ Playback failed on: {failed_platforms}\n"
        f"✅ Playing successfully on: {successful_platforms}"
    )
    
    # Try fallback content
    if 'skyroom' in failed_platforms:
        await engine.schedule_content(
            content_id=fallback_content_id,
            start_time=datetime.now(),
            platforms=['skyroom'],
            priority='emergency'
        )
```

**Module Response**:
- PlaybackState.status = `FAILED`
- Event: `PLATFORM_ERROR`
- Continues on other platforms
- Operator notified via dashboard

### Scenario 3: Sync Offset Detected

```python
# ERROR: Hall and Skyroom out of sync (>500ms)
# Automatic detection by SyncCoordinator:

async def _check_sync(self):
    for schedule_id, sync_state in self._sync_states.items():
        # Hall at 10.5s, Skyroom at 11.2s
        offset_ms = 700  # Out of tolerance!
        
        if offset_ms > self._tolerance_ms:
            # Emit warning
            event_bus.publish(Event(
                event_type=EventType.SYNC_OFFSET_DETECTED,
                data={
                    'schedule_id': schedule_id,
                    'offset_ms': offset_ms,
                    'recommendation': 'Consider manual sync adjustment'
                }
            ))

# RECOVERY options:
# 1. Operator manual adjustment
operator_dashboard.show_sync_controls(schedule_id)

# 2. Automatic re-sync (pause/resume)
await playback_controller.pause_content(schedule_id, platform='hall')
await asyncio.sleep(0.7)  # Wait for Skyroom to catch up
await playback_controller.resume_content(schedule_id, platform='hall')

# 3. Accept degraded sync
sync_state.sync_status = SyncStatus.DEGRADED
operator_dashboard.show_warning("Sync degraded but continuing")
```

**Module Response**:
- SyncState.sync_status = `OUT_OF_SYNC`
- Event: `SYNC_OFFSET_DETECTED`
- Continues playback (doesn't stop)
- Provides sync controls to operator
- Logs offset for analysis

---

## API Documentation

### REST API Endpoints

```python
from modules.content_automation.api import ContentAutomationAPI

# Create API
api = ContentAutomationAPI(engine)

# Endpoints:
# POST /content/add
# GET /content/{content_id}
# GET /content/search
# POST /schedule/create
# DELETE /schedule/{schedule_id}
# POST /emergency/stop
# GET /stats
```

### WebSocket Events

```python
from modules.content_automation.api import WebSocketHandler

# Connect
ws = WebSocketHandler(engine)

# Receives real-time events:
# - playback.started
# - playback.progress
# - sync.status.changed
# - emergency.stop
```

---

## Testing

```python
# test_content_automation.py
import pytest
from modules.content_automation import ContentAutomationEngine

@pytest.mark.asyncio
async def test_full_workflow():
    engine = ContentAutomationEngine()
    await engine.start()
    
    # Add content
    content_id = await engine.add_content(...)
    assert content_id
    
    # Schedule
    schedule_id = await engine.schedule_content(...)
    assert schedule_id
    
    # Check stats
    stats = engine.get_stats()
    assert stats['running'] == True
    
    await engine.stop()
```

---

## Performance Considerations

- **Validation**: Async, non-blocking (max 3 concurrent)
- **Scheduling**: Priority queue, O(log n) operations
- **Sync checking**: 1-second interval (configurable)
- **Event bus**: Lock-free for reads, minimal contention

---

## Security Notes

- Sanitize all file paths (prevent traversal)
- Validate API keys for external platforms
- Rate limit emergency operations
- Log all operator overrides

---

**Version**: 1.0.0  
**Status**: Production-Ready  
**Integration Time**: ~30 minutes

