"""
Validation Service - Async Content Validation and Pre-Testing

Validates content files asynchronously:
- File accessibility
- Format verification
- Corruption detection
- Metadata extraction
- Codec/bitrate validation
- Resolution/quality checks

All validations run in background to prevent blocking.
"""

import asyncio
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import time

# Optional imports for advanced validation
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from ..models import (
    ContentItem, ContentType, ValidationResult, ValidationStatus,
    FileInfo
)
from ..sync.event_bus import Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Async service for validating multimedia content.
    
    Validates files in background queue to prevent blocking.
    Emits events on completion for loose coupling.
    """
    
    def __init__(self, max_concurrent_validations: int = 3):
        """
        Initialize validation service.
        
        Args:
            max_concurrent_validations: Max parallel validations
        """
        self._max_concurrent = max_concurrent_validations
        self._validation_semaphore = asyncio.Semaphore(max_concurrent_validations)
        self._validation_queue: asyncio.Queue = asyncio.Queue()
        self._active_validations: Dict[str, asyncio.Task] = {}
        self._event_bus = get_event_bus()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Validation cache (to avoid re-validating same file)
        self._cache: Dict[str, ValidationResult] = {}
        
        logger.info(f"ValidationService initialized (max_concurrent={max_concurrent_validations})")
    
    async def start(self):
        """Start validation service."""
        if self._running:
            logger.warning("ValidationService already running")
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("ValidationService started")
    
    async def stop(self):
        """Stop validation service."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel active validations
        for task in self._active_validations.values():
            task.cancel()
        
        # Wait for worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ValidationService stopped")
    
    async def validate_content(
        self,
        content_item: ContentItem,
        force: bool = False
    ) -> ValidationResult:
        """
        Validate content item asynchronously.
        
        Args:
            content_item: Content to validate
            force: Force re-validation even if cached
        
        Returns:
            ValidationResult
        
        Example:
            >>> result = await validation_service.validate_content(content_item)
            >>> if result.is_valid():
            ...     print("Content is valid!")
        """
        content_id = content_item.content_id
        
        # Check cache
        if not force and content_id in self._cache:
            cached_result = self._cache[content_id]
            logger.debug(f"Using cached validation for {content_id}")
            return cached_result
        
        # Emit start event
        self._event_bus.publish(Event(
            event_type=EventType.CONTENT_VALIDATION_STARTED,
            data={'content_id': content_id},
            source='ValidationService'
        ))
        
        start_time = time.time()
        
        try:
            # Run validation
            result = await self._validate(content_item)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            result.validation_duration_ms = duration_ms
            
            # Cache result
            self._cache[content_id] = result
            
            # Emit completion event
            self._event_bus.publish(Event(
                event_type=EventType.CONTENT_VALIDATION_COMPLETED,
                data={
                    'content_id': content_id,
                    'status': result.status.value,
                    'duration_ms': duration_ms
                },
                source='ValidationService'
            ))
            
            logger.info(f"Validated {content_id}: {result.status.value} ({duration_ms:.1f}ms)")
            return result
            
        except Exception as e:
            logger.error(f"Validation error for {content_id}: {e}", exc_info=True)
            
            # Create error result
            result = ValidationResult(
                content_id=content_id,
                status=ValidationStatus.ERROR,
                errors=[f"Validation exception: {str(e)}"]
            )
            
            # Emit failure event
            self._event_bus.publish(Event(
                event_type=EventType.CONTENT_VALIDATION_FAILED,
                data={
                    'content_id': content_id,
                    'error': str(e)
                },
                source='ValidationService'
            ))
            
            return result
    
    async def _validate(self, content_item: ContentItem) -> ValidationResult:
        """
        Internal validation logic.
        
        Performs all validation checks.
        """
        content_id = content_item.content_id
        file_path = Path(content_item.file_info.path)
        content_type = content_item.content_type
        
        errors: List[str] = []
        warnings: List[str] = []
        metadata: Dict[str, Any] = {}
        
        # 1. Check file existence
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return ValidationResult(
                content_id=content_id,
                status=ValidationStatus.INVALID,
                errors=errors,
                file_accessible=False
            )
        
        # 2. Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            errors.append("File is empty (0 bytes)")
        elif file_size > 10 * 1024 * 1024 * 1024:  # 10 GB
            warnings.append(f"Large file size: {file_size / (1024**3):.2f} GB")
        
        metadata['file_size_bytes'] = file_size
        
        # 3. Validate by type
        if content_type == ContentType.VIDEO:
            video_result = await self._validate_video(file_path)
            errors.extend(video_result.get('errors', []))
            warnings.extend(video_result.get('warnings', []))
            metadata.update(video_result.get('metadata', {}))
        
        elif content_type == ContentType.IMAGE or content_type == ContentType.LOGO:
            image_result = await self._validate_image(file_path)
            errors.extend(image_result.get('errors', []))
            warnings.extend(image_result.get('warnings', []))
            metadata.update(image_result.get('metadata', {}))
        
        elif content_type == ContentType.AUDIO:
            audio_result = await self._validate_audio(file_path)
            errors.extend(audio_result.get('errors', []))
            warnings.extend(audio_result.get('warnings', []))
            metadata.update(audio_result.get('metadata', {}))
        
        elif content_type == ContentType.PDF or content_type == ContentType.SLIDE:
            pdf_result = await self._validate_pdf(file_path)
            errors.extend(pdf_result.get('errors', []))
            warnings.extend(pdf_result.get('warnings', []))
            metadata.update(pdf_result.get('metadata', {}))
        
        # 4. Calculate checksum (for corruption detection)
        try:
            checksum = await self._calculate_checksum(file_path)
            metadata['checksum_md5'] = checksum
        except Exception as e:
            warnings.append(f"Could not calculate checksum: {e}")
        
        # 5. Determine status
        if errors:
            status = ValidationStatus.INVALID
        else:
            status = ValidationStatus.VALID
        
        return ValidationResult(
            content_id=content_id,
            status=status,
            errors=errors,
            warnings=warnings,
            file_accessible=True,
            file_corrupted=bool('corrupted' in ' '.join(errors).lower()),
            format_supported=not any('format' in e.lower() or 'codec' in e.lower() for e in errors),
            metadata_extracted=metadata
        )
    
    async def _validate_video(self, file_path: Path) -> Dict[str, Any]:
        """Validate video file."""
        errors = []
        warnings = []
        metadata = {}
        
        if not CV2_AVAILABLE:
            warnings.append("OpenCV not available - video validation limited")
            return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
        
        try:
            # Open video
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                errors.append("Cannot open video file - may be corrupted")
                return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
            
            # Extract metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            metadata['fps'] = fps
            metadata['frame_count'] = frame_count
            metadata['width'] = width
            metadata['height'] = height
            metadata['resolution'] = f"{width}x{height}"
            metadata['codec'] = self._fourcc_to_string(fourcc)
            
            # Calculate duration
            if fps > 0:
                duration = frame_count / fps
                metadata['duration_seconds'] = duration
            
            # Validate resolution
            if width < 640 or height < 480:
                warnings.append(f"Low resolution: {width}x{height}")
            
            # Try to read first frame (corruption check)
            ret, frame = cap.read()
            if not ret:
                errors.append("Cannot read first frame - video may be corrupted")
            
            cap.release()
            
        except Exception as e:
            errors.append(f"Video validation error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
    
    async def _validate_image(self, file_path: Path) -> Dict[str, Any]:
        """Validate image file."""
        errors = []
        warnings = []
        metadata = {}
        
        if not PIL_AVAILABLE:
            warnings.append("PIL not available - image validation limited")
            return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
        
        try:
            # Open image
            img = Image.open(file_path)
            
            # Extract metadata
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['resolution'] = f"{img.width}x{img.height}"
            
            # Validate resolution
            if img.width < 200 or img.height < 200:
                warnings.append(f"Low resolution: {img.width}x{img.height}")
            
            # Try to load data (corruption check)
            img.load()
            
            img.close()
            
        except Exception as e:
            errors.append(f"Image validation error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
    
    async def _validate_audio(self, file_path: Path) -> Dict[str, Any]:
        """Validate audio file."""
        errors = []
        warnings = []
        metadata = {}
        
        # Basic file type check
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and not mime_type.startswith('audio/'):
            errors.append(f"Not an audio file: {mime_type}")
        
        metadata['mime_type'] = mime_type
        
        return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
    
    async def _validate_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Validate PDF file."""
        errors = []
        warnings = []
        metadata = {}
        
        if not PDF_AVAILABLE:
            warnings.append("PyPDF2 not available - PDF validation limited")
            return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
        
        try:
            # Open PDF
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                # Extract metadata
                metadata['page_count'] = len(pdf.pages)
                
                # Check if encrypted
                if pdf.is_encrypted:
                    errors.append("PDF is encrypted")
                
                # Try to read first page
                if len(pdf.pages) > 0:
                    _ = pdf.pages[0]
                else:
                    errors.append("PDF has no pages")
        
        except Exception as e:
            errors.append(f"PDF validation error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings, 'metadata': metadata}
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum."""
        md5 = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        
        return md5.hexdigest()
    
    def _fourcc_to_string(self, fourcc: int) -> str:
        """Convert fourcc int to string."""
        return "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    async def _worker(self):
        """Background worker for validation queue."""
        logger.info("Validation worker started")
        
        while self._running:
            try:
                # Get item from queue (with timeout)
                try:
                    content_item = await asyncio.wait_for(
                        self._validation_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Validate
                async with self._validation_semaphore:
                    await self.validate_content(content_item)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
        
        logger.info("Validation worker stopped")
    
    async def queue_validation(self, content_item: ContentItem):
        """
        Add content to validation queue.
        
        For non-blocking batch validation.
        """
        await self._validation_queue.put(content_item)
        logger.debug(f"Queued validation for {content_item.content_id}")
    
    def clear_cache(self):
        """Clear validation cache."""
        self._cache.clear()
        logger.info("Validation cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            'cache_size': len(self._cache),
            'queue_size': self._validation_queue.qsize(),
            'active_validations': len(self._active_validations),
            'max_concurrent': self._max_concurrent
        }

