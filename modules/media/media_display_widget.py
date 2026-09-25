"""
Media Display Widget Module

Custom widget for displaying media content (videos, PDFs, images) with
animated transitions and aspect ratio preservation.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsBlurEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QSize, QPoint
from PyQt6.QtGui import QPainter, QPixmap, QImage, QColor, QPen, QBrush, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QVideoSink
from PyQt6.QtMultimediaWidgets import QVideoWidget
from pathlib import Path
from PIL import Image
import PyPDF2

from .pdf_viewer import PDFViewer
from typing import Optional
from modules.utils.memory_utils import downscale_image, optimize_pixmap, release_memory, clear_old_media


class MediaDisplayWidget(QWidget):
    """
    Widget for displaying media content with transitions and aspect ratio preservation.
    
    Supports:
    - Video playback
    - PDF page display
    - Image display
    - Animated transitions
    """
    
    TRANSITION_NONE = "none"
    TRANSITION_FADE = "fade"
    TRANSITION_SLIDE = "slide"
    TRANSITION_BLUR = "blur"
    
    def __init__(self, parent=None):
        """Initialize the media display widget."""
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: #000000;")
        
        # Make responsive
        from PyQt6.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(False)
        self.setSizePolicy(size_policy)
        
        # Current media
        self._current_media_path = None
        self._current_media_type = None
        self._current_pixmap = None
        self._current_pdf_page = 0
        self._pdf_pages = []
        self._pdf_viewer: Optional[PDFViewer] = None
        
        # Video player
        self._video_player = None
        self._video_widget = None
        
        # Transition properties
        self._opacity = 1.0
        self._transition_type = self.TRANSITION_FADE
        self._transition_animation = None
        self._transition_duration = 150  # Default duration in ms (for slide/blur)
        
        # Slide transition properties
        self._slide_offset = QPoint(0, 0)
        self._slide_direction = "right"  # right, left, up, down
        
        # Blur transition properties
        self._blur_effect = None
        self._blur_radius = 0.0
        
        # Previous content for transitions (for slide effect)
        self._previous_pixmap = None
        self._previous_pixmap_pos = QPoint(0, 0)
        
        # Display properties
        self._keep_aspect_ratio = True
        self._scale_mode = Qt.AspectRatioMode.KeepAspectRatio
        
    def load_media(self, media_path: str, transition: str = TRANSITION_FADE):
        """
        Load and display media.
        
        Args:
            media_path: Path to media file
            transition: Transition type (none, fade, slide, blur)
        """
        path = Path(media_path)
        if not path.exists():
            return False
        
        # Store previous content for slide transition BEFORE loading new content
        if transition == self.TRANSITION_SLIDE:
            if self._current_pixmap and not self._current_pixmap.isNull():
                self._previous_pixmap = QPixmap(self._current_pixmap)
            else:
                self._previous_pixmap = None
        
        # Set transition type before loading
        if transition in [self.TRANSITION_NONE, self.TRANSITION_FADE, 
                         self.TRANSITION_SLIDE, self.TRANSITION_BLUR]:
            self._transition_type = transition
        else:
            self._transition_type = self.TRANSITION_FADE
        media_type = self._detect_media_type(path)
        
        if media_type == "video":
            return self._load_video(str(path))
        elif media_type == "pdf":
            return self._load_pdf(str(path))
        elif media_type == "powerpoint":
            return self._load_powerpoint(str(path))
        elif media_type == "image":
            return self._load_image(str(path))
        
        return False
    
    def _detect_media_type(self, path: Path) -> str:
        """Detect media type from file extension."""
        ext = path.suffix.lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return "video"
        elif ext == '.pdf':
            return "pdf"
        elif ext in ['.ppt', '.pptx']:
            return "powerpoint"
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
            return "image"
        return "unknown"
    
    def _load_video(self, video_path: str) -> bool:
        """Load and display video."""
        try:
            # Clear PDF if present
            if self._pdf_viewer:
                self._pdf_viewer.close()
                self._pdf_viewer = None
                self._pdf_pages = []
                self._current_pixmap = None
            
            # Clear previous video
            if self._video_widget:
                self._video_widget.setParent(None)
                self._video_widget.deleteLater()
            
            # Create video player
            self._video_player = QMediaPlayer(self)
            self._video_sink = QVideoSink()
            self._video_player.setVideoSink(self._video_sink)
            
            # Create video widget
            self._video_widget = QVideoWidget(self)
            self._video_widget.setStyleSheet("background-color: #000000;")
            self._video_player.setVideoOutput(self._video_widget)
            
            # Load video
            from PyQt6.QtCore import QUrl
            self._video_player.setSource(QUrl.fromLocalFile(video_path))
            
            # Resize video widget to fit
            self._resize_video_widget()
            
            self._current_media_path = video_path
            self._current_media_type = "video"
            self._current_pixmap = None
            
            # Apply transition
            self._apply_transition()
            
            return True
        except Exception as e:
            print(f"Error loading video: {e}")
            return False
    
    def _load_image(self, image_path: str) -> bool:
        """Load and display image with memory optimization."""
        try:
            # Clear old media to free memory
            old_pixmap = self._current_pixmap
            clear_old_media(old_pixmap)
            
            # Clear PDF if present
            if self._pdf_viewer:
                try:
                    self._pdf_viewer.close()
                except:
                    pass
                self._pdf_viewer = None
                self._pdf_pages = []
                self._current_pdf_page = 0
            
            # Clear video if present
            if self._video_player:
                try:
                    self._video_player.stop()
                except:
                    pass
                self._video_player = None
            
            if self._video_widget:
                try:
                    self._video_widget.setParent(None)
                    self._video_widget.hide()
                    self._video_widget.deleteLater()
                except:
                    pass
                self._video_widget = None
            
            # Load image
            img = Image.open(image_path)
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Optimize: Downscale large images to reduce RAM usage
            w, h = img.size
            max_dim = 1920  # Maximum dimension for display (1080p or 4K safe)
            if max(w, h) > max_dim:
                scale = max_dim / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGB888)
            self._current_pixmap = optimize_pixmap(QPixmap.fromImage(qimage), max_dim=1920)
            
            # Clear PIL image from memory
            del img
            release_memory(force=False)
            
            self._current_media_path = image_path
            self._current_media_type = "image"
            
            # Apply transition
            self._apply_transition()
            self.update()  # Trigger repaint
            
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def _load_pdf(self, pdf_path: str) -> bool:
        """Load PDF and display first page using PDFViewer (lazy loading)."""
        try:
            # Clear old media to free memory
            old_pixmap = self._current_pixmap
            clear_old_media(old_pixmap)
            
            # Clear video if present
            if self._video_widget:
                self._video_widget.setParent(None)
                self._video_widget.deleteLater()
                self._video_widget = None
            if self._video_player:
                self._video_player.stop()
                self._video_player = None
            
            # Load PDF using PDFViewer (lazy - only loads metadata initially)
            self._pdf_viewer = PDFViewer(pdf_path, dpi=200)
            
            if not self._pdf_viewer.is_valid():
                raise RuntimeError("PDF viewer failed to load PDF")
            
            # Get page count (doesn't load all pages - lazy)
            self._pdf_pages = list(range(self._pdf_viewer.get_page_count()))
            self._current_pdf_page = 0
            
            # Get first page pixmap (only loads first page - lazy loading)
            first_page = self._pdf_viewer.get_current_page()
            if first_page and not first_page.isNull():
                self._current_pixmap = optimize_pixmap(first_page, max_dim=1920)
            else:
                raise RuntimeError("Failed to render first PDF page")
            
            self._current_media_path = pdf_path
            self._current_media_type = "pdf"
            
            # Apply transition
            self._apply_transition()
            self.update()
            
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            # Clean up on error
            if self._pdf_viewer:
                self._pdf_viewer.close()
            self._pdf_viewer = None
            self._pdf_pages = []
            return False
    
    def _load_powerpoint(self, ppt_path: str) -> bool:
        """Load PowerPoint file and display first slide."""
        try:
            # Clear old media to free memory
            old_pixmap = self._current_pixmap
            clear_old_media(old_pixmap)
            
            # Clear video if present
            if self._video_widget:
                self._video_widget.setParent(None)
                self._video_widget.deleteLater()
                self._video_widget = None
            if self._video_player:
                self._video_player.stop()
                self._video_player = None
            
            # Try to use win32com (Windows only) to convert PPT to image
            try:
                import win32com.client
                import pythoncom
                import tempfile
                import os
                
                # Initialize COM
                pythoncom.CoInitialize()
                
                # Create PowerPoint COM object
                ppt_app = win32com.client.Dispatch("PowerPoint.Application")
                ppt_app.Visible = 1  # Set to 1 for visible, 0 for hidden
                
                # Open presentation
                abs_path = os.path.abspath(ppt_path)
                presentation = ppt_app.Presentations.Open(abs_path, WithWindow=False)
                
                # Export first slide as PNG
                slide = presentation.Slides[1]  # 1-based index
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # Export slide as PNG (1920x1080 for standard resolution)
                slide.Export(temp_path, "PNG", 1920, 1080)  # Width, Height in pixels
                
                # Close presentation and quit app
                presentation.Close()
                ppt_app.Quit()
                pythoncom.CoUninitialize()
                
                # Load the exported PNG as pixmap
                pixmap = QPixmap(temp_path)
                if not pixmap.isNull():
                    self._current_pixmap = optimize_pixmap(pixmap, max_dim=1920)
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                else:
                    raise RuntimeError("Failed to load exported slide image")
                
            except ImportError:
                # Fallback: Try python-pptx (limited support, can only read structure)
                try:
                    from pptx import Presentation
                    # Note: python-pptx cannot render slides directly
                    # This is a placeholder - in production, use win32com or convert to PDF first
                    print("Warning: python-pptx cannot render slides. Install pywin32 for Windows PowerPoint support.")
                    print("On Windows: pip install pywin32")
                    
                    # Create placeholder
                    self._current_pixmap = QPixmap(1920, 1080)
                    self._current_pixmap.fill(QColor(240, 240, 240))
                    painter = QPainter(self._current_pixmap)
                    painter.setPen(QColor(0, 0, 0))
                    font = QFont()
                    font.setPointSize(24)
                    painter.setFont(font)
                    painter.drawText(
                        self._current_pixmap.rect(),
                        Qt.AlignmentFlag.AlignCenter,
                        "PowerPoint file loaded\n\nFor slide rendering on Windows:\nInstall pywin32:\npip install pywin32"
                    )
                    painter.end()
                except ImportError:
                    print("Error: No PowerPoint library available. Install pywin32 for Windows:")
                    print("pip install pywin32")
                    return False
            except Exception as e:
                print(f"Error loading PowerPoint: {e}")
                import traceback
                traceback.print_exc()
                # Create error placeholder
                self._current_pixmap = QPixmap(1920, 1080)
                self._current_pixmap.fill(QColor(240, 240, 240))
                painter = QPainter(self._current_pixmap)
                painter.setPen(QColor(255, 0, 0))
                font = QFont()
                font.setPointSize(20)
                painter.setFont(font)
                painter.drawText(
                    self._current_pixmap.rect(),
                    Qt.AlignmentFlag.AlignCenter,
                    f"Error loading PowerPoint file:\n{str(e)}"
                )
                painter.end()
            
            self._current_media_path = ppt_path
            self._current_media_type = "powerpoint"
            
            # Apply transition
            self._apply_transition()
            self.update()
            
            return True
        except Exception as e:
            print(f"Error loading PowerPoint: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_transition(self):
        """Apply animated transition effect."""
        if self._transition_type == self.TRANSITION_NONE:
            self._opacity = 1.0
            self._slide_offset = QPoint(0, 0)
            self._remove_blur_effect()
            self.update()
            return
        
        # Stop any existing animation
        if self._transition_animation:
            self._transition_animation.stop()
        
        if self._transition_type == self.TRANSITION_FADE:
            self._apply_fade_transition()
        elif self._transition_type == self.TRANSITION_SLIDE:
            self._apply_slide_transition()
        elif self._transition_type == self.TRANSITION_BLUR:
            self._apply_blur_transition()
    
    def _apply_fade_transition(self):
        """Apply fade transition effect."""
        self._opacity = 0.0
        self._transition_animation = QPropertyAnimation(self, b"opacity")
        self._transition_animation.setDuration(300)  # 300ms for fade
        self._transition_animation.setStartValue(0.0)
        self._transition_animation.setEndValue(1.0)
        self._transition_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._transition_animation.start()
    
    def _apply_slide_transition(self):
        """Apply slide transition effect."""
        # Previous content should already be stored in load_media
        # Determine slide direction (right is default, slides in from right)
        self._slide_direction = "right"
        
        # Set initial position (new content starts off-screen to the right)
        widget_width = max(self.width(), 100)  # Ensure we have a width
        if self._slide_direction == "right":
            self._slide_offset = QPoint(widget_width, 0)
        elif self._slide_direction == "left":
            self._slide_offset = QPoint(-widget_width, 0)
        elif self._slide_direction == "down":
            widget_height = max(self.height(), 100)
            self._slide_offset = QPoint(0, -widget_height)
        else:  # up
            widget_height = max(self.height(), 100)
            self._slide_offset = QPoint(0, widget_height)
        
        # Animate to center position (0, 0)
        self._transition_animation = QPropertyAnimation(self, b"slideOffset")
        self._transition_animation.setDuration(self._transition_duration)
        self._transition_animation.setStartValue(self._slide_offset)
        self._transition_animation.setEndValue(QPoint(0, 0))
        self._transition_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition_animation.finished.connect(self._clear_previous_pixmap)
        self._transition_animation.start()
    
    def _clear_previous_pixmap(self):
        """Clear previous pixmap after slide transition completes."""
        self._previous_pixmap = None
        self._previous_pixmap_pos = QPoint(0, 0)
    
    def _apply_blur_transition(self):
        """Apply blur transition effect."""
        # Apply blur effect to widget
        if not self._blur_effect:
            self._blur_effect = QGraphicsBlurEffect(self)
            self.setGraphicsEffect(self._blur_effect)
        
        # Animate blur: start blurred, then clear
        self._blur_radius = 20.0  # Start with strong blur
        self._blur_effect.setBlurRadius(self._blur_radius)
        
        # Also fade in for smoother effect
        self._opacity = 0.7
        
        # Animate blur radius down to 0
        self._transition_animation = QPropertyAnimation(self, b"blurRadius")
        self._transition_animation.setDuration(self._transition_duration)
        self._transition_animation.setStartValue(20.0)
        self._transition_animation.setEndValue(0.0)
        self._transition_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._transition_animation.finished.connect(self._remove_blur_effect)
        self._transition_animation.start()
        
        # Parallel fade-in
        fade_animation = QPropertyAnimation(self, b"opacity")
        fade_animation.setDuration(self._transition_duration)
        fade_animation.setStartValue(0.7)
        fade_animation.setEndValue(1.0)
        fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        fade_animation.start()
    
    def _remove_blur_effect(self):
        """Remove blur effect after transition."""
        if self._blur_effect:
            self.setGraphicsEffect(None)
            self._blur_effect = None
        self._blur_radius = 0.0
        self._opacity = 1.0
    
    def get_slide_offset(self) -> QPoint:
        """Get slide offset (for animation)."""
        return self._slide_offset
    
    def set_slide_offset(self, offset: QPoint):
        """Set slide offset (for animation)."""
        self._slide_offset = offset
        self.update()
    
    slideOffset = pyqtProperty(QPoint, get_slide_offset, set_slide_offset)
    
    def get_blur_radius(self) -> float:
        """Get blur radius (for animation)."""
        return self._blur_radius
    
    def set_blur_radius(self, radius: float):
        """Set blur radius (for animation)."""
        self._blur_radius = max(0.0, radius)
        if self._blur_effect:
            self._blur_effect.setBlurRadius(self._blur_radius)
        self.update()
    
    blurRadius = pyqtProperty(float, get_blur_radius, set_blur_radius)
    
    def set_transition_type(self, transition_type: str):
        """
        Set transition type.
        
        Args:
            transition_type: Transition type (none, fade, slide, blur)
        """
        if transition_type in [self.TRANSITION_NONE, self.TRANSITION_FADE, 
                               self.TRANSITION_SLIDE, self.TRANSITION_BLUR]:
            self._transition_type = transition_type
    
    def set_transition_duration(self, duration_ms: int):
        """
        Set transition duration.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        self._transition_duration = max(50, min(1000, duration_ms))  # Clamp 50-1000ms
    
    def get_opacity(self) -> float:
        """Get opacity value (for animation)."""
        return self._opacity
    
    def set_opacity(self, opacity: float):
        """Set opacity value (for animation)."""
        self._opacity = max(0.0, min(1.0, opacity))
        self.update()
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def _resize_video_widget(self):
        """Resize video widget to fit while maintaining aspect ratio."""
        if not self._video_widget:
            return
        
        rect = self.rect()
        widget_size = self._calculate_display_size(rect)
        
        # Center the widget
        x = (rect.width() - widget_size.width()) // 2
        y = (rect.height() - widget_size.height()) // 2
        
        self._video_widget.setGeometry(x, y, widget_size.width(), widget_size.height())
        self._video_widget.show()
    
    def _calculate_display_size(self, container_rect: QRect) -> QSize:
        """
        Calculate display size maintaining aspect ratio.
        
        Args:
            container_rect: Container rectangle
            
        Returns:
            Calculated size
        """
        if not self._keep_aspect_ratio:
            return container_rect.size()
        
        container_size = container_rect.size()
        content_size = None
        
        if self._current_pixmap and not self._current_pixmap.isNull():
            content_size = self._current_pixmap.size()
        elif self._video_widget:
            # For video, use container size (video will scale)
            return container_size
        
        if not content_size:
            return container_size
        
        # Calculate scaling
        scale_w = container_size.width() / content_size.width()
        scale_h = container_size.height() / content_size.height()
        
        if self._scale_mode == Qt.AspectRatioMode.KeepAspectRatio:
            scale = min(scale_w, scale_h)
        elif self._scale_mode == Qt.AspectRatioMode.KeepAspectRatioByExpanding:
            scale = max(scale_w, scale_h)
        else:
            scale = 1.0
        
        return QSize(
            int(content_size.width() * scale),
            int(content_size.height() * scale)
        )
    
    def play_video(self):
        """Play video if video is loaded."""
        if self._video_player:
            self._video_player.play()
    
    def pause_video(self):
        """Pause video if video is loaded."""
        if self._video_player:
            self._video_player.pause()
    
    def stop_video(self):
        """Stop video if video is loaded."""
        if self._video_player:
            self._video_player.stop()
    
    def is_video_playing(self) -> bool:
        """Check if video is currently playing."""
        return (self._video_player and 
                self._video_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
    
    def next_pdf_page(self):
        """Navigate to next PDF page."""
        if self._current_media_type == "pdf" and self._pdf_viewer:
            if self._pdf_viewer.next_page():
                self._current_pdf_page = self._pdf_viewer.get_current_page_index()
                self._load_current_pdf_page()
    
    def previous_pdf_page(self):
        """Navigate to previous PDF page."""
        if self._current_media_type == "pdf" and self._pdf_viewer:
            if self._pdf_viewer.previous_page():
                self._current_pdf_page = self._pdf_viewer.get_current_page_index()
                self._load_current_pdf_page()
    
    def go_to_pdf_page(self, page_number: int):
        """
        Navigate to specific PDF page.
        
        Args:
            page_number: Page number (1-based)
        """
        if self._current_media_type == "pdf" and self._pdf_viewer:
            if self._pdf_viewer.go_to_page(page_number):
                self._current_pdf_page = self._pdf_viewer.get_current_page_index()
                self._load_current_pdf_page()
    
    def _load_current_pdf_page(self):
        """Load current PDF page into pixmap (lazy loading - only loads current page)."""
        if not self._pdf_viewer or not self._pdf_viewer.is_valid():
            return
        
        # Clear old page from memory
        old_pixmap = self._current_pixmap
        clear_old_media(old_pixmap)
        
        # Set current page in viewer
        if self._pdf_viewer.set_page(self._current_pdf_page):
            # Get page pixmap (lazy - only loads this page)
            page_pixmap = self._pdf_viewer.get_current_page()
            if page_pixmap and not page_pixmap.isNull():
                self._current_pixmap = optimize_pixmap(page_pixmap, max_dim=1920)
                self._apply_transition()
                self.update()
            else:
                # Fallback: create placeholder
                from PyQt6.QtGui import QColor, QPainter
                self._current_pixmap = QPixmap(800, 600)
                self._current_pixmap.fill(QColor(255, 255, 255))
                painter = QPainter(self._current_pixmap)
                painter.setPen(QColor(0, 0, 0))
                font = painter.font()
                font.setPointSize(24)
                painter.setFont(font)
                painter.drawText(
                    self._current_pixmap.rect(),
                    Qt.AlignmentFlag.AlignCenter,
                    f"Error loading PDF page {self._current_pdf_page + 1}"
                )
                painter.end()
                self.update()
        else:
            print(f"Warning: Invalid PDF page index {self._current_pdf_page}")
    
    def clear_display(self):
        """Clear all displayed media and reset widget state completely."""
        # Stop video if playing
        try:
            self.stop_video()
        except:
            pass
        
        # Clear PDF viewer
        if self._pdf_viewer:
            try:
                self._pdf_viewer.close()
            except:
                pass
            self._pdf_viewer = None
        
        self._pdf_pages = []
        self._current_pdf_page = 0
        
        # Clear PowerPoint slides if any
        # (Note: PPT slides are stored as pixmaps, so clearing pixmaps handles this)
        
        # Clear pixmaps
        if self._current_pixmap:
            clear_old_media(self._current_pixmap)
            self._current_pixmap = None
        if self._previous_pixmap:
            clear_old_media(self._previous_pixmap)
            self._previous_pixmap = None
        
        # Reset media info completely
        self._current_media_path = None
        self._current_media_type = None
        
        # Stop and clear video player
        if self._video_player:
            try:
                self._video_player.stop()
            except:
                pass
            self._video_player = None
        
        # Clear video widget (must be after stopping player)
        if self._video_widget:
            try:
                self._video_widget.setParent(None)
                self._video_widget.hide()
                self._video_widget.deleteLater()
            except:
                pass
            self._video_widget = None
        
        # Stop any ongoing transitions
        if self._transition_animation:
            try:
                self._transition_animation.stop()
                self._transition_animation = None
            except:
                pass
        
        # Reset transition state
        self._opacity = 1.0
        self._slide_offset = QPoint(0, 0)
        self._previous_pixmap_pos = QPoint(0, 0)
        
        # Clear blur effect
        if self._blur_effect:
            try:
                self.setGraphicsEffect(None)
            except:
                pass
            self._blur_effect = None
            self._blur_radius = 0.0
        
        # Force update to clear display
        self.update()
    
    def get_current_media_info(self) -> dict:
        """Get information about currently loaded media."""
        info = {
            'path': self._current_media_path,
            'type': self._current_media_type,
            'has_content': False
        }
        
        if self._current_media_type == "pdf" and self._pdf_viewer:
            info['page'] = self._pdf_viewer.get_current_page_number()
            info['total_pages'] = self._pdf_viewer.get_page_count()
            info['has_content'] = self._pdf_viewer.is_valid()
        elif self._current_pixmap and not self._current_pixmap.isNull():
            info['has_content'] = True
        
        return info
    
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        self._resize_video_widget()
        self.update()
    
    def paintEvent(self, event):
        """Paint the widget content."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # For slide transition, draw previous content sliding out
        if (self._transition_type == self.TRANSITION_SLIDE and 
            self._previous_pixmap and not self._previous_pixmap.isNull() and
            self._slide_offset != QPoint(0, 0)):
            
            # Calculate previous content position (sliding out)
            display_size = self._calculate_display_size(self.rect())
            base_x = (self.width() - display_size.width()) // 2
            base_y = (self.height() - display_size.height()) // 2
            
            # Old content slides out opposite direction (left)
            if self._slide_direction == "right":
                prev_offset = QPoint(-self._slide_offset.x(), 0)
            elif self._slide_direction == "left":
                prev_offset = QPoint(-self._slide_offset.x(), 0)
            else:  # up/down
                prev_offset = QPoint(0, -self._slide_offset.y())
            
            prev_pos = QPoint(base_x + prev_offset.x(), base_y + prev_offset.y())
            prev_rect = QRect(prev_pos, display_size)
            
            scaled_prev = self._previous_pixmap.scaled(
                display_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(prev_rect, scaled_prev)
        
        # Apply opacity for transitions (fade, blur)
        painter.setOpacity(self._opacity)
        
        # Draw current content
        if self._current_pixmap and not self._current_pixmap.isNull():
            # Calculate display size
            display_size = self._calculate_display_size(self.rect())
            
            # Apply slide offset (for slide transition)
            base_x = (self.width() - display_size.width()) // 2
            base_y = (self.height() - display_size.height()) // 2
            display_rect = QRect(
                base_x + self._slide_offset.x(),
                base_y + self._slide_offset.y(),
                display_size.width(),
                display_size.height()
            )
            
            # Draw pixmap scaled
            scaled_pixmap = self._current_pixmap.scaled(
                display_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(display_rect, scaled_pixmap)
        
        # Video is handled by video widget (already visible if playing)
    
    def close(self):
        """Clean up resources on close."""
        # Release media resources
        if self._pdf_viewer:
            self._pdf_viewer.close()
            self._pdf_viewer = None
        
        if self._video_player:
            self._video_player.stop()
            self._video_player = None
        
        if self._video_widget:
            self._video_widget.setParent(None)
            self._video_widget.deleteLater()
            self._video_widget = None
        
        # Clear pixmaps
        clear_old_media(self._current_pixmap)
        clear_old_media(self._previous_pixmap)
        self._current_pixmap = None
        self._previous_pixmap = None
        
        # Clear lists
        self._pdf_pages = []
        
        # Force garbage collection
        release_memory(force=True)
    
    def closeEvent(self, event):
        """Handle close event with resource cleanup."""
        self.close()
        super().closeEvent(event)

