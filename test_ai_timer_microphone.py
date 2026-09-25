"""
Test AI Timer Microphone Connection
تست اتصال میکروفون لپ‌تاپ به AI Timer
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.utils.device_manager import get_device_manager
from modules.ai_timing import VoiceActivityDetector, AIIntegrationController

def find_laptop_microphone():
    """پیدا کردن میکروفون لپ‌تاپ"""
    device_manager = get_device_manager()
    microphones = device_manager.get_available_microphones()
    
    print("\n" + "="*70)
    print("Searching for Laptop Microphone...")
    print("="*70)
    
    # کلمات کلیدی برای شناسایی میکروفون لپ‌تاپ
    keywords = ['microphone', 'array', 'built-in', 'internal', 'laptop', 'amd', 'realtek']
    
    laptop_mics = []
    for mic in microphones:
        name_lower = mic['name'].lower()
        if any(keyword in name_lower for keyword in keywords):
            laptop_mics.append(mic)
            print(f"[FOUND] Microphone {mic['index']}: {mic['name']}")
    
    if laptop_mics:
        # تست میکروفون‌ها
        print("\nTesting microphones...")
        for mic in laptop_mics:
            success, error = device_manager.test_microphone(mic['index'])
            if success:
                print(f"  [OK] Microphone {mic['index']} works!")
                return mic['index']
            else:
                print(f"  [FAIL] Microphone {mic['index']}: {error}")
    
    # Fallback: استفاده از میکروفون پیش‌فرض
    if microphones:
        default_mic = microphones[0]
        print(f"\n[INFO] Using default microphone: {default_mic['index']}")
        return default_mic['index']
    
    return None

def test_voice_detection(mic_index):
    """تست Voice Detection"""
    print("\n" + "="*70)
    print("Testing Voice Detection...")
    print("="*70)
    
    try:
        voice_detector = VoiceActivityDetector()
        
        print(f"Starting Voice Detection with microphone index: {mic_index}")
        if voice_detector.start_detection(microphone_index=mic_index):
            print("[OK] Voice Detection started successfully!")
            print("\n[INFO] Voice Detection is now listening...")
            print("       Speak into your laptop microphone to test.")
            print("       Press Ctrl+C to stop.")
            
            # Wait for user input
            try:
                import time
                while True:
                    if voice_detector.is_speaking():
                        print("[SPEAKING] Voice detected!")
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[STOPPING] Voice Detection...")
            
            voice_detector.stop_detection()
            print("[OK] Voice Detection stopped")
            return True
        else:
            print("[FAIL] Failed to start Voice Detection")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_timer_integration(mic_index):
    """تست یکپارچگی با AI Timer"""
    print("\n" + "="*70)
    print("Testing AI Timer Integration...")
    print("="*70)
    
    try:
        ai_controller = AIIntegrationController()
        
        print("Starting AI Timer with Voice Detection...")
        # Note: start_ai_timing uses default mic, we'll set it manually after
        success = ai_controller.start_ai_timing(
            presenter_camera=0,
            audience_camera=0,
            enable_voice=True
        )
        
        if success:
            print("[OK] AI Timer started")
            
            # Stop and restart with specific microphone
            print(f"Configuring microphone {mic_index}...")
            ai_controller._voice_detector.stop_detection()
            if ai_controller._voice_detector.start_detection(microphone_index=mic_index):
                print("[OK] Microphone configured successfully!")
                print("\n[INFO] AI Timer is now running with laptop microphone")
                print("       Press Ctrl+C to stop.")
                
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n[STOPPING] AI Timer...")
                
                ai_controller.stop_ai_timing()
                print("[OK] AI Timer stopped")
                return True
            else:
                print("[FAIL] Failed to configure microphone")
                ai_controller.stop_ai_timing()
                return False
        else:
            print("[FAIL] Failed to start AI Timer")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("\n" + "="*70)
    print("AI Timer Microphone Test - تست میکروفون AI Timer")
    print("="*70)
    
    # Step 1: Find laptop microphone
    mic_index = find_laptop_microphone()
    
    if mic_index is None:
        print("\n[ERROR] No microphone found!")
        print("        Please check:")
        print("        1. Microphone is connected")
        print("        2. Microphone permissions in Windows")
        print("        3. SpeechRecognition library is installed")
        return False
    
    print(f"\n[SUCCESS] Laptop microphone found: Index {mic_index}")
    
    # Step 2: Test Voice Detection
    print("\n" + "-"*70)
    choice = input("Test Voice Detection? (y/n): ").strip().lower()
    if choice == 'y':
        test_voice_detection(mic_index)
    
    # Step 3: Test AI Timer Integration
    print("\n" + "-"*70)
    choice = input("Test AI Timer Integration? (y/n): ").strip().lower()
    if choice == 'y':
        test_ai_timer_integration(mic_index)
    
    print("\n" + "="*70)
    print("[SUMMARY] Summary:")
    print("="*70)
    print(f"Laptop Microphone Index: {mic_index}")
    print("\nTo use in your code:")
    print(f"  voice_detector.start_detection(microphone_index={mic_index})")
    print("="*70 + "\n")
    
    return True

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

