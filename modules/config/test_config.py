"""
Configuration Module Demo Script

Standalone test script to demonstrate and test the configuration module.
This script showcases all configuration features, profile management, and settings.

Usage:
    python modules/config/test_config.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from modules.config.config_window import ConfigWindow


def main():
    """Run the configuration module demo."""
    print("=" * 60)
    print("AI-Symp-Controller - Configuration Module Demo")
    print("=" * 60)
    print("\nThis demo showcases:")
    print("  - Timer settings and appearance configuration")
    print("  - Media playback settings")
    print("  - Face AI analysis settings")
    print("  - Display/output configuration")
    print("  - Sound and alert settings")
    print("  - General preferences and accessibility")
    print("  - Asset management (logos, colors)")
    print("  - Configuration profile management")
    print("\nInstructions:")
    print("  1. Navigate through tabs to configure different modules")
    print("  2. Change settings and use 'Preview Changes' to see effects")
    print("  3. Use 'Save Configuration' to persist changes")
    print("  4. Create new profiles for different event types")
    print("  5. Export/import profiles for backup or sharing")
    print("  6. Test sound alerts using 'Test' buttons")
    print("  7. Upload logo and customize branding colors")
    print("\nProfile Management:")
    print("  - Create: Click 'New' to create a new profile")
    print("  - Load: Select profile from dropdown")
    print("  - Export: Click 'Export' to save profile to file")
    print("  - Import: Click 'Import' to load profile from file")
    print("  - Delete: Click 'Delete' to remove a profile")
    print("\nKeyboard Shortcuts:")
    print("  - Ctrl+S: Save configuration")
    print("  - Ctrl+Q: Exit")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Configuration Module Demo")
    
    # Create and show configuration window
    window = ConfigWindow()
    window.show()
    
    print("Configuration window opened successfully!")
    print("You can now configure all application settings.\n")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")


if __name__ == "__main__":
    main()

