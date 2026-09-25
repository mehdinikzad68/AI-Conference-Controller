"""
Agenda Display Widget

Widget for displaying the full symposium agenda in a clean, branded layout.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter
from typing import Optional
from pathlib import Path

from .agenda_manager import AgendaManager


class AgendaDisplayWidget(QWidget):
    """
    Widget displaying full symposium agenda.
    
    Features:
    - Clean, readable layout
    - Symposium branding (logo, title, date, location)
    - Session list with times and speakers
    - Professional styling
    """
    
    def __init__(self, agenda_manager: AgendaManager, parent=None):
        """
        Initialize agenda display widget.
        
        Args:
            agenda_manager: AgendaManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._agenda_manager = agenda_manager
        self._logo_pixmap: Optional[QPixmap] = None
        
        self.setup_ui()
        self.load_agenda_data()
    
    def setup_ui(self):
        """Setup UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Scroll area for long agendas
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section (logo, title, date, location)
        header_layout = self.create_header_section()
        content_layout.addLayout(header_layout)
        
        # Agenda items section
        self.agenda_items_layout = QVBoxLayout()
        self.agenda_items_layout.setSpacing(15)
        content_layout.addLayout(self.agenda_items_layout)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def create_header_section(self) -> QVBoxLayout:
        """Create header section with logo and symposium info."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumHeight(120)
        self.logo_label.setMaximumHeight(200)
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.logo_label)
        
        # Symposium title
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        # Date and location
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #cccccc;
                padding: 5px;
            }
        """)
        header_layout.addWidget(self.info_label)
        
        # Separator line
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #666666;")
        header_layout.addWidget(separator)
        
        # "Agenda" heading
        agenda_heading = QLabel("AGENDA")
        agenda_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        agenda_heading.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                padding: 15px;
            }
        """)
        header_layout.addWidget(agenda_heading)
        
        return header_layout
    
    def create_agenda_item_widget(self, item) -> QWidget:
        """Create widget for a single agenda item."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setSpacing(20)
        item_layout.setContentsMargins(15, 15, 15, 15)
        
        # Styling
        item_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(50, 50, 50, 200);
                border-radius: 8px;
                border: 1px solid rgba(100, 100, 100, 150);
            }
        """)
        
        # Time column
        time_label = QLabel(item.start_time)
        time_label.setFixedWidth(80)
        time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        time_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4CAF50;
            }
        """)
        item_layout.addWidget(time_label)
        
        # Speaker and title column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        speaker_label = QLabel(item.speaker.name)
        speaker_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        info_layout.addWidget(speaker_label)
        
        title_label = QLabel(item.speaker.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #cccccc;
            }
        """)
        info_layout.addWidget(title_label)
        
        if item.speaker.organization:
            org_label = QLabel(item.speaker.organization)
            org_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #999999;
                    font-style: italic;
                }
            """)
            info_layout.addWidget(org_label)
        
        item_layout.addLayout(info_layout, stretch=1)
        
        # Duration column
        duration_label = QLabel(f"{item.speaker.duration_minutes} min")
        duration_label.setFixedWidth(60)
        duration_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duration_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #bbbbbb;
            }
        """)
        item_layout.addWidget(duration_label)
        
        return item_widget
    
    def load_agenda_data(self):
        """Load and display agenda data."""
        # Load logo
        logo_path = self._agenda_manager.get_logo_path()
        if logo_path and Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Scale logo to fit
                scaled_pixmap = pixmap.scaled(
                    200, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled_pixmap)
        
        # Load symposium info
        title = self._agenda_manager.get_symposium_title()
        date = self._agenda_manager.get_symposium_date()
        location = self._agenda_manager.get_symposium_location()
        
        self.title_label.setText(title)
        
        info_parts = []
        if date:
            info_parts.append(date)
        if location:
            info_parts.append(location)
        self.info_label.setText(" | ".join(info_parts) if info_parts else "")
        
        # Clear existing agenda items
        while self.agenda_items_layout.count():
            item = self.agenda_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load agenda items
        agenda_items = self._agenda_manager.get_agenda_items()
        for item in agenda_items:
            item_widget = self.create_agenda_item_widget(item)
            self.agenda_items_layout.addWidget(item_widget)
    
    def refresh(self):
        """Refresh agenda display."""
        self.load_agenda_data()

