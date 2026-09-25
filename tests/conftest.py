"""
Pytest Configuration and Fixtures

Shared fixtures and configuration for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """
    Create QApplication instance for tests requiring Qt.
    
    This is a session-scoped fixture to avoid creating multiple QApplication instances.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Cleanup is automatic


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "timer": {
            "default_duration": 300,
            "mode": "countdown",
            "show_warning": True,
            "warning_threshold": 120,
        },
        "media": {
            "auto_play": False,
            "auto_advance": False,
        },
        "face_ai": {
            "enabled": False,
            "camera_index": 0,
        }
    }


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create temporary config file for testing."""
    import json
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f)
    return config_file

