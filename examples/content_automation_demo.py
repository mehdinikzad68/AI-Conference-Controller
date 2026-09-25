"""
Content Automation Module - Complete Demo

Demonstrates all features and integration points.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content_automation import ContentAutomationEngine
from modules.content_automation.models import ContentType, ContentMetadata, Priority
from modules.content_automation.sync.event_bus import get_event_bus, EventType
from modules.content_automation.platforms import LocalHallAdapter, SkyroomAdapter


class ContentAutomationDemo:
    """Complete demonstration of content automation module."""
    
    def __init__(self):
        self.engine = None
        self.event_log = []
    
    async def run_complete_demo(self):
        """Run complete demonstration."""
        print("=" * 60)
        print("🎬 Content Automation Module - Complete Demo")
        print("=" * 60)
        print()
        
        await self.step1_initialize()
        await self.step2_setup_event_monitoring()
        await self.step3_register_platforms()
        await self.step4_add_content()
        await self.step5_schedule_playback()
        await self.step6_monitor_status()
        await self.step7_emergency_controls()
        await self.step8_error_handling()
        await self.step9_cleanup()
        
        print("\n" + "=" * 60)
        print("✅ Demo Complete!")
        print("=" * 60)
    
    async def step1_initialize(self):
        """Step 1: Initialize engine."""
        print("Step 1: Initialize Engine")
        print("-" * 40)
        
        self.engine = ContentAutomationEngine(config={
            'storage_path': 'demo_content_library.json'
        })
        
        await self.engine.start()
        
        print("✅ Engine initialized and started")
        print()
        
        await asyncio.sleep(1)
    
    async def step2_setup_event_monitoring(self):
        """Step 2: Setup event monitoring."""
        print("Step 2: Setup Event Monitoring")
        print("-" * 40)
        
        event_bus = get_event_bus()
        
        # Subscribe to key events
        def log_event(event):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.event_log.append(f"[{timestamp}] {event.event_type.value}: {event.data}")
            print(f"  📡 Event: {event.event_type.value}")
        
        # Subscribe to all important events
        important_events = [
            EventType.CONTENT_ADDED,
            EventType.CONTENT_VALIDATION_COMPLETED,
            EventType.SCHEDULE_CREATED,
            EventType.SCHEDULE_TRIGGERED,
            EventType.PLAYBACK_STARTED,
            EventType.PLAYBACK_FAILED,
            EventType.SYNC_OFFSET_DETECTED,
            EventType.EMERGENCY_STOP
        ]
        
        for event_type in important_events:
            event_bus.subscribe(event_type, log_event)
        
        print(f"✅ Subscribed to {len(important_events)} event types")
        print()
        
        await asyncio.sleep(0.5)
    
    async def step3_register_platforms(self):
        """Step 3: Register platform adapters."""
        print("Step 3: Register Platform Adapters")
        print("-" * 40)
        
        # Mock adapters for demo
        # In real integration, pass actual controllers
        hall_adapter = LocalHallAdapter(
            media_controller=None,  # Would be your MediaController
            display_controller=None  # Would be your DisplayController
        )
        await hall_adapter.connect()
        self.engine.register_platform('hall', hall_adapter)
        print("  ✅ Local Hall adapter registered")
        
        # Skyroom adapter (requires actual API credentials)
        # skyroom_adapter = SkyroomAdapter(
        #     api_url='https://api.skyroom.ir',
        #     api_key='your_api_key',
        #     room_id='your_room_id'
        # )
        # await skyroom_adapter.connect()
        # self.engine.register_platform('skyroom', skyroom_adapter)
        print("  ⚠️  Skyroom adapter skipped (requires credentials)")
        
        print()
        await asyncio.sleep(0.5)
    
    async def step4_add_content(self):
        """Step 4: Add content to library."""
        print("Step 4: Add Content to Library")
        print("-" * 40)
        
        # For demo, create dummy files
        demo_content = [
            {
                'path': 'demo_content/opening_video.mp4',
                'type': ContentType.VIDEO,
                'metadata': ContentMetadata(
                    title='Opening Video',
                    description='Conference opening ceremony',
                    duration_seconds=180,
                    tags=['opening', 'intro', 'important']
                )
            },
            {
                'path': 'demo_content/sponsor_logo.png',
                'type': ContentType.LOGO,
                'metadata': ContentMetadata(
                    title='Sponsor Logo',
                    description='Main sponsor branding',
                    tags=['sponsor', 'branding']
                )
            },
            {
                'path': 'demo_content/presentation.pdf',
                'type': ContentType.PDF,
                'metadata': ContentMetadata(
                    title='Keynote Presentation',
                    description='Dr. Smith keynote slides',
                    tags=['presentation', 'keynote']
                )
            }
        ]
        
        # Create demo files (empty for demo purposes)
        Path('demo_content').mkdir(exist_ok=True)
        for item in demo_content:
            Path(item['path']).touch()
        
        # Add to library
        self.content_ids = {}
        for item in demo_content:
            try:
                content_id = await self.engine.add_content(
                    path=item['path'],
                    content_type=item['type'],
                    metadata=item['metadata']
                )
                self.content_ids[item['metadata'].title] = content_id
                print(f"  ✅ Added: {item['metadata'].title}")
                
                # Wait for validation
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Show stats
        stats = self.engine.get_stats()
        print(f"\n  📊 Content Stats: {stats['content']}")
        print()
        
        await asyncio.sleep(1)
    
    async def step5_schedule_playback(self):
        """Step 5: Schedule content playback."""
        print("Step 5: Schedule Content Playback")
        print("-" * 40)
        
        # Schedule opening video in 10 seconds
        opening_time = datetime.now() + timedelta(seconds=10)
        opening_id = self.content_ids.get('Opening Video')
        
        if opening_id:
            schedule_id = await self.engine.schedule_content(
                content_id=opening_id,
                start_time=opening_time,
                platforms=['hall'],
                priority='high',
                volume=0.8
            )
            print(f"  ✅ Scheduled Opening Video at {opening_time.strftime('%H:%M:%S')}")
            print(f"     Schedule ID: {schedule_id}")
        
        # Schedule logo immediately
        logo_id = self.content_ids.get('Sponsor Logo')
        if logo_id:
            schedule_id2 = await self.engine.schedule_content(
                content_id=logo_id,
                start_time=datetime.now() + timedelta(seconds=2),
                platforms=['hall'],
                priority='normal'
            )
            print(f"  ✅ Scheduled Sponsor Logo (immediate)")
        
        # Show upcoming schedules
        upcoming = self.engine.get_upcoming_schedules(limit=5)
        print(f"\n  📅 Upcoming Schedules: {len(upcoming)}")
        for schedule in upcoming:
            print(f"     • {schedule.start_time.strftime('%H:%M:%S')} - {schedule.content_id[:8]}...")
        
        print()
        await asyncio.sleep(1)
    
    async def step6_monitor_status(self):
        """Step 6: Monitor playback status."""
        print("Step 6: Monitor Playback Status")
        print("-" * 40)
        
        print("  ⏳ Waiting for scheduled playback...")
        
        # Wait for schedules to trigger
        for i in range(15):
            await asyncio.sleep(1)
            
            # Show stats every 3 seconds
            if i % 3 == 0:
                stats = self.engine.get_stats()
                schedule_stats = stats['schedule']
                print(f"  📊 Active schedules: {schedule_stats.get('by_status', {})}")
        
        print("\n  ✅ Monitoring complete")
        print()
    
    async def step7_emergency_controls(self):
        """Step 7: Demonstrate emergency controls."""
        print("Step 7: Emergency Controls")
        print("-" * 40)
        
        print("  ⚠️  Testing emergency stop...")
        
        # Add emergency content
        emergency_id = await self.engine.add_content(
            path='demo_content/emergency.mp4',
            content_type=ContentType.VIDEO,
            metadata=ContentMetadata(title='Emergency Message')
        )
        Path('demo_content/emergency.mp4').touch()
        
        # Schedule emergency playback
        await self.engine.schedule_content(
            content_id=emergency_id,
            start_time=datetime.now(),
            platforms=['hall'],
            priority='emergency'
        )
        
        print("  ✅ Emergency content scheduled")
        
        await asyncio.sleep(1)
        
        # Trigger emergency stop
        print("  🚨 Triggering EMERGENCY STOP...")
        await self.engine.emergency_stop()
        
        print("  ✅ All playbacks stopped")
        print()
        
        await asyncio.sleep(1)
    
    async def step8_error_handling(self):
        """Step 8: Demonstrate error handling."""
        print("Step 8: Error Handling Demonstration")
        print("-" * 40)
        
        # Scenario 1: File not found
        print("  Test 1: File Not Found")
        try:
            await self.engine.add_content(
                path='/nonexistent/file.mp4',
                content_type=ContentType.VIDEO,
                metadata=ContentMetadata(title='Test')
            )
        except FileNotFoundError as e:
            print(f"    ✅ Caught error: {e}")
        
        await asyncio.sleep(0.5)
        
        # Scenario 2: Invalid content type
        print("  Test 2: Invalid Platform")
        try:
            await self.engine.schedule_content(
                content_id='invalid_id',
                start_time=datetime.now(),
                platforms=['nonexistent_platform'],
                priority='normal'
            )
            print("    ⚠️  No immediate error (handled gracefully)")
        except Exception as e:
            print(f"    ✅ Caught error: {e}")
        
        print("\n  ✅ Error handling working correctly")
        print()
        
        await asyncio.sleep(0.5)
    
    async def step9_cleanup(self):
        """Step 9: Cleanup and show results."""
        print("Step 9: Cleanup")
        print("-" * 40)
        
        # Show final stats
        final_stats = self.engine.get_stats()
        print("  📊 Final Statistics:")
        print(f"     Content: {final_stats['content']['total_content']} items")
        print(f"     Schedules: {final_stats['schedule']['total_schedules']} total")
        print(f"     Events logged: {len(self.event_log)}")
        
        # Show event log
        print("\n  📋 Event Log (last 10):")
        for log_entry in self.event_log[-10:]:
            print(f"     {log_entry}")
        
        # Stop engine
        await self.engine.stop()
        print("\n  ✅ Engine stopped")
        
        # Cleanup demo files
        import shutil
        if Path('demo_content').exists():
            shutil.rmtree('demo_content')
        if Path('demo_content_library.json').exists():
            Path('demo_content_library.json').unlink()
        print("  ✅ Demo files cleaned up")
        
        print()


async def main():
    """Run demo."""
    demo = ContentAutomationDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run demo
    asyncio.run(main())

