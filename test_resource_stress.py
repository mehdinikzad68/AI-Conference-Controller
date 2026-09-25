"""
Resource Stress Test Script

Tests application resource usage under heavy load:
- Multiple media files loaded/unloaded
- Face AI started/stopped repeatedly
- Memory leak detection
- Resource monitoring during stress test
"""

import sys
import time
import gc
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.timer import TimerController, TimerWindow
from modules.media import MediaController, MediaWindow
from modules.face_ai import FaceAIController, FaceAIWindow
from modules.display import DisplayController, DisplayManagerWindow
from modules.config import ConfigManager
from modules.utils.resource_monitor import get_memory_usage, get_cpu_usage, check_resource_limits

try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False
    print("Warning: tracemalloc not available. Memory profiling limited.")


def log_resources(iteration: int):
    """Log current resource usage."""
    mem = get_memory_usage()
    cpu = get_cpu_usage()
    print(f"[Iteration {iteration}] RAM: {mem['percent']:.1f}% "
          f"({mem['used_gb']:.2f}GB / {mem['total_gb']:.2f}GB), "
          f"CPU: {cpu:.1f}%")


def stress_test_media(app: QApplication, iterations: int = 10):
    """Stress test media module with repeated load/unload cycles."""
    print("\n" + "="*60)
    print("MEDIA MODULE STRESS TEST")
    print("="*60)
    
    media_window = MediaWindow()
    media_window.show()
    app.processEvents()
    
    # Create test image file paths (use dummy paths for testing)
    test_files = [
        "test_image1.jpg",
        "test_image2.png",
        "test_video.mp4",
        "test_pdf.pdf"
    ]
    
    initial_mem = get_memory_usage()
    log_resources(0)
    
    for i in range(1, iterations + 1):
        print(f"\nIteration {i}/{iterations}")
        
        # Try loading different media types
        for test_file in test_files:
            if Path(test_file).exists():
                try:
                    media_window.load_media_file(test_file)
                    app.processEvents()
                    time.sleep(0.5)  # Give time for loading
                except Exception as e:
                    print(f"  Error loading {test_file}: {e}")
        
        # Clear media
        media_window.clear_media()
        app.processEvents()
        
        # Force garbage collection
        gc.collect()
        
        log_resources(i)
        
        # Check for memory leaks
        current_mem = get_memory_usage()
        mem_increase = current_mem['used_gb'] - initial_mem['used_gb']
        if mem_increase > 0.5:  # More than 500MB increase
            print(f"  WARNING: Memory increased by {mem_increase:.2f}GB")
    
    media_window.close()
    final_mem = get_memory_usage()
    mem_leak = final_mem['used_gb'] - initial_mem['used_gb']
    print(f"\nMemory leak: {mem_leak:.2f}GB")
    
    return mem_leak


def stress_test_face_ai(app: QApplication, cycles: int = 5):
    """Stress test Face AI with start/stop cycles."""
    print("\n" + "="*60)
    print("FACE AI MODULE STRESS TEST")
    print("="*60)
    
    controller = FaceAIController()
    window = FaceAIWindow(controller=controller)
    window.show()
    app.processEvents()
    
    initial_mem = get_memory_usage()
    log_resources(0)
    
    for i in range(1, cycles + 1):
        print(f"\nCycle {i}/{cycles}")
        
        # Start analysis
        print("  Starting Face AI analysis...")
        if controller.start_analysis(camera_index=0, fps=10):
            app.processEvents()
            time.sleep(2)  # Run for 2 seconds
            log_resources(i * 2 - 1)
        
        # Stop analysis
        print("  Stopping Face AI analysis...")
        controller.stop_analysis()
        app.processEvents()
        time.sleep(1)
        gc.collect()
        log_resources(i * 2)
        
        # Check resource limits
        status = check_resource_limits()
        if status['ram_high'] or status['cpu_high']:
            print(f"  WARNING: Resources high - RAM: {status['ram_percent']:.1f}%, "
                  f"CPU: {status['cpu_percent']:.1f}%")
    
    window.close()
    controller.stop_analysis()
    final_mem = get_memory_usage()
    mem_leak = final_mem['used_gb'] - initial_mem['used_gb']
    print(f"\nMemory leak: {mem_leak:.2f}GB")
    
    return mem_leak


def stress_test_timer(app: QApplication, iterations: int = 20):
    """Stress test timer module with multiple timer creation/destruction."""
    print("\n" + "="*60)
    print("TIMER MODULE STRESS TEST")
    print("="*60)
    
    timer_window = TimerWindow()
    timer_window.show()
    app.processEvents()
    
    initial_mem = get_memory_usage()
    log_resources(0)
    
    for i in range(1, iterations + 1):
        print(f"\nIteration {i}/{iterations}")
        
        # Add timer
        timer_window.add_new_timer(f"Test Timer {i}")
        app.processEvents()
        time.sleep(0.2)
        
        # Close timer (remove last tab)
        if timer_window.get_tab_count() > 1:
            timer_window.close_timer_tab(timer_window.get_tab_count() - 1)
        app.processEvents()
        
        gc.collect()
        log_resources(i)
    
    timer_window.close()
    final_mem = get_memory_usage()
    mem_leak = final_mem['used_gb'] - initial_mem['used_gb']
    print(f"\nMemory leak: {mem_leak:.2f}GB")
    
    return mem_leak


def main():
    """Run comprehensive stress test suite."""
    print("="*60)
    print("AI-Symp-Controller - Resource Stress Test")
    print("="*60)
    print("\nThis script tests resource usage and memory leaks under heavy load.")
    print("Tests include:")
    print("  - Media module load/unload cycles")
    print("  - Face AI start/stop cycles")
    print("  - Timer creation/destruction")
    print("  - Memory leak detection")
    print("\nPress Ctrl+C to stop early")
    print("="*60)
    
    # Start memory tracing if available
    if TRACEMALLOC_AVAILABLE:
        tracemalloc.start()
        print("\nMemory tracing enabled (tracemalloc)")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Resource Stress Test")
    
    try:
        results = {}
        
        # Test 1: Media module
        try:
            results['media'] = stress_test_media(app, iterations=10)
        except Exception as e:
            print(f"\nMedia stress test failed: {e}")
            results['media'] = None
        
        # Test 2: Face AI (may fail if camera not available)
        try:
            results['face_ai'] = stress_test_face_ai(app, cycles=5)
        except Exception as e:
            print(f"\nFace AI stress test failed: {e}")
            results['face_ai'] = None
        
        # Test 3: Timer module
        try:
            results['timer'] = stress_test_timer(app, iterations=20)
        except Exception as e:
            print(f"\nTimer stress test failed: {e}")
            results['timer'] = None
        
        # Final summary
        print("\n" + "="*60)
        print("STRESS TEST SUMMARY")
        print("="*60)
        for test_name, leak in results.items():
            if leak is not None:
                status = "PASS" if abs(leak) < 0.1 else "WARN" if abs(leak) < 0.5 else "FAIL"
                print(f"{test_name:15} Memory leak: {leak:+.2f}GB [{status}]")
            else:
                print(f"{test_name:15} Skipped/Failed")
        
        # Memory snapshot if available
        if TRACEMALLOC_AVAILABLE:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            print("\nTop 10 memory allocations:")
            for stat in top_stats[:10]:
                print(stat)
        
        print("\n" + "="*60)
        print("Stress test complete!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean exit
    app.quit()


if __name__ == "__main__":
    main()

