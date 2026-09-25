"""
Comprehensive Tests for Enhanced AgendaManager

Tests validation, sanitization, and new features.
"""

import pytest
import json
import tempfile
from pathlib import Path

from modules.symposium.agenda_manager import (
    AgendaManager, AgendaItem, SpeakerInfo
)
from modules.symposium.time_validator import TimeValidationError
from modules.utils.input_sanitizer import InputSanitizationError


class TestEnhancedAgendaManager:
    """Test enhanced AgendaManager with validation."""
    
    def test_add_valid_session(self):
        """Test adding valid session."""
        manager = AgendaManager()
        
        session = AgendaItem(
            session_id="session_01",
            start_time="09:00",
            speaker=SpeakerInfo(name="John Doe", title="Test Talk", duration_minutes=30)
        )
        
        success, error = manager.add_agenda_item(session, validate=True)
        assert success
        assert error is None
        assert len(manager.get_agenda_items()) == 1
    
    def test_add_invalid_time(self):
        """Test that invalid time is rejected."""
        manager = AgendaManager()
        
        session = AgendaItem(
            session_id="invalid",
            start_time="25:99",  # Invalid
            speaker=SpeakerInfo(name="Test", title="Test", duration_minutes=30)
        )
        
        success, error = manager.add_agenda_item(session, validate=True)
        assert not success
        assert error is not None
    
    def test_time_normalization(self):
        """Test that times are normalized."""
        manager = AgendaManager()
        
        session = AgendaItem(
            session_id="s1",
            start_time="9:5",  # Should be normalized to "09:05"
            speaker=SpeakerInfo(name="Test", title="Test", duration_minutes=30)
        )
        
        success, error = manager.add_agenda_item(session, validate=True)
        assert success
        assert session.start_time == "09:05"
    
    def test_overlap_detection(self):
        """Test that overlapping sessions are detected."""
        manager = AgendaManager()
        
        # Add first session
        session1 = AgendaItem(
            session_id="s1",
            start_time="09:00",
            speaker=SpeakerInfo(name="Speaker 1", title="Talk 1", duration_minutes=60)
        )
        success, error = manager.add_agenda_item(session1, validate=True)
        assert success
        
        # Try to add overlapping session
        session2 = AgendaItem(
            session_id="s2",
            start_time="09:30",  # Overlaps with s1!
            speaker=SpeakerInfo(name="Speaker 2", title="Talk 2", duration_minutes=60)
        )
        success, error = manager.add_agenda_item(session2, validate=True)
        assert not success
        assert "Conflict" in error
    
    def test_proper_time_sorting(self):
        """Test that sessions are sorted correctly (not as strings)."""
        manager = AgendaManager()
        
        # Add in wrong order
        sessions = [
            ("s3", "10:00"),
            ("s1", "9:00"),  # Should come first
            ("s2", "9:30"),
        ]
        
        for sid, time in sessions:
            session = AgendaItem(
                session_id=sid,
                start_time=time,
                speaker=SpeakerInfo(name=f"Speaker {sid}", title=f"Talk {sid}", duration_minutes=20)
            )
            manager.add_agenda_item(session, validate=False)  # Skip validation for this test
        
        items = manager.get_agenda_items()
        
        # Should be sorted: 09:00, 09:30, 10:00
        assert items[0].start_time == "09:00"
        assert items[1].start_time == "09:30"
        assert items[2].start_time == "10:00"
    
    def test_speaker_sanitization(self):
        """Test that speaker data is sanitized."""
        # Create speaker with null bytes
        speaker_data = {
            'name': 'John\x00Doe',
            'title': 'Test\x00Talk',
            'email': 'JOHN@EXAMPLE.COM',
            'bio': 'A' * 10000  # Very long
        }
        
        speaker = SpeakerInfo.from_dict(speaker_data, sanitize=True)
        
        # Null bytes should be removed
        assert '\x00' not in speaker.name
        assert '\x00' not in speaker.title
        
        # Email should be lowercased
        assert speaker.email == 'john@example.com'
        
        # Bio should be truncated
        assert len(speaker.bio) <= 5000
    
    def test_unicode_names(self):
        """Test that Unicode names are handled correctly."""
        manager = AgendaManager()
        
        unicode_names = [
            "محمد رضا احمدی",  # Farsi
            "张伟",  # Chinese
            "José García",  # Spanish
        ]
        
        for i, name in enumerate(unicode_names):
            session = AgendaItem(
                session_id=f"s{i}",
                start_time=f"09:{i*10:02d}",
                speaker=SpeakerInfo(name=name, title=f"Talk {i}", duration_minutes=10)
            )
            success, error = manager.add_agenda_item(session, validate=True)
            assert success, f"Failed for name: {name}"


class TestAgendaLoadSave:
    """Test loading and saving with validation."""
    
    def test_save_and_load(self):
        """Test complete save/load cycle."""
        manager = AgendaManager()
        manager.set_symposium_info("Test Symposium", "2025-11-04", "Test Hall")
        
        # Add sessions
        for i in range(3):
            session = AgendaItem(
                session_id=f"session_{i:02d}",
                start_time=f"09:{i*20:02d}",
                speaker=SpeakerInfo(
                    name=f"Speaker {i}",
                    title=f"Talk {i}",
                    duration_minutes=15
                )
            )
            manager.add_agenda_item(session, validate=False)
        
        # Save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        success = manager.save_to_file(temp_path)
        assert success
        
        # Load
        manager2 = AgendaManager()
        success = manager2.load_from_file(temp_path)
        assert success
        
        # Verify
        assert manager2.get_symposium_title() == "Test Symposium"
        assert len(manager2.get_agenda_items()) == 3
        
        # Cleanup
        Path(temp_path).unlink()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

