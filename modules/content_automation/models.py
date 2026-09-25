"""
Data Models and Schemas

Comprehensive data models for content, scheduling, validation, and playback.

All models use dataclasses for immutability and type safety.
Supports JSON serialization for API/storage.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json


# ==================== Enums ====================

class ContentType(Enum):
    """Supported content types"""
    VIDEO = "video"
    SLIDE = "slide"
    IMAGE = "image"
    AUDIO = "audio"
    LOGO = "logo"
    PDF = "pdf"
    LIVESTREAM = "livestream"
    SCREEN_SHARE = "screen_share"


class ValidationStatus(Enum):
    """Content validation status"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


class PlaybackStatus(Enum):
    """Playback status"""
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    PREPARING = "preparing"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EMERGENCY_STOPPED = "emergency_stopped"


class SyncStatus(Enum):
    """Platform synchronization status"""
    SYNCED = "synced"
    SYNCING = "syncing"
    OUT_OF_SYNC = "out_of_sync"
    FAILED = "failed"
    DEGRADED = "degraded"  # Partial sync


class PlatformType(Enum):
    """Target platform types"""
    LOCAL_HALL = "local_hall"
    SKYROOM = "skyroom"
    ZOOM = "zoom"
    TEAMS = "teams"
    CUSTOM = "custom"


