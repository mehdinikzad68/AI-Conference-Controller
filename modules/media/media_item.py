"""
Media Item Module

Represents a single media item (video, PDF, image) in the media library.
"""

from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import PyPDF2


class MediaItem(QObject):
    """
    Represents a single media file with metadata and thumbnail.
    
    Supports video (MP4), PDF, and image (JPG, PNG) files.
    """
    
    # Signals
    thumbnail_loaded = pyqtSignal(QPixmap)
    
    # Supported media types
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_PDF = "pdf"
    MEDIA_TYPE_PPT = "powerpoint"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_UNKNOWN = "unknown"
    
    def __init__(self, file_path: str):
        """
        Initialize media item.
        
        Args:
            file_path: Path to the media file
        """
        super().__init__()
        self._file_path = Path(file_path)
        self._media_type = self._detect_media_type()
        self._thumbnail = None
        self._metadata = {}
        
        # Load metadata
        self._load_metadata()
        
    def _detect_media_type(self) -> str:
        """Detect media type from file extension."""
        ext = self._file_path.suffix.lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return self.MEDIA_TYPE_VIDEO
        elif ext == '.pdf':
            return self.MEDIA_TYPE_PDF
        elif ext in ['.ppt', '.pptx']:
            return self.MEDIA_TYPE_PPT
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
            return self.MEDIA_TYPE_IMAGE
        else:
            return self.MEDIA_TYPE_UNKNOWN
    
    def _load_metadata(self):
        """Load metadata for the media file."""
        self._metadata = {
            'name': self._file_path.name,
            'path': str(self._file_path),
            'size': self._file_path.stat().st_size if self._file_path.exists() else 0,
            'type': self._media_type
        }
        
        if self._media_type == self.MEDIA_TYPE_PDF:
            try:
                with open(self._file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    self._metadata['page_count'] = len(pdf_reader.pages)
            except Exception:
                self._metadata['page_count'] = 0
        elif self._media_type == self.MEDIA_TYPE_PPT:
            try:
                # Try to get slide count using python-pptx
                from pptx import Presentation
                presentation = Presentation(self._file_path)
                self._metadata['slide_count'] = len(presentation.slides)
            except ImportError:
                self._metadata['slide_count'] = 0
            except Exception:
                self._metadata['slide_count'] = 0
                
    def generate_thumbnail(self, size=(200, 150)) -> QPixmap:
        """
        Generate thumbnail for the media item.
        
        Args:
            size: Thumbnail size (width, height)
            
        Returns:
            QPixmap thumbnail
        """
        if self._media_type == self.MEDIA_TYPE_IMAGE:
            try:
                img = Image.open(self._file_path)
                img.thumbnail(size, Image.Resampling.LANCZOS)
                qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGB888)
                if img.mode == 'RGBA':
                    qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)
                return QPixmap.fromImage(qimage)
            except Exception:
                pass
        elif self._media_type == self.MEDIA_TYPE_PDF:
            try:
                with open(self._file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    if len(pdf_reader.pages) > 0:
                        page = pdf_reader.pages[0]
                        # For PDF, create a simple placeholder
                        # In a full implementation, you'd render the first page
                        pixmap = QPixmap(size[0], size[1])
                        pixmap.fill()  # White background
                        return pixmap
            except Exception:
                pass
        elif self._media_type == self.MEDIA_TYPE_VIDEO:
            # For video, create a placeholder thumbnail
            # In a full implementation, extract frame using opencv
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill()  # Dark background for video
            return pixmap
        
        # Default placeholder
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill()
        return pixmap
    
    def get_file_path(self) -> str:
        """Get the file path."""
        return str(self._file_path)
    
    def get_media_type(self) -> str:
        """Get media type."""
        return self._media_type
    
    def get_name(self) -> str:
        """Get file name."""
        return self._metadata.get('name', 'Unknown')
    
    def get_metadata(self) -> dict:
        """Get metadata dictionary."""
        return self._metadata.copy()
    
    def exists(self) -> bool:
        """Check if file exists."""
        return self._file_path.exists()

