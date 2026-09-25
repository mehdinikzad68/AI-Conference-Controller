"""
Media Worker Thread

QThread worker for loading and processing media files in background.
Prevents UI freezing during media operations.
"""

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage
import logging
from pathlib import Path
from typing import Optional
import time

logger = logging.getLogger(__name__)


class MediaLoadWorker(QThread):
    """
    Worker thread for loading media files.
    
    Loads images, PDFs, and other media in background thread
    to prevent UI blocking during file operations.
    
    Signals:
        media_loaded: Emitted when media is loaded (file_path, pixmap, metadata)
        progress_updated: Emitted with loading progress (0-100)
        error_occurred: Emitted when an error occurs
        loading_started: Emitted when loading starts
        loading_finished: Emitted when loading finishes
    """
    
    media_loaded = pyqtSignal(str, QPixmap, dict)  # path, pixmap, metadata
    progress_updated = pyqtSignal(int)  # 0-100
    error_occurred = pyqtSignal(str, str)  # file_path, error_message
    loading_started = pyqtSignal(str)  # file_path
    loading_finished = pyqtSignal()
    
    def __init__(self):
        """Initialize media load worker."""
        super().__init__()
        
        self._file_path: Optional[str] = None
        self._mutex = QMutex()
        self._cancelled = False
    
    def load_media(self, file_path: str):
        """
        Set media file to load.
        
        Args:
            file_path: Path to media file
        """
        with QMutexLocker(self._mutex):
            self._file_path = file_path
            self._cancelled = False
    
    def run(self):
        """Main thread execution loop."""
        with QMutexLocker(self._mutex):
            file_path = self._file_path
            if not file_path:
                return
        
        try:
            logger.info(f"Media Load Worker starting: {file_path}")
            self.loading_started.emit(file_path)
            
            path = Path(file_path)
            if not path.exists():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                self.error_occurred.emit(file_path, error_msg)
                return
            
            # Get file extension
            ext = path.suffix.lower()
            
            # Load based on file type
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                self._load_image(file_path)
            elif ext == '.pdf':
                self._load_pdf(file_path)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                self.error_occurred.emit(file_path, f"Unsupported file type: {ext}")
            
            self.loading_finished.emit()
            logger.info(f"Media Load Worker finished: {file_path}")
        
        except Exception as e:
            error_msg = f"Media loading error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(file_path, error_msg)
            self.loading_finished.emit()
    
    def _load_image(self, file_path: str):
        """
        Load image file.
        
        Args:
            file_path: Path to image file
        """
        self.progress_updated.emit(10)
        
        if self._check_cancelled():
            return
        
        # Load image
        pixmap = QPixmap(file_path)
        
        self.progress_updated.emit(50)
        
        if self._check_cancelled():
            return
        
        if pixmap.isNull():
            error_msg = f"Failed to load image: {file_path}"
            logger.error(error_msg)
            self.error_occurred.emit(file_path, error_msg)
            return
        
        # Compress large images
        max_dimension = 1920
        if pixmap.width() > max_dimension or pixmap.height() > max_dimension:
            logger.info(f"Scaling large image: {pixmap.width()}x{pixmap.height()}")
            pixmap = pixmap.scaled(
                max_dimension, max_dimension,
                aspectRatioMode=1,  # KeepAspectRatio
                transformMode=1  # SmoothTransformation
            )
        
        self.progress_updated.emit(90)
        
        if self._check_cancelled():
            return
        
        # Metadata
        metadata = {
            'type': 'image',
            'width': pixmap.width(),
            'height': pixmap.height(),
            'format': Path(file_path).suffix
        }
        
        self.progress_updated.emit(100)
        self.media_loaded.emit(file_path, pixmap, metadata)
    
    def _load_pdf(self, file_path: str):
        """
        Load PDF file (first page).
        
        Args:
            file_path: Path to PDF file
        """
        try:
            import fitz  # PyMuPDF
            
            self.progress_updated.emit(10)
            
            if self._check_cancelled():
                return
            
            # Open PDF
            doc = fitz.open(file_path)
            
            self.progress_updated.emit(30)
            
            if self._check_cancelled():
                doc.close()
                return
            
            if len(doc) == 0:
                error_msg = "PDF has no pages"
                logger.error(error_msg)
                self.error_occurred.emit(file_path, error_msg)
                doc.close()
                return
            
            # Render first page
            page = doc[0]
            mat = fitz.Matrix(2.0, 2.0)  # 200 DPI
            pix = page.get_pixmap(matrix=mat)
            
            self.progress_updated.emit(70)
            
            if self._check_cancelled():
                doc.close()
                return
            
            # Convert to QPixmap
            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(img)
            
            self.progress_updated.emit(90)
            
            # Metadata
            metadata = {
                'type': 'pdf',
                'page_count': len(doc),
                'current_page': 1,
                'width': pixmap.width(),
                'height': pixmap.height()
            }
            
            doc.close()
            
            self.progress_updated.emit(100)
            self.media_loaded.emit(file_path, pixmap, metadata)
        
        except ImportError:
            error_msg = "PyMuPDF not installed. Install with: pip install PyMuPDF"
            logger.error(error_msg)
            self.error_occurred.emit(file_path, error_msg)
        
        except Exception as e:
            error_msg = f"PDF loading error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(file_path, error_msg)
    
    def _check_cancelled(self) -> bool:
        """
        Check if operation was cancelled.
        
        Returns:
            True if cancelled
        """
        with QMutexLocker(self._mutex):
            return self._cancelled
    
    def cancel(self):
        """Cancel current operation."""
        with QMutexLocker(self._mutex):
            self._cancelled = True
        logger.info("Media loading cancelled")


