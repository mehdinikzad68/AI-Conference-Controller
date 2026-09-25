"""
Test script for AI Timer feature integration.

Demonstrates AI-driven adaptive timing with presenter and audience tracking.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from modules.timer.timer_window import TimerWindow


def main():
    """Run AI Timer test demo."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Create timer window
    window = TimerWindow()
    window.setWindowTitle("AI Timer Test - AI-Symp-Controller")
    window.show()
    
    print("\n" + "="*60)
    print("AI Timer Test Demo")
    print("="*60)
    print("\nInstructions:")
    print("1. Set timer duration using the sliders or input box")
    print("2. Scroll down to 'AI Timer / Smart Timing (Beta)' section")
    print("3. Check 'Enable AI Timer' checkbox")
    print("4. Start the timer using the 'Start' button")
    print("5. Watch AI metrics update in real-time:")
    print("   - AI Status: Should show 'Active' when running")
    print("   - Presenter State: Will show presenter activity")
    print("   - Audience Focus: Progress bar showing engagement")
    print("   - Event Log: Shows AI-driven adjustments")
    print("\n6. Test manual controls:")
    print("   - Pause/Resume AI Timer buttons")
    print("   - Override AI button")
    print("\n7. Observe AI-driven behavior:")
    print("   - Timer may pause if presenter is away")
    print("   - Timer may slow if audience engagement is low")
    print("   - Extension requests may appear for high engagement")
    print("\n" + "="*60)
    print("Press Ctrl+C or close window to exit")
    print("="*60 + "\n")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    main()

