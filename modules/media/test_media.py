"""
Media Module Demo Script

Standalone test script to demonstrate and test the media playback module.
This script can be run independently to showcase all media features.

Usage:
    python modules/media/test_media.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.media.media_window import MediaWindow


def main():
    """Run the media module demo."""
    print("=" * 60)
    print("AI-Symp-Controller - Media Module Demo")
    print("=" * 60)
    print("\nThis demo showcases:")
    print("  - Drag-and-drop file upload")
    print("  - Video playback (MP4, AVI, MOV, MKV)")
    print("  - PDF presentation viewing")
    print("  - Image display (JPG, PNG)")
    print("  - Animated transitions")
    print("  - Playback controls")
    print("  - Fullscreen mode (F11)")
    print("\nInstructions:")
    print("  1. Drag and drop media files or click 'Browse Files...'")
    print("  2. Select a file from the list to load it")
    print("  3. Use Play/Pause/Stop controls for videos")
    print("  4. Use Previous/Next to navigate between files")
    print("  5. For PDFs, use Page buttons to navigate")
    print("  6. Press F11 for fullscreen mode (projector display)")
    print("\nKeyboard Shortcuts:")
    print("  - Space: Play/Pause")
    print("  - Left/Right Arrow: Previous/Next media")
    print("  - F11: Toggle fullscreen")
    print("  - Ctrl+O: Add files")
    print("  - Ctrl+Q: Exit")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Media Module Demo")
    
    # Create and show media window
    window = MediaWindow()
    window.show()
    
    print("Media window opened successfully!")
    print("You can now interact with the media interface.\n")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    main()

