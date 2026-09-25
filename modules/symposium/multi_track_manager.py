"""
Multi-Track Session Manager

Manages multiple parallel tracks/rooms for large conferences.

This fixes the CRITICAL issue where the system only supports single-track events.

Features:
- Multiple parallel rooms/tracks
- Per-room session management
- Conflict detection (same room, overlapping time)
- Independent timers per room
- Room resource management (displays, cameras)

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
import logging

from modules.symposium.agenda_manager import AgendaItem, SpeakerInfo
from modules.symposium.session_controller import SessionController
from modules.symposium.time_validator import TimeValidator, TimeRange
from modules.timer.timer_controller import TimerController

logger = logging.getLogger(__name__)


@dataclass
class Room:
    """Physical or virtual room/track."""
    room_id: str
    name: str
    capacity: int = 100
    location: str = ""
    display_id: Optional[str] = None  # Associated display output
    camera_id: Optional[str] = None   # Associated Face AI camera
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'room_id': self.room_id,
            'name': self.name,
            'capacity': self.capacity,
            'location': self.location,
            'display_id': self.display_id,
            'camera_id': self.camera_id,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Room':
        """Create from dictionary."""
        return cls(
            room_id=data.get('room_id', ''),
            name=data.get('name', ''),
            capacity=data.get('capacity', 100),
            location=data.get('location', ''),
            display_id=data.get('display_id'),
            camera_id=data.get('camera_id'),
            notes=data.get('notes', '')
        )


@dataclass
class MultiTrackAgendaItem:
    """Enhanced agenda item with room support."""
    session_id: str
    start_time: str
    speaker: SpeakerInfo
    room_id: str  # ✅ NEW: Which room/track
    session_type: str = "talk"
    notes: str = ""
    end_time: Optional[str] = None  # Calculated from start_time + duration
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'speaker': self.speaker.to_dict(),
            'room_id': self.room_id,
            'session_type': self.session_type,
            'notes': self.notes,
            'end_time': self.end_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MultiTrackAgendaItem':
        """Create from dictionary."""
        return cls(
            session_id=data.get('session_id', ''),
            start_time=data.get('start_time', '09:00'),
            speaker=SpeakerInfo.from_dict(data.get('speaker', {})),
            room_id=data.get('room_id', 'default'),
            session_type=data.get('session_type', 'talk'),
            notes=data.get('notes', ''),
            end_time=data.get('end_time')
        )
    
    def calculate_end_time(self) -> str:
        """Calculate and cache end time."""
        if not self.end_time:
            time_range = TimeValidator.calculate_end_time(
                self.start_time,
                self.speaker.duration_minutes
            )
            self.end_time = time_range.end_time
        return self.end_time


class MultiTrackManager(QObject):
    """
    Manages multiple parallel tracks/rooms.
    
    Features:
    - Multi-room scheduling
    - Conflict detection (per room)
    - Independent timers per room
    - Synchronized agenda view
    - Room resource management
    """
    
    # Signals
    track_conflict_detected = pyqtSignal(str, str, str)  # (room_id, session_id_1, session_id_2)
    room_session_started = pyqtSignal(str, str)  # (room_id, session_id)
    room_session_ended = pyqtSignal(str, str)  # (room_id, session_id)
    room_added = pyqtSignal(str)  # room_id
    room_removed = pyqtSignal(str)  # room_id
    
    def __init__(self):
        """Initialize multi-track manager."""
        super().__init__()
        
        self._rooms: Dict[str, Room] = {}
        self._session_controllers: Dict[str, SessionController] = {}  # One per room
        self._agenda_items: List[MultiTrackAgendaItem] = []
        
        logger.info("MultiTrackManager initialized")
    
    def add_room(self, room: Room) -> bool:
        """
        Add a room/track.
        
        Args:
            room: Room to add
        
        Returns:
            True if added successfully
        """
        if room.room_id in self._rooms:
            logger.warning(f"Room {room.room_id} already exists")
            return False
        
        self._rooms[room.room_id] = room
        
        # Create dedicated session controller for this room
        self._session_controllers[room.room_id] = SessionController()
        
        logger.info(f"Added room: {room.room_id} ({room.name})")
        self.room_added.emit(room.room_id)
        
        return True
    
    def remove_room(self, room_id: str) -> bool:
        """
        Remove a room/track.
        
        Args:
            room_id: Room ID to remove
        
        Returns:
            True if removed successfully
        """
        if room_id not in self._rooms:
            logger.warning(f"Room {room_id} not found")
            return False
        
        # Check if room has active sessions
        active_session = self._session_controllers[room_id].get_current_session()
        if active_session:
            logger.error(f"Cannot remove room {room_id} - has active session")
            return False
        
        # Remove room
        del self._rooms[room_id]
        del self._session_controllers[room_id]
        
        # Remove sessions in this room
        self._agenda_items = [
            item for item in self._agenda_items
            if item.room_id != room_id
        ]
        
        logger.info(f"Removed room: {room_id}")
        self.room_removed.emit(room_id)
        
        return True
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return self._rooms.get(room_id)
    
    def get_all_rooms(self) -> List[Room]:
        """Get all rooms."""
        return list(self._rooms.values())
    
    def add_session(
        self,
        session: MultiTrackAgendaItem,
        validate: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Add session with conflict detection.
        
        Args:
            session: Session to add
            validate: If True, validate and check conflicts
        
        Returns:
            Tuple of (success, error_message)
        """
        if validate:
            # Validate room exists
            if session.room_id not in self._rooms:
                error_msg = f"Room '{session.room_id}' does not exist"
                logger.error(error_msg)
                return (False, error_msg)
            
            # Validate time
            try:
                session.start_time = TimeValidator.normalize_time(session.start_time)
            except Exception as e:
                error_msg = f"Invalid start time: {str(e)}"
                logger.error(error_msg)
                return (False, error_msg)
            
            # Validate duration
            valid, error, warning = TimeValidator.validate_duration(
                session.speaker.duration_minutes,
                strict=False
            )
            if not valid:
                return (False, error)
            
            if warning:
                logger.warning(f"Session {session.session_id}: {warning}")
            
            # Calculate end time
            session.calculate_end_time()
            
            # Check for conflicts (same room only)
            conflicts = self._detect_conflicts(session)
            if conflicts:
                conflict_session = conflicts[0]
                error_msg = (
                    f"⚠️ Schedule Conflict in Room '{session.room_id}'!\n\n"
                    f"New session '{session.session_id}': "
                    f"{session.start_time}-{session.end_time}\n"
                    f"Conflicts with '{conflict_session.session_id}': "
                    f"{conflict_session.start_time}-{conflict_session.end_time}\n\n"
                    f"Please adjust timing."
                )
                logger.warning(error_msg)
                
                self.track_conflict_detected.emit(
                    session.room_id,
                    session.session_id,
                    conflict_session.session_id
                )
                
                return (False, error_msg)
        
        # Add session
        self._agenda_items.append(session)
        
        # Sort by room, then time
        self._agenda_items.sort(
            key=lambda x: (
                x.room_id,
                TimeValidator.parse_time_to_minutes(x.start_time)
            )
        )
        
        logger.info(f"Added session {session.session_id} in room {session.room_id} at {session.start_time}")
        return (True, None)
    
    def _detect_conflicts(self, new_session: MultiTrackAgendaItem) -> List[MultiTrackAgendaItem]:
        """
        Detect scheduling conflicts in the same room.
        
        Args:
            new_session: New session to check
        
        Returns:
            List of conflicting sessions
        """
        conflicts = []
        
        for existing in self._agenda_items:
            # Only check same room
            if existing.room_id != new_session.room_id:
                continue
            
            # Check time overlap
            if TimeValidator.detect_overlap(
                existing.start_time, existing.speaker.duration_minutes,
                new_session.start_time, new_session.speaker.duration_minutes
            ):
                conflicts.append(existing)
        
        return conflicts
    
    def start_room_session(self, room_id: str, session_id: str) -> bool:
        """
        Start session in specific room.
        
        Args:
            room_id: Room ID
            session_id: Session ID to start
        
        Returns:
            True if started successfully
        """
        if room_id not in self._session_controllers:
            logger.error(f"Room {room_id} not found")
            return False
        
        # Find session
        session = next(
            (s for s in self._agenda_items if s.session_id == session_id and s.room_id == room_id),
            None
        )
        
        if not session:
            logger.error(f"Session {session_id} not found in room {room_id}")
            return False
        
        # Convert to AgendaItem for SessionController
        agenda_item = AgendaItem(
            session_id=session.session_id,
            start_time=session.start_time,
            speaker=session.speaker,
            session_type=session.session_type,
            notes=session.notes
        )
        
        # Start via room's controller
        controller = self._session_controllers[room_id]
        success = controller.start_session(agenda_item)
        
        if success:
            logger.info(f"Started session {session_id} in room {room_id}")
            self.room_session_started.emit(room_id, session_id)
        
        return success
    
    def end_room_session(self, room_id: str) -> bool:
        """
        End current session in specific room.
        
        Args:
            room_id: Room ID
        
        Returns:
            True if ended successfully
        """
        if room_id not in self._session_controllers:
            logger.error(f"Room {room_id} not found")
            return False
        
        controller = self._session_controllers[room_id]
        current_session = controller.get_current_session()
        
        if current_session:
            session_id = current_session.session_id
            controller.end_session()
            logger.info(f"Ended session {session_id} in room {room_id}")
            self.room_session_ended.emit(room_id, session_id)
            return True
        
        return False
    
    def get_active_sessions(self) -> Dict[str, Optional[AgendaItem]]:
        """
        Get currently active session in each room.
        
        Returns:
            Dict mapping room_id -> active session (or None)
        """
        active = {}
        for room_id, controller in self._session_controllers.items():
            active[room_id] = controller.get_current_session()
        return active
    
    def get_room_schedule(self, room_id: str) -> List[MultiTrackAgendaItem]:
        """
        Get all sessions for a specific room.
        
        Args:
            room_id: Room ID
        
        Returns:
            List of sessions in chronological order
        """
        return [s for s in self._agenda_items if s.room_id == room_id]
    
    def get_all_sessions(self) -> List[MultiTrackAgendaItem]:
        """Get all sessions across all rooms."""
        return self._agenda_items.copy()
    
    def get_concurrent_sessions(self, time_str: str) -> List[MultiTrackAgendaItem]:
        """
        Get all sessions happening at a specific time.
        
        Args:
            time_str: Time to check (HH:MM)
        
        Returns:
            List of concurrent sessions
        """
        time_minutes = TimeValidator.parse_time_to_minutes(time_str)
        concurrent = []
        
        for session in self._agenda_items:
            start_minutes = TimeValidator.parse_time_to_minutes(session.start_time)
            end_minutes = start_minutes + session.speaker.duration_minutes
            
            if start_minutes <= time_minutes < end_minutes:
                concurrent.append(session)
        
        return concurrent
    
    def export_schedule(self) -> dict:
        """
        Export full schedule to dictionary.
        
        Returns:
            Dictionary with rooms and sessions
        """
        return {
            'rooms': [room.to_dict() for room in self._rooms.values()],
            'sessions': [session.to_dict() for session in self._agenda_items]
        }
    
    def import_schedule(self, data: dict) -> Tuple[bool, Optional[str]]:
        """
        Import schedule from dictionary.
        
        Args:
            data: Dictionary with rooms and sessions
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Clear existing
            self._rooms.clear()
            self._session_controllers.clear()
            self._agenda_items.clear()
            
            # Import rooms
            for room_data in data.get('rooms', []):
                room = Room.from_dict(room_data)
                self.add_room(room)
            
            # Import sessions
            for session_data in data.get('sessions', []):
                session = MultiTrackAgendaItem.from_dict(session_data)
                success, error = self.add_session(session, validate=True)
                if not success:
                    logger.warning(f"Skipped session {session.session_id}: {error}")
            
            logger.info(f"Imported {len(self._rooms)} rooms and {len(self._agenda_items)} sessions")
            return (True, None)
            
        except Exception as e:
            error_msg = f"Error importing schedule: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Multi-Track Manager Test ===\n")
    
    # Create manager
    manager = MultiTrackManager()
    
    # Add rooms
    manager.add_room(Room(room_id="hall_a", name="Hall A", capacity=200))
    manager.add_room(Room(room_id="hall_b", name="Hall B", capacity=150))
    manager.add_room(Room(room_id="hall_c", name="Hall C", capacity=100))
    
    print(f"Added {len(manager.get_all_rooms())} rooms\n")
    
    # Add parallel sessions
    session_a = MultiTrackAgendaItem(
        session_id="a1",
        start_time="09:00",
        speaker=SpeakerInfo(name="Speaker A", title="Talk A", duration_minutes=60),
        room_id="hall_a"
    )
    
    session_b = MultiTrackAgendaItem(
        session_id="b1",
        start_time="09:00",  # Same time, different room - OK
        speaker=SpeakerInfo(name="Speaker B", title="Talk B", duration_minutes=60),
        room_id="hall_b"
    )
    
    success, error = manager.add_session(session_a)
    print(f"Add session A: {success}")
    
    success, error = manager.add_session(session_b)
    print(f"Add session B: {success}")
    
    # Test conflict detection
    print("\n=== Testing Conflict Detection ===")
    conflicting_session = MultiTrackAgendaItem(
        session_id="a2",
        start_time="09:30",  # Overlaps with a1!
        speaker=SpeakerInfo(name="Speaker A2", title="Talk A2", duration_minutes=60),
        room_id="hall_a"  # Same room as a1
    )
    
    success, error = manager.add_session(conflicting_session)
    print(f"Add conflicting session: {success}")
    if not success:
        print(f"Error: {error}")
    
    # Get concurrent sessions
    print("\n=== Concurrent Sessions at 09:15 ===")
    concurrent = manager.get_concurrent_sessions("09:15")
    for session in concurrent:
        print(f"  - {session.session_id} in {session.room_id}: {session.speaker.name}")

