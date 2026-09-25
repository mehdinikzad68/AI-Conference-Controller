"""
Integration Tests - Full Workflow

Tests complete workflows across multiple modules.

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import pytest
import tempfile
from pathlib import Path
import time


class TestSymposiumWorkflow:
    """Test complete symposium workflow."""
    
    def test_create_and_run_symposium(self):
        """Test creating and running a complete symposium."""
        from modules.symposium.agenda_manager import AgendaManager, AgendaItem, SpeakerInfo
        from modules.symposium.time_validator import TimeValidator
        
        # 1. Create agenda
        manager = AgendaManager()
        manager.set_symposium_info(
            title="Test Symposium 2025",
            date="2025-11-04",
            location="Main Hall"
        )
        
        # 2. Add sessions
        sessions = [
            ("09:00", "Dr. Smith", "AI in Healthcare", 45),
            ("10:00", "Prof. Johnson", "Machine Learning Trends", 60),
            ("11:15", "Dr. Lee", "Future of Robotics", 30),
        ]
        
        for start_time, speaker_name, title, duration in sessions:
            item = AgendaItem(
                session_id=f"session_{start_time.replace(':', '')}",
                start_time=start_time,
                speaker=SpeakerInfo(
                    name=speaker_name,
                    title=title,
                    duration_minutes=duration
                )
            )
            
            success, error = manager.add_agenda_item(item, validate=True)
            assert success, f"Failed to add session: {error}"
        
        # 3. Verify agenda
        items = manager.get_agenda_items()
        assert len(items) == 3
        
        # 4. Check sorting
        assert items[0].start_time == "09:00"
        assert items[1].start_time == "10:00"
        assert items[2].start_time == "11:15"
        
        # 5. Save and reload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            success = manager.save_to_file(temp_path)
            assert success
            
            # Reload
            manager2 = AgendaManager()
            success = manager2.load_from_file(temp_path)
            assert success
            
            # Verify
            assert manager2.get_symposium_title() == "Test Symposium 2025"
            assert len(manager2.get_agenda_items()) == 3
        finally:
            Path(temp_path).unlink()
    
    def test_overlap_detection_workflow(self):
        """Test that overlapping sessions are properly detected."""
        from modules.symposium.agenda_manager import AgendaManager, AgendaItem, SpeakerInfo
        
        manager = AgendaManager()
        
        # Add first session (09:00-10:00)
        session1 = AgendaItem(
            session_id="s1",
            start_time="09:00",
            speaker=SpeakerInfo(name="Speaker 1", title="Talk 1", duration_minutes=60)
        )
        success, _ = manager.add_agenda_item(session1, validate=True)
        assert success
        
        # Try to add overlapping session (09:30-10:30)
        session2 = AgendaItem(
            session_id="s2",
            start_time="09:30",
            speaker=SpeakerInfo(name="Speaker 2", title="Talk 2", duration_minutes=60)
        )
        success, error = manager.add_agenda_item(session2, validate=True)
        assert not success
        assert "Conflict" in error
        
        # Add non-overlapping session (10:00-11:00) - should work
        session3 = AgendaItem(
            session_id="s3",
            start_time="10:00",
            speaker=SpeakerInfo(name="Speaker 3", title="Talk 3", duration_minutes=60)
        )
        success, _ = manager.add_agenda_item(session3, validate=True)
        assert success


class TestMultiTrackWorkflow:
    """Test multi-track symposium workflow."""
    
    def test_parallel_sessions(self):
        """Test running parallel sessions in different rooms."""
        from modules.symposium.multi_track_manager import MultiTrackManager, Room
        from modules.symposium.agenda_manager import SpeakerInfo
        
        # Create manager
        manager = MultiTrackManager()
        
        # Add rooms
        manager.add_room(Room(room_id="hall_a", name="Hall A", capacity=200))
        manager.add_room(Room(room_id="hall_b", name="Hall B", capacity=150))
        manager.add_room(Room(room_id="hall_c", name="Hall C", capacity=100))
        
        # Add parallel sessions (same time, different rooms)
        from modules.symposium.multi_track_manager import MultiTrackAgendaItem
        
        sessions = [
            ("hall_a", "09:00", "Dr. Smith", "AI Track", 60),
            ("hall_b", "09:00", "Prof. Johnson", "ML Track", 60),
            ("hall_c", "09:00", "Dr. Lee", "Robotics Track", 60),
        ]
        
        for room_id, start_time, speaker, title, duration in sessions:
            item = MultiTrackAgendaItem(
                session_id=f"{room_id}_{start_time}",
                start_time=start_time,
                speaker=SpeakerInfo(name=speaker, title=title, duration_minutes=duration),
                room_id=room_id
            )
            
            success, error = manager.add_session(item)
            assert success, f"Failed to add session: {error}"
        
        # Verify concurrent sessions
        concurrent = manager.get_concurrent_sessions("09:15")
        assert len(concurrent) == 3
        
        # Verify room assignment
        assert all(s.room_id in ["hall_a", "hall_b", "hall_c"] for s in concurrent)


class TestConfigAndCacheIntegration:
    """Test config manager with cache integration."""
    
    def test_cached_config_access(self):
        """Test that config access can be cached."""
        from modules.config.config_manager import ConfigManager
        from modules.performance.cache_manager import CacheManager, cached
        
        # Create managers
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            cache = CacheManager(memory_size=50, ttl=60.0)
            
            # Set some config
            config.set('timer.default_duration', 3600)
            config.set('display.resolution', '1920x1080')
            config.save_config()
            
            # Define cached getter
            @cached(cache, "config_", ttl=30)
            def get_config_value(key):
                return config.get(key)
            
            # First call - cache miss
            value1 = get_config_value('timer.default_duration')
            assert value1 == 3600
            
            # Second call - cache hit
            value2 = get_config_value('timer.default_duration')
            assert value2 == 3600
            
            # Check cache stats
            stats = cache.get_stats()
            assert stats['memory']['hits'] > 0
            
        finally:
            Path(config_path).unlink()


class TestAuthenticationWorkflow:
    """Test authentication workflow."""
    
    def test_login_logout_workflow(self):
        """Test complete login/logout workflow."""
        from modules.security.auth_system import AuthenticationManager, UserRole
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            users_path = f.name
        
        try:
            auth = AuthenticationManager(users_path)
            
            # Login as admin
            session = auth.login("admin", "admin123")
            assert session is not None
            
            # Validate session
            valid_session = auth.validate_session(session)
            assert valid_session is not None
            assert valid_session.role == UserRole.ADMIN
            
            # Check permissions
            assert auth.has_permission(session, UserRole.OPERATOR)
            assert auth.has_permission(session, UserRole.VIEWER)
            
            # Logout
            auth.logout(session)
            
            # Session should be invalid now
            invalid_session = auth.validate_session(session)
            assert invalid_session is None
            
        finally:
            Path(users_path).unlink(missing_ok=True)
    
    def test_failed_login_lockout(self):
        """Test that failed logins lead to lockout."""
        from modules.security.auth_system import AuthenticationManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            users_path = f.name
        
        try:
            auth = AuthenticationManager(users_path)
            
            # Try wrong password multiple times
            for i in range(6):
                session = auth.login("admin", "wrong_password")
                assert session is None
            
            # Should be locked out now
            assert auth._attempt_tracker.is_locked_out("admin")
            
            # Even correct password won't work
            session = auth.login("admin", "admin123")
            assert session is None
            
        finally:
            Path(users_path).unlink(missing_ok=True)


class TestEndToEndSymposium:
    """End-to-end symposium simulation."""
    
    def test_full_symposium_day(self):
        """Simulate a full symposium day."""
        from modules.symposium.agenda_manager import AgendaManager, AgendaItem, SpeakerInfo
        from modules.symposium.multi_track_manager import MultiTrackManager, Room
        
        print("\n=== Simulating Full Symposium Day ===\n")
        
        # 1. Setup
        print("1. Setting up symposium...")
        manager = AgendaManager()
        manager.set_symposium_info(
            title="AI Conference 2025",
            date="2025-11-04",
            location="Convention Center"
        )
        
        # 2. Create schedule
        print("2. Creating schedule...")
        schedule = [
            ("08:30", "Registration", 30),
            ("09:00", "Opening Keynote - Dr. Sarah Johnson", 60),
            ("10:00", "Coffee Break", 15),
            ("10:15", "Session 1 - Machine Learning", 45),
            ("11:00", "Session 2 - Deep Learning", 45),
            ("11:45", "Lunch", 60),
            ("12:45", "Panel Discussion", 60),
            ("13:45", "Closing Remarks", 15),
        ]
        
        for i, (start_time, title, duration) in enumerate(schedule):
            item = AgendaItem(
                session_id=f"session_{i:02d}",
                start_time=start_time,
                speaker=SpeakerInfo(
                    name="Various" if "Break" in title else "TBD",
                    title=title,
                    duration_minutes=duration
                )
            )
            
            success, error = manager.add_agenda_item(item, validate=True)
            assert success, f"Failed: {error}"
        
        # 3. Verify schedule
        print("3. Verifying schedule...")
        items = manager.get_agenda_items()
        assert len(items) == len(schedule)
        
        # Check times are in order
        for i in range(len(items) - 1):
            assert items[i].start_time <= items[i+1].start_time
        
        # 4. Save
        print("4. Saving schedule...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            success = manager.save_to_file(temp_path)
            assert success
            
            # Verify file size
            file_size = Path(temp_path).stat().st_size
            assert file_size > 100  # Should have content
            
            print(f"   Schedule saved ({file_size} bytes)")
            
        finally:
            Path(temp_path).unlink()
        
        print("\n✅ Full symposium simulation successful!\n")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