class ThumbnailGeneratorWorker(QThread):
    """
    Worker thread for generating thumbnails.
    
    Generates thumbnails for media files in background.
    
    Signals:
        thumbnail_generated: Emitted when thumbnail is ready (file_path, thumbnail)
        progress_updated: Emitted with progress
        error_occurred: Emitted on error
    """
    
    thumbnail_generated = pyqtSignal(str, QPixmap)  # file_path, thumbnail
    progress_updated = pyqtSignal(int, int)  # current, total
    error_occurred = pyqtSignal(str, str)  # file_path, error
    all_finished = pyqtSignal()
    
    def __init__(self, thumbnail_size: int = 100):
        """
        Initialize thumbnail generator.
        
        Args:
            thumbnail_size: Size of thumbnails (square)
        """
        super().__init__()
        
        self._file_paths: list = []
        self._thumbnail_size = thumbnail_size
        self._mutex = QMutex()
        self._cancelled = False
    
    def set_files(self, file_paths: list):
        """
        Set files to generate thumbnails for.
        
        Args:
            file_paths: List of file paths
        """
        with QMutexLocker(self._mutex):
            self._file_paths = file_paths.copy()
            self._cancelled = False
    
    def run(self):
        """Generate thumbnails for all files."""
        with QMutexLocker(self._mutex):
            files = self._file_paths.copy()
        
        total = len(files)
        
        for i, file_path in enumerate(files):
            if self._check_cancelled():
                break
            
            try:
                # Generate thumbnail
                pixmap = QPixmap(file_path)
                
                if not pixmap.isNull():
                    # Scale to thumbnail size
                    thumbnail = pixmap.scaled(
                        self._thumbnail_size,
                        self._thumbnail_size,
                        aspectRatioMode=1,  # KeepAspectRatio
                        transformMode=1  # SmoothTransformation
                    )
                    
                    self.thumbnail_generated.emit(file_path, thumbnail)
                else:
                    logger.warning(f"Failed to generate thumbnail: {file_path}")
            
            except Exception as e:
                error_msg = f"Thumbnail generation error: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(file_path, error_msg)
            
            # Update progress
            self.progress_updated.emit(i + 1, total)
        
        self.all_finished.emit()
    
    def _check_cancelled(self) -> bool:
        """Check if cancelled."""
        with QMutexLocker(self._mutex):
            return self._cancelled
    
    def cancel(self):
        """Cancel generation."""
        with QMutexLocker(self._mutex):
            self._cancelled = True
        logger.info("Thumbnail generation cancelled")

