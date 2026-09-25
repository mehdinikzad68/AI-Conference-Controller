"""
Media Timer Overlay Test Script

Standalone test script to demonstrate timer overlay integration with media content.
This script showcases the timer overlay on top of videos, PDFs, and images.

Usage:
    python modules/media/test_media_overlay.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.media.media_window import MediaWindow
from modules.timer.timer_controller import TimerController


def main():
    """Run the media timer overlay test."""
    print("=" * 60)
    print("AI-Symp-Controller - Media Timer Overlay Test")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("  - Timer overlay on top of media content")
    print("  - Works with videos, PDFs, and images")
    print("  - Fade in/out animations")
    print("  - Position controls (corners, center)")
    print("  - Draggable overlay")
    print("  - Fullscreen support")
    print("  - OBS Studio compatible")
    print("\nInstructions:")
    print("  1. Load media files (drag and drop or browse)")
    print("  2. Check 'Show Timer Overlay' checkbox")
    print("  3. Set timer duration (minutes)")
    print("  4. Choose overlay position from dropdown")
    print("  5. Click 'Start Timer' to begin countdown")
    print("  6. Timer will show warnings at < 2 minutes")
    print("  7. Use Pause/Reset as needed")
    print("  8. Overlay auto-hides when timer finishes (after 3 seconds)")
    print("  9. Press F11 for fullscreen mode")
    print("\nFeatures:")
    print("  - Drag overlay to custom position")
    print("  - All timer animations work (gradient colors, warnings)")
    print("  - Smooth fade transitions")
    print("  - Position presets for quick placement")
    print("\nOBS Studio:")
    print("  - Timer overlay appears on top of media in Window Capture")
    print("  - No flicker, smooth updates")
    print("  - Works in both windowed and fullscreen modes")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Media Timer Overlay Test")
    
    # Create timer controller for overlay
    timer_controller = TimerController()
    
    # Create media window with timer controller
    window = MediaWindow(timer_controller=timer_controller)
    window.show()
    
    print("Media window with timer overlay opened!")
    print("Enable 'Show Timer Overlay' to see timer on media.\n")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")


if __name__ == "__main__":
    main()

