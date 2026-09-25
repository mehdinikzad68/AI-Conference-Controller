"""
Memory Management Utilities

Functions for optimizing RAM usage through image compression, downscaling, and cleanup.
"""

import cv2
import numpy as np
import gc
from typing import Optional, Tuple
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from PIL import Image
import io


def downscale_image(image: np.ndarray, max_dim: int = 1080) -> np.ndarray:
    """
    Downscale image to reduce RAM consumption.
    
    Maintains aspect ratio while limiting maximum dimension.
    
    Args:
        image: Input image as numpy array (BGR format from OpenCV)
        max_dim: Maximum dimension (width or height) in pixels (default: 1080)
        
    Returns:
        Downscaled image as numpy array
    """
    if image is None or image.size == 0:
        return image
    
    h, w = image.shape[:2]
    
    # Calculate scale factor to fit within max_dim
    scale = min(max_dim / h, max_dim / w, 1.0)
    
    # Only downscale if necessary
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return image


def compress_image(
    image_path: str,
    max_dim: int = 1080,
    quality: int = 85,
    format: str = 'JPEG'
) -> Optional[bytes]:
    """
    Load and compress an image file to reduce memory footprint.
    
    Args:
        image_path: Path to image file
        max_dim: Maximum dimension in pixels (default: 1080)
        quality: JPEG quality 0-100 (default: 85)
        format: Output format 'JPEG' or 'PNG' (default: 'JPEG')
        
    Returns:
        Compressed image bytes, or None on error
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get dimensions
            w, h = img.size
            
            # Downscale if needed
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Compress to bytes
            output = io.BytesIO()
            img.save(output, format=format, quality=quality, optimize=True)
            return output.getvalue()
    except Exception as e:
        print(f"Error compressing image {image_path}: {e}")
        return None


def optimize_pixmap(pixmap: QPixmap, max_dim: int = 1080) -> QPixmap:
    """
    Optimize QPixmap by downscaling if too large.
    
    Args:
        pixmap: Input QPixmap
        max_dim: Maximum dimension in pixels
        
    Returns:
        Optimized QPixmap (may be same if already small enough)
    """
    if pixmap.isNull():
        return pixmap
    
    w = pixmap.width()
    h = pixmap.height()
    
    # Only optimize if larger than max_dim
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return pixmap.scaled(
            new_w, new_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    return pixmap


def release_memory(force: bool = False):
    """
    Release unused memory through garbage collection.
    
    Args:
        force: If True, force full garbage collection cycle
    """
    if force:
        # Force multiple collection cycles for thorough cleanup
        for _ in range(3):
            collected = gc.collect()
            if collected == 0:
                break
    else:
        gc.collect()


def clear_old_media(old_pixmap: Optional[QPixmap] = None):
    """
    Clear old media object to free memory.
    
    Args:
        old_pixmap: Old QPixmap to clear (optional)
    """
    if old_pixmap and not old_pixmap.isNull():
        # QPixmap will be automatically cleaned up when reference is removed
        del old_pixmap
    
    # Force garbage collection
    release_memory(force=False)

