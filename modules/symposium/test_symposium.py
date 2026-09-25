"""
Symposium Display Test Script

Standalone test script to demonstrate symposium display features.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.symposium import SymposiumWindow, AgendaManager, AgendaItem, SpeakerInfo


def create_sample_agenda():
    """Create a sample agenda for testing."""
    agenda_manager = AgendaManager()
    
    # Set symposium info
    agenda_manager.set_symposium_info(
        title="AI & Machine Learning Symposium 2025",
        date="March 15, 2025",
        location="Main Conference Hall",
        logo_path=None  # Can be set if logo file exists
    )
    
    # Add sample sessions
    speaker1 = SpeakerInfo(
        name="Dr. Sarah Johnson",
        title="Deep Learning in Computer Vision",
        organization="MIT AI Lab",
        duration_minutes=30,
        media_path=None
    )
    
    item1 = AgendaItem(
        session_id="session_01",
        start_time="09:00",
        speaker=speaker1,
        session_type="talk"
    )
    agenda_manager.add_agenda_item(item1)
    
    speaker2 = SpeakerInfo(
        name="Prof. Michael Chen",
        title="Natural Language Processing: Recent Advances",
        organization="Stanford University",
        duration_minutes=45,
        media_path=None
    )
    
    item2 = AgendaItem(
        session_id="session_02",
        start_time="09:45",
        speaker=speaker2,
        session_type="talk"
    )
    agenda_manager.add_agenda_item(item2)
    
    return agenda_manager


def main():
    """Run the symposium display test."""
    print("=" * 60)
    print("AI-Symp-Controller - Symposium Display Test")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("  - Full symposium agenda display")
    print("  - Speaker introduction slides")
    print("  - Smart timer overlay with progress bar")
    print("  - 20% warning threshold with visual effects")
    print("  - Scene switching (F1-F5 keys)")
    print("  - Session management and timing")
    print("  - Media integration (if media files provided)")
    print("  - OBS Studio compatibility")
    print("\nKeyboard Shortcuts:")
    print("  F1 - Show Agenda")
    print("  F2 - Show Speaker Intro")
    print("  F3 - Show Session (with media)")
    print("  F4 - Show Logo/Branding")
    print("  F5 - Show Break Screen")
    print("  Space - Pause/Resume session")
    print("  Ctrl+N - Next session")
    print("  Ctrl+P - Previous session")
    print("\nFeatures:")
    print("  - Timer overlay shows horizontal progress bar")
    print("  - Color transitions: Green → Yellow → Red")
    print("  - Warning at 20% remaining time")
    print("  - Pulsing border and blinking effects")
    print("  - Warning message display")
    print("  - Adjustable position and opacity")
    print("\nOBS Studio:")
    print("  - Window title includes '[OBS]' for easy identification")
    print("  - Fullscreen support for projector display")
    print("  - Smooth transitions between scenes")
    print("\n" + "=" * 60)
    
    app = QApplication(sys.argv)
    
    # Create symposium window
    window = SymposiumWindow()
    
    # Load sample agenda
    agenda_manager = create_sample_agenda()
    window.get_agenda_manager()._agenda_items = agenda_manager.get_agenda_items()
    window.get_agenda_manager().set_symposium_info(
        agenda_manager.get_symposium_title(),
        agenda_manager.get_symposium_date(),
        agenda_manager.get_symposium_location(),
        agenda_manager.get_logo_path()
    )
    window.on_agenda_loaded()
    
    # Show window
    window.show()
    
    print("\nSymposium window displayed. Use keyboard shortcuts to navigate.")
    print("Close the window to exit.\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

