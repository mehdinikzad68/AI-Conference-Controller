"""
Example: AI Timer with Laptop Microphone
مثال: استفاده از AI Timer با میکروفون لپ‌تاپ
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.ai_timing import AIIntegrationController, VoiceActivityDetector
from modules.utils.device_manager import get_device_manager

def setup_ai_timer_with_laptop_mic():
    """
    راه‌اندازی AI Timer با میکروفون لپ‌تاپ
    
    این تابع:
    1. میکروفون لپ‌تاپ را به صورت خودکار پیدا می‌کند
    2. AI Timer را راه‌اندازی می‌کند
    3. Voice Detection را با میکروفون لپ‌تاپ فعال می‌کند
    """
    
    print("="*70)
    print("Setting up AI Timer with Laptop Microphone")
    print("="*70)
    
    # Step 1: Find laptop microphone
    print("\n[Step 1] Finding laptop microphone...")
    device_manager = get_device_manager()
    laptop_mic_index = device_manager.get_laptop_microphone()
    
    if laptop_mic_index is None:
        print("[ERROR] No laptop microphone found!")
        print("        Please check microphone connection and permissions")
        return None
    
    # Get microphone name
    microphones = device_manager.get_available_microphones()
    mic_name = next((m['name'] for m in microphones if m['index'] == laptop_mic_index), "Unknown")
    
    print(f"[OK] Laptop microphone found:")
    print(f"     Index: {laptop_mic_index}")
    print(f"     Name: {mic_name}")
    
    # Step 2: Create AI Timer Controller
    print("\n[Step 2] Creating AI Timer Controller...")
    ai_controller = AIIntegrationController()
    print("[OK] AI Timer Controller created")
    
    # Step 3: Start AI Timer (without voice first)
    print("\n[Step 3] Starting AI Timer...")
    success = ai_controller.start_ai_timing(
        presenter_camera=0,      # دوربین سخنران
        audience_camera=0,       # دوربین حضار (می‌توانید تغییر دهید)
        enable_voice=False       # ابتدا بدون voice شروع می‌کنیم
    )
    
    if not success:
        print("[ERROR] Failed to start AI Timer")
        return None
    
    print("[OK] AI Timer started")
    
    # Step 4: Configure laptop microphone
    print(f"\n[Step 4] Configuring laptop microphone (Index {laptop_mic_index})...")
    
    # Stop current voice detection if any
    if ai_controller._voice_detector._is_detecting:
        ai_controller._voice_detector.stop_detection()
    
    # Start with laptop microphone
    if ai_controller._voice_detector.start_detection(microphone_index=laptop_mic_index):
        print("[OK] Laptop microphone configured and active!")
        print("\n[INFO] AI Timer is now running with:")
        print(f"       - Presenter Camera: 0")
        print(f"       - Audience Camera: 0")
        print(f"       - Laptop Microphone: {laptop_mic_index} ({mic_name})")
        print("\n[INFO] Voice Detection is active and listening for speaker voice")
        
        return ai_controller
    else:
        print("[WARNING] Failed to start voice detection with laptop microphone")
        print("          AI Timer is running but without voice detection")
        return ai_controller

def example_usage():
    """مثال استفاده"""
    
    # راه‌اندازی
    ai_controller = setup_ai_timer_with_laptop_mic()
    
    if ai_controller is None:
        print("\n[ERROR] Failed to setup AI Timer")
        return
    
    # استفاده
    print("\n" + "="*70)
    print("AI Timer is running!")
    print("="*70)
    print("\nThe system will:")
    print("  - Monitor presenter through camera")
    print("  - Listen to speaker through laptop microphone")
    print("  - Analyze audience engagement")
    print("  - Adapt timer based on AI analysis")
    print("\nPress Ctrl+C to stop...")
    
    try:
        import time
        while True:
            # Check if speaking
            if ai_controller._voice_detector.is_speaking():
                print("[SPEAKING] Presenter is speaking...")
            
            # Check engagement
            engagement = ai_controller.get_current_engagement()
            if engagement:
                print(f"[ENGAGEMENT] Current: {engagement:.1f}%")
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n[STOPPING] Stopping AI Timer...")
    
    # Cleanup
    ai_controller.stop_ai_timing()
    print("[OK] AI Timer stopped")

# Alternative: استفاده مستقیم از VoiceActivityDetector
def simple_voice_detection_example():
    """مثال ساده: فقط Voice Detection"""
    
    print("="*70)
    print("Simple Voice Detection Example")
    print("="*70)
    
    # پیدا کردن میکروفون لپ‌تاپ
    device_manager = get_device_manager()
    laptop_mic = device_manager.get_laptop_microphone()
    
    if laptop_mic is None:
        print("[ERROR] No laptop microphone found")
        return
    
    print(f"[OK] Using microphone index: {laptop_mic}")
    
    # ایجاد Voice Detector
    voice_detector = VoiceActivityDetector()
    
    # شروع
    if voice_detector.start_detection(microphone_index=laptop_mic):
        print("[OK] Voice Detection started")
        print("\n[INFO] Listening for speaker voice...")
        print("       Press Ctrl+C to stop")
        
        try:
            import time
            while True:
                if voice_detector.is_speaking():
                    print("[SPEAKING] Voice detected!")
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        voice_detector.stop_detection()
        print("\n[OK] Voice Detection stopped")
    else:
        print("[ERROR] Failed to start Voice Detection")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Timer with Laptop Microphone")
    parser.add_argument("--simple", action="store_true", 
                       help="Run simple voice detection only")
    
    args = parser.parse_args()
    
    if args.simple:
        simple_voice_detection_example()
    else:
        example_usage()

