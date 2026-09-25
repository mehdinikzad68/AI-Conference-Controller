"""
Display Module Demo Script

Standalone test script to demonstrate and test the display management module.
This script showcases multi-display detection, content routing, and OBS integration.

Usage:
    python modules/display/test_display.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.display.display_manager_window import DisplayManagerWindow


def main():
    """Run the display module demo."""
    print("=" * 60)
    print("AI-Symp-Controller - Display Module Demo")
    print("=" * 60)
    print("\nThis demo showcases:")
    print("  - Automatic display detection")
    print("  - Multi-display management")
    print("  - Content routing (timer, media, face AI)")
    print("  - Preview and test modes")
    print("  - Fullscreen support")
    print("  - OBS Studio compatibility")
    print("\nInstructions:")
    print("  1. All connected displays will be automatically detected")
    print("  2. Select a display from the list")
    print("  3. Choose content type (Timer, Media, Face AI)")
    print("  4. Click 'Route Content to Display' to send content")
    print("  5. Use 'Preview' to test each display")
    print("  6. Use 'Fullscreen Selected' for projector mode")
    print("  7. Use 'Test All Displays' to verify connections")
    print("\nKeyboard Shortcuts:")
    print("  - Ctrl+R: Refresh displays")
    print("  - Ctrl+Q: Exit")
    print("\nOBS Studio Integration:")
    print("  - Each display output appears as separate window")
    print("  - Use Window Capture in OBS to capture individual displays")
    print("  - Window names: 'Display Output - Display 1', etc.")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Display Module Demo")
    
    # Create and show display manager window
    window = DisplayManagerWindow()
    window.show()
    
    print("Display manager window opened successfully!")
    print(f"Detected {len(window._screens)} display(s)\n")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    main()

