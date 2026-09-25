"""Test Content Automation Module"""

import asyncio
import sys
from pathlib import Path

print("Testing Content Automation Module...")

async def test_content_automation():
    """Test content automation functionality"""
    try:
        print("\n1. Importing module...")
        from modules.content_automation import ContentAutomationEngine
        from modules.content_automation.models import ContentType, ContentMetadata
        print("   [OK] Imports successful")
        
        print("\n2. Creating engine...")
        engine = ContentAutomationEngine(config={
            'storage_path': 'test_content_library.json'
        })
        print("   [OK] Engine created")
        
        print("\n3. Starting engine...")
        await engine.start()
        print("   [OK] Engine started")
        
        print("\n4. Getting stats...")
        stats = engine.get_stats()
        print(f"   [OK] Stats: {stats}")
        
        print("\n5. Stopping engine...")
        await engine.stop()
        print("   [OK] Engine stopped")
        
        print("\n[SUCCESS] All tests passed!")
        
        # Cleanup
        if Path('test_content_library.json').exists():
            Path('test_content_library.json').unlink()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_content_automation())
    sys.exit(0 if result else 1)