class Priority(Enum):
    """Content priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    EMERGENCY = 3


# ==================== Content Models ====================

@dataclass
class ContentMetadata:
    """
    Metadata for content items.
    
    Extensible via custom_fields for future requirements.
    """
    title: str
    description: str = ""
    duration_seconds: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetadata':
        """Create from dictionary"""
        data = data.copy()
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class FileInfo:
    """File information and validation data"""
    path: str
    size_bytes: int
    format: str
    mime_type: str
    checksum_md5: str
    resolution: Optional[str] = None  # For video/image: "1920x1080"
    bitrate: Optional[int] = None      # For video/audio
    codec: Optional[str] = None
    accessible: bool = True
    corrupted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ContentItem:
    """
    Represents a multimedia content item.
    
    Immutable after creation (use update methods to modify).
    """
    content_id: str
    content_type: ContentType
    file_info: FileInfo
    metadata: ContentMetadata
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'content_id': self.content_id,
            'content_type': self.content_type.value,
            'file_info': self.file_info.to_dict(),
            'metadata': self.metadata.to_dict(),
            'validation_status': self.validation_status.value,
            'validation_errors': self.validation_errors,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentItem':
        """Create from dictionary"""
        return cls(
            content_id=data['content_id'],
            content_type=ContentType(data['content_type']),
            file_info=FileInfo.from_dict(data['file_info']),
            metadata=ContentMetadata.from_dict(data['metadata']),
            validation_status=ValidationStatus(data['validation_status']),
            validation_errors=data.get('validation_errors', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def is_valid(self) -> bool:
        """Check if content is validated and ready"""
        return self.validation_status == ValidationStatus.VALID
    
    def get_duration(self) -> Optional[float]:
        """Get content duration in seconds"""
        return self.metadata.duration_seconds


@dataclass
class ScheduleItem:
    """
    Scheduled content playback item.
    
    Supports both absolute time and relative time scheduling.
    """
    schedule_id: str
    content_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    platforms: List[PlatformType] = field(default_factory=lambda: [PlatformType.LOCAL_HALL])
    priority: Priority = Priority.NORMAL
    auto_advance: bool = True
    loop: bool = False
    volume: float = 1.0  # 0.0 to 1.0
    playback_status: PlaybackStatus = PlaybackStatus.SCHEDULED
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'schedule_id': self.schedule_id,
            'content_id': self.content_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'platforms': [p.value for p in self.platforms],
            'priority': self.priority.value,
            'auto_advance': self.auto_advance,
            'loop': self.loop,
            'volume': self.volume,
            'playback_status': self.playback_status.value,
            'actual_start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
            'actual_end_time': self.actual_end_time.isoformat() if self.actual_end_time else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleItem':
        """Create from dictionary"""
        return cls(
            schedule_id=data['schedule_id'],
            content_id=data['content_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            platforms=[PlatformType(p) for p in data['platforms']],
            priority=Priority(data.get('priority', 1)),
            auto_advance=data.get('auto_advance', True),
            loop=data.get('loop', False),
            volume=data.get('volume', 1.0),
            playback_status=PlaybackStatus(data.get('playback_status', 'scheduled')),
            actual_start_time=datetime.fromisoformat(data['actual_start_time']) if data.get('actual_start_time') else None,
            actual_end_time=datetime.fromisoformat(data['actual_end_time']) if data.get('actual_end_time') else None,
            metadata=data.get('metadata', {})
        )
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """Check if scheduled time has arrived"""
        current_time = current_time or datetime.now()
        return current_time >= self.start_time
    
    def is_active(self) -> bool:
        """Check if currently playing"""
        return self.playback_status == PlaybackStatus.PLAYING


@dataclass
class ValidationResult:
    """Result of content validation"""
    content_id: str
    status: ValidationStatus
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    validation_duration_ms: float = 0.0
    file_accessible: bool = True
    file_corrupted: bool = False
    format_supported: bool = True
    metadata_extracted: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content_id': self.content_id,
            'status': self.status.value,
            'errors': self.errors,
            'warnings': self.warnings,
            'validated_at': self.validated_at.isoformat(),
            'validation_duration_ms': self.validation_duration_ms,
            'file_accessible': self.file_accessible,
            'file_corrupted': self.file_corrupted,
            'format_supported': self.format_supported,
            'metadata_extracted': self.metadata_extracted
        }
    
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.status == ValidationStatus.VALID and not self.errors


@dataclass
class PlaybackState:
    """Current playback state"""
    schedule_id: str
    content_id: str
    status: PlaybackStatus
    platform: PlatformType
    progress_seconds: float = 0.0
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'schedule_id': self.schedule_id,
            'content_id': self.content_id,
            'status': self.status.value,
            'platform': self.platform.value,
            'progress_seconds': self.progress_seconds,
            'duration_seconds': self.duration_seconds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'error_message': self.error_message
        }
    
    def get_progress_percentage(self) -> float:
        """Get playback progress as percentage"""
        if self.duration_seconds and self.duration_seconds > 0:
            return (self.progress_seconds / self.duration_seconds) * 100.0
        return 0.0


@dataclass
class SyncState:
    """Synchronization state across platforms"""
    schedule_id: str
    platforms: Dict[PlatformType, PlaybackState]
    sync_status: SyncStatus = SyncStatus.SYNCED
    sync_offset_ms: float = 0.0  # Max offset between platforms
    last_sync_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'schedule_id': self.schedule_id,
            'platforms': {k.value: v.to_dict() for k, v in self.platforms.items()},
            'sync_status': self.sync_status.value,
            'sync_offset_ms': self.sync_offset_ms,
            'last_sync_at': self.last_sync_at.isoformat()
        }
    
    def is_synced(self, tolerance_ms: float = 500.0) -> bool:
        """Check if all platforms are synchronized within tolerance"""
        return self.sync_offset_ms <= tolerance_ms


# ==================== Error Models ====================

@dataclass
class ContentAutomationError:
    """Standardized error reporting"""
    error_id: str
    error_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    recovery_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'error_id': self.error_id,
            'error_type': self.error_type,
            'severity': self.severity,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'recovery_actions': self.recovery_actions
        }


# ==================== Helper Functions ====================

def serialize_model(obj: Any) -> str:
    """Serialize any model to JSON string"""
    if hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict(), indent=2)
    return json.dumps(obj, default=str)


def deserialize_model(json_str: str, model_class: type) -> Any:
    """Deserialize JSON string to model"""
    data = json.loads(json_str)
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    return model_class(**data)

