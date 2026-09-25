"""Test main.py imports and initialization"""

import sys
print("Testing main.py imports...")

try:
    # Test imports
    print("1. Testing PyQt6 imports...")
    from PyQt6.QtWidgets import QApplication, QMainWindow
    print("   [OK] PyQt6 OK")
    
    print("2. Testing module imports...")
    from modules.timer import TimerController, TimerWindow
    from modules.media import MediaController, MediaWindow
    from modules.face_ai import FaceAIController, FaceAIWindow
    from modules.display import DisplayController, DisplayManagerWindow
    from modules.config import ConfigManager, ConfigWindow
    from modules.symposium import SymposiumWindow
    print("   [OK] Core modules OK")
    
    print("3. Testing content automation import...")
    from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
    print("   [OK] Content Automation OK")
    
    print("4. Testing async imports...")
    import asyncio
    import qasync
    print("   [OK] Async support OK")
    
    print("\n[SUCCESS] All imports successful!")
    print("\nNote: Cannot test full GUI without display.")
    print("To run full app: python main.py")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

