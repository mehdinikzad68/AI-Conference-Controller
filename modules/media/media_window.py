"""
Media Window Module

Main window for media playback with drag-and-drop, file management,
playback controls, and OBS Studio optimization.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QCheckBox, QGroupBox,
    QSlider, QSizePolicy, QFrame, QScrollArea, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QFont, QIcon
from pathlib import Path
import sys

from .media_item import MediaItem
from .media_display_widget import MediaDisplayWidget
from .timer_overlay_widget import TimerOverlayWidget
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QScrollArea


class DragDropWidget(QWidget):
    """
    Widget that accepts drag-and-drop file operations.
    """
    
    files_dropped = pyqtSignal(list)  # Emits list of file paths
    
    def __init__(self, parent=None):
        """Initialize drag-and-drop widget."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            QWidget {
                border: 3px dashed #666666;
                border-radius: 10px;
                background-color: #2d2d2d;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("Drag & Drop Media Files Here\n(MP4, PDF, PPT, PPTX, JPG, PNG)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 12px; color: #cccccc;")
        layout.addWidget(label)
        
        button = QPushButton("Browse Files...")
        button.setMaximumWidth(200)
        button.clicked.connect(self.browse_files)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()
    
    def browse_files(self):
        """Open file browser dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.pdf *.jpg *.jpeg *.png *.bmp);;"
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;"
            "PDF Files (*.pdf);;"
            "Image Files (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;"
            "All Files (*.*)"
        )
        if files:
            self.files_dropped.emit(files)


class MediaThumbnailItem(QListWidgetItem):
    """List widget item with media thumbnail."""
    
    def __init__(self, media_item: MediaItem, parent=None):
        """Initialize thumbnail item."""
        super().__init__(parent)
        self.media_item = media_item
        
        # Set display text
        self.setText(media_item.get_name())
        
        # Generate thumbnail
        thumbnail = media_item.generate_thumbnail()
        if thumbnail:
            self.setIcon(QIcon(thumbnail))
        
        # Set tooltip
        metadata = media_item.get_metadata()
        tooltip = f"File: {media_item.get_name()}\n"
        tooltip += f"Type: {metadata.get('type', 'unknown')}\n"
        if metadata.get('type') == 'pdf':
            tooltip += f"Pages: {metadata.get('page_count', 0)}\n"
        tooltip += f"Size: {metadata.get('size', 0) / 1024:.1f} KB"
        self.setToolTip(tooltip)


class MediaWindow(QMainWindow):
    """
    Main media playback window with drag-and-drop, file management, and playback controls.
    
    Features:
    - Drag-and-drop file upload
    - File list with thumbnails
    - Video, PDF, and image playback
    - Animated transitions
    - Timer overlay integration
    - Fullscreen support
    - OBS Studio optimized
    """
    
    def __init__(self, parent=None, timer_controller=None):
        """
        Initialize the media window.
        
        Args:
            parent: Parent widget (typically MainWindow)
            timer_controller: Optional TimerController instance for overlay
        """
        super().__init__(parent)
        
        # Media library
        self._media_items = []  # List of MediaItem objects
        self._current_media_index = -1
        
        # Timer overlay
        self._timer_overlay_enabled = False
        self._timer_overlay_widget = None
        self._timer_controller = timer_controller  # Store for overlay creation
        
        # Transition settings
        self._current_transition = "fade"  # Will be converted to constant
        self._transition_duration = 150  # milliseconds
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller - Media Player")
        self.setMinimumSize(850, 600)
        self.resize(1200, 750)
        
        # Make responsive
        make_responsive(self)
        
        # Apply system theme
        self.apply_theme()
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        """Apply theme based on system settings."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for scrolling when menu is hidden."""
        central = self.centralWidget()
        if isinstance(central, QScrollArea):
            scrollbar = central.verticalScrollBar()
            if scrollbar.isVisible():
                delta = event.angleDelta().y()
                scrollbar.setValue(scrollbar.value() - delta // 8)
                event.accept()
                return
        event.ignore()
    
    def init_ui(self):
        """Initialize the user interface with scrollable support."""
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        central_widget = QWidget()
        make_responsive(central_widget)
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Left panel: File list and controls
        left_panel = self.create_left_panel()
        make_responsive(left_panel)
        main_layout.addWidget(left_panel, stretch=1)
        
        # Right panel: Media display
        right_panel = self.create_right_panel()
        make_responsive(right_panel)
        main_layout.addWidget(right_panel, stretch=3)
        
        # Menu bar
        self.setup_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready - Drag and drop media files to begin")
        
    def create_left_panel(self) -> QWidget:
        """Create left panel with file list and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Drag and drop area
        drag_drop = DragDropWidget()
        drag_drop.files_dropped.connect(self.add_media_files)
        layout.addWidget(drag_drop)
        
        # File list group
        file_group = QGroupBox("Media Library")
        file_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(300)
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.file_list.itemDoubleClicked.connect(self.on_file_activated)
        file_layout.addWidget(self.file_list)
        
        # File list buttons
        file_buttons = QHBoxLayout()
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_selected_file)
        remove_btn.setToolTip("Remove selected file from library")
        file_buttons.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_files)
        clear_btn.setToolTip("Remove all files from library")
        file_buttons.addWidget(clear_btn)
        file_layout.addLayout(file_buttons)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Playback controls group
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QVBoxLayout()
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_media)
        self.prev_btn.setToolTip("Go to previous media item")
        button_layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setToolTip("Play/Pause current media")
        button_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setToolTip("Stop playback")
        button_layout.addWidget(self.stop_btn)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_media)
        self.next_btn.setToolTip("Go to next media item")
        button_layout.addWidget(self.next_btn)
        
        controls_layout.addLayout(button_layout)
        
        # PDF navigation (for PDF files)
        pdf_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("◀ Previous Page")
        self.prev_page_btn.clicked.connect(self.previous_page)
        self.prev_page_btn.setToolTip("Navigate to previous PDF page (PDF only)")
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.setMinimumHeight(30)
        pdf_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("Page: - / -")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-size: 11px; font-weight: bold; padding: 0 12px;")
        pdf_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton("Next Page ▶")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setToolTip("Navigate to next PDF page (PDF only)")
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.setMinimumHeight(30)
        pdf_layout.addWidget(self.next_page_btn)
        
        controls_layout.addLayout(pdf_layout)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Timer overlay controls group
        overlay_group = QGroupBox("Timer Overlay")
        overlay_layout = QVBoxLayout()
        
        # Enable overlay checkbox
        self.timer_overlay_check = QCheckBox("Show Timer Overlay")
        self.timer_overlay_check.setToolTip("Display animated timer on top of media content")
        self.timer_overlay_check.toggled.connect(self.toggle_timer_overlay)
        overlay_layout.addWidget(self.timer_overlay_check)
        
        # Position selector
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        self.timer_position_combo = QComboBox()
        self.timer_position_combo.addItems([
            "Top Right", "Top Left", "Top Center", 
            "Bottom Right", "Bottom Left", "Center"
        ])
        self.timer_position_combo.setToolTip("Timer overlay position on screen")
        self.timer_position_combo.currentTextChanged.connect(self.change_overlay_position)
        self.timer_position_combo.setEnabled(False)
        position_layout.addWidget(self.timer_position_combo)
        overlay_layout.addLayout(position_layout)
        
        # Timer controls (when overlay is visible)
        timer_controls_layout = QHBoxLayout()
        
        self.timer_start_btn = QPushButton("Start Timer")
        self.timer_start_btn.clicked.connect(self.start_timer)
        self.timer_start_btn.setEnabled(False)
        self.timer_start_btn.setToolTip("Start the timer overlay")
        timer_controls_layout.addWidget(self.timer_start_btn)
        
        self.timer_pause_btn = QPushButton("Pause")
        self.timer_pause_btn.clicked.connect(self.pause_timer)
        self.timer_pause_btn.setEnabled(False)
        self.timer_pause_btn.setToolTip("Pause the timer")
        timer_controls_layout.addWidget(self.timer_pause_btn)
        
        self.timer_reset_btn = QPushButton("Reset")
        self.timer_reset_btn.clicked.connect(self.reset_timer)
        self.timer_reset_btn.setEnabled(False)
        self.timer_reset_btn.setToolTip("Reset timer to initial time")
        timer_controls_layout.addWidget(self.timer_reset_btn)
        
        overlay_layout.addLayout(timer_controls_layout)
        
        # Timer duration input
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (min):"))
        self.timer_duration_spin = QSpinBox()
        self.timer_duration_spin.setMinimum(1)
        self.timer_duration_spin.setMaximum(120)
        self.timer_duration_spin.setValue(5)
        self.timer_duration_spin.setToolTip("Timer duration in minutes")
        self.timer_duration_spin.setEnabled(False)
        duration_layout.addWidget(self.timer_duration_spin)
        overlay_layout.addLayout(duration_layout)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Transition effects group
        transition_group = QGroupBox("Transition Effects")
        transition_layout = QVBoxLayout()
        
        # Transition type selector
        transition_type_layout = QHBoxLayout()
        transition_type_layout.addWidget(QLabel("Effect:"))
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["Fade", "Slide", "Blur", "None"])
        self.transition_combo.setCurrentText("Fade")
        self.transition_combo.setToolTip("Transition effect when switching between media items")
        self.transition_combo.currentTextChanged.connect(self.on_transition_changed)
        transition_type_layout.addWidget(self.transition_combo)
        transition_layout.addLayout(transition_type_layout)
        
        # Transition duration (optional, for advanced users)
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Speed:"))
        self.transition_duration_spin = QSpinBox()
        self.transition_duration_spin.setMinimum(50)
        self.transition_duration_spin.setMaximum(1000)
        self.transition_duration_spin.setValue(150)
        self.transition_duration_spin.setSuffix(" ms")
        self.transition_duration_spin.setToolTip("Transition animation duration (lower = faster)")
        self.transition_duration_spin.valueChanged.connect(self.on_transition_duration_changed)
        duration_layout.addWidget(self.transition_duration_spin)
        transition_layout.addLayout(duration_layout)
        
        transition_group.setLayout(transition_layout)
        layout.addWidget(transition_group)
        
        # Fullscreen button
        fullscreen_btn = QPushButton("Toggle Fullscreen (F11)")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        fullscreen_btn.setToolTip("Enter fullscreen mode for projector display")
        layout.addWidget(fullscreen_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with media display."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Media display widget (container for overlay) - made responsive
        self.media_display = MediaDisplayWidget()
        make_responsive(self.media_display)
        self.media_display.setLayout(QVBoxLayout())
        self.media_display.layout().setContentsMargins(0, 0, 0, 0)
        
        # Note: Timer overlay will be added as child of media_display
        layout.addWidget(self.media_display)
        
        # Media info label
        self.media_info_label = QLabel("No media loaded")
        self.media_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_info_label.setStyleSheet("padding: 8px; font-size: 10px; color: #cccccc;")
        layout.addWidget(self.media_info_label)
        
        return panel
    
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_files_action = file_menu.addAction("Add Files...")
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.browse_and_add_files)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fullscreen_action = view_menu.addAction("Fullscreen")
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About Media Player")
        about_action.triggered.connect(self.show_about)
    
    def add_media_files(self, file_paths: list):
        """Add media files to the library."""
        added_count = 0
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    media_item = MediaItem(str(path))
                    self._media_items.append(media_item)
                    
                    # Add to list widget
                    list_item = MediaThumbnailItem(media_item, self.file_list)
                    self.file_list.addItem(list_item)
                    
                    added_count += 1
                except Exception as e:
                    print(f"Error adding file {file_path}: {e}")
        
        if added_count > 0:
            self.statusBar().showMessage(f"Added {added_count} file(s) to library", 3000)
            # Select first item if none selected
            if self._current_media_index == -1 and len(self._media_items) > 0:
                self.file_list.setCurrentRow(0)
                self.load_media_at_index(0)
    
    def browse_and_add_files(self):
        """Open file browser to add files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.pdf *.ppt *.pptx *.jpg *.jpeg *.png *.bmp);;"
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;"
            "PDF Files (*.pdf);;"
            "PowerPoint Files (*.ppt *.pptx);;"
            "Image Files (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;"
            "All Files (*.*)"
        )
        if files:
            self.add_media_files(files)
    
    def remove_selected_file(self):
        """Remove selected file from library."""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            # Remove from list
            item = self.file_list.takeItem(current_row)
            if item:
                # Remove from media items
                if current_row < len(self._media_items):
                    self._media_items.pop(current_row)
                
                # Update current index
                if current_row == self._current_media_index:
                    self._current_media_index = -1
                    self.media_display.clear_display()  # Clear all media display
                    self.media_info_label.setText("No media loaded")
                    # Clear PDF navigation buttons
                    self.prev_page_btn.setEnabled(False)
                    self.next_page_btn.setEnabled(False)
                    self.page_label.setText("Page: - / -")
                elif current_row < self._current_media_index:
                    self._current_media_index -= 1
                
                # Select new item if available
                if self.file_list.count() > 0:
                    if current_row >= self.file_list.count():
                        current_row = self.file_list.count() - 1
                    self.file_list.setCurrentRow(current_row)
                    self.load_media_at_index(current_row)
                else:
                    self.file_list.setCurrentRow(-1)
    
    def clear_all_files(self):
        """Clear all files from library."""
        reply = QMessageBox.question(
            self,
            "Clear All Files",
            "Are you sure you want to remove all files from the library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.file_list.clear()
            self._media_items.clear()
            self._current_media_index = -1
            self.media_display.clear_display()  # Clear all media display
            self.media_info_label.setText("No media loaded")
            # Clear PDF navigation buttons
            self.prev_page_btn.setEnabled(False)
            self.next_page_btn.setEnabled(False)
            self.page_label.setText("Page: - / -")
            self.statusBar().showMessage("All files cleared", 2000)
    
    def on_file_selected(self, item: QListWidgetItem):
        """Handle file selection from list."""
        row = self.file_list.row(item)
        self.load_media_at_index(row)
    
    def on_file_activated(self, item: QListWidgetItem):
        """Handle file double-click (activate/play)."""
        row = self.file_list.row(item)
        self.load_media_at_index(row)
        self.play_btn.click()  # Start playing
    
    def load_media_at_index(self, index: int):
        """Load media at specified index."""
        if 0 <= index < len(self._media_items):
            media_item = self._media_items[index]
            file_path = media_item.get_file_path()
            
            # Clear previous media display before loading new one (important for format switching)
            # This ensures clean state when switching between different media types
            self.media_display.clear_display()
            
            # Load in display widget with current transition
            if self.media_display.load_media(file_path, transition=self._current_transition):
                self._current_media_index = index
                
                # Update info label
                metadata = media_item.get_metadata()
                info_text = f"File: {media_item.get_name()}\n"
                info_text += f"Type: {metadata.get('type', 'unknown').upper()}"
                if metadata.get('type') == 'pdf':
                    info_text += f" | Pages: {metadata.get('page_count', 0)}"
                elif metadata.get('type') == 'powerpoint':
                    info_text += f" | Slides: {metadata.get('slide_count', 0)}"
                self.media_info_label.setText(info_text)
                
                # Update PDF navigation buttons (also for PowerPoint)
                is_pdf = metadata.get('type') == 'pdf'
                is_ppt = metadata.get('type') == 'powerpoint'
                self.prev_page_btn.setEnabled(is_pdf or is_ppt)  # Enable for PDF and PPT
                self.next_page_btn.setEnabled(is_pdf or is_ppt)
                if is_pdf:
                    info = self.media_display.get_current_media_info()
                    current_page = info.get('page', 1)
                    total_pages = info.get('total_pages', 1)
                    self.page_label.setText(f"Page: {current_page} / {total_pages}")
                    # Update button states based on page position
                    self.prev_page_btn.setEnabled(current_page > 1)
                    self.next_page_btn.setEnabled(current_page < total_pages)
                elif is_ppt:
                    # Handle PowerPoint slides
                    info = self.media_display.get_current_media_info()
                    current_slide = info.get('page', 1)
                    total_slides = info.get('total_pages', 1)
                    self.page_label.setText(f"Slide: {current_slide} / {total_slides}")
                    self.prev_page_btn.setEnabled(current_slide > 1)
                    self.next_page_btn.setEnabled(current_slide < total_slides)
                else:
                    self.page_label.setText("Page: - / -")
                
                # Update button states
                self.update_playback_buttons()
            else:
                # Loading failed - update index anyway to prevent navigation issues
                # But don't mark as current since load failed
                error_msg = f"Could not load media file:\n{file_path}\n\nFile may be corrupted or format not supported."
                QMessageBox.warning(self, "Error Loading Media", error_msg)
                
                # If this was the current index, clear it
                if self._current_media_index == index:
                    self._current_media_index = -1
                    self.media_info_label.setText("No media loaded")
                    self.update_playback_buttons()
    
    def toggle_playback(self):
        """Toggle play/pause for current media."""
        if self._current_media_index < 0:
            return
        
        media_item = self._media_items[self._current_media_index]
        media_type = media_item.get_media_type()
        
        if media_type == MediaItem.MEDIA_TYPE_VIDEO:
            if self.media_display.is_video_playing():
                self.media_display.pause_video()
                self.play_btn.setText("▶ Play")
            else:
                self.media_display.play_video()
                self.play_btn.setText("⏸ Pause")
        else:
            # For images and PDFs, "play" just means show
            self.play_btn.setText("▶ Play")
            self.statusBar().showMessage("Use Previous/Next to navigate", 2000)
    
    def stop_playback(self):
        """Stop playback."""
        self.media_display.stop_video()
        self.play_btn.setText("▶ Play")
        self.statusBar().showMessage("Playback stopped", 2000)
    
    def previous_media(self):
        """Go to previous media item."""
        if len(self._media_items) == 0:
            return
        
        # Handle case where current index is invalid (-1)
        if self._current_media_index < 0:
            # If no current index, start from last item
            if len(self._media_items) > 0:
                new_index = len(self._media_items) - 1
            else:
                return
        elif self._current_media_index > 0:
            new_index = self._current_media_index - 1
        else:
            new_index = len(self._media_items) - 1  # Wrap around
        
        # Try to load, skip to next if loading fails
        max_attempts = len(self._media_items)
        attempts = 0
        while attempts < max_attempts:
            self.file_list.setCurrentRow(new_index)
            self.load_media_at_index(new_index)
            
            # Check if load was successful
            if self._current_media_index == new_index:
                # Success - we're done
                break
            else:
                # Load failed - try previous item
                attempts += 1
                if new_index > 0:
                    new_index = new_index - 1
                else:
                    new_index = len(self._media_items) - 1
        
        # Update list selection to match current index
        if 0 <= self._current_media_index < len(self._media_items):
            self.file_list.setCurrentRow(self._current_media_index)
    
    def next_media(self):
        """Go to next media item."""
        if len(self._media_items) == 0:
            return
        
        # Handle case where current index is invalid (-1)
        if self._current_media_index < 0:
            # If no current index, start from first item
            if len(self._media_items) > 0:
                new_index = 0
            else:
                return
        elif self._current_media_index < len(self._media_items) - 1:
            new_index = self._current_media_index + 1
        else:
            new_index = 0  # Wrap around
        
        # Try to load, skip to next if loading fails
        max_attempts = len(self._media_items)
        attempts = 0
        while attempts < max_attempts:
            self.file_list.setCurrentRow(new_index)
            self.load_media_at_index(new_index)
            
            # Check if load was successful
            if self._current_media_index == new_index:
                # Success - we're done
                break
            else:
                # Load failed - try next item
                attempts += 1
                if new_index < len(self._media_items) - 1:
                    new_index = new_index + 1
                else:
                    new_index = 0
        
        # Update list selection to match current index
        if 0 <= self._current_media_index < len(self._media_items):
            self.file_list.setCurrentRow(self._current_media_index)
    
    def previous_page(self):
        """Go to previous PDF page."""
        self.media_display.previous_pdf_page()
        info = self.media_display.get_current_media_info()
        current_page = info.get('page', 1)
        total_pages = info.get('total_pages', 1)
        self.page_label.setText(f"Page: {current_page} / {total_pages}")
        # Update button states
        self.prev_page_btn.setEnabled(current_page > 1)
        self.next_page_btn.setEnabled(current_page < total_pages)
        self.statusBar().showMessage(f"PDF Page {current_page} of {total_pages}", 2000)
    
    def next_page(self):
        """Go to next PDF page."""
        self.media_display.next_pdf_page()
        info = self.media_display.get_current_media_info()
        current_page = info.get('page', 1)
        total_pages = info.get('total_pages', 1)
        self.page_label.setText(f"Page: {current_page} / {total_pages}")
        # Update button states
        self.prev_page_btn.setEnabled(current_page > 1)
        self.next_page_btn.setEnabled(current_page < total_pages)
        self.statusBar().showMessage(f"PDF Page {current_page} of {total_pages}", 2000)
    
    def update_playback_buttons(self):
        """Update playback button states."""
        has_media = self._current_media_index >= 0
        self.play_btn.setEnabled(has_media)
        self.stop_btn.setEnabled(has_media)
        self.prev_btn.setEnabled(len(self._media_items) > 1)
        self.next_btn.setEnabled(len(self._media_items) > 1)
    
    def toggle_timer_overlay(self, enabled: bool):
        """Toggle timer overlay on media content."""
        self._timer_overlay_enabled = enabled
        
        if enabled:
            # Create overlay if it doesn't exist
            if not self._timer_overlay_widget:
                # Try to get timer controller from parent (main window)
                timer_controller = None
                if self.parent():
                    try:
                        # Try to access parent's timer controller
                        parent = self.parent()
                        if hasattr(parent, 'timer_controller'):
                            timer_controller = parent.timer_controller
                    except:
                        pass
                
                # Create overlay widget as child of media display
                self._timer_overlay_widget = TimerOverlayWidget(
                    self.media_display,
                    timer_controller
                )
                # Set size
                self._timer_overlay_widget.setFixedSize(280, 310)
                
                # Set initial position
                position_map = {
                    "Top Right": TimerOverlayWidget.POSITION_TOP_RIGHT,
                    "Top Left": TimerOverlayWidget.POSITION_TOP_LEFT,
                    "Top Center": TimerOverlayWidget.POSITION_TOP_CENTER,
                    "Bottom Right": TimerOverlayWidget.POSITION_BOTTOM_RIGHT,
                    "Bottom Left": TimerOverlayWidget.POSITION_BOTTOM_LEFT,
                    "Center": TimerOverlayWidget.POSITION_CENTER
                }
                position = self.timer_position_combo.currentText()
                self._timer_overlay_widget.set_position(position_map.get(position, TimerOverlayWidget.POSITION_TOP_RIGHT))
                
                # Connect overlay signals
                self._timer_overlay_widget.overlay_closed.connect(lambda: self.timer_overlay_check.setChecked(False))
                
                # Store timer controller reference
                if timer_controller:
                    self._timer_controller = timer_controller
                else:
                    self._timer_controller = self._timer_overlay_widget.get_timer_controller()
            
            # Set timer duration
            if self._timer_overlay_widget:
                duration_seconds = self.timer_duration_spin.value() * 60
                self._timer_overlay_widget.set_timer_time(duration_seconds)
            
            # Show overlay with fade-in
            if self._timer_overlay_widget:
                self._timer_overlay_widget.show_overlay(fade_in=True, duration=300)
                self._timer_overlay_widget.raise_()
            
            # Enable controls
            self.timer_position_combo.setEnabled(True)
            self.timer_start_btn.setEnabled(True)
            self.timer_reset_btn.setEnabled(True)
            self.timer_duration_spin.setEnabled(True)
            
            self.statusBar().showMessage("Timer overlay enabled", 2000)
        else:
            # Hide overlay with fade-out
            if self._timer_overlay_widget:
                self._timer_overlay_widget.hide_overlay(fade_out=True, duration=300)
            
            # Disable controls
            self.timer_position_combo.setEnabled(False)
            self.timer_start_btn.setEnabled(False)
            self.timer_pause_btn.setEnabled(False)
            self.timer_reset_btn.setEnabled(False)
            self.timer_duration_spin.setEnabled(False)
            
            self.statusBar().showMessage("Timer overlay disabled", 2000)
    
    def change_overlay_position(self, position_text: str):
        """Change timer overlay position."""
        if not self._timer_overlay_widget:
            return
        
        position_map = {
            "Top Right": TimerOverlayWidget.POSITION_TOP_RIGHT,
            "Top Left": TimerOverlayWidget.POSITION_TOP_LEFT,
            "Top Center": TimerOverlayWidget.POSITION_TOP_CENTER,
            "Bottom Right": TimerOverlayWidget.POSITION_BOTTOM_RIGHT,
            "Bottom Left": TimerOverlayWidget.POSITION_BOTTOM_LEFT,
            "Center": TimerOverlayWidget.POSITION_CENTER
        }
        
        position = position_map.get(position_text, TimerOverlayWidget.POSITION_TOP_RIGHT)
        self._timer_overlay_widget.set_position(position)
    
    def start_timer(self):
        """Start the timer overlay."""
        if self._timer_overlay_widget:
            # Update duration before starting
            duration_seconds = self.timer_duration_spin.value() * 60
            self._timer_overlay_widget.set_timer_time(duration_seconds)
            self._timer_overlay_widget.start_timer()
            self.timer_start_btn.setEnabled(False)
            self.timer_pause_btn.setEnabled(True)
            self.timer_duration_spin.setEnabled(False)
            self.statusBar().showMessage("Timer started", 2000)
    
    def pause_timer(self):
        """Pause the timer overlay."""
        if self._timer_overlay_widget:
            self._timer_overlay_widget.pause_timer()
            self.timer_start_btn.setEnabled(False)
            self.timer_pause_btn.setEnabled(False)
            # Show resume button instead
            self.timer_pause_btn.setText("Resume")
            self.timer_pause_btn.clicked.disconnect()
            self.timer_pause_btn.clicked.connect(self.resume_timer)
            self.statusBar().showMessage("Timer paused", 2000)
    
    def resume_timer(self):
        """Resume the timer overlay."""
        if self._timer_overlay_widget:
            self._timer_overlay_widget.resume_timer()
            self.timer_pause_btn.setText("Pause")
            self.timer_pause_btn.clicked.disconnect()
            self.timer_pause_btn.clicked.connect(self.pause_timer)
            self.statusBar().showMessage("Timer resumed", 2000)
    
    def reset_timer(self):
        """Reset the timer overlay."""
        if self._timer_overlay_widget:
            self._timer_overlay_widget.reset_timer()
            duration_seconds = self.timer_duration_spin.value() * 60
            self._timer_overlay_widget.set_timer_time(duration_seconds)
            self.timer_start_btn.setEnabled(True)
            self.timer_pause_btn.setEnabled(False)
            self.timer_duration_spin.setEnabled(True)
            self.timer_pause_btn.setText("Pause")
            self.timer_pause_btn.clicked.disconnect()
            self.timer_pause_btn.clicked.connect(self.pause_timer)
            self.statusBar().showMessage("Timer reset", 2000)
    
    def on_transition_changed(self, transition_name: str):
        """Handle transition type change."""
        # Map UI names to widget constants
        transition_map = {
            "Fade": MediaDisplayWidget.TRANSITION_FADE,
            "Slide": MediaDisplayWidget.TRANSITION_SLIDE,
            "Blur": MediaDisplayWidget.TRANSITION_BLUR,
            "None": MediaDisplayWidget.TRANSITION_NONE
        }
        
        self._current_transition = transition_map.get(transition_name, MediaDisplayWidget.TRANSITION_FADE)
        self.media_display.set_transition_type(self._current_transition)
        
        # Update duration visibility (blur and slide can be slower)
        if transition_name == "Fade":
            self.transition_duration_spin.setValue(300)
        elif transition_name == "Slide":
            self.transition_duration_spin.setValue(150)
        elif transition_name == "Blur":
            self.transition_duration_spin.setValue(200)
        else:  # None
            self.transition_duration_spin.setValue(0)
        
        self.statusBar().showMessage(f"Transition effect: {transition_name}", 2000)
    
    def on_transition_duration_changed(self, duration_ms: int):
        """Handle transition duration change."""
        self._transition_duration = duration_ms
        self.media_display.set_transition_duration(duration_ms)
        self.statusBar().showMessage(f"Transition speed: {duration_ms}ms", 1500)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("Exited fullscreen mode")
        else:
            self.showFullScreen()
            self.statusBar().showMessage("Entered fullscreen mode - Press F11 to exit")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Media Player",
            "<h2>AI-Symp-Controller - Media Player</h2>"
            "<p><b>Version 1.0.0</b></p>"
            "<p>Advanced media playback module with:</p>"
            "<ul>"
            "<li>Video playback (MP4, AVI, MOV, MKV)</li>"
            "<li>PDF presentation support</li>"
            "<li>Image display (JPG, PNG, BMP)</li>"
            "<li>Drag-and-drop file upload</li>"
            "<li>Animated transitions</li>"
            "<li>Fullscreen mode for projectors</li>"
            "<li>OBS Studio optimized</li>"
            "</ul>"
            "<p>Optimized for Windows 11 and HP Envy x360</p>"
        )
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_media()
        elif event.key() == Qt.Key.Key_Right:
            self.next_media()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.media_display.stop_video()
        event.accept()

