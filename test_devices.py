"""
Device Testing Script - تست دستگاه‌های میکروفون و دوربین

این اسکریپت لیست تمام دوربین‌ها و میکروفون‌های موجود را نمایش می‌دهد
و آن‌ها را تست می‌کند.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.utils.device_manager import get_device_manager

def main():
    """تست دستگاه‌ها"""
    print("\n" + "="*70)
    print("Device Testing - Test Devices")
    print("="*70 + "\n")
    
    device_manager = get_device_manager()
    
    # لیست دوربین‌ها
    print("[CAMERAS] Checking Cameras...")
    print("-" * 70)
    cameras = device_manager.get_available_cameras(test=True)
    
    available_cameras = []
    for cam in cameras:
        if cam['available']:
            available_cameras.append(cam)
            print(f"[OK] Camera {cam['index']}: {cam['name']}")
            if cam['resolution']:
                print(f"   Resolution: {cam['resolution']}, FPS: {cam['fps']:.1f}")
            
            # تست دقیق‌تر
            success, error = device_manager.test_camera(cam['index'])
            if success:
                print(f"   Status: [OK] Working")
            else:
                print(f"   Status: [WARNING] {error}")
        else:
            print(f"[FAIL] Camera {cam['index']}: Not available")
    
    print(f"\n[INFO] Total: {len(available_cameras)} available camera(s)")
    
    # لیست میکروفون‌ها
    print("\n[MICROPHONES] Checking Microphones...")
    print("-" * 70)
    microphones = device_manager.get_available_microphones()
    
    available_microphones = []
    for mic in microphones:
        available_microphones.append(mic)
        print(f"[OK] Microphone {mic['index']}: {mic['name']}")
        
        # تست میکروفون
        success, error = device_manager.test_microphone(mic['index'])
        if success:
            print(f"   Status: [OK] Working")
        else:
            print(f"   Status: [WARNING] {error}")
    
    print(f"\n[INFO] Total: {len(available_microphones)} available microphone(s)")
    
    # خلاصه
    print("\n" + "="*70)
    print("[SUMMARY] Summary:")
    print("="*70)
    
    if available_cameras:
        default_cam = device_manager.get_default_camera()
        print(f"[OK] Default Camera: Index {default_cam}")
        print(f"   Recommended for Face AI: Camera {default_cam}")
    else:
        print("[FAIL] No cameras available")
        print("   [TIP] Check camera connection and permissions")
    
    if available_microphones:
        default_mic = device_manager.get_default_microphone()
        print(f"[OK] Default Microphone: Index {default_mic}")
        print(f"   Recommended for Voice Detection: Microphone {default_mic}")
    else:
        print("[FAIL] No microphones available")
        print("   [TIP] Install: pip install SpeechRecognition pyaudio")
    
    print("\n" + "="*70)
    print("[TIPS] Usage Tips:")
    print("="*70)
    print("1. For Face AI: Use camera index from above")
    print("2. For Voice Detection: Use microphone index from above")
    print("3. If devices don't work, check permissions in Windows Settings")
    print("4. Make sure no other app is using the camera/microphone")
    print("="*70 + "\n")


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

