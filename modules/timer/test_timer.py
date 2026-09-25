"""
Timer Module Demo Script

Standalone test script to demonstrate and test the smart animated timer module.
This script can be run independently to showcase all timer features.

Usage:
    python modules/timer/test_timer.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.timer.timer_window import TimerWindow


def main():
    """Run the timer module demo."""
    print("=" * 60)
    print("AI-Symp-Controller - Timer Module Demo")
    print("=" * 60)
    print("\nThis demo showcases:")
    print("  - Animated circular countdown timer")
    print("  - Gradient color transitions (green → yellow → red)")
    print("  - Time input controls (slider and numeric input)")
    print("  - Start/Pause/Resume/Reset functionality")
    print("  - Multi-timer support with tabs")
    print("  - Visual and audio alerts")
    print("  - Fullscreen mode (F11)")
    print("\nInstructions:")
    print("  1. Set the session time using sliders or input box")
    print("  2. Click 'Start' to begin countdown")
    print("  3. Watch for warning alerts when < 2 minutes remain")
    print("  4. Timer will show 'END OF SPEECH' when finished")
    print("  5. Use '+ Add Timer' to create multiple timers")
    print("  6. Press F11 for fullscreen mode (projector display)")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Timer Module Demo")
    
    # Create and show timer window
    window = TimerWindow()
    window.show()
    
    print("Timer window opened successfully!")
    print("You can now interact with the timer interface.\n")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    main()

