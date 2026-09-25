"""
Content Manager - Content Library Management

Manages the content library:
- Add/update/remove content
- Search and filtering
- Metadata management
- Storage and retrieval
- Integration with validation service

Thread-safe and async-compatible.
"""

import asyncio
import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..models import ContentItem, ContentType, ContentMetadata, FileInfo, ValidationStatus
from ..sync.event_bus import Event, EventType, get_event_bus
from .validation_service import ValidationService

logger = logging.getLogger(__name__)


class ContentManager:
    """
    Manages content library with validation integration.
    
    Features:
    - CRUD operations
    - Automatic validation
    - Search and filtering
    - Persistence (JSON storage)
    - Event notifications
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        validation_service: Optional[ValidationService] = None,
        auto_validate: bool = True
    ):
        """
        Initialize content manager.
        
        Args:
            storage_path: Path to store content library JSON
            validation_service: Validation service instance
            auto_validate: Automatically validate new content
        """
        self._storage_path = Path(storage_path) if storage_path else Path("content_library.json")
        self._validation_service = validation_service or ValidationService()
        self._auto_validate = auto_validate
        self._event_bus = get_event_bus()
        
        # Content library
        self._content: Dict[str, ContentItem] = {}
        self._lock = asyncio.Lock()
        
        # Load existing library
        self._load_library()
        
        logger.info(f"ContentManager initialized (storage={self._storage_path})")
    
    async def add_content(
        self,
        file_path: str,
        content_type: ContentType,
        metadata: ContentMetadata,
        validate: bool = True
    ) -> ContentItem:
        """
        Add new content to library.
        
        Args:
            file_path: Path to content file
            content_type: Type of content
            metadata: Content metadata
            validate: Trigger validation immediately
        
        Returns:
            Created ContentItem
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If content already exists
        
        Example:
            >>> metadata = ContentMetadata(
            ...     title="Opening Video",
            ...     description="Conference opening",
            ...     duration_seconds=120
            ... )
            >>> content = await manager.add_content(
            ...     '/media/opening.mp4',
            ...     ContentType.VIDEO,
            ...     metadata
            ... )
        """
        file_path_obj = Path(file_path)
        
        # Check file exists
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate content ID
        content_id = str(uuid.uuid4())
        
        # Create file info
        file_info = FileInfo(
            path=str(file_path),
            size_bytes=file_path_obj.stat().st_size,
            format=file_path_obj.suffix[1:],  # Remove dot
            mime_type=self._guess_mime_type(file_path),
            checksum_md5="",  # Will be filled by validation
        )
        
        # Create content item
        content_item = ContentItem(
            content_id=content_id,
            content_type=content_type,
            file_info=file_info,
            metadata=metadata,
            validation_status=ValidationStatus.PENDING
        )
        
        # Add to library
        async with self._lock:
            self._content[content_id] = content_item
        
        # Save
        await self._save_library()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.CONTENT_ADDED,
            data={
                'content_id': content_id,
                'content_type': content_type.value,
                'title': metadata.title
            },
            source='ContentManager'
        ))
        
        logger.info(f"Added content: {content_id} ({metadata.title})")
        
        # Validate if requested
        if validate and self._auto_validate:
            await self._validation_service.queue_validation(content_item)
        
        return content_item
    
    async def update_content(
        self,
        content_id: str,
        metadata: Optional[ContentMetadata] = None,
        validation_status: Optional[ValidationStatus] = None
    ) -> ContentItem:
        """
        Update content metadata or status.
        
        Args:
            content_id: Content ID
            metadata: New metadata (None = no change)
            validation_status: New validation status (None = no change)
        
        Returns:
            Updated ContentItem
        
        Raises:
            KeyError: If content not found
        """
        async with self._lock:
            if content_id not in self._content:
                raise KeyError(f"Content not found: {content_id}")
            
            content_item = self._content[content_id]
            
            # Update metadata
            if metadata:
                content_item.metadata = metadata
            
            # Update validation status
            if validation_status:
                content_item.validation_status = validation_status
            
            # Update timestamp
            content_item.updated_at = datetime.now()
        
        # Save
        await self._save_library()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.CONTENT_UPDATED,
            data={'content_id': content_id},
            source='ContentManager'
        ))
        
        logger.info(f"Updated content: {content_id}")
        return content_item
    
    async def remove_content(self, content_id: str) -> bool:
        """
        Remove content from library.
        
        Args:
            content_id: Content ID
        
        Returns:
            True if removed
        """
        async with self._lock:
            if content_id in self._content:
                del self._content[content_id]
            else:
                return False
        
        # Save
        await self._save_library()
        
        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.CONTENT_REMOVED,
            data={'content_id': content_id},
            source='ContentManager'
        ))
        
        logger.info(f"Removed content: {content_id}")
        return True
    
    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """
        Get content by ID.
        
        Args:
            content_id: Content ID
        
        Returns:
            ContentItem or None
        """
        return self._content.get(content_id)
    
    def get_all_content(self) -> List[ContentItem]:
        """Get all content items."""
        return list(self._content.values())
    
    def search_content(
        self,
        content_type: Optional[ContentType] = None,
        tags: Optional[List[str]] = None,
        title_contains: Optional[str] = None,
        validated_only: bool = False
    ) -> List[ContentItem]:
        """
        Search content with filters.
        
        Args:
            content_type: Filter by type
            tags: Filter by tags (any match)
            title_contains: Filter by title substring
            validated_only: Only validated content
        
        Returns:
            List of matching ContentItems
        """
        results = list(self._content.values())
        
        # Filter by type
        if content_type:
            results = [c for c in results if c.content_type == content_type]
        
        # Filter by tags
        if tags:
            results = [c for c in results if any(t in c.metadata.tags for t in tags)]
        
        # Filter by title
        if title_contains:
            query = title_contains.lower()
            results = [c for c in results if query in c.metadata.title.lower()]
        
        # Filter validated
        if validated_only:
            results = [c for c in results if c.is_valid()]
        
        return results
    
    def get_content_by_type(self, content_type: ContentType) -> List[ContentItem]:
        """Get all content of specific type."""
        return [c for c in self._content.values() if c.content_type == content_type]
    
    def _load_library(self):
        """Load content library from storage."""
        if not self._storage_path.exists():
            logger.info("No existing library found, starting fresh")
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize content items
            for content_dict in data.get('content', []):
                content_item = ContentItem.from_dict(content_dict)
                self._content[content_item.content_id] = content_item
            
            logger.info(f"Loaded {len(self._content)} content items from library")
            
        except Exception as e:
            logger.error(f"Error loading library: {e}", exc_info=True)
    
    async def _save_library(self):
        """Save content library to storage."""
        try:
            # Serialize content items
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'content': [c.to_dict() for c in self._content.values()]
            }
            
            # Write to file
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved library ({len(self._content)} items)")
            
        except Exception as e:
            logger.error(f"Error saving library: {e}", exc_info=True)
    
    def _guess_mime_type(self, file_path: str) -> str:
        """Guess MIME type from file extension."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def get_stats(self) -> Dict[str, Any]:
        """Get content library statistics."""
        total = len(self._content)
        by_type = {}
        validated = 0
        
        for content in self._content.values():
            # Count by type
            type_name = content.content_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            # Count validated
            if content.is_valid():
                validated += 1
        
        return {
            'total_content': total,
            'by_type': by_type,
            'validated': validated,
            'pending_validation': total - validated
        }

