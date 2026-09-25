"""Test Full Integration with Main App"""

import asyncio
import sys
from pathlib import Path

print("Testing Full Integration...")

async def test_integration():
    """Test content automation integration"""
    try:
        print("\n1. Importing integration...")
        from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
        print("   [OK] Integration imported")
        
        print("\n2. Creating integration (without controllers)...")
        integration = ContentAutomationIntegration(
            media_controller=None,  # Will skip adapter registration
            display_controller=None,
            config={'storage_path': 'test_integration.json'}
        )
        print("   [OK] Integration created")
        
        print("\n3. Starting services...")
        await integration.start()
        print("   [OK] Services started")
        
        print("\n4. Getting stats...")
        stats = integration.get_stats()
        print(f"   [OK] Engine running: {stats['running']}")
        print(f"        Content count: {stats['content']['total_content']}")
        print(f"        Schedules: {stats['schedule']['total_schedules']}")
        
        print("\n5. Testing emergency stop...")
        await integration.emergency_stop()
        print("   [OK] Emergency stop works")
        
        print("\n6. Stopping services...")
        await integration.stop()
        print("   [OK] Services stopped")
        
        print("\n[SUCCESS] Full integration test passed!")
        
        # Cleanup
        if Path('test_integration.json').exists():
            Path('test_integration.json').unlink()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_integration())
    sys.exit(0 if result else 1)

