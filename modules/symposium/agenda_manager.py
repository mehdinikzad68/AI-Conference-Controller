"""
Agenda Manager Module

Manages symposium agenda, speaker information, session scheduling, and transitions.

Enhanced with:
- Time validation (fixes string sort bug)
- Input sanitization
- Overlap detection
- Duration validation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
import json
import logging

# Import validation modules
from modules.symposium.time_validator import TimeValidator, TimeValidationError
from modules.utils.input_sanitizer import InputSanitizer, InputSanitizationError

logger = logging.getLogger(__name__)


@dataclass
class SpeakerInfo:
    """Information about a speaker."""
    name: str
    title: str  # Talk title
    photo_path: Optional[str] = None
    bio: str = ""
    duration_minutes: int = 30
    media_path: Optional[str] = None  # PDF, PPT, video file
    organization: str = ""
    email: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'title': self.title,
            'photo_path': str(self.photo_path) if self.photo_path else None,
            'bio': self.bio,
            'duration_minutes': self.duration_minutes,
            'media_path': str(self.media_path) if self.media_path else None,
            'organization': self.organization,
            'email': self.email
        }
    
    @classmethod
    def from_dict(cls, data: dict, sanitize: bool = True) -> 'SpeakerInfo':
        """
        Create from dictionary with optional input sanitization.
        
        Args:
            data: Dictionary with speaker data
            sanitize: If True, sanitize all inputs
        
        Returns:
            SpeakerInfo instance
        """
        name = data.get('name', '')
        title = data.get('title', '')
        bio = data.get('bio', '')
        organization = data.get('organization', '')
        email = data.get('email', '')
        
        if sanitize:
            # Sanitize name
            try:
                name, warnings = InputSanitizer.sanitize_name(name, "speaker_name")
                for warning in warnings:
                    logger.warning(warning)
            except InputSanitizationError as e:
                logger.error(f"Invalid speaker name: {e}")
                name = "Unknown Speaker"
            
            # Sanitize title
            try:
                title, warnings = InputSanitizer.sanitize_title(title)
                for warning in warnings:
                    logger.warning(warning)
            except InputSanitizationError as e:
                logger.error(f"Invalid title: {e}")
                title = "Untitled"
            
            # Sanitize bio
            bio, warnings = InputSanitizer.sanitize_bio(bio)
            for warning in warnings:
                logger.warning(warning)
            
            # Sanitize organization
            organization, org_warnings = InputSanitizer.sanitize_string(
                organization,
                max_length=200,
                field_name="organization"
            )
            
            # Validate email
            valid, error, email = InputSanitizer.validate_email(email)
            if not valid:
                logger.warning(f"Invalid email '{email}': {error}")
                email = ""
        
        return cls(
            name=name,
            title=title,
            photo_path=data.get('photo_path'),
            bio=bio,
            duration_minutes=data.get('duration_minutes', 30),
            media_path=data.get('media_path'),
            organization=organization,
            email=email
        )


@dataclass
class AgendaItem:
    """A single agenda item (session)."""
    session_id: str
    start_time: str  # Format: "HH:MM"
    speaker: SpeakerInfo
    session_type: str = "talk"  # talk, break, panel, etc.
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'speaker': self.speaker.to_dict(),
            'session_type': self.session_type,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgendaItem':
        """Create from dictionary."""
        return cls(
            session_id=data.get('session_id', ''),
            start_time=data.get('start_time', '09:00'),
            speaker=SpeakerInfo.from_dict(data.get('speaker', {})),
            session_type=data.get('session_type', 'talk'),
            notes=data.get('notes', '')
        )


class AgendaManager(QObject):
    """
    Manages symposium agenda and speaker information.
    
    Features:
    - Load/save agenda from JSON
    - Current session tracking
    - Speaker information management
    - Session navigation
    """
    
    # Signals
    agenda_loaded = pyqtSignal()
    current_session_changed = pyqtSignal(str)  # Emits session_id
    session_started = pyqtSignal(str)  # Emits session_id
    session_ended = pyqtSignal(str)  # Emits session_id
    
    def __init__(self):
        """Initialize agenda manager."""
        super().__init__()
        self._agenda_items: List[AgendaItem] = []
        self._current_session_index: int = -1
        self._symposium_title: str = "Symposium"
        self._symposium_date: str = ""
        self._symposium_location: str = ""
        self._logo_path: Optional[str] = None
    
    def set_symposium_info(self, title: str, date: str = "", location: str = "", logo_path: Optional[str] = None):
        """
        Set symposium information.
        
        Args:
            title: Symposium title
            date: Event date
            location: Event location
            logo_path: Path to logo image
        """
        self._symposium_title = title
        self._symposium_date = date
        self._symposium_location = location
        self._logo_path = logo_path
    
    def get_symposium_title(self) -> str:
        """Get symposium title."""
        return self._symposium_title
    
    def get_symposium_date(self) -> str:
        """Get symposium date."""
        return self._symposium_date
    
    def get_symposium_location(self) -> str:
        """Get symposium location."""
        return self._symposium_location
    
    def get_logo_path(self) -> Optional[str]:
        """Get logo path."""
        return self._logo_path
    
    def add_agenda_item(self, item: AgendaItem, validate: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Add an agenda item with validation.
        
        Args:
            item: AgendaItem to add
            validate: If True, validate time and detect overlaps
        
        Returns:
            Tuple of (success, error_message)
        
        Raises:
            TimeValidationError: If time validation fails in strict mode
            InputSanitizationError: If input validation fails
        """
        if validate:
            # Validate start time
            try:
                item.start_time = TimeValidator.normalize_time(item.start_time)
            except TimeValidationError as e:
                error_msg = f"Invalid start time for session {item.session_id}: {str(e)}"
                logger.error(error_msg)
                return (False, error_msg)
            
            # Validate duration
            valid, error, warning = TimeValidator.validate_duration(
                item.speaker.duration_minutes,
                strict=False  # Allow warnings but not strict rejection
            )
            if not valid:
                error_msg = f"Invalid duration for session {item.session_id}: {error}"
                logger.error(error_msg)
                return (False, error_msg)
            
            if warning:
                logger.warning(f"Session {item.session_id}: {warning}")
            
            # Check for overlaps (single-track mode)
            for existing in self._agenda_items:
                if TimeValidator.detect_overlap(
                    existing.start_time, existing.speaker.duration_minutes,
                    item.start_time, item.speaker.duration_minutes
                ):
                    # Calculate end times for display
                    existing_end = TimeValidator.calculate_end_time(
                        existing.start_time, existing.speaker.duration_minutes
                    )
                    new_end = TimeValidator.calculate_end_time(
                        item.start_time, item.speaker.duration_minutes
                    )
                    
                    error_msg = (
                        f"⚠️ Schedule Conflict Detected!\n\n"
                        f"New session '{item.session_id}': {new_end}\n"
                        f"Conflicts with '{existing.session_id}': {existing_end}\n\n"
                        f"Please adjust timing or use multi-track mode."
                    )
                    logger.warning(error_msg)
                    return (False, error_msg)
        
        # Add item
        self._agenda_items.append(item)
        
        # Sort properly using TimeValidator (fixes string sort bug!)
        self._agenda_items.sort(
            key=lambda x: TimeValidator.parse_time_to_minutes(x.start_time)
        )
        
        logger.info(f"Added session {item.session_id} at {item.start_time}")
        return (True, None)
    
    def remove_agenda_item(self, session_id: str) -> bool:
        """
        Remove an agenda item.
        
        Args:
            session_id: Session ID to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, item in enumerate(self._agenda_items):
            if item.session_id == session_id:
                self._agenda_items.pop(i)
                if self._current_session_index >= i:
                    self._current_session_index = max(-1, self._current_session_index - 1)
                return True
        return False
    
    def get_agenda_items(self) -> List[AgendaItem]:
        """Get all agenda items."""
        return self._agenda_items.copy()
    
    def get_agenda_item(self, session_id: str) -> Optional[AgendaItem]:
        """Get agenda item by session ID."""
        for item in self._agenda_items:
            if item.session_id == session_id:
                return item
        return None
    
    def set_current_session(self, session_id: str) -> bool:
        """
        Set current session.
        
        Args:
            session_id: Session ID to set as current
            
        Returns:
            True if set successfully
        """
        for i, item in enumerate(self._agenda_items):
            if item.session_id == session_id:
                self._current_session_index = i
                self.current_session_changed.emit(session_id)
                return True
        return False
    
    def get_current_session(self) -> Optional[AgendaItem]:
        """Get current session."""
        if 0 <= self._current_session_index < len(self._agenda_items):
            return self._agenda_items[self._current_session_index]
        return None
    
    def get_next_session(self) -> Optional[AgendaItem]:
        """Get next session."""
        if self._current_session_index < len(self._agenda_items) - 1:
            return self._agenda_items[self._current_session_index + 1]
        return None
    
    def get_previous_session(self) -> Optional[AgendaItem]:
        """Get previous session."""
        if self._current_session_index > 0:
            return self._agenda_items[self._current_session_index - 1]
        return None
    
    def start_current_session(self) -> bool:
        """
        Start current session.
        
        Returns:
            True if started successfully
        """
        current = self.get_current_session()
        if current:
            self.session_started.emit(current.session_id)
            return True
        return False
    
    def end_current_session(self) -> bool:
        """
        End current session.
        
        Returns:
            True if ended successfully
        """
        current = self.get_current_session()
        if current:
            self.session_ended.emit(current.session_id)
            return True
        return False
    
    def move_to_next_session(self) -> bool:
        """
        Move to next session.
        
        Returns:
            True if moved successfully
        """
        if self._current_session_index < len(self._agenda_items) - 1:
            self._current_session_index += 1
            current = self.get_current_session()
            if current:
                self.current_session_changed.emit(current.session_id)
            return True
        return False
    
    def move_to_previous_session(self) -> bool:
        """
        Move to previous session.
        
        Returns:
            True if moved successfully
        """
        if self._current_session_index > 0:
            self._current_session_index -= 1
            current = self.get_current_session()
            if current:
                self.current_session_changed.emit(current.session_id)
            return True
        return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load agenda from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load symposium info
            if 'symposium' in data:
                symposium_info = data['symposium']
                self.set_symposium_info(
                    title=symposium_info.get('title', 'Symposium'),
                    date=symposium_info.get('date', ''),
                    location=symposium_info.get('location', ''),
                    logo_path=symposium_info.get('logo_path')
                )
            
            # Load agenda items with validation
            self._agenda_items = []
            if 'agenda' in data:
                for i, item_data in enumerate(data['agenda']):
                    try:
                        item = AgendaItem.from_dict(item_data)
                        
                        # Validate and add (without overlap check during load)
                        success, error = self.add_agenda_item(item, validate=False)
                        if not success:
                            logger.warning(f"Skipped invalid item {i}: {error}")
                    except Exception as e:
                        logger.error(f"Error loading agenda item {i}: {e}")
            
            # Sort properly using TimeValidator
            self._agenda_items.sort(
                key=lambda x: TimeValidator.parse_time_to_minutes(x.start_time)
            )
            
            self._current_session_index = -1
            self.agenda_loaded.emit()
            return True
        except Exception as e:
            print(f"Error loading agenda: {e}")
            return False
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save agenda to JSON file.
        
        Args:
            file_path: Path to save JSON file
            
        Returns:
            True if saved successfully
        """
        try:
            data = {
                'symposium': {
                    'title': self._symposium_title,
                    'date': self._symposium_date,
                    'location': self._symposium_location,
                    'logo_path': self._logo_path
                },
                'agenda': [item.to_dict() for item in self._agenda_items]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving agenda: {e}")
            return False

