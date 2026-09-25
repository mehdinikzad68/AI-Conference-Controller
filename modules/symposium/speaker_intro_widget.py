"""
Speaker Introduction Widget

Widget for displaying speaker introduction slide before each session.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
from typing import Optional
from pathlib import Path

from .agenda_manager import SpeakerInfo


class SpeakerIntroWidget(QWidget):
    """
    Widget displaying speaker introduction slide.
    
    Features:
    - Speaker photo (optional)
    - Speaker name
    - Talk title
    - Duration/time allocation
    - Professional styling
    """
    
    def __init__(self, parent=None):
        """Initialize speaker intro widget."""
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI layout."""
        # Main layout (centered)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.addStretch()
        
        # Content container
        content_layout = QVBoxLayout()
        content_layout.setSpacing(25)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Speaker photo
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setFixedSize(200, 200)
        self.photo_label.setStyleSheet("""
            QLabel {
                border: 3px solid #4CAF50;
                border-radius: 100px;
                background-color: rgba(50, 50, 50, 200);
            }
        """)
        content_layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Speaker name
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #ffffff;
                padding: 15px;
            }
        """)
        content_layout.addWidget(self.name_label)
        
        # Organization (optional)
        self.org_label = QLabel()
        self.org_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.org_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #bbbbbb;
                padding: 5px;
                font-style: italic;
            }
        """)
        content_layout.addWidget(self.org_label)
        
        # Separator
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setFixedWidth(400)
        separator.setStyleSheet("background-color: #666666;")
        content_layout.addWidget(separator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Talk title
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                color: #ffffff;
                padding: 20px;
            }
        """)
        content_layout.addWidget(self.title_label)
        
        # Duration
        self.duration_label = QLabel()
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                padding: 15px;
            }
        """)
        content_layout.addWidget(self.duration_label)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
    
    def set_speaker_info(self, speaker_info: SpeakerInfo):
        """
        Set speaker information to display.
        
        Args:
            speaker_info: SpeakerInfo object
        """
        # Load photo if available
        if speaker_info.photo_path and Path(speaker_info.photo_path).exists():
            pixmap = QPixmap(speaker_info.photo_path)
            if not pixmap.isNull():
                # Scale to fit circular label
                scaled_pixmap = pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Center crop for circular display
                x = (scaled_pixmap.width() - 200) // 2
                y = (scaled_pixmap.height() - 200) // 2
                cropped = scaled_pixmap.copy(x, y, 200, 200)
                self.photo_label.setPixmap(cropped)
            else:
                self.photo_label.clear()
        else:
            self.photo_label.clear()
        
        # Set text
        self.name_label.setText(speaker_info.name)
        
        if speaker_info.organization:
            self.org_label.setText(speaker_info.organization)
            self.org_label.show()
        else:
            self.org_label.hide()
        
        self.title_label.setText(speaker_info.title)
        
        duration_text = f"{speaker_info.duration_minutes} minutes"
        self.duration_label.setText(duration_text)
    
    def clear(self):
        """Clear speaker information."""
        self.photo_label.clear()
        self.name_label.clear()
        self.org_label.clear()
        self.title_label.clear()
        self.duration_label.clear()

