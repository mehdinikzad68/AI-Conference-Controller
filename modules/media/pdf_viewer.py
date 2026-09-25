"""
PDF Viewer Module

High-quality PDF rendering component using PyMuPDF (fitz) for fast, 
high-resolution PDF page display optimized for projectors and OBS Studio.
"""

from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import Optional, List
import io

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    try:
        from pdf2image import convert_from_path
        from PIL import Image as PILImage
        PDF2IMAGE_AVAILABLE = True
    except ImportError:
        PDF2IMAGE_AVAILABLE = False


class PDFViewer:
    """
    High-quality PDF viewer using PyMuPDF (primary) or pdf2image (fallback).
    
    Provides fast, high-resolution PDF page rendering optimized for:
    - Projector displays (1080p, 4K)
    - OBS Studio window capture
    - Smooth page navigation
    - High DPI scaling
    """
    
    def __init__(self, pdf_path: str, dpi: int = 200):
        """
        Initialize PDF viewer.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for rendering (default 200, use 300 for high quality)
        """
        self._pdf_path = Path(pdf_path)
        self._dpi = dpi
        self._document = None
        self._page_count = 0
        self._current_page_index = 0
        self._use_pymupdf = PYMUPDF_AVAILABLE
        
        # Load PDF
        self._load_pdf()
        
    def _load_pdf(self):
        """Load PDF document using available library."""
        if not self._pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self._pdf_path}")
        
        if self._use_pymupdf:
            try:
                self._document = fitz.open(str(self._pdf_path))
                self._page_count = len(self._document)
            except Exception as e:
                raise RuntimeError(f"Failed to open PDF with PyMuPDF: {e}")
        elif PDF2IMAGE_AVAILABLE:
            # Use pdf2image for page count
            try:
                from pdf2image import convert_from_path
                # Just get page count, don't convert all pages yet
                # We'll use PyPDF2 for this
                import PyPDF2
                with open(self._pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    self._page_count = len(reader.pages)
            except Exception as e:
                raise RuntimeError(f"Failed to open PDF: {e}")
        else:
            raise RuntimeError(
                "No PDF rendering library available. Please install PyMuPDF:\n"
                "pip install PyMuPDF\n"
                "Or install pdf2image (requires poppler-utils):\n"
                "pip install pdf2image"
            )
    
    def is_valid(self) -> bool:
        """Check if PDF is loaded and valid."""
        if self._use_pymupdf:
            return self._document is not None and not self._document.is_closed
        else:
            return self._page_count > 0
    
    def get_page_count(self) -> int:
        """Get total number of pages in PDF."""
        return self._page_count
    
    def get_current_page_index(self) -> int:
        """Get current page index (0-based)."""
        return self._current_page_index
    
    def get_current_page_number(self) -> int:
        """Get current page number (1-based, user-facing)."""
        return self._current_page_index + 1
    
    def set_page(self, page_index: int) -> bool:
        """
        Set current page.
        
        Args:
            page_index: Page index (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= page_index < self._page_count:
            self._current_page_index = page_index
            return True
        return False
    
    def get_current_page(self) -> Optional[QPixmap]:
        """
        Get current page as QPixmap.
        
        Returns:
            QPixmap of current page, or None if error
        """
        return self.get_page(self._current_page_index)
    
    def get_page(self, page_index: int) -> Optional[QPixmap]:
        """
        Get specific page as QPixmap.
        
        Args:
            page_index: Page index (0-based)
            
        Returns:
            QPixmap of page, or None if error
        """
        if not self.is_valid() or not (0 <= page_index < self._page_count):
            return None
        
        try:
            if self._use_pymupdf:
                return self._render_page_pymupdf(page_index)
            else:
                return self._render_page_pdf2image(page_index)
        except Exception as e:
            print(f"Error rendering PDF page {page_index}: {e}")
            return None
    
    def _render_page_pymupdf(self, page_index: int) -> QPixmap:
        """
        Render page using PyMuPDF (fast and high quality).
        
        Args:
            page_index: Page index to render
            
        Returns:
            QPixmap of rendered page
        """
        page = self._document[page_index]
        
        # Calculate zoom factor based on DPI
        # PyMuPDF uses 72 DPI as base, so 200 DPI = 200/72 ≈ 2.78
        zoom = self._dpi / 72.0
        
        # Get page as pixmap
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to QImage then QPixmap
        img_data = pix.tobytes("ppm")
        qimage = QImage.fromData(img_data)
        
        if qimage.isNull():
            # Fallback: convert via PIL
            from PIL import Image
            import numpy as np
            
            # Convert pixmap to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # Convert to numpy array
            img_array = np.array(img)
            # Create QImage from numpy array
            height, width, channel = img_array.shape
            bytes_per_line = 3 * width
            qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        return QPixmap.fromImage(qimage)
    
    def _render_page_pdf2image(self, page_index: int) -> QPixmap:
        """
        Render page using pdf2image (slower fallback).
        
        Args:
            page_index: Page index to render
            
        Returns:
            QPixmap of rendered page
        """
        from pdf2image import convert_from_path
        from PIL import Image as PILImage
        
        # Convert specific page
        images = convert_from_path(
            str(self._pdf_path),
            dpi=self._dpi,
            first_page=page_index + 1,
            last_page=page_index + 1
        )
        
        if not images:
            return None
        
        pil_image = images[0]
        
        # Convert PIL Image to QPixmap
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Load as QImage
        qimage = QImage.fromData(img_bytes.read())
        
        return QPixmap.fromImage(qimage)
    
    def next_page(self) -> bool:
        """Navigate to next page."""
        if self._current_page_index < self._page_count - 1:
            self._current_page_index += 1
            return True
        return False
    
    def previous_page(self) -> bool:
        """Navigate to previous page."""
        if self._current_page_index > 0:
            self._current_page_index -= 1
            return True
        return False
    
    def go_to_page(self, page_number: int) -> bool:
        """
        Navigate to specific page number (1-based).
        
        Args:
            page_number: Page number (1-based, user-facing)
            
        Returns:
            True if successful
        """
        return self.set_page(page_number - 1)
    
    def close(self):
        """Close PDF document and free resources."""
        if self._use_pymupdf and self._document:
            self._document.close()
            self._document = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
