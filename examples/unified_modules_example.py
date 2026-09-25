"""
Unified Modules Example - مثال کامل استفاده همزمان همه ماژول‌ها

این مثال نشان می‌دهد چگونه همه ماژول‌ها را به صورت هماهنگ استفاده کنید.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.operator.unified_controller import UnifiedController
from modules.utils.device_manager import get_device_manager


async def example_full_conference():
    """
    مثال 1: همایش کامل با همه ماژول‌ها
    """
    print("="*70)
    print("Example 1: Full Conference with All Modules")
    print("="*70)
    
    # Step 1: Create Unified Controller
    print("\n[Step 1] Creating Unified Controller...")
    unified = UnifiedController()
    
    # Step 2: Initialize all modules
    print("[Step 2] Initializing all modules...")
    unified.initialize_modules()
    print("[OK] All modules initialized")
    
    # Step 3: Find devices
    print("\n[Step 3] Finding devices...")
    device_manager = get_device_manager()
    
    cameras = device_manager.get_available_cameras(test=True)
    available_cameras = [c for c in cameras if c['available']]
    print(f"  Found {len(available_cameras)} cameras")
    
    laptop_mic = device_manager.get_laptop_microphone()
    print(f"  Laptop microphone: Index {laptop_mic}")
    
    # Step 4: Start full session
    print("\n[Step 4] Starting full session...")
    session_id = "demo_conference_001"
    
    success = await unified.start_full_session(
        session_id=session_id,
        presenter_camera=0 if len(available_cameras) > 0 else 0,
        audience_camera=1 if len(available_cameras) > 1 else 0,
        laptop_microphone=laptop_mic,
        enable_ai_timing=True,
        enable_content_automation=True
    )
    
    if not success:
        print("[ERROR] Failed to start session")
        return
    
    print(f"[OK] Session started: {session_id}")
    
    # Step 5: Monitor status
    print("\n[Step 5] Monitoring module status...")
    print("-" * 70)
    
    for i in range(10):
        status = unified.get_module_status()
        print(f"\n[Update {i+1}]")
        
        for module, state in status.items():
            if isinstance(state, dict) and 'active' in state:
                icon = "[OK]" if state['active'] else "[OFF]"
                print(f"  {icon} {module}: {state.get('active', False)}")
        
        # Get unified stats
        stats = unified.get_unified_stats()
        if stats.get('ai_timing'):
            engagement = stats['ai_timing'].get('engagement', 0)
            print(f"  Engagement: {engagement:.1f}%")
        
        await asyncio.sleep(2)
    
    # Step 6: Stop session
    print("\n[Step 6] Stopping session...")
    await unified.stop_full_session()
    print("[OK] Session stopped")
    
    print("\n" + "="*70)
    print("[SUCCESS] Example completed!")
    print("="*70)


async def example_selective_modules():
    """
    مثال 2: استفاده انتخابی از ماژول‌ها
    """
    print("\n" + "="*70)
    print("Example 2: Selective Module Usage")
    print("="*70)
    
    unified = UnifiedController()
    unified.initialize_modules()
    
    # فقط Timer + Media (بدون AI)
    print("\n[INFO] Starting session with Timer + Media only...")
    
    # Start only what we need
    if unified.timer_controller:
        print("[OK] Timer ready")
    
    if unified.media_controller:
        print("[OK] Media ready")
    
    # Face AI manual start
    if unified.face_ai_controller:
        unified.face_ai_controller.start_analysis(camera_index=0, fps=15)
        print("[OK] Face AI started manually")
    
    print("\n[INFO] Selective modules active")
    print("       - Timer: Ready")
    print("       - Media: Ready")
    print("       - Face AI: Running")
    print("       - AI Timing: Disabled")
    print("       - Content Automation: Disabled")
    
    # Stop
    unified.face_ai_controller.stop_analysis()
    print("\n[OK] Modules stopped")


async def example_with_manual_control():
    """
    مثال 3: کنترل دستی همه ماژول‌ها
    """
    print("\n" + "="*70)
    print("Example 3: Manual Control of All Modules")
    print("="*70)
    
    unified = UnifiedController()
    unified.initialize_modules()
    
    device_manager = get_device_manager()
    laptop_mic = device_manager.get_laptop_microphone()
    
    print("\n[INFO] Manual module activation...")
    
    # 1. Content Automation
    print("\n1. Starting Content Automation...")
    await unified.content_automation.start()
    print("   [OK] Content Automation started")
    
    # 2. Face AI
    print("\n2. Starting Face AI...")
    if unified.face_ai_controller.start_analysis(camera_index=0, fps=15):
        print("   [OK] Face AI started")
    else:
        print("   [FAIL] Face AI failed")
    
    # 3. AI Timing
    print("\n3. Starting AI Timing...")
    if unified.ai_integration_controller.start_ai_timing(
        presenter_camera=0,
        audience_camera=0,
        enable_voice=True
    ):
        print("   [OK] AI Timing started")
        
        # Configure microphone
        if laptop_mic:
            unified.ai_integration_controller._voice_detector.stop_detection()
            unified.ai_integration_controller._voice_detector.start_detection(
                microphone_index=laptop_mic
            )
            print(f"   [OK] Microphone configured: {laptop_mic}")
    else:
        print("   [FAIL] AI Timing failed")
    
    # 4. Display
    print("\n4. Preparing Display...")
    unified.display_controller.refresh_displays()
    screens = unified.display_controller.get_available_screens()
    print(f"   [OK] {len(screens)} displays available")
    
    # Status
    print("\n[STATUS] All modules:")
    status = unified.get_module_status()
    for module, state in status.items():
        if isinstance(state, dict):
            active = state.get('active', False)
            icon = "[OK]" if active else "[OFF]"
            print(f"  {icon} {module}")
    
    # Cleanup
    print("\n[INFO] Stopping all modules...")
    unified.ai_integration_controller.stop_ai_timing()
    unified.face_ai_controller.stop_analysis()
    await unified.content_automation.stop()
    print("[OK] All modules stopped")


def main():
    """Run examples."""
    print("\n" + "="*70)
    print("Unified Modules Examples")
    print("="*70)
    print("\nChoose an example:")
    print("1. Full Conference (All modules)")
    print("2. Selective Modules")
    print("3. Manual Control")
    print("4. Run all examples")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(example_full_conference())
    elif choice == "2":
        asyncio.run(example_selective_modules())
    elif choice == "3":
        asyncio.run(example_with_manual_control())
    elif choice == "4":
        asyncio.run(example_full_conference())
        asyncio.run(example_selective_modules())
        asyncio.run(example_with_manual_control())
    else:
        print("[ERROR] Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

